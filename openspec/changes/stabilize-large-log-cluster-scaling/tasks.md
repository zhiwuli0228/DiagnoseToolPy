## 1. Cluster Admission And Task State

- [ ] 1.1 Add same-source cluster task coordination in `diagnose_tool/api/routes_cluster.py` and supporting runtime state helpers
  - Files: `diagnose_tool/api/routes_cluster.py`, `diagnose_tool/core/` helper module if needed, `tests/test_cluster_api.py`
  - Behavior: prevent duplicate same-source full scans from running concurrently; return or reuse active task identity for duplicate submissions
  - Tests: duplicate same-source request, different-source request, failed-task resubmission
  - Verification: `uv run pytest tests/test_cluster_api.py`

- [ ] 1.2 Persist explicit terminal failure state for timed-out or failed cluster tasks
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`, `diagnose_tool/api/routes_cluster.py`, `tests/test_cluster_analyzer.py`
  - Behavior: cluster tasks must not remain indefinitely in `scanning`; progress output must reflect terminal failure reason
  - Tests: timeout transition, failed progress persistence
  - Verification: `uv run pytest tests/test_cluster_analyzer.py`

## 2. Byte-Based Progress And Scan Efficiency

- [ ] 2.1 Extend cluster progress output with byte counters and current-file context
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`, `docs/01-architecture/storage-contract.md` if contract wording changes, `tests/test_cluster_analyzer.py`
  - Behavior: write `processed_bytes`, `total_bytes`, and current file/message during large scans
  - Tests: progress fields present, progress advances within large-file simulation
  - Verification: `uv run pytest tests/test_cluster_analyzer.py`

- [ ] 2.2 Reduce scan-stage per-line work while preserving streaming reads and bounded samples
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`, `diagnose_tool/analyzer/reader.py`, `tests/test_cluster_analyzer.py`, `tests/test_reader.py`
  - Behavior: avoid expensive clustering work for non-matching lines and keep memory bounded for large files
  - Tests: non-matching line fast path, bounded sample retention, large-file stream regression
  - Verification: `uv run pytest tests/test_cluster_analyzer.py tests/test_reader.py`

## 3. Benchmark Contract And Evidence

- [ ] 3.1 Correct benchmark metrics so submit latency is reported independently from eventual task success
  - Files: `tests/load/analysis_benchmark.py`, `tests/test_analysis_benchmark.py`
  - Behavior: cluster submit latency remains finite even if the task later times out
  - Tests: failed task summary still includes measured submit latency
  - Verification: `uv run pytest tests/test_analysis_benchmark.py`

- [ ] 3.2 Keep benchmark dataset preparation and profile evidence aligned with the large-directory requirement
  - Files: `tests/load/analysis_benchmarks.yaml`, `tests/load/prepare_analysis_datasets.py`, `tests/load/README.md`, `tests/test_prepare_analysis_datasets.py`
  - Behavior: profile-scoped dataset preparation and benchmark evidence remain the canonical validation path
  - Tests: profile dataset filtering, prepared-directory reuse/size checks
  - Verification: `uv run pytest tests/test_prepare_analysis_datasets.py`

## 4. Documentation And Acceptance

- [ ] 4.1 Publish the end-to-end scaling design and evolution plan for future agents and reviewers
  - Files: `docs/01-architecture/large-log-cluster-scaling-design.md`, `openspec/changes/stabilize-large-log-cluster-scaling/*.md`
  - Behavior: document current bottleneck, chosen architecture, evolution phases, and acceptance criteria
  - Tests: doc review against benchmark evidence and architecture rules
  - Verification: manual review of design doc and OpenSpec artifacts

- [ ] 4.2 Update continuity docs after implementation and rerun benchmark evidence
  - Files: `docs/00-project/current-state.md`, `tests/load/artifacts/*` generated outputs
  - Behavior: record implemented scaling behavior and attach benchmark-backed verification results
  - Tests: rerun `smoke_scan_sample` and `directory_concurrency_baseline`
  - Verification: benchmark artifacts show the intended completion or bounded failure behavior
