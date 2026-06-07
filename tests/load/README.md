# DiagnoseToolPy Load Test (Locust)

This directory contains a Locust-based load test for measuring end-to-end
throughput, latency, and error rate of the DiagnoseToolPy backend.

## Files

| File | Committed? | Purpose |
|---|---|---|
| `locustfile.py` | yes | User scenario (mixed endpoints, 50 users default) |
| `run_bench.sh` | yes | One-shot Locust runner with preflight health check |
| `diff_results.py` | yes | Compare two CSV runs, emit markdown, enforce thresholds |
| `analysis_benchmarks.yaml` | yes | Canonical analysis benchmark standard: datasets, profiles, thresholds |
| `analysis_benchmark.py` | yes | Automated runner for large-log scan and cluster benchmarks |
| `prepare_analysis_datasets.py` | yes | Prepares declared benchmark datasets, including ZIP-to-directory extraction |
| `run_analysis_bench.ps1` | yes | PowerShell entrypoint for agents to execute the analysis benchmark standard |
| `acceptance_suites.yaml` | yes | Canonical acceptance suite definitions that map requirement-level acceptance to benchmark profiles |
| `requirement_acceptance.py` | yes | Acceptance suite helper for resolving profiles and generating acceptance summaries |
| `run_requirement_acceptance.ps1` | yes | One-command requirement acceptance entrypoint |
| `collect_process_stats.ps1` | yes | Background sampler for Python/uvicorn process CPU and memory evidence |
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

All metrics in `results_diff.md` (P95, average latency, throughput, failure rate) are
read from Locust's single `Aggregated` row only — not computed across per-endpoint
rows. This matches the design's "source of truth from Locust's aggregated data path" rule.

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

## Automated Analysis Benchmark Standard

The Locust workflow above measures lightweight HTTP throughput. It does not
cover the real heavy-path problem for this project: large ZIP scans, large
directory scans, and asynchronous exception clustering on large inputs.

Use the analysis benchmark standard for those cases.

### Standard Inputs

The canonical manifest is:

```text
tests/load/analysis_benchmarks.yaml
```

It defines:

- dataset IDs and source paths
- ZIP and expanded-directory benchmark inputs
- optional ZIP-backed directory preparation rules
- benchmark profiles
- concurrency and iterations
- request, poll, and task timeouts
- PASS/FAIL thresholds

Agents should treat that manifest as the source of truth instead of inventing
ad-hoc benchmark arguments.

### Standard Execution

PowerShell:

```powershell
.\tests\load\run_analysis_bench.ps1 -Profile smoke_scan_sample
.\tests\load\run_analysis_bench.ps1
.\tests\load\run_analysis_bench.ps1 -Profile cluster_baseline
.\tests\load\run_analysis_bench.ps1 -Profile directory_concurrency_heavy
.\tests\load\run_requirement_acceptance.ps1
```

Direct Python:

```bash
uv run python tests/load/prepare_analysis_datasets.py --profile smoke_scan_sample
uv run python tests/load/analysis_benchmark.py
uv run python tests/load/analysis_benchmark.py --profile cluster_baseline
```

Optional host override:

```powershell
.\tests\load\run_analysis_bench.ps1 -BaseUrl http://127.0.0.1:18080
```

### Standard Outputs

The runner writes machine-readable and review-friendly artifacts under a
timestamped run directory:

```text
tests/load/artifacts/{run_id}/
```

For each profile:

- `{profile}.json` — raw run records and computed summary
- `{profile}.md` — markdown review report
- `index.json` — run index for all executed profiles
- `process-stats.csv` — sampled backend/runtime process CPU and memory snapshots
- `run-meta.json` — execution metadata (host, config, run id, exit code)

Requirement acceptance runs add:

- `acceptance-summary.json` - suite-level pass/fail and profile aggregation
- `acceptance-summary.md` - suite-level review summary
- `acceptance-run-meta.json` - acceptance entrypoint metadata

`acceptance-summary.json` and `acceptance-summary.md` are generated only when the
benchmark run itself succeeds. If the benchmark runner exits non-zero, the
finalizer skips summary generation and the run meta records the benchmark and
acceptance exit codes.

### Standard Semantics

`source_scan` scenario:

- calls `POST /api/source/scan`
- measures metadata scan latency and failure rate

`cluster_task` scenario:

- calls `POST /api/cluster`
- measures submit latency
- polls `GET /api/cluster/{task_id}` until `done` or timeout
- records wall-clock completion time and completion rate

The current standard includes both ZIP inputs and the expanded directory
input backed by `E:\006tooldevelop\logsearch\out-final-expanded.zip`. The
wrapper prepares `E:\006tooldevelop\logsearch\prepared\out-final-expanded`
automatically before the benchmark, so agents do not need to unzip the large
directory manually.

`run_analysis_bench.ps1` starts `collect_process_stats.ps1` automatically.
Agents should treat `process-stats.csv` as required evidence when reporting
large-input performance behavior.
It also runs `prepare_analysis_datasets.py` before the benchmark so directory
profiles target a real extracted dataset instead of an empty placeholder tree.

### Feasibility Rule

Any new or changed benchmark workflow should be validated at small scale before
being treated as ready. The required smoke path is:

```powershell
.\tests\load\run_analysis_bench.ps1 -Profile smoke_scan_sample
```

This verifies:

- wrapper argument binding
- dataset preparation selection
- artifact directory creation
- benchmark runner invocation path

Only after the smoke profile works should heavier profiles such as
`directory_concurrency_baseline` or `directory_concurrency_heavy` be used as
evidence.

## Requirement Acceptance

The benchmark standard is necessary but not sufficient for sign-off. The
canonical acceptance entrypoint is:

```powershell
.\tests\load\run_requirement_acceptance.ps1
```

This executes the suite defined in:

```text
tests/load/acceptance_suites.yaml
```

The default suite for the current requirement is:

- `smoke_scan_sample`
- `directory_concurrency_baseline`

This means every acceptance run automatically:

1. validates the wrapper and artifact flow at small scale
2. validates the real current requirement against the large-directory baseline
3. emits a suite-level acceptance summary

Reviewers should treat `acceptance-summary.json` and `acceptance-summary.md`
as the top-level acceptance artifacts for the current requirement.

### Agent Workflow

When another agent needs benchmark evidence, it should:

1. Verify the backend is running and reachable on `/health`.
2. Review `tests/load/analysis_benchmarks.yaml`.
3. Run `run_analysis_bench.ps1` for the required profile set.
4. Attach the generated `tests/load/artifacts/*.json` and `*.md` artifacts.
5. Treat threshold failures as benchmark failures, not as documentation-only warnings.
