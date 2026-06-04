# DiagnoseToolPy Load Test (Locust)

This directory contains a Locust scenario for measuring end-to-end
throughput, latency, and error rate.

## Files

- `locustfile.py` — user scenario
- `run_bench.sh` — single-run helper (tag + host)
- `diff_results.py` — compare two CSV runs, emit markdown, exit non-zero on threshold fail
- `results_*.csv`, `report_*.html` — generated; gitignored
- `results_diff.md` — generated; committed for the PR

## Run

```bash
# 1. Start backend on :18080
uv run uvicorn diagnose_tool.main:app --host 127.0.0.1 --port 18080

# 2. Baseline (on main, pre-change)
git checkout claude_master
./tests/load/run_bench.sh baseline

# 3. After (on feature branch)
git checkout perf/p0-gzip-and-route-lazy
./tests/load/run_bench.sh after

# 4. Compare
uv run python tests/load/diff_results.py
```

## Acceptance Thresholds (P0)

| Metric | Threshold |
|---|---|
| Failure rate | < 5% |
| P95 latency | < 6000ms |
| Throughput | >= 6.5 req/s (conservative +20% vs 5.47 baseline) |
