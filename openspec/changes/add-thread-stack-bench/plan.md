# Implementation Plan: add-thread-stack-bench

## Goal

Archive the load benchmark, real-world fixtures, JSON snapshot, and capability / load reports for `diagnose_tool/analyzer/thread_stack_parser.py` as a single version-tracked change. This is a **closeout** of files that already exist in the working tree.

The plan is not "write the code" but "verify the existing files match the new artifacts, run the parser against the real fixtures, cross-check the report numbers against the JSON, and produce the apply / verify / finalize receipts". Each step below is a checkpoint rather than a forward-only instruction.

## Pre-conditions

- The working tree contains the implementation files that the change introduces:
  - `tests/load/thread_stack_bench.py`
  - `tests/load/thread_stack_bench.json`
  - `tests/load/real_dump_sample1.txt`
  - `tests/load/real_dump_sample2.txt`
  - `tests/load/thread-stack-capability-report.md`
  - `tests/load/thread-stack-load-report.md`
- `diagnose_tool/analyzer/thread_stack_parser.py`, `tests/test_thread_stack_parser.py`, and `tests/test_stack_parser.py` are untouched.
- The Python environment has `uv` available; the bench uses only the standard library plus the existing parser module.

## Steps

### Step 1 — Lock the artifact set

Confirm `openspec/changes/add-thread-stack-bench/` contains: `brainstorm.md`, `design.md`, `proposal.md`, `tasks.md`, `plan.md`, plus `specs/thread-stack-bench/spec.md`. `openspec status --change add-thread-stack-bench --json` must show every artifact with `status: done` once the apply and verify receipts are written later in this plan.

### Step 2 — Re-run the bench and inspect the JSON

```bash
uv run python tests/load/thread_stack_bench.py --blocks 10 100 1000
```

Expected: the script writes a JSON with three entries, each with all 10 numeric fields and a 3-key `status_distribution`. `failures` must be 0 for every scale point at HEAD. Compare the entries against `tests/load/thread_stack_bench.json`; if the bench is rerun, the JSON is overwritten, so the reports need a refresh — for the closeout we keep the existing snapshot.

If the JSON does not round-trip or any field is missing, stop and fix the bench script before continuing.

### Step 3 — Re-parse the real fixtures

```bash
python -c "from diagnose_tool.analyzer.thread_stack_parser import parse_thread_dump_all; r=parse_thread_dump_all(open('tests/load/real_dump_sample1.txt').read()); print(len(r), [x.parse_status.value for x in r])"
python -c "from diagnose_tool.analyzer.thread_stack_parser import parse_thread_dump_all; r=parse_thread_dump_all(open('tests/load/real_dump_sample2.txt').read()); print(len(r), [x.parse_status.value for x in r])"
```

Expected: Java 8 sample returns 8 entries (6 FULL, 2 PARTIAL per the capability report). Java 11 sample returns 12 entries (4 FULL, 8 PARTIAL per the report). The status distribution must match the report's per-thread tables. If it does not, the capability report is stale and the report needs a refresh — for the closeout we accept the current state as documented.

### Step 4 — Cross-check the spec against the implementation

Spot-check each requirement against the file paths in the working tree:

- `tests/load/thread_stack_bench.py` exists and exposes `_make_thread_block`, `make_synthetic_dump`, `run_bench`, `main`, and the argparse CLI.
- `tests/load/thread_stack_bench.json` exists and contains `benchmarks` + `timestamp`.
- `tests/load/real_dump_sample1.txt` and `real_dump_sample2.txt` exist and are non-empty.
- `tests/load/thread-stack-capability-report.md` covers 38 synthetic + 27 regression + 498 full-suite + the two real fixture tables.
- `tests/load/thread-stack-load-report.md` covers the three scale points and the methodology.

### Step 5 — Run the full test suite

```bash
uv run pytest -q
```

Expected: `498 passed`. This confirms the bench change did not regress the parser or the test suite. If any test fails, stop and fix before continuing.

### Step 6 — Write the apply receipt

Write `openspec/changes/add-thread-stack-bench/apply.md` with:

- Change name, iteration 1, applied timestamp.
- Workspace: `claude_master`, no worktree, no PR.
- Commits: 0 of N at receipt time (the commit happens in step 9).
- Tasks: 4 of 4 sections marked complete.
- Tests / load change summary (this change touches only `tests/load/`).
- Verification fix section: leave empty unless a defect was caught.

### Step 7 — Write the verify report

Write `openspec/changes/add-thread-stack-bench/verify.md` with:

- Scorecard: completeness (4/4 tasks, 6/6 requirements), correctness (all scenarios covered), coherence (7/7 design decisions followed).
- CRITICAL / WARNING / SUGGESTION sections: each empty unless a real issue is found.
- Final assessment: "All checks passed. Ready for archive." unless a real issue was caught.

### Step 8 — Write the finalize receipt

Write `openspec/changes/add-thread-stack-bench/finalize.md` with:

- Branch: `claude_master`. Base branch: `main`. Final state: `kept-open`. PR URL: `N/A`.
- Workspace: no worktree, no cleanup.
- Tests: `passing (498/498)`.
- Git-side closeout: skipped, with the uncommitted-files table mirroring the working tree.

### Step 9 — Commit and archive

1. Stage the change folder plus the 6 implementation files by explicit path (no `git add -A`).
2. Commit with a conventional-commit message:

   ```text
   feat(tests/load): add load benchmark and capability/load reports for thread stack parser
   ```

3. Run `openspec archive add-thread-stack-bench -y --skip-specs`. The delta spec lives only inside the change folder; the main `openspec/specs/` set is intentionally not modified by this change.

## Out of scope (deferred)

- Fixing the Java 11 module-qualified `Native Method` detection in `thread_stack_parser.py`. The capability report documents the issue; the fix is a separate change.
- A streaming-mode benchmark. The current bench measures the existing `parse_thread_dump_all` over an in-memory string, which is sufficient for the three scale points.
- A CI workflow. The bench is a manual, on-demand command; the JSON and reports are the persisted evidence.
- Adding the bench as a profile in `analysis_benchmarks.yaml`. The analysis-bench profile system targets HTTP endpoints, not analyzer modules.

## Validation checkpoints

| Checkpoint | Command | Pass criterion |
|------------|---------|----------------|
| Artifact set complete | `openspec status --change add-thread-stack-bench --json` | every artifact `done` |
| Bench runs | `uv run python tests/load/thread_stack_bench.py --blocks 10` | exit 0, JSON has the entry |
| JSON schema | `python -c "import json; d=json.load(open('tests/load/thread_stack_bench.json')); assert d['benchmarks'] and all(set(['n_blocks','raw_bytes','total_seconds','avg_us','p50_us','p95_us','p99_us','peak_memory_bytes','failures','result_count']).issubset(e) and set(['FULL','PARTIAL','RAW']).issubset(e['status_distribution']) for e in d['benchmarks'])"` | exit 0 |
| Real fixture parses | `python -c "from diagnose_tool.analyzer.thread_stack_parser import parse_thread_dump_all; assert len(parse_thread_dump_all(open('tests/load/real_dump_sample1.txt').read()))==8; assert len(parse_thread_dump_all(open('tests/load/real_dump_sample2.txt').read()))==12"` | exit 0 |
| Full test suite | `uv run pytest -q` | `498 passed` |
| Status complete | `openspec status --change add-thread-stack-bench --json` | `isComplete: true` |
