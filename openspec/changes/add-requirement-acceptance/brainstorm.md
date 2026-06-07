## Context

DiagnoseToolPy already has a hardened analysis benchmark runner (`tests/load/analysis_benchmark.py` + `tests/load/run_analysis_bench.ps1`) and a documented profile system in `tests/load/analysis_benchmarks.yaml`. What it lacked was a way to answer the question "is this requirement accepted?" without hand-picking benchmark profiles per requirement and stitching the per-profile summary files together by eye. The current `current-state.md` lists "Requirement acceptance flow standardized" and "Requirement acceptance finalization hardened" as implemented, but the corresponding change has no proposal/spec/archive entry — only uncommitted files in the working tree. This change closes that gap.

The user's explicit framing for the change: "standardize requirement-level acceptance so the benchmark standard is necessary but not sufficient for sign-off; one command over the analysis benchmark produces a suite-level pass/fail plus the supporting evidence pointers."

## Goals

- A single canonical command, `tests/load/run_requirement_acceptance.ps1`, that takes a requirement-suite id, runs the underlying analysis benchmark, and produces a suite-level acceptance summary.
- A canonical, version-tracked config `tests/load/acceptance_suites.yaml` that maps `suite_id → list of benchmark profile ids`. No new profile definitions live here — only the mapping.
- A Python module `tests/load/requirement_acceptance.py` that loads suite configs, aggregates per-profile benchmark results into a single suite summary, renders Markdown, and finalizes artifacts. The module exposes the same operations as a CLI for CI / future reuse, but the PowerShell wrapper is the supported entrypoint for humans/agents.
- Deterministic summary artifacts: `acceptance-summary.json` (machine-readable) and `acceptance-summary.md` (human review). Both are written **only** when the benchmark run itself succeeds.
- A `acceptance-run-meta.json` that always records the benchmark exit code and the acceptance finalizer exit code, so partial failures are still inspectable.
- Hardened validation: non-boolean `summary.passed` values are rejected so a stray `"false"` string cannot be treated as a passing suite.

## Non-Goals

- Do not replace or re-architect `analysis_benchmark.py` or `analysis_benchmarks.yaml`. This change only adds an acceptance layer on top.
- Do not introduce a database or persistent acceptance ledger. Suite-level summaries are produced per run and live under `tests/load/artifacts/acceptance-{runId}/`.
- Do not redefine benchmark thresholds or profile semantics. The acceptance layer reads existing `summary.passed` values from the benchmark output.
- Do not change preflight, dataset preparation, or the process-stats collector. They are reused as-is from `run_analysis_bench.ps1`.
- Out of scope for this change: `tests/load/thread_stack_bench.py`, the two `real_dump_sample*.txt` fixtures, and `tests/load/thread-stack-{capability,load}-report.md`. Those belong to a separate `add-thread-stack-bench` change that will follow its own SuperSpec cycle.

## Approach Selection

Three approaches were considered:

- **A. Single PowerShell entrypoint only** — `run_requirement_acceptance.ps1` runs benchmark + writes summary inline. Easiest for one-shot use but couples the entrypoint to a specific benchmark and leaves no programmatic surface for CI.
- **B. Python-only CLI** — subcommands on `requirement_acceptance.py` (`suite-profiles`, `summarize`, `finalize`) and the operator orchestrates the steps. Reusable but every run requires manual orchestration.
- **C. PowerShell entrypoint + reusable Python CLI** *(chosen, matches existing project pattern)* — the PowerShell wrapper is the canonical command for agents/humans (mirrors `run_analysis_bench.ps1`), and the Python CLI is reusable inside CI, future automation, and any other pipeline that wants the same suite semantics. Two surfaces to keep in sync, but each surface is small and stable.

The existing uncommitted implementation is already approach C. No re-design needed; the change artifacts document what was built and the rationale so future contributors can extend it.

## Key Design Decisions

1. **Suite config is a separate YAML from `analysis_benchmarks.yaml`.** A requirement changes more often than a benchmark profile, and they answer different questions (one is "what should we measure for this requirement", the other is "what does the benchmark actually do"). Keeping them separate avoids accidental coupling.

2. **Suite-level pass = AND of per-profile `summary.passed`.** This matches the existing benchmark semantics: a profile's `summary.passed` is already the AND of its individual `checks`. Suite-level aggregation is the natural extension.

3. **Preflight `GET /health` before any benchmark work.** Same preflight pattern as `run_analysis_bench.ps1`. A missing backend fails fast with exit code 3 instead of producing a misleading acceptance failure later.

4. **Summary is only written on benchmark success.** When the benchmark itself fails, `acceptance-summary.{json,md}` are not produced. The `acceptance-run-meta.json` still records the failure with both exit codes so the run is fully auditable. This avoids publishing an authoritative-looking "FAIL" summary derived from a partially-run benchmark that never produced a clean profile output.

5. **Non-boolean `summary.passed` is a config error, not a soft pass.** The previous finalizer accepted the value as-is; a `"false"` string would have been treated as truthy. The hardened version rejects it explicitly so suite integrity cannot be accidentally weakened.

6. **Process-stats collector reused as-is.** No new instrumentation in this change. The same `tests/load/collect_process_stats.ps1` from the analysis bench path is started in the background and stopped on completion.

## Open Questions

- Should suite names be addressable from the URL/CLI in addition to the YAML id (e.g., a `--suite` flag vs. an env var)? Current implementation: `--suite` CLI arg, PowerShell parameter with default. No further action for this change.
- Should the acceptance summary be uploaded to a casebook or dashboard? Out of scope for this change — file artifacts only, consistent with the rest of the load/ test area.
