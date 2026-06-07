# Apply Receipt

> Generated at the end of the apply phase to mark code-implementation
> complete and provide verify with the state it needs.
> Overwritten on each apply iteration; iteration counter grows.

**Change**: `add-thread-stack-bench`
**Iteration**: `1`
**Applied at**: 2026-06-07
**Executor**: `executing-plans`

---

## Workspace

- **Worktree**: none (implemented directly on `claude_master`)
- **Branch**: `claude_master`

---

## Commits

- **Range**: `none` (changes not yet committed at receipt time)
- **Count**: `0`

---

## Tasks

- **Completed**: `4 of 4` sections in tasks.md flipped to `- [x]`
- **Remaining**: `none`

---

## Implementation Summary

### Tests / Load

| File | Change |
|------|--------|
| `tests/load/thread_stack_bench.py` | NEW — argparse CLI (`--blocks`, `--output`), `_make_thread_block` (realistic HotSpot header + 8 frames + lock hint), `make_synthetic_dump`, `run_bench` (two-pass timing + `tracemalloc` peak memory + status distribution + failure count), `main` writes JSON to default or `--output` path |
| `tests/load/thread_stack_bench.json` | NEW — one snapshot of the bench output for `[100, 1000, 10000]`; schema `{ benchmarks: [{n_blocks, raw_bytes, total_seconds, avg_us, p50_us, p95_us, p99_us, peak_memory_bytes, failures, result_count, status_distribution}], timestamp }` |
| `tests/load/real_dump_sample1.txt` | NEW — Java 8 jstack output (8 threads, public GitHub sample). `parse_thread_dump_all` returns 6 FULL + 2 PARTIAL |
| `tests/load/real_dump_sample2.txt` | NEW — Java 11 jstack output (12 threads, public GitHub sample, includes a module-qualified `Native Method` frame). `parse_thread_dump_all` returns 4 FULL + 8 PARTIAL |
| `tests/load/thread-stack-capability-report.md` | NEW — coverage table, test execution summary (38/38 + 27/27 + 526/526), per-thread tables for the two real fixtures, known issues (Java 11 module-qualified `Native Method` not detected as native; threads with no frames correctly marked PARTIAL), evidence paths, conclusion (PASS with 1 minor known issue) |
| `tests/load/thread-stack-load-report.md` | NEW — test purpose, scale, data source, test method, per-scale results (total time, p50/p95/p99, peak memory, status distribution, failure count), real-dump validation table, conclusion |

### Tests

| File | Count |
|------|-------|
| `tests/` (full suite at HEAD) | 526 passed (38 thread-stack-parser + 27 stack-parser + 461 other) |

### Backend / Frontend / Docs

No backend, no frontend, no casebase, no retrieval, no exporter changes. `diagnose_tool/analyzer/thread_stack_parser.py`, `tests/test_thread_stack_parser.py`, and `tests/test_stack_parser.py` are untouched.

---

## Verification Fixes Applied

- Re-ran `uv run python tests/load/thread_stack_bench.py --blocks 100 1000 10000` to refresh the JSON snapshot after an earlier `--blocks 10` smoke run had overwritten it.
- Updated `tests/load/thread-stack-load-report.md` to match the refreshed JSON percentiles (p50/p95/p99) and corrected the sample2 FULL/PARTIAL count (4 / 8, not 5 / 7).
- Updated `tests/load/thread-stack-capability-report.md` to reflect the current full-suite test count (526, not 498) after the thread-stack-evidence-basket change added 28 tests.

---

## Next step

Run `openspec status --change add-thread-stack-bench --json` and the verify report step, then commit and `openspec archive` with `--skip-specs`.
