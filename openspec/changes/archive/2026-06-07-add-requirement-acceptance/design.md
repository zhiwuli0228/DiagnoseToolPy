## Context

DiagnoseToolPy's analysis benchmark layer produces per-profile artifacts (`{profile}.json`, `{profile}.md`, `process-stats.csv`, `run-meta.json`) under `tests/load/artifacts/{profile}-{runId}/`. What is missing is a requirement-level concept: a "suite" that names which profiles must pass together for one user-facing requirement to be considered accepted, plus a single command that produces a suite-level verdict. This change adds that layer on top of the existing benchmark infrastructure without touching the benchmark runner itself.

## Goals / Non-Goals

**Goals**
- One canonical PowerShell entrypoint: `tests/load/run_requirement_acceptance.ps1`.
- One canonical, version-tracked suite config: `tests/load/acceptance_suites.yaml`.
- A reusable Python module: `tests/load/requirement_acceptance.py` (load, summarize, finalize, render) with subcommands `suite-profiles` / `summarize` / `finalize`.
- Suite-level summary artifacts (`acceptance-summary.json` + `acceptance-summary.md`) generated only when the benchmark run succeeds.
- Always-written `acceptance-run-meta.json` with both exit codes.
- Strict validation of `summary.passed` (must be boolean).
- Regression tests in `tests/test_requirement_acceptance.py`.
- `tests/load/README.md` updated to document the new entrypoint.

**Non-Goals**
- No change to `analysis_benchmark.py` or `analysis_benchmarks.yaml`.
- No change to `run_analysis_bench.ps1` or its preflight logic.
- No casebase/dashboard upload; artifacts are files only.
- Out of scope (separate change): `thread_stack_bench.py`, `thread-stack-*-report.md`, `real_dump_sample*.txt`.
- No new benchmark profile definitions. The acceptance layer only maps suites to existing profiles.

## Decisions

### 1. Suite model: `id → list of profile ids`

`acceptance_suites.yaml` is a flat list of suites. Each suite has `id`, `description`, and `profiles` (a non-empty list of profile ids that must exist in `analysis_benchmarks.yaml`). The file is intentionally tiny and is tracked in the repository. The current change ships two suites:

- `smoke_acceptance` — minimal end-to-end check that the pipeline itself runs.
- `current_large_log_cluster_requirement` — the requirement for the current sign-off (smoke + heavy directory concurrency).

### 2. Suite pass = AND of per-profile `summary.passed`

The benchmark already returns `summary.passed` as a boolean AND of its `checks`. The acceptance layer reads that value as-is and ANDs across the suite's profiles. No new weighting, no thresholds, no profile ranking — just AND. This makes the suite semantics predictable and trivially auditable from the per-profile outputs.

### 3. Preflight `GET /health` before any benchmark work

The entrypoint reuses the same preflight pattern as `run_analysis_bench.ps1`: `Invoke-WebRequest -TimeoutSec 5` against `BaseUrl/health`. Failure exits with code 3 and a clear error message before any dataset preparation, collector start, or benchmark launch. This protects the run from being invalidated by a missing or restarting backend.

### 4. Summary only on benchmark success

`finalize_suite_run` returns early when the benchmark exit code is non-zero. The `acceptance-summary.{json,md}` files are not written. `acceptance-run-meta.json` is always written and includes both the benchmark exit code and the finalizer exit code, so the run is still inspectable. This prevents publishing a misleading "FAIL" suite summary derived from a benchmark that never produced a clean per-profile output.

### 5. Strict boolean `summary.passed`

`summarize_suite` requires each per-profile `summary.passed` to be a real `bool`. A string such as `"false"` raises `AcceptanceConfigError("summary.passed for profile '...' must be a boolean")`. This closes a class of "looks like a passing suite because truthy string" bugs that would otherwise be silent.

### 6. Process-stats collector reused as-is

`run_requirement_acceptance.ps1` starts `collect_process_stats.ps1` in the background with the same arguments used by the analysis-bench entrypoint. The collector is stopped in a `finally` block using a `.collector-stop` sentinel file plus `Stop-Process` if needed. No new instrumentation.

### 7. Suite config is a separate file from the benchmark config

`acceptance_suites.yaml` and `analysis_benchmarks.yaml` answer different questions and have different lifecycles. Keeping them separate avoids accidental coupling and lets a requirement evolve (add a profile, drop a profile) without touching the benchmark's profile semantics.

## Architecture

```text
  +---------------------------------------+
  | run_requirement_acceptance.ps1        |
  |  - preflight GET /health              |
  |  - resolve suite profiles             |
  |  - prepare datasets                   |
  |  - start process-stats collector      |
  |  - run analysis_benchmark.py          |
  |  - stop collector                     |
  |  - call requirement_acceptance.py     |
  |    finalize (or skip on failure)      |
  |  - write acceptance-run-meta.json     |
  +---------------------------------------+
                  |
                  v
  +---------------------------------------+
  | requirement_acceptance.py             |
  |  load_suites / get_suite              |
  |  summarize_suite                      |
  |  finalize_suite_run                   |
  |  render_markdown                      |
  +---------------------------------------+
                  |
                  v
  +---------------------------------------+
  | acceptance_suites.yaml                |
  |  (tracked; id + description +        |
  |   profiles[])                         |
  +---------------------------------------+

Output artifacts under tests/load/artifacts/acceptance-{runId}/:
  - {profile}.json, {profile}.md   (from analysis_benchmark.py, unchanged)
  - acceptance-summary.json        (only if benchmark exit 0)
  - acceptance-summary.md          (only if benchmark exit 0)
  - acceptance-run-meta.json       (always; both exit codes)
  - process-stats.csv              (from collect_process_stats.ps1, unchanged)
```

## Data Flow

1. Operator runs `pwsh tests/load/run_requirement_acceptance.ps1 -SuiteId current_large_log_cluster_requirement`.
2. `runId` is generated; `tests/load/artifacts/acceptance-$runId` is created.
3. Preflight `GET /health` → if non-200 within 5 s, exit 3 with a clear message.
4. `requirement_acceptance.py suite-profiles` resolves the suite and prints the profile list.
5. `prepare_analysis_datasets.py --config tests/load/analysis_benchmarks.yaml --profile <p>` for each profile in the suite.
6. `collect_process_stats.ps1` is launched in the background; a `.collector-stop` file is created in `finally` to stop the collector.
7. `analysis_benchmark.py --config … --host … --output-dir … --profile <p> …` runs all suite profiles in one process.
8. `requirement_acceptance.py finalize --benchmark-exit-code $benchmarkExitCode`:
   - If `$benchmarkExitCode != 0`: returns immediately with `passed: False`, `summary_written: False`, no `acceptance-summary.*` files.
   - Else: `summarize_suite` reads each `{profile}.json` `summary.passed` (rejects non-boolean), aggregates to `suite.passed`, writes `acceptance-summary.json` and `acceptance-summary.md`.
9. `acceptance-run-meta.json` is always written with `benchmark_exit_code`, `finalize_exit_code`, `summary_generated`, `acceptance_passed`, suite id, profiles, host, and `generated_at`.
10. Process exits with the finalizer exit code (0 on suite pass, 1 on suite fail, benchmark exit code when benchmark itself failed).

## Module Responsibilities

### `tests/load/run_requirement_acceptance.ps1`
- Argument parsing (`-SuiteId`, `-BaseUrl`, `-BenchmarkConfig`, `-SuiteConfig`, `-SampleIntervalSeconds`).
- Run id + artifact directory creation.
- `/health` preflight.
- Resolve suite profiles via the Python CLI.
- Run `prepare_analysis_datasets.py` for each profile.
- Background `collect_process_stats.ps1` start/stop.
- Run `analysis_benchmark.py` with all suite profiles in one invocation.
- Call `requirement_acceptance.py finalize`.
- Write `acceptance-run-meta.json` (always).
- Exit with the finalizer's exit code.

### `tests/load/requirement_acceptance.py`
- `load_suites(config_path) -> dict[id, AcceptanceSuite]`: parse YAML, validate shape.
- `get_suite(config_path, suite_id) -> AcceptanceSuite`: lookup with explicit error.
- `summarize_suite(artifacts_dir, suite) -> dict`: per-profile `summary.passed` AND; rejects non-boolean; aggregates metrics/checks/json_report/markdown_report.
- `finalize_suite_run(artifacts_dir, suite, benchmark_exit_code) -> dict`: returns early with `summary_written: False` on benchmark failure; otherwise summarizes and writes both `acceptance-summary.json` and `acceptance-summary.md`.
- `render_markdown(summary) -> str`: human-reviewable table with profile results, failed-check pointers, and JSON/MD paths for each profile.
- `main`/`parse_args` CLI with subcommands `suite-profiles`, `summarize`, `finalize`.

### `tests/load/acceptance_suites.yaml`
- Tracked.
- Schema: `suites: [{ id, description, profiles: [profile_id, ...] }]`.
- Shipped suites: `smoke_acceptance`, `current_large_log_cluster_requirement`.

### `tests/test_requirement_acceptance.py`
- `test_load_suites_reads_profiles`: YAML config round-trips.
- `test_summarize_suite_aggregates_profile_results`: AND of `summary.passed`; per-profile ordering preserved.
- `test_summarize_suite_rejects_non_boolean_passed`: `"false"` string rejected with `AcceptanceConfigError`.
- `test_finalize_suite_run_skips_summary_when_benchmark_failed`: non-zero benchmark exit ⇒ no `acceptance-summary.*` written.
- `test_repo_acceptance_suite_matches_current_requirement`: the tracked `current_large_log_cluster_requirement` suite references the expected profiles.

### `tests/load/README.md`
- Adds `acceptance_suites.yaml`, `requirement_acceptance.py`, `run_requirement_acceptance.ps1` to the tools table.
- Adds `.\tests\load\run_requirement_acceptance.ps1` to the PowerShell examples.
- Adds a "Requirement Acceptance" section explaining the canonical entrypoint, the suite config, the summary artifacts, and the run-meta.

## Storage

- New tracked file: `tests/load/acceptance_suites.yaml`.
- New tracked file: `tests/load/requirement_acceptance.py`.
- New tracked file: `tests/load/run_requirement_acceptance.ps1`.
- New tracked file: `tests/test_requirement_acceptance.py`.
- Modified tracked file: `tests/load/README.md`.
- Generated at run time (gitignored, per the existing `tests/load/artifacts/` rule):
  - `tests/load/artifacts/acceptance-{runId}/{profile}.json`
  - `tests/load/artifacts/acceptance-{runId}/{profile}.md`
  - `tests/load/artifacts/acceptance-{runId}/acceptance-summary.json`
  - `tests/load/artifacts/acceptance-{runId}/acceptance-summary.md`
  - `tests/load/artifacts/acceptance-{runId}/acceptance-run-meta.json`
  - `tests/load/artifacts/acceptance-{runId}/process-stats.csv`

No durable database is introduced. The suite YAML is the only durable config; the per-run artifacts under `acceptance-{runId}/` are re-creatable from the benchmark output and the suite config, so they are treated as cache, not truth.

## Error Handling

- `AcceptanceConfigError` for invalid suite YAML shape, unknown suite id, missing profile output, and non-boolean `summary.passed`. Surfaces as a non-zero exit code with a clear message.
- Preflight failure exits with code 3 and a clear message ("backend did not return 200 within 5s"). No benchmark work, no collector start, no dataset preparation.
- Benchmark failure: `finalize_suite_run` returns `summary_written: False` and `passed: False` without writing `acceptance-summary.*`. The PowerShell entrypoint's `acceptance-run-meta.json` records both exit codes so the run is fully auditable.
- Process-stats collector is stopped in `finally` via a `.collector-stop` sentinel and `Stop-Process` as a fallback. Collector leak is bounded to the lifetime of the entrypoint.
- All tracked files use LF line endings (consistent with the rest of the repo). The new PS1 file is UTF-8 with no BOM.

## Memory Behavior

- `requirement_acceptance.py` reads `{profile}.json` files one at a time and only the `summary` key for aggregation. The full per-profile `summary` is then re-serialized to `acceptance-summary.json` in one shot. No streaming concerns at this layer; the underlying benchmark runner already does the streaming.
- The Markdown renderer is pure string concatenation over a small dict, so it is O(profiles_in_suite) and bounded.

## Tests

- `uv run pytest tests/test_requirement_acceptance.py -q` covers the helper logic.
- Manual smoke test: `pwsh tests/load/run_requirement_acceptance.ps1 -SuiteId smoke_acceptance` against a running backend produces `acceptance-summary.json`/`acceptance-summary.md` and `acceptance-run-meta.json` with `summary_generated: true` and `acceptance_passed: true`.
- Manual non-pass test: same command with a profile whose `summary.passed` is `false` should produce a `FAIL` row in the Markdown and `acceptance_passed: false` in the run meta.
- Manual benchmark-fail test: stop the backend before running; preflight should exit 3 with no summary artifacts.

## Compatibility

- No backend or frontend code is changed.
- `analysis_benchmark.py` and `analysis_benchmarks.yaml` are untouched.
- The acceptance layer reads the existing per-profile `summary.passed` semantics; if a future change to the benchmark alters that contract, the acceptance summary will report it as a suite failure (correct behavior).
- The preflight URL and timeouts mirror `run_analysis_bench.ps1` to keep the two entrypoints consistent.

## Open Questions

- Future: should the suite config support YAML anchors to share profile lists across suites? Not needed now (only two suites).
- Future: should the suite summary be added to `case-draft.md` or a dashboard? Deferred — current change is file artifacts only.
- Future: should the run-meta include a hash of the benchmark + suite config so reviewers can tell when the same suite produced different results? Useful but deferred.
