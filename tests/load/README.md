# DiagnoseToolPy Load Test (Locust)

This directory contains a Locust-based load test for measuring end-to-end
throughput, latency, and error rate of the DiagnoseToolPy backend.

## Files

| File | Committed? | Purpose |
|---|---|---|
| `locustfile.py` | yes | User scenario (mixed endpoints, 50 users default) |
| `run_bench.sh` | yes | One-shot Locust runner with preflight health check |
| `diff_results.py` | yes | Compare two CSV runs, emit markdown, enforce thresholds |
| `results_baseline_stats.csv` | gitignored | Raw Locust stats for the baseline run |
| `results_baseline_failures.csv` | gitignored | Raw Locust failure details for the baseline run |
| `results_after_stats.csv` | gitignored | Raw Locust stats for the after run |
| `results_after_failures.csv` | gitignored | Raw Locust failure details for the after run |
| `report_baseline.html` | gitignored | Locust HTML report for baseline (debug only) |
| `report_after.html` | gitignored | Locust HTML report for after (debug only) |
| `results_diff.md` | yes | Generated markdown summary; derived from CSVs |

## Preflight (mandatory)

`run_bench.sh` performs a `GET $HOST/health` check before invoking Locust.
If the backend is not reachable, the script exits with code 3 and a message
telling you how to start the server. The preflight is strict: any non-200
response (including 404 from a misrouted proxy) is treated as failure.
There are no retries.

## Authoritative Artifacts

The following five files form one benchmark evidence set for a comparison
cycle:

- `results_baseline_stats.csv`
- `results_after_stats.csv`
- `results_baseline_failures.csv`
- `results_after_failures.csv`
- `results_diff.md`

The `results_*_stats.csv` and `results_*_failures.csv` files are the
**source of truth** for that cycle. `results_diff.md` is a derived summary
generated from the CSVs by `diff_results.py`.

Rules:

1. `results_diff.md` must be regenerated after the final baseline and after
   CSV files exist.
2. Review conclusions must be based on the CSV files and generated markdown
   from the same run pair.
3. If a later rerun overwrites either baseline or after files,
   `results_diff.md` must be regenerated before review.

## How to Run

```bash
# 1. Start backend on :18080
uv run uvicorn diagnose_tool.main:app --host 127.0.0.1 --port 18080

# 2. Baseline (on main, pre-change)
git checkout claude_master
bash tests/load/run_bench.sh baseline

# 3. After (on feature branch)
git checkout perf/p0-gzip-and-route-lazy
bash tests/load/run_bench.sh after

# 4. Compare
uv run python tests/load/diff_results.py
```

If a later rerun overwrites either baseline or after files, regenerate
`results_diff.md` before review (step 4).

## Regenerate the Summary

If you have refreshed `results_baseline_stats.csv` or `results_after_stats.csv`
without re-running the full comparison workflow, regenerate the markdown
summary manually:

```bash
uv run python tests/load/diff_results.py
```

This reads the current CSV files, recomputes the diff, and writes
`results_diff.md`.

## Invalid Runs

A run is **invalid** if:

- the preflight failed but Locust somehow started (should not happen),
- the aggregated failure rate is approximately 100% AND
  `results_after_failures.csv` contains only connection-refused or transport
  errors,
- the Aggregated row is missing or duplicated in the stats CSV.

Invalid runs are NOT acceptable evidence for review. If `diff_results.py`
exits 2, the run is invalid — investigate the cause (server down, wrong
`--host`, port conflict) and rerun. `diff_results.py` exits 1 only when
thresholds are genuinely violated, which is a real performance signal.

## Acceptance Thresholds (P0)

| Metric | Threshold |
|---|---|
| Failure rate | < 5% |
| P95 latency | < 6000ms |
| Throughput | >= 6.0 req/s |
