# Exception Cluster Matching Performance Implementation Plan

> **For agentic workers:** Use the local OpenSpec apply flow to implement this plan task-by-task.

**Goal:** Reduce post-scan exception categorization time by stabilizing cluster identity, reusing case match data, bounding historical matching, and exposing phase metrics.

**Architecture:** The analyzer remains responsible for cluster orchestration and streaming aggregation. Retrieval provides a reusable file-backed case matcher that works without embeddings. Durable case truth remains in `data/cases/{case_id}/case.md` and `metadata.yaml`; any loaded matcher or generated index is rebuildable.

**Tech Stack:** Python 3.11+, pathlib, dataclasses/Pydantic where existing code uses them, PyYAML, pytest, ruff, existing FastAPI task APIs.

---

## Task 1: Baseline and Regression Tests

- [ ] **Step 1:** Open `diagnose_tool/analyzer/cluster_analyzer.py` and identify current `_build_group_key`, `_compute_time_distribution`, and `_match_historical_cases` behavior.
- [ ] **Step 2:** Add a test in `tests/test_cluster_analyzer.py` that feeds two parsed error dicts with the same exception class and different timestamps, then asserts one group key without `[HH:MM]` or `[HH]`.
- [ ] **Step 3:** Add a test that verifies time data is still represented in cluster distribution for multi-time samples.
- [ ] **Step 4:** Add retrieval failure-mode fixtures under temporary test directories for empty casebase, malformed `metadata.yaml`, and metadata-only case.
- [ ] **Step 5:** Add a top-N test using synthetic `AggregatedGroup` objects and a small matching limit.
- [ ] **Step 6:** Run `uv run pytest tests/test_cluster_analyzer.py tests/test_retrieval.py` and confirm new tests fail for the current implementation where expected.

Commit point: regression tests describe the intended behavior before implementation.

## Task 2: Stable Exception Grouping

- [ ] **Step 1:** Update `diagnose_tool/analyzer/cluster_analyzer.py` so `_build_group_key` does not append timestamp-derived suffixes.
- [ ] **Step 2:** If shared aggregator behavior is used for cluster grouping, update `diagnose_tool/analyzer/log_aggregator.py` consistently or keep the change isolated to cluster flow.
- [ ] **Step 3:** Ensure `_build_sample_message` can still include human-readable time if needed without affecting the group key.
- [ ] **Step 4:** Update or add `_compute_time_distribution` tests to verify timing context remains available.
- [ ] **Step 5:** Run `uv run pytest tests/test_cluster_analyzer.py tests/test_header_parser.py`.

Commit point: exception grouping identity is stable and time remains context.

## Task 3: Task-local Case Match Index

- [ ] **Step 1:** Add a retrieval helper module such as `diagnose_tool/retrieval/case_match_index.py`.
- [ ] **Step 2:** Define a small record type containing `case_id`, metadata fields, bounded summary/body text, and skip/error status as needed.
- [ ] **Step 3:** Implement a loader that iterates `data/cases/` once, reads `metadata.yaml` safely, and reads selected `case.md` sections when present.
- [ ] **Step 4:** Implement scoring helpers equivalent to existing keyword/rule/body matching using loaded records instead of filesystem reads.
- [ ] **Step 5:** Update `ClusterAnalyzer._match_historical_cases` to create/load the case matcher once per task matching phase and reuse it for groups.
- [ ] **Step 6:** Add a test with mocked file reads or loader call counts proving the casebase is not re-read per group.
- [ ] **Step 7:** Run `uv run pytest tests/test_retrieval.py tests/test_cluster_analyzer.py`.

Commit point: historical matching reuses task-local case data and still works from files.

## Task 4: Bounded Historical Matching

- [ ] **Step 1:** Add a default matching limit constant near cluster analyzer configuration, for example `MAX_MATCHED_GROUPS = 50`.
- [ ] **Step 2:** Sort aggregated groups by count before matching and select only the first `MAX_MATCHED_GROUPS` for historical case matching.
- [ ] **Step 3:** Build cluster results for all groups; set `matched_cases=[]` for groups outside the matching window.
- [ ] **Step 4:** If configuration is added, update `config/app.yaml`, config models, and config tests; otherwise document the constant as an implementation default.
- [ ] **Step 5:** Run `uv run pytest tests/test_cluster_analyzer.py`.

Commit point: matching work is bounded while all clusters remain visible.

## Task 5: Phase Metrics and Benchmark Evidence

- [ ] **Step 1:** Add timing capture around scan/aggregate, case matching, result writing, and matched-lines cache writing in `diagnose_tool/analyzer/cluster_analyzer.py`.
- [ ] **Step 2:** Extend progress updates with additive fields such as `phase_timings_ms`, `group_count`, `matched_group_count`, and `case_index_case_count`.
- [ ] **Step 3:** Ensure failures write terminal status and preserve available metrics.
- [ ] **Step 4:** Update `tests/test_cluster_analyzer.py` or `tests/test_cluster_api.py` to assert the additive progress fields are present when available.
- [ ] **Step 5:** Update `tests/load/analysis_benchmark.py` to include phase metrics in JSON/Markdown benchmark artifacts when returned by the API.
- [ ] **Step 6:** Run `uv run pytest tests/test_cluster_analyzer.py tests/test_cluster_api.py tests/test_analysis_benchmark.py`.

Commit point: post-scan bottlenecks are observable through task and benchmark evidence.

## Task 6: Documentation and Acceptance

- [ ] **Step 1:** Update `docs/00-project/current-state.md` with the completed optimization capability and any remaining limitations.
- [ ] **Step 2:** Update `docs/01-architecture/large-log-cluster-scaling-design.md` or add a focused architecture note describing stable group keys, top-N matching, and case match index behavior.
- [ ] **Step 3:** Confirm docs state no mandatory database was introduced and indexes remain rebuildable caches.
- [ ] **Step 4:** Run focused tests: `uv run pytest tests/test_cluster_analyzer.py tests/test_retrieval.py tests/test_cluster_api.py tests/test_analysis_benchmark.py`.
- [ ] **Step 5:** Run lint: `uv run ruff check .`.
- [ ] **Step 6:** When a local benchmark server and datasets are available, run `powershell -ExecutionPolicy Bypass -File tests/load/run_requirement_acceptance.ps1`.

Commit point: implementation is documented and verification evidence is ready for OpenSpec verify/finalize.
