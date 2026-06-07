## ADDED Requirements

### Requirement: Canonical Suite Config
The system MUST provide a version-tracked acceptance suite config at `tests/load/acceptance_suites.yaml` that maps a stable `suite_id` to a non-empty list of benchmark profile ids. The list of profile ids MUST correspond to profile ids that exist in `tests/load/analysis_benchmarks.yaml`.

Suite entries MUST contain at least `id` and `profiles`, and MAY contain a human-readable `description`. The config MUST be a flat list of suites and MUST NOT redefine benchmark profile semantics.

#### Scenario: Suite config is parseable
- **WHEN** the suite config is loaded by the acceptance module
- **THEN** each suite entry exposes `id`, `description`, and `profiles` as a non-empty list of strings

#### Scenario: Suite config omits optional description
- **WHEN** a suite entry has no `description` field
- **THEN** the module treats the suite id as the description fallback and does not raise

#### Scenario: Suite config rejects empty profile list
- **WHEN** a suite entry has an empty `profiles` list
- **THEN** the module raises a config error and refuses to load the suite

### Requirement: Suite Aggregation Module
The system MUST provide a Python module at `tests/load/requirement_acceptance.py` that loads the suite config, reads per-profile benchmark summary files, aggregates them into a single suite verdict, and renders both a machine-readable summary and a human-reviewable Markdown summary.

Suite pass MUST be the logical AND of every profile's `summary.passed`. A `summary.passed` that is not a Python `bool` MUST be rejected with a config error. The module MUST be invokable as a CLI with at least the subcommands `suite-profiles`, `summarize`, and `finalize`.

#### Scenario: Suite pass is AND of per-profile pass flags
- **WHEN** the aggregator reads per-profile `summary.passed` values that are a mix of `true` and `false`
- **THEN** the resulting suite `passed` value is `false`

#### Scenario: Non-boolean summary.passed is rejected
- **WHEN** a per-profile `summary.passed` is the string `"false"` or any other non-boolean value
- **THEN** the aggregator raises a config error containing the profile id and a "must be a boolean" message and does not produce a suite summary

#### Scenario: Unknown suite id is rejected
- **WHEN** a caller asks for a suite id that is not in the config
- **THEN** the module raises a config error naming the unknown suite id

#### Scenario: Missing per-profile output is rejected
- **WHEN** a profile in the suite has no corresponding `{profile}.json` in the artifacts directory
- **THEN** the aggregator raises a config error naming the missing profile and refuses to produce a suite summary

### Requirement: Single Acceptance Entrypoint
The system MUST provide a PowerShell entrypoint at `tests/load/run_requirement_acceptance.ps1` that takes a suite id and runs the canonical acceptance flow: preflight `GET /health`, resolve suite profiles, prepare datasets, run the analysis benchmark, finalize the suite summary, and write a run-meta artifact.

The entrypoint MUST exit with the benchmark runner's exit code when the benchmark itself fails, exit with the finalizer's exit code otherwise, and exit with code 3 when the preflight fails.

#### Scenario: Preflight failure aborts the run
- **WHEN** `GET /health` does not return 200 within 5 seconds
- **THEN** the entrypoint exits with code 3 and does not run the benchmark, does not write `acceptance-summary.*`, and records `summary_generated: false` in the run meta

#### Scenario: Benchmark success produces suite summary
- **WHEN** the benchmark runs to completion and every profile in the suite reports `summary.passed: true`
- **THEN** the entrypoint writes `acceptance-summary.json` and `acceptance-summary.md` and the run meta records `summary_generated: true` and `acceptance_passed: true`

#### Scenario: Benchmark success but a profile fails
- **WHEN** the benchmark runs to completion and at least one profile in the suite reports `summary.passed: false`
- **THEN** the entrypoint writes `acceptance-summary.json` and `acceptance-summary.md` whose `passed` is `false`, and the run meta records `summary_generated: true` and `acceptance_passed: false`

#### Scenario: Benchmark itself fails
- **WHEN** the benchmark runner exits non-zero
- **THEN** the entrypoint does not write `acceptance-summary.json` or `acceptance-summary.md`, the run meta records `summary_generated: false` and the benchmark exit code, and the entrypoint exits with that same benchmark exit code

### Requirement: Suite Summary Artifacts
The system MUST produce two suite-level summary artifacts under `tests/load/artifacts/acceptance-{runId}/` whenever the benchmark run itself succeeds: `acceptance-summary.json` (machine-readable) and `acceptance-summary.md` (human-reviewable).

The JSON summary MUST include `suite_id`, `description`, `generated_at`, `artifacts_dir`, `passed`, and a `profiles` array. Each `profiles` entry MUST include `profile_id`, `passed`, `metrics`, `checks`, `json_report`, and `markdown_report`. The Markdown summary MUST list every profile with its pass/fail status and the names of any failed checks, and MUST list the JSON and Markdown paths for each profile as review pointers.

#### Scenario: JSON summary round-trips
- **WHEN** the JSON summary is loaded and inspected
- **THEN** it contains the suite id, the overall pass/fail, and one entry per suite profile with its metrics and checks

#### Scenario: Markdown summary lists failed checks
- **WHEN** the Markdown summary is rendered for a suite that has at least one failing profile
- **THEN** the table row for that profile includes the names of the failed checks and the row's Result column reads `FAIL`

### Requirement: Run-Meta Always Recorded
The system MUST always write `tests/load/artifacts/acceptance-{runId}/acceptance-run-meta.json` after an acceptance run, regardless of whether the benchmark succeeded.

The run meta MUST include `run_id`, `suite_id`, `host`, `benchmark_config`, `suite_config`, `profiles`, `sample_interval_seconds`, `artifact_root`, `process_stats_csv`, `benchmark_exit_code`, `acceptance_exit_code`, `summary_generated`, `acceptance_passed`, and `generated_at`.

#### Scenario: Run meta records partial failure
- **WHEN** the benchmark fails after preflight passes
- **THEN** the run meta records both `benchmark_exit_code` and `acceptance_exit_code` (which equals the benchmark exit code in this path), `summary_generated: false`, and `acceptance_passed: false`

#### Scenario: Run meta records clean pass
- **WHEN** the benchmark and the suite both pass
- **THEN** the run meta records `benchmark_exit_code: 0`, `acceptance_exit_code: 0`, `summary_generated: true`, and `acceptance_passed: true`

### Requirement: Acceptance Tests
The system MUST provide regression tests at `tests/test_requirement_acceptance.py` covering: parsing the suite config, the AND-aggregation of per-profile pass flags, the rejection of non-boolean `summary.passed`, the finalize-on-benchmark-failure path that does not write `acceptance-summary.*`, and a check that the tracked `current_large_log_cluster_requirement` suite references the expected profile ids.

#### Scenario: All acceptance tests pass
- **WHEN** the test suite is run with the acceptance tests included
- **THEN** every test in `tests/test_requirement_acceptance.py` passes
