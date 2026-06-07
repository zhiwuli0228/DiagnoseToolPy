## Why

`diagnose_tool/analyzer/thread_stack_parser.py` is shipped and tested: 38 synthetic capability tests pass, 27 `stack_parser` regression tests pass, and the full suite of 498 tests is green. What is missing is the durable **evidence layer** that proves the parser is correct and fast under realistic load, kept under version control so reviewers and future contributors can audit it without rerunning anything.

The current `current-state.md` lists the parser as implemented but does not point to any tracked benchmark or evidence report. This change closes that gap: a single command to rerun the bench, a tracked JSON snapshot of the most recent run, two real-world fixture dumps, and two human-readable reports (capability + load).

## What Changes

**Load benchmark script**
- From: no tracked load benchmark for the thread stack parser; performance is implicit from unit tests.
- To: `tests/load/thread_stack_bench.py` exposes a one-command bench with `--blocks` and `--output` arguments, generates realistic HotSpot thread dump blocks, and measures total time, per-block p50/p95/p99 latency, peak memory, failure count, status distribution, and result count.
- Reason: a tracked, rerunnable command is the only way to keep the parser's performance honest over time.
- Impact: non-breaking; pure addition. The parser is untouched.

**JSON evidence snapshot**
- From: no per-bench JSON record.
- To: `tests/load/thread_stack_bench.json` captures one snapshot of the bench output. Rerunning overwrites.
- Reason: a version-tracked JSON makes the current numbers reviewable from the repo without rerunning.
- Impact: non-breaking; the file is small (~3 KB at the default scale points).

**Real-world fixtures**
- From: no tracked real-world dump samples; the capability report references "see sample1 / sample2" with no path.
- To: `tests/load/real_dump_sample1.txt` (Java 8 jstack, 8 threads) and `tests/load/real_dump_sample2.txt` (Java 11 jstack, 12 threads) are tracked.
- Reason: real dumps anchor the capability report to actual JVM output and give future regression tests a fixture pair to use.
- Impact: non-breaking; pure addition.

**Capability and load reports**
- From: no human-readable evidence report for the parser.
- To: `tests/load/thread-stack-capability-report.md` (synthetic + real coverage, known issues, evidence paths) and `tests/load/thread-stack-load-report.md` (per-scale results, scaling discussion) are tracked.
- Reason: a reviewer can sign off on the parser's correctness and performance without re-running anything.
- Impact: non-breaking; pure addition.

## Capabilities

### New Capabilities
- `thread-stack-bench`: load benchmark script, JSON snapshot, real-world fixtures, and capability + load reports for `diagnose_tool/analyzer/thread_stack_parser.py`.

### Modified Capabilities
- None. The parser, its tests, and the existing analysis benchmark are not modified.

## Affected Modules

- `tests/load/` — new files: `thread_stack_bench.py`, `thread_stack_bench.json`, `real_dump_sample1.txt`, `real_dump_sample2.txt`, `thread-stack-capability-report.md`, `thread-stack-load-report.md`.
- `diagnose_tool/`, `frontend/`, `casebase/`, `retrieval/`, `exporter/`, `tests/test_*`, `tests/test_stack_parser.py`, `tests/test_thread_stack_parser.py`: **no changes**.

## Storage Impact

- New tracked Python file: `tests/load/thread_stack_bench.py` (small, standalone script).
- New tracked JSON file: `tests/load/thread_stack_bench.json` (small, current-run snapshot).
- New tracked fixture files: `tests/load/real_dump_sample1.txt`, `tests/load/real_dump_sample2.txt` (small, public samples).
- New tracked documentation: `tests/load/thread-stack-capability-report.md`, `tests/load/thread-stack-load-report.md` (Markdown, hand-authored).
- No new durable database, no new index, no new cache that needs invalidation.

## Constraints

- No mandatory database.
- No new dependency. The bench only uses `argparse`, `gc`, `json`, `statistics`, `time`, `tracemalloc`, and the existing parser module.
- The parser itself is not modified. The bench is a measurement on top of the public API.
- All new tracked files use LF line endings and UTF-8.

## Risks

- The JSON snapshot will drift from the reports if the bench is rerun and the reports are not refreshed. Mitigation: the reports cite the JSON by path; a reviewer can `diff` the JSON to detect drift, and the change's verify step cross-checks the report numbers against the JSON.
- Real-world fixtures are small and may not exercise every parser edge case. Mitigation: the fixtures are paired with the synthetic generator, which is broader; the parser's own tests still cover edge cases.
- A new dependency (e.g., `pytest-benchmark`) is tempting but explicitly out of scope. Mitigation: the bench uses only the standard library and the parser; no install step is needed.

## Verification

- `uv run python tests/load/thread_stack_bench.py` produces a JSON with `failures == 0` for every scale point at HEAD.
- The capability report's test counts (38/38 synthetic, 27/27 regression, 498/498 full suite) match the current `tests/` state at the time of the report.
- The load report's per-scale numbers match the JSON.
- The two real fixture files are byte-identical to the originals (they are tracked as data, not regenerated).
- `uv run pytest` still passes 498/498 (the bench does not touch the test suite).
- The parser's known issue (Java 11 module-qualified Native Method) is still PARTIAL/RAW, captured in the capability report's "Known Issues" section.

## Impact

- `tests/load/`: 6 new tracked files. No modifications to existing files.
- No backend, no frontend, no casebase, no retrieval, no exporter.
- No docs beyond the two new Markdown files in `tests/load/`.
- Out of scope (separate change): fixing the Java 11 module-qualified Native Method detection. The capability report documents the issue.
