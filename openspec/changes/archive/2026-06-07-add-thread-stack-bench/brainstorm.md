## Context

`diagnose_tool/analyzer/thread_stack_parser.py` is already shipped and tested — 38 synthetic capability tests pass, 27 `stack_parser` regression tests pass, and the full suite of 498 tests is green. What is missing is the **evidence layer** that proves the parser is correct and fast under realistic load, kept under version control so reviewers can audit it.

This change archives the load benchmark script, a real-world fixture pair (Java 8 + Java 11 jstack), the synthetic-bench JSON output, and the human-reviewable capability / load reports. It does not modify the parser itself.

## Goals

- A single, version-tracked load benchmark command for the thread stack parser: `uv run python tests/load/thread_stack_bench.py`.
- Synthetic data generator that produces realistic HotSpot thread dump blocks at configurable scale (100 / 1k / 10k).
- Per-scale measurement: total wall time, per-block p50/p95/p99 latency, peak memory (tracemalloc), failure count, status distribution, result count.
- A canonical JSON evidence file (`tests/load/thread_stack_bench.json`) capturing one run; subsequent runs overwrite the file deterministically.
- Real-world fixture pair (`real_dump_sample1.txt` Java 8, `real_dump_sample2.txt` Java 11) used both by the report and by future regression tests.
- Human-readable reports: a capability report covering synthetic + real inputs, and a load report covering the three scale points.

## Non-Goals

- Do not change `diagnose_tool/analyzer/thread_stack_parser.py` or any of its tests.
- Do not change `tests/test_thread_stack_parser.py` or `tests/test_stack_parser.py`.
- Do not add a CI workflow; this is evidence, not automation.
- Do not introduce a new dependency; the bench only uses `argparse`, `gc`, `json`, `statistics`, `time`, `tracemalloc`, and the existing `diagnose_tool.analyzer.thread_stack_parser`.
- Do not change the parser's known-issue behavior (Java 11 module-qualified Native Method detection). The capability report captures the issue; fixing it is a separate change.
- Out of scope: a streaming-mode benchmark. The current bench measures the existing `parse_thread_dump_all` over a single in-memory string, which is sufficient for the report's scale points.

## Approach Selection

Three approaches were considered:

- **A. Inline-only evidence** — embed the bench code in the reports and re-run on demand. Simple, but no machine-checkable artifact and no script to re-run.
- **B. Script + JSON + report (current implementation, chosen)** — a tracked Python script, a tracked JSON output capturing one run, and tracked Markdown reports. The script is rerunnable; the JSON is the current snapshot of results; the reports are human review.
- **C. CI-runnable benchmark** — wire the bench into a CI pipeline with thresholds. Defers the human-review experience; not what the user asked for.

The current implementation is B. The script can be rerun to refresh the JSON, the reports document the current run and explain the methodology, and the real-world fixtures are kept under `tests/load/` for future regression. No CI integration in this change.

## Key Design Decisions

1. **One tracked JSON snapshot, not a CI artifact.** The JSON captures one representative run. Re-running overwrites it. This is consistent with how `analysis_benchmark.py` produces per-run artifacts; we do not add a per-run directory here because the bench is a single-process run with deterministic output.
2. **Synthetic blocks are realistic, not random.** Each synthetic block has a real HotSpot-style header, a state line, 8 frames, and (for BLOCKED/WAITING) a lock hint. This gives the bench a workload that exercises the parser's hot paths instead of measuring synthetic worst case.
3. **Per-block re-parse for accurate percentiles.** The total-time measurement is `parse_thread_dump_all` over the whole dump; per-block percentiles come from a second pass that calls `parse_thread_dump` on each block. The bench measures both, so the JSON captures end-to-end and per-block latency.
4. **Real-world fixtures are kept small and public.** The two real dumps are ~8 threads and ~12 threads respectively, sourced from public GitHub examples. They are small enough to keep in the repo and large enough to exercise the parser on real JVM output (including a Java 11 module-qualified case).
5. **Capability and load are reported separately.** The capability report covers correctness (synthetic + real) and lists known issues. The load report covers performance (throughput, latency, memory). Two files, two audiences, no overlap.

## Open Questions

- Should the bench become a per-profile target of `analysis_benchmarks.yaml`? Deferred — the analysis-bench profile system targets HTTP endpoints, not the analyzer modules.
- Should the bench have a unit test file? Deferred — the bench itself is a test artifact; its own tests would be circular. The capability report is the regression evidence.
