## Why

The analysis benchmark standard (`tests/load/analysis_benchmark.py` + `tests/load/run_analysis_bench.ps1` + `tests/load/analysis_benchmarks.yaml`) is necessary but not sufficient for requirement sign-off. To know whether a given requirement is accepted, a reviewer has to hand-pick benchmark profiles, run them, manually AND the per-profile pass flags, and stitch summary files together. That is error-prone and makes sign-off a one-off act rather than a reproducible command.

This change introduces a thin requirement-acceptance layer on top of the existing benchmark: a canonical suite config, a reusable Python module that aggregates per-profile results, a single PowerShell entrypoint that runs the benchmark and finalizes the suite summary, and the suite-level summary artifacts (plus a run-meta) that make acceptance a one-command operation. The benchmark runner itself is untouched.

## What Changes

**Canonical suite config**
- From: no tracked mapping from requirement to benchmark profile; sign-off is ad-hoc.
- To: `tests/load/acceptance_suites.yaml` defines `id → description → list of benchmark profile ids`. Shipped suites cover the smoke check and the current large-log cluster scaling requirement.
- Reason: a version-tracked, requirement-shaped config is the smallest durable artifact that lets reviewers and agents answer "is this requirement accepted?" by name.
- Impact: non-breaking; only adds a new config file in the existing `tests/load/` layout.

**Suite aggregation module**
- From: no programmatic way to combine per-profile benchmark results into a single suite verdict.
- To: `tests/load/requirement_acceptance.py` loads suite configs, reads per-profile `summary.passed` from the benchmark output, ANDs them into a suite pass/fail, and renders both `acceptance-summary.json` and `acceptance-summary.md`. Exposes the same operations as subcommands (`suite-profiles`, `summarize`, `finalize`) for programmatic reuse.
- Reason: keeps the aggregation logic in one testable place and makes the same logic callable from CI without going through PowerShell.
- Impact: non-breaking; pure addition.

**Single PowerShell entrypoint**
- From: requirement sign-off is a multi-step manual procedure.
- To: `tests/load/run_requirement_acceptance.ps1` runs the canonical sequence: preflight `GET /health` → resolve suite profiles → prepare datasets → background process-stats collector → run `analysis_benchmark.py` for all suite profiles → call the Python finalizer → write `acceptance-run-meta.json` → exit with the finalizer's exit code.
- Reason: a single command removes the chance for a reviewer to skip the preflight or forget to write the run meta.
- Impact: non-breaking; pure addition. The existing `run_analysis_bench.ps1` is untouched.

**Suite-level summary and run-meta**
- From: no suite-level summary; the only per-profile summaries are scattered under `artifacts/{profile}-{runId}/`.
- To: per-run `tests/load/artifacts/acceptance-{runId}/acceptance-summary.json` and `.md` (only on benchmark success), plus an always-written `acceptance-run-meta.json` with both exit codes.
- Reason: the suite-level summary is the artifact a reviewer signs off on; the run meta keeps partial-failure runs inspectable.
- Impact: non-breaking; new artifacts under the existing gitignored `tests/load/artifacts/` tree.

**Hardened validation**
- From: `summary.passed` is read as-is; a string like `"false"` would be truthy.
- To: non-boolean `summary.passed` is rejected with `AcceptanceConfigError` and a non-zero exit code.
- Reason: closes a class of silent "passing suite" bugs at the lowest layer.
- Impact: non-breaking; the benchmark runner already emits booleans, so this only matters for malformed custom benchmark outputs.

**Tests and docs**
- From: no regression coverage for the aggregation logic; `tests/load/README.md` does not document a requirement-acceptance entrypoint.
- To: `tests/test_requirement_acceptance.py` covers load, summarize-aggregation, non-boolean rejection, finalize-on-failure, and the repo suite. `tests/load/README.md` documents the new entrypoint, the suite config, and the produced artifacts.
- Reason: regression coverage and discoverability for the new layer.
- Impact: non-breaking; pure addition.

## Capabilities

### New Capabilities
- `requirement-acceptance`: canonical suite config, suite-level aggregation, single PowerShell entrypoint, suite-level summary and run-meta artifacts, hardened boolean validation, and regression tests.

### Modified Capabilities
- None. The benchmark runner and the existing analysis-bench entrypoint are not changed.

## Affected Modules

- `tests/load/` — new files: `acceptance_suites.yaml`, `requirement_acceptance.py`, `run_requirement_acceptance.ps1`. Modified: `README.md`.
- `tests/` — new file: `test_requirement_acceptance.py`.
- Backend, frontend, casebase, retrieval, exporter: **no changes**.

## Storage Impact

- One new tracked config: `tests/load/acceptance_suites.yaml` (small, hand-maintained, version-tracked).
- One new tracked helper: `tests/load/requirement_acceptance.py` (small, no runtime state).
- One new tracked entrypoint: `tests/load/run_requirement_acceptance.ps1` (PowerShell).
- One new tracked test file: `tests/test_requirement_acceptance.py`.
- Per-run generated artifacts under `tests/load/artifacts/acceptance-{runId}/`: `{profile}.json`, `{profile}.md`, `acceptance-summary.json`, `acceptance-summary.md`, `acceptance-run-meta.json`, `process-stats.csv`. The `tests/load/artifacts/` directory is already treated as run-time output (gitignored via the existing `tests/load/` artifact rules), so no durable storage change.
- No new durable database, no new index, no new cache that needs invalidation.

## Constraints

- No mandatory database.
- No new benchmark profile definitions; this change only maps existing profiles to suites.
- The existing benchmark runner (`analysis_benchmark.py` and `analysis_benchmarks.yaml`) is not modified.
- The existing `run_analysis_bench.ps1` is not modified.
- All new tracked files use LF line endings and UTF-8 (PowerShell file has no BOM).
- Preflight, dataset preparation, and process-stats collection are reused as-is from the analysis-bench path; no new instrumentation in this change.

## Risks

- A future change to the benchmark's per-profile `summary.passed` contract could silently change suite semantics. Mitigation: the suite summary re-derives the verdict from the per-profile output, so any contract change is observable as a suite failure rather than a silent drift. The strict boolean check raises an explicit error if the contract is violated in a non-obvious way.
- The new PowerShell entrypoint mirrors the existing `run_analysis_bench.ps1`; if the two drift, operators get inconsistent preflight/collector behavior. Mitigation: preflight and collector invocation are intentionally identical; any future drift should be reconciled in a single follow-up change rather than carried as a hidden difference.
- The suite YAML is hand-maintained. A typo in a profile id would surface as a missing-profile-output error at finalize time, not at config load. Acceptable for a small config with one author and one consumer.

## Verification

- `uv run pytest tests/test_requirement_acceptance.py -q` must pass.
- A smoke run against a running backend must produce `acceptance-summary.json` and `acceptance-summary.md` with `passed: true` and `summary_written: true`, and `acceptance-run-meta.json` with `summary_generated: true` and `acceptance_passed: true`.
- A run with a forced per-profile failure (e.g., a profile whose `summary.passed` is `false`) must produce a suite FAIL row in the Markdown and `acceptance_passed: false` in the run meta, with `summary_written: true` (because the benchmark succeeded).
- A run with the backend down must exit with code 3 before any benchmark work, with no `acceptance-summary.*` files and `summary_generated: false` in the run meta.
- A run with a hand-edited `{profile}.json` whose `summary.passed` is the string `"false"` must fail with `AcceptanceConfigError` and a non-zero exit code.

## Impact

- `tests/load/`: new files (`acceptance_suites.yaml`, `requirement_acceptance.py`, `run_requirement_acceptance.ps1`) + `README.md` update.
- `tests/`: new file (`test_requirement_acceptance.py`).
- No backend, no frontend, no casebase, no retrieval, no exporter, no docs beyond `tests/load/README.md`.
- Out of scope (separate change): `thread_stack_bench.py`, `thread-stack-*-report.md`, `real_dump_sample*.txt`. Those belong to `add-thread-stack-bench` and will get their own SuperSpec cycle.
