# Verification Report: add-thread-stack-bench

## Summary

| Dimension    | Status                       |
|--------------|------------------------------|
| Completeness | 4/4 tasks, 6/6 requirements  |
| Correctness  | 14/14 scenarios covered      |
| Coherence    | 7/7 design decisions followed |

---

## Completeness

### Task Completion

All 4 task sections in `tasks.md` are marked `[x]`:

| Task | Status |
|------|--------|
| 1.1 Bench script | done |
| 1.2 JSON snapshot for default scale points | done |
| 2.1 Java 8 fixture | done |
| 2.2 Java 11 fixture | done |
| 3.1 Capability report | done |
| 3.2 Load report | done |
| 4.1 Report numbers match JSON | done |
| 4.2 Full test suite passes | done |
| 4.3 Receipts | done |

### Spec Coverage

All 6 requirements from `specs/thread-stack-bench/spec.md` have implementation evidence:

| Requirement | Status | Key Files |
|-------------|--------|-----------|
| R1 Load Benchmark Command | COVERED | `thread_stack_bench.py:137-160` argparse CLI |
| R2 Synthetic Block Generator | COVERED | `thread_stack_bench.py:38-69` deterministic generator |
| R3 Per-Scale Measurements | COVERED | `thread_stack_bench.py:76-134` two-pass timing + `tracemalloc` |
| R4 JSON Snapshot Schema | COVERED | `thread_stack_bench.json` (all 10 numeric fields + 3-key status_distribution) |
| R5 Real-World Fixtures | COVERED | `real_dump_sample1.txt` (8 threads, 6 FULL + 2 PARTIAL), `real_dump_sample2.txt` (12 threads, 4 FULL + 8 PARTIAL) |
| R6 Capability And Load Reports | COVERED | `thread-stack-capability-report.md`, `thread-stack-load-report.md` |

---

## Correctness

### Scenario Coverage

All 14 scenarios are COVERED:

| Scenario | Evidence |
|----------|----------|
| Default invocation produces a JSON snapshot | `thread_stack_bench.py:139` default `--blocks [100, 1000, 10000]`; `--output` defaults to `Path(__file__).resolve().parent / "thread_stack_bench.json"` |
| Custom scale points are honored | argparse `nargs="+"` at `thread_stack_bench.py:139-140` |
| Custom output path is honored | `thread_stack_bench.py:154-155` reads `args.output` first |
| Synthetic block contains all required sections | `_make_thread_block` produces header + state line + 8 frames |
| BLOCKED block contains a waiting-to-lock hint | `thread_stack_bench.py:55-56` |
| WAITING block contains a parking hint | `thread_stack_bench.py:57-58` |
| Scale point N=100 records all metrics | JSON entry for `n_blocks=100` has all 10 numeric fields + 3-key status_distribution |
| Per-block pass times each block | `thread_stack_bench.py:99-110` iterates over `result_count` blocks |
| Per-block failure does not abort the run | `thread_stack_bench.py:109-110` catches exception and increments `failures` |
| JSON round-trips | `python -c "import json; d=json.load(open('tests/load/thread_stack_bench.json')); ..."` exits 0 |
| Percentile ordering is non-decreasing | `p50 <= p95 <= p99` holds for all three scale points in the refreshed JSON |
| Java 8 sample parses successfully | `parse_thread_dump_all(real_dump_sample1.txt)` returns 8 entries, all FULL or PARTIAL |
| Java 11 sample parses successfully | `parse_thread_dump_all(real_dump_sample2.txt)` returns 12 entries, all FULL or PARTIAL |
| Report numbers match the JSON | The load report's per-scale p50/p95/p99 and peak-memory figures match the JSON entries; the sample2 FULL/PARTIAL count (4/8) matches both the JSON-derived status distribution and the capability report's per-thread table |

### Test Results

Full suite passes:

| Suite | Count | Result |
|-------|-------|--------|
| `uv run pytest -q` | 526 | PASS |

The bench is also a manual check that produces valid output: `uv run python tests/load/thread_stack_bench.py --blocks 100 1000 10000` exits 0 and writes the JSON with `failures == 0` for every scale point.

---

## Coherence

### Design Decision Adherence

| Decision | Status | Evidence |
|----------|--------|----------|
| 1. Bench script is a single Python file with subcommand-less CLI | FOLLOWED | `thread_stack_bench.py` is a single file with `argparse` + `main()` |
| 2. Synthetic block generation is deterministic and realistic | FOLLOWED | `_make_thread_block` uses no randomness; the headers, state, frames, and lock hints match the design |
| 3. Two-pass timing: total and per-block | FOLLOWED | `thread_stack_bench.py:88-90` total, `thread_stack_bench.py:99-110` per-block |
| 4. Memory measurement via `tracemalloc` | FOLLOWED | `thread_stack_bench.py:81-82, 112-113` start/stop and `get_traced_memory` |
| 5. JSON is one snapshot, overwritten on rerun | FOLLOWED | `thread_stack_bench.py:155-159` writes to the default or `--output` path with `indent=2` |
| 6. Real-world fixtures are tracked | FOLLOWED | `real_dump_sample1.txt` and `real_dump_sample2.txt` are tracked in the change |
| 7. Capability and load reports are separate, hand-authored, and stable | FOLLOWED | Two distinct Markdown files; capability covers correctness, load covers performance |

### Code Pattern Consistency

- `thread_stack_bench.py` follows the same `argparse` style as `prepare_analysis_datasets.py` and `analysis_benchmark.py`.
- The bench adds `sys.path.insert(0, project_root)` so it can be run as a script without installation, matching the analysis-bench scripts.
- The two reports are written in the same Markdown style as the rest of `tests/load/` reports and use a consistent table layout.
- The capability report's "Evidence Paths" section points at the same paths the verify report uses, so a reviewer can re-run the same checks.

---

## Issues

**CRITICAL**: None

**WARNING**: None

**SUGGESTION**: None

---

## Final Assessment

All checks passed. Ready for archive (use `--skip-specs` if the main spec is not yet added by this change, as the delta spec lives only inside the change folder).
