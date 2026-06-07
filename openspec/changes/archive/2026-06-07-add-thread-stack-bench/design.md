## Context

`diagnose_tool/analyzer/thread_stack_parser.py` already passes 38 synthetic capability tests and 27 `stack_parser` regression tests, and the full test suite (498 tests) is green. The remaining gap is the **evidence layer** for the parser's correctness and performance, version-tracked so reviewers and future contributors can audit it without rerunning anything.

This change adds the load benchmark script, the current-run JSON evidence, the two real-world fixture dumps, and the human-readable capability and load reports. It does not touch the parser, the existing tests, or the existing analysis benchmark.

## Goals / Non-Goals

**Goals**
- A version-tracked Python load benchmark: `tests/load/thread_stack_bench.py`.
- A synthetic data generator that produces realistic HotSpot thread dump blocks at configurable scale (default: 100, 1k, 10k).
- Per-scale measurement: total wall time, per-block p50/p95/p99 latency, peak memory (via `tracemalloc`), failure count, status distribution, and result count.
- A canonical JSON evidence file: `tests/load/thread_stack_bench.json` (one snapshot of the most recent run; rerunning overwrites).
- Real-world fixture pair: `tests/load/real_dump_sample1.txt` (Java 8 jstack) and `tests/load/real_dump_sample2.txt` (Java 11 jstack).
- Human-readable reports: `tests/load/thread-stack-capability-report.md` and `tests/load/thread-stack-load-report.md`.

**Non-Goals**
- No change to `diagnose_tool/analyzer/thread_stack_parser.py`.
- No change to `tests/test_thread_stack_parser.py` or `tests/test_stack_parser.py`.
- No new dependency. The bench uses only `argparse`, `gc`, `json`, `statistics`, `time`, `tracemalloc`, and the existing parser module.
- No CI workflow. The bench is a manual, on-demand command; the JSON and reports are the persisted evidence.
- No fix for the Java 11 module-qualified Native Method detection issue. The capability report documents it; fixing it is a separate change.
- No streaming-mode benchmark. The current bench measures the existing `parse_thread_dump_all` over an in-memory string, which is sufficient for the report's three scale points.

## Decisions

### 1. Bench script is a single Python file with subcommand-less CLI

`thread_stack_bench.py` is a plain `argparse` script with two arguments: `--blocks` (one or more scale points, default `[100, 1000, 10000]`) and `--output` (JSON path, default `tests/load/thread_stack_bench.json`). This mirrors the simplicity of `prepare_analysis_datasets.py` and avoids introducing a subcommand tree for a one-purpose tool.

### 2. Synthetic block generation is deterministic and realistic

`_make_thread_block(index, state)` produces:
- A real HotSpot-style header: `"worker-NNNNNN" #N daemon prio=5 tid=0x... nid=0x... {state.lower()} [0x...]`.
- A `java.lang.Thread.State: {STATE}` line.
- 8 stack frames cycling across `com.example.module{0..7}.Service{index%10}` with mixed source types (file:line, Native Method when `index%5==0` and depth==0, Unknown Source when `index%7==0` and depth==1).
- A lock hint for BLOCKED (`waiting to lock <0x...> (a java.lang.Object)`) and WAITING (`parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock)`).

Deterministic across runs (no randomness), so JSON snapshots are reproducible.

### 3. Two-pass timing: total and per-block

- **Total time** is `time.perf_counter()` around `parse_thread_dump_all(raw)`. This is the end-to-end throughput.
- **Per-block latency** is a second pass that splits the dump on `\n\n` and times `parse_thread_dump(block_text)` per block. Percentiles (p50/p95/p99) come from this pass.

The per-block pass is intentional: `parse_thread_dump_all` may not measure each block individually, and the per-block distribution is what matters for tail-latency analysis.

### 4. Memory measurement via `tracemalloc`

`tracemalloc.start()` runs across the full bench. `get_traced_memory()` after the per-block pass gives the peak allocated-bytes figure. The `stop()` call is paired with the `start()`. No subprocess; no external profiler. This is enough to detect regressions in synthetic-dump memory usage and is consistent with what the analysis-bench entrypoint does for the process-stats collector.

### 5. JSON is one snapshot, overwritten on rerun

The bench writes a single `benchmarks` array (one entry per scale point) plus a `timestamp`. Rerunning overwrites. The reports cite the JSON by file path; if the JSON is rerun and the numbers change, the reports are stale and a reviewer should rerun and update.

### 6. Real-world fixtures are tracked

`real_dump_sample1.txt` is a small Java 8 jstack output (8 threads). `real_dump_sample2.txt` is a small Java 11 jstack output (12 threads), chosen to exercise the module-qualified Native Method case (documented as a known issue in the capability report). Both are tracked because they are small, public, and stable references for future regression coverage.

### 7. Capability and load reports are separate, hand-authored, and stable

The capability report (`thread-stack-capability-report.md`) covers the 38 synthetic tests, the 27 regression tests, the full-suite pass count (498/498), and the per-thread results for both real dumps. The load report (`thread-stack-load-report.md`) covers the three scale points, the per-block latency percentiles, the peak memory figures, the status distribution, and the failure count (always 0 for synthetic). The numbers in the reports match the JSON.

## Architecture

```text
  +----------------------------+
  | thread_stack_bench.py      |
  |  - argparse: --blocks,      |
  |    --output                 |
  |  - _make_thread_block       |
  |  - make_synthetic_dump      |
  |  - run_bench (2-pass timing)|
  |  - main: write JSON         |
  +----------------------------+
                |
                v
  +----------------------------+
  | thread_stack_bench.json     |  (tracked; one snapshot)
  |  benchmarks:                |
  |    - {n_blocks, raw_bytes,  |
  |       total_seconds,        |
  |       avg_us, p50_us,       |
  |       p95_us, p99_us,       |
  |       peak_memory_bytes,    |
  |       failures,             |
  |       result_count,         |
  |       status_distribution}  |
  |  timestamp                  |
  +----------------------------+

  Tracked fixtures and reports:
  - real_dump_sample1.txt     (Java 8 jstack, 8 threads)
  - real_dump_sample2.txt     (Java 11 jstack, 12 threads)
  - thread-stack-capability-report.md
  - thread-stack-load-report.md
```

## Data Flow

1. Operator runs `uv run python tests/load/thread_stack_bench.py` (or with `--blocks 100 1000 10000 --output path/to.json`).
2. For each scale point `N`:
   a. `make_synthetic_dump(N)` produces a realistic thread dump string of size ~0.66 KB per block.
   b. `gc.collect()` + `tracemalloc.start()` to baseline memory.
   c. `parse_thread_dump_all(raw)` runs end-to-end; total wall time recorded.
   d. The dump is split on `\n\n`; per-block `parse_thread_dump` is timed, and the result's `parse_status.value` is folded into `status_distribution`. Failures are counted but do not abort the run.
   e. `tracemalloc.get_traced_memory()` gives the peak allocated-bytes; `tracemalloc.stop()` ends the trace.
   f. Per-block durations are sorted; p50/p95/p99 and the mean are computed.
3. The aggregated result for `N` is appended to `benchmarks`.
4. The JSON is written to the default or `--output` path.

## Module Responsibilities

### `tests/load/thread_stack_bench.py`
- `argparse` CLI (`--blocks`, `--output`).
- Synthetic block + dump generators (`_make_thread_block`, `make_synthetic_dump`).
- `run_bench(n_blocks) -> dict`: two-pass timing + memory + status distribution + failure count.
- `main()`: iterates over `--blocks`, prints a one-line per-scale summary, writes the JSON.

### `tests/load/thread_stack_bench.json`
- One snapshot of the most recent run.
- Schema: `{ benchmarks: [ { n_blocks, raw_bytes, total_seconds, avg_us, p50_us, p95_us, p99_us, peak_memory_bytes, failures, result_count, status_distribution }, ... ], timestamp }`.

### `tests/load/real_dump_sample1.txt`
- Java 8 jstack output, 8 threads, sourced from a public GitHub example.

### `tests/load/real_dump_sample2.txt`
- Java 11 jstack output, 12 threads, sourced from a public GitHub example. Includes a module-qualified `Native Method` frame (documented in the capability report's known issues).

### `tests/load/thread-stack-capability-report.md`
- Coverage table (synthetic + real).
- Test execution summary (38/38, 27/27, 498/498).
- Real-world dump tables (Java 8 and Java 11).
- Known issues.
- Synthetic test cases (35 expected-vs-actual rows).
- Evidence paths.
- Conclusion: PASS with 1 minor known issue.

### `tests/load/thread-stack-load-report.md`
- Test purpose, scale, data source, test method.
- Per-scale results (total time, p50/p95/p99, peak memory, status distribution, failure count).
- Discussion of scaling characteristics.

## Storage

All seven files are tracked. The JSON is the only file that is "data" in any meaningful sense; everything else is source code, fixture, or documentation. The JSON is small (~3 KB at the current scale points) and is not regenerated on every CI run, so the repo does not get noisy.

No new durable database, no new index, no new cache.

## Error Handling

- `parse_thread_dump` exceptions are caught per block and counted as `failures`; the bench does not abort. A non-zero `failures` value in the JSON is a clear signal that the parser regressed.
- The CLI returns a non-zero exit code on argparse errors (e.g., `--blocks` is empty).
- The JSON write uses `Path.write_text(json.dumps(output, indent=2), encoding="utf-8")`; an unwritable path surfaces as a normal Python exception with a clear message.

## Memory Behavior

- The synthetic dump is materialized in memory as a single string (up to ~6.6 MB at the 10k-block scale). This is intentional: the bench measures the end-to-end parser over the full dump. No streaming.
- `tracemalloc` tracks Python-level allocations only; the parser does not use C extensions, so the figure is representative.
- `gc.collect()` runs once per scale point before the trace starts, so the measured peak excludes the natural collection noise from generating the synthetic dump.

## Tests

- The bench itself is a test artifact; it does not need a regression test.
- The capability report is the regression evidence for the parser. Running the bench script is a manual check.
- The numbers in the reports and the JSON should match. A reviewer can re-run the bench and `diff` the new JSON against the report; if they diverge materially, the report needs a refresh.

## Compatibility

- The parser is unchanged; no API impact.
- No backend, no frontend, no casebase, no retrieval, no exporter changes.
- The bench script imports the parser via `sys.path.insert(0, project_root)` so it can be run as `python tests/load/thread_stack_bench.py` from the project root without installation.

## Open Questions

- Should the bench become a per-profile target of `analysis_benchmarks.yaml`? Deferred — the analysis-bench profile system targets HTTP endpoints.
- Should the JSON snapshot be replaced by a per-run directory? Deferred — the current single-snapshot approach is sufficient for evidence.
