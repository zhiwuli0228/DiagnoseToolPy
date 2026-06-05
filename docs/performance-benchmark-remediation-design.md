# Performance Benchmark Remediation Design

## 1. Problem Statement

The current load-test evidence chain is not reliable enough for review or merge decisions.

Observed issues:

1. `tests/load/results_diff.md` reports a passing result, but the current `results_after_stats.csv` and `results_after_failures.csv` show a full failure run caused by connection refusal.
2. `tests/load/diff_results.py` computes P95 by weighting per-endpoint P95 values, which is not a valid percentile aggregation method.
3. `data/indexes/bm25/corpus.jsonl` is still appearing in tracked diffs even though the project treats rebuildable indexes as cache data and `.gitignore` excludes it.

This means the repository can present a performance conclusion that is inconsistent with the raw benchmark artifacts.

## 2. Goal

Restore a trustworthy performance benchmarking workflow for `tests/load/` so that:

1. the markdown summary is derived from the exact raw artifacts under review,
2. the metric calculation matches Locust's authoritative aggregated row,
3. failed or invalid runs cannot silently look like valid evidence,
4. rebuildable cache data does not pollute benchmark-related review.

## 3. Scope

In scope:

- `tests/load/diff_results.py`
- `tests/load/run_bench.sh`
- `tests/load/README.md`
- `tests/load/results_diff.md` regeneration rules
- repository handling for `data/indexes/bm25/corpus.jsonl`

Out of scope:

- frontend or backend runtime performance optimization
- changing the Locust scenario mix
- changing current P0 thresholds unless separately approved

## 4. Root Cause Analysis

### 4.1 Artifact inconsistency

The report file is treated as review evidence, but the workflow does not guarantee that:

- baseline and after files are from the same comparison cycle,
- the target server was reachable for each run,
- the committed markdown summary was regenerated after the latest CSV files were produced.

### 4.2 Invalid metric derivation

Locust already emits an `Aggregated` row that contains:

- `Requests/s`
- `Average Response Time`
- percentile columns such as `95%`
- aggregated failure data

The current script re-derives P95 from endpoint rows. That is invalid because percentiles are not additive or weight-averagable across distributions.

### 4.3 Rebuildable cache tracked in review

`data/indexes/bm25/corpus.jsonl` is a rebuildable local index, not durable truth. If it remains tracked, unrelated performance or feature reviews may include noisy data changes with no governance value.

## 5. Target State

After remediation:

1. `diff_results.py` reads only the `Aggregated` row for throughput, average latency, P95, request count, and failure count.
2. `diff_results.py` fails fast if the required aggregated fields are missing or malformed.
3. `run_bench.sh` verifies target reachability before invoking Locust.
4. A run that produces connection-refused failures is treated as an invalid benchmark attempt, not as acceptable evidence for comparison.
5. `results_diff.md` is regenerated only from the current `results_baseline_stats.csv` and `results_after_stats.csv`.
6. `corpus.jsonl` is no longer part of normal tracked review diffs.

## 6. Design

### 6.1 `diff_results.py` data model

Implementation agents should replace the current implicit tuple aggregation with an explicit aggregated metrics model.

Recommended fields:

- `requests_per_sec: float`
- `p95_ms: float`
- `avg_ms: float`
- `request_count: int`
- `failure_count: int`
- `failure_rate_pct: float`

Recommended behavior:

1. Read CSV rows.
2. Find exactly one `Name == "Aggregated"` row.
3. Parse all required numeric fields from that row.
4. Compute failure rate from aggregated request and failure counts.
5. Render markdown from those values only.

The script must exit non-zero when:

- either stats file is missing,
- no aggregated row exists,
- multiple aggregated rows exist,
- aggregated numeric fields cannot be parsed,
- threshold checks fail.

### 6.2 Invalid-run detection

The benchmark workflow should distinguish:

- valid benchmark result
- threshold failure
- invalid execution environment

Minimum requirement:

- if aggregated failure count is greater than zero, the markdown must still show the real numbers;
- if `results_after_failures.csv` contains only connection or transport failures, reviewers must treat the run as invalid environment evidence and rerun it.

Preferred implementation:

- `run_bench.sh` performs a preflight `GET /health` check against the target host;
- if the health probe fails, the script exits before starting Locust.

This prevents a stopped server from producing misleading comparison files.

### 6.3 Artifact coherence rules

The workflow must treat the following files as one evidence set:

- `results_baseline_stats.csv`
- `results_after_stats.csv`
- `results_baseline_failures.csv`
- `results_after_failures.csv`
- `results_diff.md`

Rules:

1. `results_diff.md` must be regenerated after the final baseline and after CSV files exist.
2. Review conclusions must be based on the CSV files and generated markdown from the same run pair.
3. If a later rerun overwrites either baseline or after files, `results_diff.md` must be regenerated before review.

Recommended documentation note:

- `results_diff.md` is a derived summary, not the source of truth.
- The `results_*` CSV files are the authoritative benchmark artifacts for that comparison cycle.

### 6.4 Cache artifact governance

`data/indexes/bm25/corpus.jsonl` should be treated consistently with project rules:

- rebuildable
- local cache
- not durable truth

Required remediation:

1. remove the file from version tracking if it is currently tracked,
2. keep `.gitignore` excluding it,
3. do not use changes in this file as feature or performance evidence.

## 7. Required Documentation Updates

Implementation agents must update:

- `tests/load/README.md`
- `docs/00-project/current-state.md` if the remediation is completed and merged

`tests/load/README.md` must clearly state:

- preflight requirement for a live backend,
- which files are authoritative,
- how to regenerate the markdown summary,
- that connection-refused runs are invalid benchmark evidence.

## 8. Verification Requirements

Minimum tests for the remediation:

1. unit test: `diff_results.py` uses the `Aggregated` row rather than weighted endpoint rows,
2. unit test: malformed or missing aggregated row causes non-zero exit,
3. unit test: failure-rate threshold breach causes non-zero exit,
4. unit test: throughput threshold breach causes non-zero exit,
5. unit test: rendered markdown matches aggregated input values,
6. script-level verification: benchmark helper fails early when `/health` is unreachable.

If shell-script automation is difficult to unit test directly, the implementation agent must at least document and manually verify the preflight behavior.

## 9. Acceptance Criteria

The remediation is complete only when all of the following are true:

1. `results_diff.md` matches the current baseline and after CSV artifacts.
2. P95, average latency, throughput, and failure rate are sourced from Locust's aggregated data path.
3. A stopped backend cannot produce a superficially valid benchmark report without a visible failure.
4. The repository no longer surfaces `data/indexes/bm25/corpus.jsonl` as a normal tracked change.
5. The benchmark README documents the corrected workflow.

## 10. Execution Order For Implementation Agents

1. Fix `diff_results.py` metric sourcing and error handling.
2. Add regression tests for valid and invalid CSV inputs.
3. Add preflight health verification to `run_bench.sh`.
4. Update `tests/load/README.md`.
5. Remove `data/indexes/bm25/corpus.jsonl` from tracking if still tracked.
6. Rerun baseline and after benchmarks against a live server.
7. Regenerate `results_diff.md`.
8. Submit the artifact set for review.
