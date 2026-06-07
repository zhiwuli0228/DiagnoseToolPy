## 1. Suite Config And Aggregation Module

- [x] 1.1 Add canonical suite config at `tests/load/acceptance_suites.yaml` with the two shipped suites and validate shape
  - Files: `tests/load/acceptance_suites.yaml`, `tests/load/requirement_acceptance.py`
  - Behavior: `load_suites` and `get_suite` parse the YAML, surface clear errors on missing/empty `profiles`, and expose `AcceptanceSuite` objects
  - Tests: `test_load_suites_reads_profiles`, `test_repo_acceptance_suite_matches_current_requirement`
  - Verification: `uv run pytest tests/test_requirement_acceptance.py -q`
- [x] 1.2 Implement suite aggregation with strict boolean validation
  - Files: `tests/load/requirement_acceptance.py`
  - Behavior: `summarize_suite` reads each `{profile}.json`, ANDs `summary.passed` values, rejects non-boolean values with `AcceptanceConfigError`, returns the per-profile metrics/checks/json_report/markdown_report
  - Tests: `test_summarize_suite_aggregates_profile_results`, `test_summarize_suite_rejects_non_boolean_passed`
  - Verification: `uv run pytest tests/test_requirement_acceptance.py -q`
- [x] 1.3 Implement finalize, markdown renderer, and CLI subcommands
  - Files: `tests/load/requirement_acceptance.py`
  - Behavior: `finalize_suite_run` skips summary on benchmark failure, otherwise writes `acceptance-summary.json` and `acceptance-summary.md`; `render_markdown` produces the human-review table and review pointers; CLI exposes `suite-profiles`, `summarize`, `finalize`
  - Tests: `test_finalize_suite_run_skips_summary_when_benchmark_failed`
  - Verification: `uv run pytest tests/test_requirement_acceptance.py -q` and a manual `python -m tests.load.requirement_acceptance` smoke run

## 2. PowerShell Entrypoint And Run Meta

- [x] 2.1 Implement the canonical PowerShell entrypoint
  - Files: `tests/load/run_requirement_acceptance.ps1`
  - Behavior: arg parsing, preflight `GET /health` with 5-second timeout, suite profile resolution via the Python CLI, dataset preparation, background `collect_process_stats.ps1` start, `analysis_benchmark.py` invocation, finalize call, always-written `acceptance-run-meta.json`, and exit-code propagation
  - Tests: smoke run against a running backend produces the expected artifacts
  - Verification: `pwsh tests/load/run_requirement_acceptance.ps1 -SuiteId smoke_acceptance` against `http://127.0.0.1:18080`
- [x] 2.2 Update `tests/load/README.md` with the new entrypoint, the suite config, and the produced artifacts
  - Files: `tests/load/README.md`
  - Behavior: add the three new files to the tools table, add the PowerShell invocation to the example block, add a "Requirement Acceptance" section explaining the entrypoint, the suite config, and the artifacts
  - Tests: documentation review only
  - Verification: `git diff tests/load/README.md` shows the expected additions

## 3. Verification And Project Hygiene

- [x] 3.1 Run the full regression test
  - Files: `tests/test_requirement_acceptance.py`
  - Behavior: every test in the file passes
  - Tests: `uv run pytest tests/test_requirement_acceptance.py -q`
  - Verification: terminal output reports `5 passed`
- [x] 3.2 Generate apply / verify / finalize receipts
  - Files: `openspec/changes/add-requirement-acceptance/apply.md`, `verify.md`, `finalize.md`
  - Behavior: capture the implementation summary, the verification scorecard, and the closeout evidence in the OpenSpec artifacts
  - Tests: review only
  - Verification: `openspec status --change add-requirement-acceptance --json` reports `isComplete: true`
