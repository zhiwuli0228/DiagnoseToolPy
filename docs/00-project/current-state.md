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
- [x] Runtime/generated data removed from Git tracking (`data/input/uploads/`, `data/output/`, `data/sessions/`, `data/temp/`, `data/runtime/`, rebuildable indexes, and case drafts are now treated as local/generated artifacts)
- [x] Playwright/debug local artifacts removed from Git tracking; `.playwright-mcp/` and root-level temporary screenshots/page dumps/console captures remain local-only instead of repository history

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

- Test suggestion generation not implemented.
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
