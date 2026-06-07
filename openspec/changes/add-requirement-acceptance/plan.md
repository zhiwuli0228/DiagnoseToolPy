# Implementation Plan: add-requirement-acceptance

## Goal

Stand up the requirement-acceptance layer on top of the existing analysis benchmark, document the implementation through the SuperSpec artifact set, and commit the change.

This change is a **closeout** of code that already exists in the working tree. The plan is therefore not "write the code" but "verify the code matches the new artifacts, run the tests, and produce the apply / verify / finalize receipts". Each step below is a checkpoint rather than a forward-only instruction.

## Pre-conditions

- The working tree contains the implementation files that the change introduces:
  - `tests/load/acceptance_suites.yaml`
  - `tests/load/requirement_acceptance.py`
  - `tests/load/run_requirement_acceptance.ps1`
  - `tests/test_requirement_acceptance.py`
  - `tests/load/README.md` (modified)
- `tests/load/analysis_benchmark.py`, `tests/load/analysis_benchmarks.yaml`, and `tests/load/run_analysis_bench.ps1` are untouched.
- The Python environment has `uv` available, `pyyaml` is installed (it is a current dependency), and `pytest` is available.
- The backend is reachable on `http://127.0.0.1:18080` for the optional manual smoke test (only required if the user wants to exercise the full entrypoint; the unit tests do not need the backend).

## Steps

### Step 1 — Lock the artifact set

1. Confirm `openspec/changes/add-requirement-acceptance/` contains: `brainstorm.md`, `design.md`, `proposal.md`, `tasks.md`, `plan.md`, plus `specs/requirement-acceptance/spec.md`.
2. `openspec status --change add-requirement-acceptance --json` must show every artifact with `status: done` once the apply and verify receipts are written later in this plan.

### Step 2 — Run the unit tests

```bash
uv run pytest tests/test_requirement_acceptance.py -q
```

Expected: `5 passed`. Each test maps to a specific requirement:

- `test_load_suites_reads_profiles` → Suite Config parseable
- `test_repo_acceptance_suite_matches_current_requirement` → Suite Config matches the repo's current requirement
- `test_summarize_suite_aggregates_profile_results` → Suite Aggregation AND
- `test_summarize_suite_rejects_non_boolean_passed` → Strict boolean validation
- `test_finalize_suite_run_skips_summary_when_benchmark_failed` → Finalize-on-benchmark-failure

If any test fails, stop and fix the implementation before continuing.

### Step 3 — Cross-check the spec against the implementation

Spot-check each requirement against the file paths in the working tree:

- `tests/load/acceptance_suites.yaml` exists and contains both `smoke_acceptance` and `current_large_log_cluster_requirement`.
- `tests/load/requirement_acceptance.py` exposes `load_suites`, `get_suite`, `summarize_suite`, `finalize_suite_run`, `render_markdown`, and the CLI subcommands.
- `tests/load/run_requirement_acceptance.ps1` performs preflight, calls the Python CLI, runs the benchmark, and writes `acceptance-run-meta.json`.
- `tests/test_requirement_acceptance.py` covers all five scenarios above.
- `tests/load/README.md` mentions the three new files, the `run_requirement_acceptance.ps1` example, and the "Requirement Acceptance" section.

### Step 4 — (Optional) Manual smoke run

Only if a backend is running and the user wants to exercise the full entrypoint:

```bash
pwsh tests/load/run_requirement_acceptance.ps1 -SuiteId smoke_acceptance
```

Expected: `acceptance-summary.json`, `acceptance-summary.md`, `acceptance-run-meta.json`, and `process-stats.csv` are written under `tests/load/artifacts/acceptance-{runId}/`. The run meta reports `summary_generated: true` and `acceptance_passed: true`.

The unit tests are sufficient for the closeout. This step is for reviewer confidence only and is not required for the verify pass.

### Step 5 — Write the apply receipt

Write `openspec/changes/add-requirement-acceptance/apply.md` with:

- Change name, iteration 1, applied timestamp.
- Workspace: claude_master, no worktree, no PR.
- Commits: `0 of N` at this point (the commit happens in step 8).
- Tasks: 3 of 3 sections marked complete.
- Backend / frontend / tests / docs change summary (this change touches only `tests/load/` + `tests/`).
- Verification fix section: leave empty unless a defect was caught.

### Step 6 — Write the verify report

Write `openspec/changes/add-requirement-acceptance/verify.md` with:

- Scorecard: completeness (3/3 tasks, 6/6 requirements), correctness (all scenarios covered), coherence (design decisions followed).
- CRITICAL / WARNING / SUGGESTION sections: each empty unless a real issue is found.
- Final assessment: "All checks passed. Ready for archive." unless a real issue was caught.

### Step 7 — Write the finalize receipt

Write `openspec/changes/add-requirement-acceptance/finalize.md` with:

- Branch: `claude_master`. Base branch: `main`. Final state: `kept-open`. PR URL: `N/A`.
- Workspace: no worktree, no cleanup.
- Tests: `passing (5/5)`.
- Git-side closeout: skipped, with the uncommitted-files table mirroring the working tree.

### Step 8 — Commit and archive

1. Stage the change folder plus the new/modified implementation files by explicit path (no `git add -A`).
2. Commit with a conventional-commit message:

   ```text
   feat(tests/load): add requirement-level acceptance over analysis benchmark
   ```

3. Run `openspec archive add-requirement-acceptance -y --skip-specs` (skip specs because the main `requirement-acceptance` spec is intentionally not added to `openspec/specs/`; this change does not modify the main spec set and the delta spec remains inside the change folder as a record of what was added). If the user later wants the main spec to gain a `requirement-acceptance` capability, that is a separate change.

## Out of scope (deferred)

- `tests/load/thread_stack_bench.py` and the two `real_dump_sample*.txt` fixtures.
- `tests/load/thread-stack-capability-report.md` and `tests/load/thread-stack-load-report.md`.
- The above belong to a separate `add-thread-stack-bench` change with its own SuperSpec cycle.
- No changes to backend, frontend, casebase, retrieval, or exporter.

## Validation checkpoints

| Checkpoint | Command | Pass criterion |
|------------|---------|----------------|
| Artifact set complete | `openspec status --change add-requirement-acceptance --json` | every artifact `done` |
| Unit tests | `uv run pytest tests/test_requirement_acceptance.py -q` | `5 passed` |
| Suite config shape | `python -c "import yaml,sys; d=yaml.safe_load(open('tests/load/acceptance_suites.yaml')); assert d['suites'] and all(s['profiles'] for s in d['suites'])"` | exit 0 |
| Repo suite matches current requirement | `uv run pytest tests/test_requirement_acceptance.py::test_repo_acceptance_suite_matches_current_requirement -q` | 1 passed |
| Status complete | `openspec status --change add-requirement-acceptance --json` | `isComplete: true` |
