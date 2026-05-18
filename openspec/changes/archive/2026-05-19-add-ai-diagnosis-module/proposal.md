# Proposal: add-ai-diagnosis-module

## Change ID

`add-ai-diagnosis-module`

## Date

2026-05-19

## Problem

DiagnoseToolPy can analyze logs and generate structured evidence packs, but users must manually copy evidence to an external LLM to obtain a preliminary AI diagnosis. There is no integrated, one-click path from evidence pack to AI preliminary diagnosis stored alongside the case.

## User Goal

Enable users to trigger an AI preliminary diagnosis for a completed analysis task with a single API call, using a configurable LLM provider (OpenAI-compatible), and have the result saved as `ai-diagnosis.md` in the case directory for human review.

## Current Behavior

- No AI diagnosis integration exists.
- `diagnose_tool/retrieval/prompt_context.py` generates AI prompt context (reference cases only) but does not call any LLM.
- `docs/05-domain/prompt-template.md` defines the prompt template but is not used programmatically.
- Case storage contract supports `ai-diagnosis.md` but no code writes it.
- Users must manually copy evidence to an LLM interface.

## Target Behavior

1. LLM provider is configured via `config/app.yaml` (`llm` section).
2. `POST /api/diagnosis` accepts `{ "task_id": "<id>" }` and:
   - Loads the evidence pack for the task.
   - Builds the AI diagnosis prompt using `prompt-template.md` + `prompt_context.py`.
   - Calls the configured LLM via OpenAI-compatible API.
   - Saves the result as `data/cases/{case_id}/ai-diagnosis.md` (marked as preliminary).
   - Returns the diagnosis text to the caller.
3. If `llm.enabled` is `false` or the `llm` section is missing, the API returns HTTP 503 with a clear message.
4. If the task does not exist, the API returns HTTP 404.
5. The `ai-diagnosis.md` file is clearly marked as **preliminary AI diagnosis**, not confirmed root cause.

## Scope

### In Scope

- `diagnose_tool/core/llm_config.py` — LLM provider configuration dataclass + YAML loading
- `diagnose_tool/core/llm_client.py` — OpenAI-compatible LLM HTTP client (httpx)
- `diagnose_tool/analyzer/diagnosis.py` — Diagnosis orchestrator (pure Python, no FastAPI dep)
- `diagnose_tool/api/routes_diagnosis.py` — `POST /api/diagnosis` endpoint
- `diagnose_tool/main.py` — Register the new router
- `config/app.yaml` — Add `llm` configuration section
- `tests/test_llm_config.py` — Config loading tests
- `tests/test_llm_client.py` — LLM client tests (mocked httpx)
- `tests/test_diagnosis.py` — Orchestrator tests
- `tests/test_diagnosis_api.py` — API endpoint tests
- `frontend/src/api/diagnosisApi.ts` — Frontend API client
- `frontend/src/pages/AIDiagnosisPage.tsx` — AI diagnosis page
- `frontend/src/App.tsx` — Route registration
- `frontend/src/types/api.ts` — TypeScript type updates

### Out of Scope

- Bugfix prompt generation
- Test suggestion generation
- Monitoring suggestion generation
- Multi-LLM comparison or routing
- Vector / embedding-based retrieval
- Dynamic LLM provider switching UI
- Streaming LLM responses (non-streaming only for v1)

## Affected Modules

| Module | Role |
|--------|------|
| `diagnose_tool/core/llm_config` | New — LLM configuration |
| `diagnose_tool/core/llm_client` | New — HTTP client for LLM API |
| `diagnose_tool/analyzer/diagnosis` | New — Orchestration (pure Python) |
| `diagnose_tool/api/routes_diagnosis` | New — FastAPI router |
| `diagnose_tool/casebase` | Extended — Writes `ai-diagnosis.md` |
| `frontend/src/pages` | Extended — New AIDiagnosisPage |
| `frontend/src/api` | Extended — New diagnosisApi |

## Acceptance Criteria

1. **Config-driven LLM**: `llm` section in `config/app.yaml` with fields `enabled`, `model`, `base_url`, `api_key`, `timeout`. Missing or invalid config does not crash the app; `llm.enabled: false` is the safe default.
2. **API Endpoint**: `POST /api/diagnosis` with `{ "task_id": "<id>" }` returns HTTP 200 with `{ "diagnosis": "...", "case_id": "..." }` on success.
3. **Error Responses**: HTTP 404 for unknown task_id, HTTP 503 when LLM not enabled/configured, HTTP 400 for malformed request.
4. **File Output**: Diagnosis result written to `data/cases/{case_id}/ai-diagnosis.md` with "PRELIMINARY AI DIAGNOSIS" header and clear disclaimer that this is not the confirmed root cause.
5. **Prompt Construction**: Prompt built from `docs/05-domain/prompt-template.md` + evidence-pack content + retrieval context from `prompt_context.py`.
6. **No Embedding Requirement**: The diagnosis flow does not require embedding models; it works with keyword/BM25 retrieval context only.
7. **Tests**: All new Python modules have pytest tests covering success and failure paths.
8. **Frontend**: `AIDiagnosisPage` can call `/api/diagnosis` and display the result; `npm run build` passes.

## Risk Points

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| AI diagnosis treated as confirmed root cause | Medium | High | Prominent "preliminary" label in file and UI |
| LLM API key leaked in logs | Low | Critical | Strict log sanitization; key never in response |
| LLM API timeout blocking API worker | Medium | Medium | Configurable timeout; non-streaming with total timeout |
| Concurrent LLM calls exhausting resources | Low | Medium | Semaphore limit on concurrent calls |
| Config missing causing app crash | Low | Medium | `llm.enabled: false` default; graceful fallback |

## Validation Approach

1. `uv run pytest tests/` — all new and existing tests pass.
2. `uv run ruff check diagnose_tool/` — no lint errors.
3. `cd frontend && npm run build` — TypeScript compilation succeeds.
4. Manual smoke test: `POST /api/diagnosis` with a known task_id returns a diagnosis within timeout.
5. Manual smoke test: `POST /api/diagnosis` without LLM config returns 503, not 500.

## opencode Implementation Prompt

See `tasks.md` for the full opencode prompt to be used after this proposal is approved.