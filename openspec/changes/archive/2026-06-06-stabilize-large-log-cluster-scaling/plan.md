# Large Log Cluster Scaling Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development
> to implement this plan task-by-task.

**Goal:** Make large-directory cluster execution complete or fail explicitly under benchmark pressure, while preserving streaming reads and file-based runtime state.

**Architecture:** Add source-aware task admission in the cluster API, enrich cluster progress with byte-based telemetry, reduce scan-stage per-line cost, and tighten benchmark reporting so acceptance maps directly to real evidence. The implementation stays inside existing FastAPI, analyzer, and local file-state boundaries.

**Tech Stack:** Python 3.12, FastAPI, pathlib, file-based task outputs, pytest, PowerShell benchmark wrappers.

---

## Task 1: Cluster Admission And Runtime State

- [ ] **Step 1:** Inspect `diagnose_tool/api/routes_cluster.py` and define a normalized source-key helper plus active-task lookup shape under `data/output/`.
- [ ] **Step 2:** Add tests in `tests/test_cluster_api.py` for duplicate same-source submit, different-source submit, and terminal-task resubmission.
- [ ] **Step 3:** Implement same-source admission reuse/serialization logic and ensure the response remains API-compatible.
- [ ] **Step 4:** Add explicit terminal failure persistence for background task exceptions/timeouts and verify `progress.json` does not remain stuck in `scanning`.
- [ ] **Step 5:** Run `uv run pytest tests/test_cluster_api.py tests/test_cluster_analyzer.py`.

## Task 2: Byte-Based Progress

- [ ] **Step 1:** Extend `ClusterAnalyzer._prepare_file_list()` totals and progress structures to track bytes as well as files.
- [ ] **Step 2:** Update `ClusterAnalyzer._scan_and_aggregate_streaming()` so progress writes occur by byte thresholds and include current-file context.
- [ ] **Step 3:** Add regression tests in `tests/test_cluster_analyzer.py` for progress fields and intra-file progress movement.
- [ ] **Step 4:** Run `uv run pytest tests/test_cluster_analyzer.py`.

## Task 3: Scan-Stage Efficiency

- [ ] **Step 1:** Add a low-cost severity prefilter path before expensive parse/group operations in `diagnose_tool/analyzer/cluster_analyzer.py`.
- [ ] **Step 2:** Review `diagnose_tool/analyzer/reader.py` for any avoidable overhead while preserving line-by-line streaming.
- [ ] **Step 3:** Add tests for bounded sample retention and non-matching line behavior in `tests/test_cluster_analyzer.py` and `tests/test_reader.py`.
- [ ] **Step 4:** Run `uv run pytest tests/test_cluster_analyzer.py tests/test_reader.py`.

## Task 4: Benchmark Contract

- [ ] **Step 1:** Update `tests/load/analysis_benchmark.py` so cluster submit latency is recorded even when eventual completion fails.
- [ ] **Step 2:** Add or extend tests in `tests/test_analysis_benchmark.py` for failed cluster-run summaries.
- [ ] **Step 3:** Confirm `tests/load/prepare_analysis_datasets.py --profile smoke_scan_sample` still validates only `sample_zip`.
- [ ] **Step 4:** Run `uv run pytest tests/test_analysis_benchmark.py tests/test_prepare_analysis_datasets.py`.

## Task 5: End-To-End Verification

- [ ] **Step 1:** Start backend locally and run `.\tests\load\run_analysis_bench.ps1 -Profile smoke_scan_sample`.
- [ ] **Step 2:** Run `.\tests\load\run_analysis_bench.ps1 -Profile directory_concurrency_baseline`.
- [ ] **Step 3:** Review generated `directory_concurrency_baseline.md`, `directory_concurrency_baseline.json`, and `process-stats.csv` against the acceptance criteria in `docs/01-architecture/large-log-cluster-scaling-design.md`.
- [ ] **Step 4:** Update `docs/00-project/current-state.md` with implemented scaling behavior and verified benchmark outcome.
