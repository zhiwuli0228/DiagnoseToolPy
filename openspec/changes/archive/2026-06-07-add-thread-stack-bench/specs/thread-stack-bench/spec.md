## ADDED Requirements

### Requirement: Load Benchmark Command
The system MUST provide a version-tracked load benchmark for `diagnose_tool/analyzer/thread_stack_parser.py` at `tests/load/thread_stack_bench.py`. The command MUST accept a `--blocks` argument (one or more positive integers) and an optional `--output` argument (a path for the JSON snapshot).

The default `--blocks` scale points MUST be `[100, 1000, 10000]`. The default `--output` path MUST be `tests/load/thread_stack_bench.json` (next to the script). The command MUST be invokable as `uv run python tests/load/thread_stack_bench.py` from the project root with no additional setup.

#### Scenario: Default invocation produces a JSON snapshot
- **WHEN** the operator runs `uv run python tests/load/thread_stack_bench.py` with no arguments
- **THEN** the script runs the three default scale points and writes `tests/load/thread_stack_bench.json` in the same directory as the script

#### Scenario: Custom scale points are honored
- **WHEN** the operator passes `--blocks 50 500`
- **THEN** the script runs exactly two scale points and the JSON `benchmarks` array has exactly two entries

#### Scenario: Custom output path is honored
- **WHEN** the operator passes `--output /tmp/bench.json`
- **THEN** the script writes the JSON to `/tmp/bench.json` and not to the default path

### Requirement: Synthetic Block Generator
The system MUST generate realistic HotSpot thread dump blocks for the benchmark. Each block MUST contain a thread header with a quoted name, a daemon/priority/tid/nid sequence, a state in `{RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, NEW, TERMINATED}`, a `java.lang.Thread.State: <STATE>` line, 8 stack frames (mixing `file:line`, `Native Method`, and `Unknown Source`), and a lock hint for BLOCKED and WAITING states.

The block generator MUST be deterministic — given the same `index` and `state`, it MUST produce byte-identical output across runs. Blocks MUST be joined with `\n\n` to form a full dump.

#### Scenario: Synthetic block contains all required sections
- **WHEN** `_make_thread_block(0, "RUNNABLE")` is called
- **THEN** the returned string contains a thread header with a quoted name, a `java.lang.Thread.State` line, 8 `at ...` frames, and is valid input for `parse_thread_dump`

#### Scenario: BLOCKED block contains a waiting-to-lock hint
- **WHEN** `_make_thread_block(0, "BLOCKED")` is called
- **THEN** the returned string contains a `waiting to lock <0x...> (a java.lang.Object)` line

#### Scenario: WAITING block contains a parking hint
- **WHEN** `_make_thread_block(0, "WAITING")` is called
- **THEN** the returned string contains a `parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock)` line

### Requirement: Per-Scale Measurements
For each scale point `N`, the benchmark MUST measure: total wall time (seconds, `time.perf_counter()`), per-block p50/p95/p99 latency (microseconds, derived from a second per-block pass), peak memory in bytes (via `tracemalloc`), failure count (exceptions raised by `parse_thread_dump`), result count (`len(parse_thread_dump_all(raw))`), and a status distribution counting `FULL` / `PARTIAL` / `RAW` outcomes.

The benchmark MUST NOT abort on a per-block exception; the failure MUST be counted and the run MUST continue.

#### Scenario: Scale point N=100 records all metrics
- **WHEN** the benchmark runs with `--blocks 100`
- **THEN** the corresponding JSON entry contains `n_blocks=100`, `raw_bytes` (positive), `total_seconds`, `avg_us`, `p50_us`, `p95_us`, `p99_us`, `peak_memory_bytes`, `failures`, `result_count`, and a `status_distribution` object with `FULL` / `PARTIAL` / `RAW` keys

#### Scenario: Per-block pass times each block
- **WHEN** the benchmark records per-block latency
- **THEN** the number of per-block timing samples equals `result_count` (every parsed block was timed)

#### Scenario: Per-block failure does not abort the run
- **WHEN** `parse_thread_dump` raises for one block
- **THEN** the bench increments `failures`, continues with the remaining blocks, and the resulting JSON entry records the failure count

### Requirement: JSON Snapshot Schema
The output JSON MUST be a UTF-8 object with a top-level `benchmarks` array and a `timestamp` string. Each entry in `benchmarks` MUST contain `n_blocks` (int), `raw_bytes` (int), `total_seconds` (float, rounded to 4 decimal places), `avg_us` (float, rounded to 2 decimal places), `p50_us` / `p95_us` / `p99_us` (floats, rounded to 2 decimal places), `peak_memory_bytes` (int), `failures` (int), `result_count` (int), and `status_distribution` (object with `FULL` / `PARTIAL` / `RAW` integer keys).

#### Scenario: JSON round-trips
- **WHEN** the output JSON is loaded and inspected
- **THEN** it has a `benchmarks` array, a `timestamp` string, and every entry has all 10 numeric fields plus a 3-key `status_distribution`

#### Scenario: Percentile ordering is non-decreasing
- **WHEN** a benchmark entry's `p50_us` / `p95_us` / `p99_us` are inspected
- **THEN** `p50_us <= p95_us <= p99_us` for that entry

### Requirement: Real-World Fixtures
The system MUST track two real-world JVM thread dump samples under `tests/load/`: `real_dump_sample1.txt` (a Java 8 jstack output) and `real_dump_sample2.txt` (a Java 11 jstack output). The samples MUST be small enough to keep in the repo (8 threads and 12 threads respectively) and MUST exercise the parser on actual JVM output.

The Java 11 sample MUST include at least one module-qualified frame (a `module@version/` prefix in a `Native Method` location) so the parser's known issue with that pattern is reproducible from the tracked fixture.

#### Scenario: Java 8 sample parses successfully
- **WHEN** `parse_thread_dump_all(real_dump_sample1.txt)` is called
- **THEN** the result list has 8 entries and every entry's `parse_status` is either `FULL` or `PARTIAL`

#### Scenario: Java 11 sample parses successfully
- **WHEN** `parse_thread_dump_all(real_dump_sample2.txt)` is called
- **THEN** the result list has 12 entries and every entry's `parse_status` is either `FULL` or `PARTIAL`

### Requirement: Capability And Load Reports
The system MUST track two human-readable reports under `tests/load/`: `thread-stack-capability-report.md` and `thread-stack-load-report.md`.

The capability report MUST cover the 38 synthetic capability tests, the 27 `stack_parser` regression tests, the full-suite pass count (498/498), the per-thread results for both real fixtures, the known issues (Java 11 module-qualified `Native Method` not detected as native, threads with no frames correctly marked `PARTIAL`), the evidence paths, and a conclusion (PASS with 1 minor known issue).

The load report MUST cover the test purpose, the three scale points, the data source (the synthetic generator in `thread_stack_bench.py`), the test method, the per-scale results (total time, per-block p50/p95/p99, peak memory, status distribution, failure count), and a discussion of scaling characteristics.

#### Scenario: Capability report covers all 38 synthetic tests
- **WHEN** the capability report's "Test Cases — Expected vs Actual (Synthetic)" table is inspected
- **THEN** it contains 35+ rows and every row's `Status` column is `PASS`

#### Scenario: Load report covers all three scale points
- **WHEN** the load report is inspected
- **THEN** it contains results for 100, 1,000, and 10,000 thread blocks, each with total time, p50/p95/p99, peak memory, and status distribution

#### Scenario: Report numbers match the JSON
- **WHEN** the per-scale numbers in the load report are compared with the matching entries in `thread_stack_bench.json`
- **THEN** the totals, percentiles, and peak-memory figures are consistent (any reviewer-detectable drift means the report needs a refresh)
