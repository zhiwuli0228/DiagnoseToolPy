# Current State

This file is the **project continuity snapshot**. Update it after every completed change.

## Current Phase

SuperSpec autonomous validation workflow enabled on `claude_master`. Bugfix Prompt Export delivered. Performance benchmark evidence chain remediated and merged into `claude_master`.

## Implemented

- [x] Project concept defined
- [x] Harness document hierarchy defined
- [x] OpenSpec configuration draft prepared
- [x] Python package structure created
- [x] FastAPI app created
- [x] Config loading implemented
- [x] Directory whitelist validation implemented
- [x] Server directory scan API implemented
- [x] Streaming log reader implemented
- [x] Multiline stack trace merger implemented
- [x] Complex log header parser implemented
- [x] Rule classifier implemented
- [x] Evidence package generator implemented
- [x] Key logs generator implemented
- [x] Raw samples JSONL generator implemented
- [x] Timeline aggregation implemented
- [x] HTML report generator implemented
- [x] Case draft generator implemented
- [x] Case metadata draft generator implemented
- [x] Retrieval query generator implemented
- [x] Case base file storage implemented
- [x] Case index rebuild implemented
- [x] Manual case creation API implemented
- [x] Keyword retrieval implemented
- [x] Rule-based retrieval implemented
- [x] BM25 retrieval implemented (optional, requires rank-bm25)
- [x] Prompt context generator implemented
- [x] Docker Compose deployment implemented
- [x] React frontend shell implemented
- [x] LLM provider configuration (llm_config.py)
- [x] OpenAI-compatible LLM client (llm_client.py)
- [x] AI diagnosis orchestrator (analyzer/diagnosis.py)
- [x] POST /api/diagnosis endpoint
- [x] Frontend AI diagnosis page (AIDiagnosisPage.tsx)
- [x] Evidence basket for selected log diagnosis
- [x] POST /api/diagnosis/search endpoint
- [x] POST /api/diagnosis/cluster endpoint
- [x] Evidence cache with context (matched-lines.jsonl)
- [x] Smart evidence compression module
- [x] Cluster matched lines retrieval API
- [x] Bugfix prompt generation export
- [x] Performance benchmark evidence chain remediated (`tests/load/diff_results.py` reads Locust `Aggregated` row only; `tests/load/run_bench.sh` performs `/health` preflight; `tests/load/results_diff.md` regenerated from current baseline/after CSVs; `data/indexes/bm25/corpus.jsonl` untracked as rebuildable cache)
- [x] Large-input analysis path remediated (`/api/source/scan` now inspects ZIP metadata without `extractall`; `/api/source/upload` writes uploads in chunks; cluster cache generation no longer rebuilds a full in-memory error list after aggregation)
- [x] Automated analysis benchmark standard added (`tests/load/analysis_benchmarks.yaml` defines datasets/profiles/thresholds, including a ZIP-backed prepared large-directory workload extracted from `E:\006tooldevelop\logsearch\out-final-expanded.zip` and heavier directory concurrency; `tests/load/prepare_analysis_datasets.py` prepares directory datasets; `tests/load/analysis_benchmark.py` runs large-log scan/cluster benchmarks and writes JSON/Markdown artifacts; `tests/load/run_analysis_bench.ps1` creates per-run artifact directories and automatically captures process CPU/memory evidence via `tests/load/collect_process_stats.ps1`)
- [x] Requirement acceptance flow standardized (change `add-requirement-acceptance`; `tests/load/acceptance_suites.yaml` defines acceptance suites; `tests/load/run_requirement_acceptance.ps1` is the one-command acceptance trigger; `tests/load/requirement_acceptance.py` writes suite-level acceptance summaries so current requirement sign-off no longer depends on manually selecting benchmark profiles)
- [x] Requirement acceptance finalization hardened (change `add-requirement-acceptance`; `tests/load/requirement_acceptance.py` now rejects non-boolean `summary.passed` values and only writes `acceptance-summary.*` when the benchmark run itself succeeds; `tests/load/run_requirement_acceptance.ps1` records benchmark and acceptance exit codes in `acceptance-run-meta.json`)
- [x] Large-log cluster scaling stabilized for the same-source admission and byte-based-progress bottleneck identified by `directory_concurrency_baseline` (`diagnose_tool/core/cluster_runtime.py` introduces a process-local same-source registry; `POST /api/cluster` returns the active task with `reused: true` instead of starting a redundant full scan and allows resubmission after terminal-failed/done; `ClusterAnalyzer.run` writes `processed_bytes`/`total_bytes`/`current_file`/`message` to `progress.json` and emits a terminal `failed` state when the scan raises; `tests/load/analysis_benchmark.py` records cluster `submit_ms` and `wall_time_seconds` even when the task later times out so summary metrics stay finite; design captured in `docs/01-architecture/large-log-cluster-scaling-design.md` with Phase 1 stabilization and explicit Phase 2 reuse / Phase 3 throughput evolution)
- [x] Runtime/generated data removed from Git tracking (`data/input/uploads/`, `data/output/`, `data/sessions/`, `data/temp/`, `data/runtime/`, rebuildable indexes, and case drafts are now treated as local/generated artifacts)
- [x] Playwright/debug local artifacts removed from Git tracking; `.playwright-mcp/` and root-level temporary screenshots/page dumps/console captures remain local-only instead of repository history
- [x] JVM thread dump parser implemented (change `add-thread-stack-parsing`; `diagnose_tool/analyzer/thread_stack_parser.py`; parses HotSpot/OpenJDK thread dump blocks into structured ThreadDumpResult with thread name, state, ordered frames, lock hints; conservative: returns RAW/PARTIAL on malformed input; 38 tests in `tests/test_thread_stack_parser.py`)
- [x] Thread stack parser load + capability evidence (change `add-thread-stack-bench`; `tests/load/thread_stack_bench.py` synthetic HotSpot block generator + two-pass timing + `tracemalloc` peak memory; `tests/load/thread_stack_bench.json` snapshot for `[100, 1,000, 10,000]`; `tests/load/real_dump_sample{1,2}.txt` Java 8 and Java 11 jstack samples; `tests/load/thread-stack-capability-report.md` and `thread-stack-load-report.md` human-review reports)
- [x] Thread stack evidence basket (thread evidence is now selectable as diagnosis evidence; parsed thread blocks stored as rebuildable task artifacts under data/output/{task_id}/artifacts/thread-stack-results.jsonl; stable thread_ref for downstream resolution; API endpoint GET /api/diagnosis/thread-results/{task_id}; frontend thread results panel with add-one/add-all; thread evidence carried through preview, diagnosis, and workspace export)
- [x] Test suggestion generation (change `add-test-suggestion-generation`; `diagnose_tool/analyzer/test_suggester.py` reads completed `ai-diagnosis.md` + `evidence-pack.md`, calls LLM with focused prompt from `docs/05-domain/test-suggestion-template.md`, writes `data/output/{task_id}/test-suggestions.md`; `POST /api/diagnosis/test-suggestions` manual endpoint; auto-hook at end of `DiagnosisOrchestrator.run()` (configurable, default on); frontend `TestSuggestionsPanel` parses `### Test:` headings into copyable code cards; fifth Tab "测试建议" on `TaskDetailPage`; "Generate test suggestions" button in Actions Tab)

## Current Constraints

- No mandatory external database.
- File-based task state.
- Markdown/YAML casebase.
- Embedding disabled by default.
- Vector retrieval optional only.

## Current Directory Plan

```text
DiagnoseToolPy/
├── AGENTS.md
├── openspec/config.yaml
├── docs/
├── config/
├── diagnose_tool/        # FastAPI backend
├── frontend/             # React + Vite + TypeScript frontend
├── data/
└── tests/
```

## Known Gaps

- Monitoring suggestion generation not implemented.
- Monitoring suggestion generation not implemented.
- Vector retrieval not implemented.
- Complete log analysis UI not implemented.
- Complete case management UI not implemented.

## Next Recommended Work

1. Use the SuperSpec validation workflow for the next governed change.
2. Implement complete log analysis UI.
3. Implement complete case management UI.
4. Implement test suggestion generation (V0.4 extended).
5. Implement monitoring suggestion generation (V0.4 extended).
