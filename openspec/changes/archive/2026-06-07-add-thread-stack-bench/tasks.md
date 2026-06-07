## 1. Bench Script And Snapshot

- [x] 1.1 Implement the load benchmark script with synthetic block generator, two-pass timing, and memory tracking
  - Files: `tests/load/thread_stack_bench.py`
  - Behavior: argparse CLI (`--blocks`, `--output`), `_make_thread_block` and `make_synthetic_dump` generators, `run_bench` with `tracemalloc` peak memory, `main` writes JSON to the default or `--output` path
  - Tests: rerun produces valid JSON; per-block failures are counted and do not abort
  - Verification: `uv run python tests/load/thread_stack_bench.py --blocks 10` and inspect the JSON
- [x] 1.2 Capture the JSON snapshot for the default scale points
  - Files: `tests/load/thread_stack_bench.json`
  - Behavior: contains the `benchmarks` array for `n_blocks in [100, 1000, 10000]` and a `timestamp`
  - Tests: JSON validates the schema defined in the spec
  - Verification: `python -c "import json; d=json.load(open('tests/load/thread_stack_bench.json')); assert d['benchmarks'] and all('p50_us' in e for e in d['benchmarks'])"`

## 2. Real-World Fixtures

- [x] 2.1 Track the Java 8 jstack sample
  - Files: `tests/load/real_dump_sample1.txt`
  - Behavior: 8 threads from a Java HotSpot 8 jstack output; `parse_thread_dump_all` returns 8 entries, all `FULL` or `PARTIAL`
  - Tests: re-run the parser on the fixture
  - Verification: `python -c "from diagnose_tool.analyzer.thread_stack_parser import parse_thread_dump_all; r=parse_thread_dump_all(open('tests/load/real_dump_sample1.txt').read()); assert len(r)==8 and all(x.parse_status.value in ('FULL','PARTIAL') for x in r)"`
- [x] 2.2 Track the Java 11 jstack sample
  - Files: `tests/load/real_dump_sample2.txt`
  - Behavior: 12 threads from a Java HotSpot 11 jstack output, including a module-qualified `Native Method` frame; `parse_thread_dump_all` returns 12 entries, all `FULL` or `PARTIAL`
  - Tests: re-run the parser on the fixture
  - Verification: same shape as the Java 8 fixture

## 3. Capability And Load Reports

- [x] 3.1 Author the capability report
  - Files: `tests/load/thread-stack-capability-report.md`
  - Behavior: coverage table, test execution summary (38/38, 27/27, 498/498), per-thread tables for the two real fixtures, known issues, evidence paths, conclusion
  - Tests: review only
  - Verification: cross-check the test counts against `uv run pytest` output
- [x] 3.2 Author the load report
  - Files: `tests/load/thread-stack-load-report.md`
  - Behavior: test purpose, scale, data source, test method, per-scale results, scaling discussion
  - Tests: review only
  - Verification: cross-check the numbers against `tests/load/thread_stack_bench.json`

## 4. Verification And Project Hygiene

- [x] 4.1 Cross-check report numbers against the JSON snapshot
  - Files: `tests/load/thread-stack-load-report.md`, `tests/load/thread_stack_bench.json`
  - Behavior: the totals, p50/p95/p99, and peak-memory figures in the report are consistent with the JSON entries
  - Tests: review only
  - Verification: manual `diff` of the report's per-scale numbers against the JSON
- [x] 4.2 Run the full test suite to confirm no regression
  - Files: `tests/`
  - Behavior: 498/498 pass
  - Tests: `uv run pytest -q`
  - Verification: terminal output reports `498 passed`
- [x] 4.3 Generate apply / verify / finalize receipts
  - Files: `openspec/changes/add-thread-stack-bench/apply.md`, `verify.md`, `finalize.md`
  - Behavior: capture the implementation summary, the verification scorecard, and the closeout evidence
  - Tests: review only
  - Verification: `openspec status --change add-thread-stack-bench --json` reports `isComplete: true`
