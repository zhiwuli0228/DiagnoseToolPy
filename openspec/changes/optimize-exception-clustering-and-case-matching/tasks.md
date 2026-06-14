## 1. Baseline and Regression Tests

- [ ] 1.1 Add grouping regression tests
  - Files: `tests/test_cluster_analyzer.py`
  - Behavior: same exception class across different minutes produces one stable group key; time remains available as distribution metadata
  - Tests: same exception in two timestamps, normalized message fallback, no time suffix in group key
  - Verification: `uv run pytest tests/test_cluster_analyzer.py`

- [ ] 1.2 Add case matching failure-mode tests
  - Files: `tests/test_cluster_analyzer.py`, `tests/test_retrieval.py`
  - Behavior: empty casebase, malformed `metadata.yaml`, and missing `case.md` do not fail cluster matching
  - Tests: empty directory, invalid YAML, metadata-only case
  - Verification: `uv run pytest tests/test_cluster_analyzer.py tests/test_retrieval.py`

- [ ] 1.3 Add top-N matching behavior tests
  - Files: `tests/test_cluster_analyzer.py`
  - Behavior: groups outside the matching limit remain counted and sampled but receive empty `matched_cases`
  - Tests: more groups than matching limit, groups within matching limit
  - Verification: `uv run pytest tests/test_cluster_analyzer.py`

## 2. Stable Exception Grouping

- [ ] 2.1 Remove time fragments from cluster group identity
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`, optionally `diagnose_tool/analyzer/log_aggregator.py`
  - Behavior: group key uses exception class or normalized message template only
  - Tests: grouping tests from task 1.1 pass
  - Verification: `uv run pytest tests/test_cluster_analyzer.py tests/test_header_parser.py`

- [ ] 2.2 Preserve time distribution outside the group key
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`
  - Behavior: cluster result still exposes timing context without fragmenting categories
  - Tests: cluster time distribution test
  - Verification: `uv run pytest tests/test_cluster_analyzer.py`

## 3. Task-local Case Match Index

- [ ] 3.1 Add reusable case match loading helper
  - Files: `diagnose_tool/retrieval/`, `tests/test_retrieval.py`
  - Behavior: load case metadata and selected case text once into a reusable in-memory representation
  - Tests: valid case, missing metadata, malformed metadata, missing case body
  - Verification: `uv run pytest tests/test_retrieval.py`

- [ ] 3.2 Replace per-group filesystem matching in cluster flow
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`, `diagnose_tool/retrieval/`
  - Behavior: historical matching reuses the task-local loaded case records across groups
  - Tests: mocked loader/read counter proves files are not re-read per group
  - Verification: `uv run pytest tests/test_cluster_analyzer.py tests/test_retrieval.py`

- [ ] 3.3 Preserve embedding-disabled matching behavior
  - Files: `diagnose_tool/retrieval/`, `tests/test_retrieval.py`
  - Behavior: local metadata/body matching works without vector indexes or embedding configuration
  - Tests: embedding-disabled retrieval scenario
  - Verification: `uv run pytest tests/test_retrieval.py`

## 4. Bounded Historical Matching

- [ ] 4.1 Apply top-N matching limit
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`, optional `diagnose_tool/core/config.py`, `config/app.yaml`
  - Behavior: only top-N groups by count perform historical case matching; all groups remain in output
  - Tests: task 1.3 passes
  - Verification: `uv run pytest tests/test_cluster_analyzer.py`

- [ ] 4.2 Decide and document matching limit configuration
  - Files: `config/app.yaml`, `docs/01-architecture/large-log-cluster-scaling-design.md` or a focused architecture note
  - Behavior: default limit is documented; if configurable, config loading is covered
  - Tests: config test if a new setting is added
  - Verification: `uv run pytest tests/test_config.py tests/test_cluster_analyzer.py`

## 5. Phase Metrics and Benchmark Evidence

- [ ] 5.1 Record post-scan phase timings
  - Files: `diagnose_tool/analyzer/cluster_analyzer.py`
  - Behavior: progress output includes aggregation, case matching, and cache/result writing timing or metric evidence
  - Tests: progress output includes expected additive fields
  - Verification: `uv run pytest tests/test_cluster_analyzer.py tests/test_cluster_api.py`

- [ ] 5.2 Update load benchmark reporting
  - Files: `tests/load/analysis_benchmark.py`, `tests/load/analysis_benchmarks.yaml`
  - Behavior: benchmark artifacts report scan, aggregation, case matching, and cache-writing timings when available
  - Tests: benchmark summary parsing tests
  - Verification: `uv run pytest tests/test_analysis_benchmark.py`

- [ ] 5.3 Run requirement acceptance for large-log cluster behavior
  - Files: generated benchmark artifacts under `tests/load/artifacts/`
  - Behavior: acceptance run shows terminal cluster status and phase evidence
  - Tests: requirement acceptance wrapper
  - Verification: `powershell -ExecutionPolicy Bypass -File tests/load/run_requirement_acceptance.ps1`

## 6. Documentation and Final Checks

- [ ] 6.1 Update durable docs
  - Files: `docs/00-project/current-state.md`, relevant `docs/01-architecture/*.md`
  - Behavior: record optimized exception clustering and matching capability, metric fields, and remaining limitations
  - Tests: documentation review
  - Verification: confirm docs mention no mandatory database and streaming behavior preserved

- [ ] 6.2 Run full focused verification
  - Files: no source changes expected beyond completed tasks
  - Behavior: all affected tests and lint pass
  - Tests: cluster, retrieval, config/API as applicable
  - Verification: `uv run pytest tests/test_cluster_analyzer.py tests/test_retrieval.py tests/test_cluster_api.py tests/test_analysis_benchmark.py` and `uv run ruff check .`
