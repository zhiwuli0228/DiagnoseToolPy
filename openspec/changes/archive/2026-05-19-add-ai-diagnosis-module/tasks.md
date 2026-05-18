# Tasks: add-ai-diagnosis-module

## Change ID

`add-ai-diagnosis-module`

## Overview

Implement one-click AI preliminary diagnosis for DiagnoseToolPy. This task list assumes the OpenSpec proposal, design, and spec have been approved.

**Before starting implementation**, read the following files:
1. `AGENT.md` (hard constraints, especially section 3.6)
2. `openspec/config.yaml`
3. `openspec/changes/add-ai-diagnosis-module/proposal.md`
4. `openspec/changes/add-ai-diagnosis-module/design.md`
5. `openspec/changes/add-ai-diagnosis-module/specs/ai-diagnosis/spec.md`
6. `docs/00-project/current-state.md`
7. `docs/05-domain/prompt-template.md`
8. `diagnose_tool/retrieval/prompt_context.py`
9. `diagnose_tool/core/config.py`

---

## Phase 1: Config and Client (Core Infrastructure)

### TASK 1.1 — Read existing config infrastructure

**Files to inspect**:
- `diagnose_tool/core/config.py`
- `config/app.yaml`
- `pyproject.toml`

**Goal**: Understand how `load_config()` works so `load_llm_config()` is consistent and backward-compatible.

---

### TASK 1.2 — Implement `diagnose_tool/core/llm_config.py`

**Goal**: Create `AppLLMConfig` dataclass and `load_llm_config()` function.

**Implementation requirements**:
- Use `@dataclass(frozen=True)` consistent with existing `AppConfig` style.
- Load from `config/app.yaml` under the `llm` key.
- Safe defaults if section is missing: `enabled=False, model="gpt-4o-mini", base_url="https://api.openai.com/v1", api_key="", timeout=60`.
- Raise `ConfigError` on invalid YAML structure (not on missing section).
- Store `data_dir` from parent config to resolve case output paths.

**Verification**:
```bash
uv run pytest tests/test_llm_config.py -v
uv run ruff check diagnose_tool/core/llm_config.py
```

---

### TASK 1.3 — Write `tests/test_llm_config.py`

**Coverage**:
1. Full valid config loads correctly.
2. `llm` section entirely absent → returns `enabled=False`.
3. `llm.enabled` absent in YAML → treated as `false`.
4. Invalid YAML → raises `ConfigError`.
5. Default values are applied when fields are absent.

**Fixtures**: Use temporary YAML files via `tmp_path`.

---

### TASK 1.4 — Read existing httpx usage (if any)

**Files to inspect**:
- `pyproject.toml` (check httpx version)
- `tests/` for existing httpx mocking patterns

**Goal**: Follow existing patterns for httpx sync client mocking.

---

### TASK 1.5 — Implement `diagnose_tool/core/llm_client.py`

**Goal**: Create `LLMClient` class wrapping OpenAI-compatible `/chat/completions` API.

**Implementation requirements**:
- `LLMClientError` exception class.
- `LLMClient.__init__(config: AppLLMConfig)`.
- `chat(messages, model=None, base_url=None, api_key=None, timeout=None) -> str`.
- Use `httpx` synchronous client (`httpx.Client`).
- `Semaphore(5)` to limit concurrent calls.
- Build URL as `{base_url}/chat/completions`.
- Request body: `{"model": ..., "messages": ...}`.
- Add `Authorization: Bearer <api_key>` header if `api_key` is non-empty.
- Timeout: use per-call timeout if provided, else config timeout.
- Raise `LLMClientError` on non-200 responses, timeouts, network errors.
- **Never log API key or full request/response bodies**.
- Return the `content` of the first assistant message in the response.

**Verification**:
```bash
uv run pytest tests/test_llm_client.py -v
uv run ruff check diagnose_tool/core/llm_client.py
```

---

### TASK 1.6 — Write `tests/test_llm_client.py`

**Coverage**:
1. Successful LLM call → returns assistant message content.
2. LLM API returns non-200 → raises `LLMClientError`.
3. Network error → raises `LLMClientError`.
4. Timeout → raises `LLMClientError`.
5. `api_key` included in header when non-empty.
6. `api_key` not included in header when empty.
7. Per-call `model` overrides config.
8. Semaphore limits to 5 concurrent calls.

**Mocking**: Use `unittest.mock.patch` to mock `httpx.Client`.

---

## Phase 2: Diagnosis Orchestrator

### TASK 2.1 — Read existing analyzer and casebase files

**Files to inspect**:
- `diagnose_tool/analyzer/evidence.py` (evidence-pack.md path convention)
- `diagnose_tool/analyzer/retrieval_query.py` (RetrievalQuery class)
- `diagnose_tool/retrieval/query_builder.py` (how retrieval is invoked)
- `diagnose_tool/retrieval/prompt_context.py` (generate_prompt_context)
- `diagnose_tool/casebase/case_writer.py` (write paths)
- `diagnose_tool/casebase/case_models.py` (CaseMetadata)

**Goal**: Understand how to:
- Resolve `data/output/{task_id}/evidence-pack.md`.
- Build retrieval query from task output.
- Get or infer `case_id` for the case directory.
- Write `ai-diagnosis.md`.

---

### TASK 2.2 — Read prompt template

**Files to inspect**:
- `docs/05-domain/prompt-template.md`

**Goal**: Understand the template structure (`{evidence_pack}`, `{similar_cases}` placeholders) so the orchestrator can fill them.

---

### TASK 2.3 — Implement `diagnose_tool/analyzer/diagnosis.py`

**Goal**: Create `DiagnosisOrchestrator` class.

**Implementation requirements**:
- `DiagnosisError` (base), `TaskNotFoundError`, `EvidenceNotFoundError` exceptions.
- `DiagnosisOrchestrator.__init__(llm_config: AppLLMConfig, data_dir: Path)`.
- `DiagnosisOrchestrator.run(task_id: str) -> tuple[str, str]`:
  - Returns `(case_id, diagnosis_text)`.
  - Reads `data/output/{task_id}/evidence-pack.md`.
  - Reads `data/output/{task_id}/retrieval-query.json` if exists.
  - Calls retrieval to get similar cases (use existing retrieval module).
  - Calls `prompt_context.generate_prompt_context()` to build retrieval context.
  - Reads `docs/05-domain/prompt-template.md` (server-side read, not bundled).
  - Builds the full prompt by inserting evidence pack and retrieval context into the template.
  - Calls `LLMClient.chat()` with the prompt.
  - Determines `case_id` (from task_id; create `data/cases/{case_id}/` if needed).
  - Writes `ai-diagnosis.md` with preliminary header + LLM response.
  - Returns `(case_id, diagnosis_text)`.
- **FastAPI independence**: No `fastapi`, `pydantic`, or `starlette` imports.
- Use `pathlib.Path` for all file operations.
- Handle encoding safely (`utf-8`, `errors="replace"`).

**Verification**:
```bash
uv run pytest tests/test_diagnosis.py -v
uv run ruff check diagnose_tool/analyzer/diagnosis.py
```

---

### TASK 2.4 — Write `tests/test_diagnosis.py`

**Coverage**:
1. `TaskNotFoundError` raised when `data/output/{task_id}` does not exist.
2. `EvidenceNotFoundError` raised when `evidence-pack.md` missing.
3. Successful flow: returns `(case_id, diagnosis_text)`, `ai-diagnosis.md` written with preliminary header.
4. LLM not enabled → raises appropriate error (propagate from LLMClient or check early).
5. `retrieval-query.json` missing → uses empty retrieval context (graceful degradation).

**Fixtures**: Use temporary directories with pre-created evidence-pack.md.

---

## Phase 3: API Endpoint

### TASK 3.1 — Read existing API routes

**Files to inspect**:
- `diagnose_tool/main.py`
- `diagnose_tool/api/routes_case.py`
- `diagnose_tool/api/routes_source.py`

**Goal**: Understand router registration pattern and error handling style.

---

### TASK 3.2 — Implement `diagnose_tool/api/routes_diagnosis.py`

**Goal**: Create `POST /api/diagnosis` FastAPI route.

**Implementation requirements**:
- `DiagnosisRequest(BaseModel)` with `task_id: str` (min_length=1).
- `DiagnosisResponse(BaseModel)` with `case_id: str`, `diagnosis: str`.
- `router = APIRouter(prefix="/api", tags=["diagnosis"])`.
- `@router.post("/diagnosis", response_model=DiagnosisResponse)`.
- Load `AppLLMConfig` at module level (once at import).
- Create `DiagnosisOrchestrator(llm_config, data_dir)`.
- Call `orchestrator.run(task_id)`.
- Map exceptions:
  - `TaskNotFoundError` / `EvidenceNotFoundError` → `HTTPException(status_code=404)`
  - `LLMClientError` → `HTTPException(status_code=500, detail="AI diagnosis failed: <safe msg>")`
  - If `not llm_config.enabled` → `HTTPException(status_code=503, detail="AI diagnosis is not enabled...")`
- Return `DiagnosisResponse(case_id=..., diagnosis=...)`.
- **Never expose API key, full paths, or stack traces in error messages**.

**Verification**:
```bash
uv run pytest tests/test_diagnosis_api.py -v
uv run ruff check diagnose_tool/api/routes_diagnosis.py
```

---

### TASK 3.3 — Write `tests/test_diagnosis_api.py`

**Coverage**:
1. `POST /api/diagnosis` with valid task_id → 200 with `case_id` and `diagnosis`.
2. `POST /api/diagnosis` with unknown task_id → 404.
3. `POST /api/diagnosis` with `llm.enabled=false` → 503.
4. `POST /api/diagnosis` with empty `task_id` → 400.
5. LLM API error → 500 with safe message (API key not leaked).
6. `case_id` and `diagnosis` fields present in 200 response.

**Mocking**: Use `pytest-mock` or `unittest.mock` to mock the `DiagnosisOrchestrator.run()` method.

---

### TASK 3.4 — Update `diagnose_tool/main.py`

**Goal**: Register `routes_diagnosis` router.

**Change**:
```python
from diagnose_tool.api.routes_diagnosis import router as diagnosis_router
app.include_router(diagnosis_router)
```

**Verification**:
```bash
uv run pytest tests/test_main.py -v
```

---

### TASK 3.5 — Update `config/app.yaml`

**Goal**: Add `llm` configuration section.

```yaml
llm:
  enabled: false
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"
  api_key: ""
  timeout: 60
```

**Verification**: Ensure app starts without the `llm` section and with the `llm` section.

---

## Phase 4: Frontend

### TASK 4.1 — Read existing frontend structure

**Files to inspect**:
- `frontend/src/App.tsx` (routing)
- `frontend/src/api/client.ts` (axios wrapper)
- `frontend/src/types/api.ts` (existing types)
- `frontend/src/pages/AnalysisTasksPage.tsx` (existing page pattern)

**Goal**: Follow existing patterns for API calls and page structure.

---

### TASK 4.2 — Implement `frontend/src/api/diagnosisApi.ts`

**Goal**: Create `diagnose(taskId: string)` function.

**Implementation**:
```typescript
import type { DiagnosisResponse } from '../types/api';

export async function diagnose(taskId: string): Promise<DiagnosisResponse> {
  const response = await fetch('/api/diagnosis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}
```

---

### TASK 4.3 — Update `frontend/src/types/api.ts`

**Add**:
```typescript
export interface DiagnosisResponse {
  case_id: string;
  diagnosis: string;
}
```

---

### TASK 4.4 — Implement `frontend/src/pages/AIDiagnosisPage.tsx`

**Goal**: Create AI diagnosis page.

**Requirements**:
- Task ID input field.
- "Diagnose" button.
- Calls `diagnose(taskId)`.
- On success: displays diagnosis markdown with a prominent preliminary/disclaimer banner.
- On error: displays error message from API (safe, user-friendly).
- Uses Ant Design components (`Card`, `Alert`, `Input`, `Button`, `Typography`).

**Disclaimer banner** (required):
```tsx
<Alert
  message="Preliminary AI Diagnosis"
  description="This diagnosis was generated by an AI model and is NOT the confirmed root cause. A human engineer must review and validate before treating as fact."
  type="warning"
  showIcon
/>
```

**Verification**:
```bash
cd frontend && npm run build
```

---

### TASK 4.5 — Update `frontend/src/App.tsx`

**Add route**:
```tsx
<Route path="/diagnosis" element={<AIDiagnosisPage />} />
```

**Also add navigation link** in the layout (e.g., in `AppLayout` or sidebar) to allow navigation to `/diagnosis`.

---

## Phase 5: Integration and Final Validation

### TASK 5.1 — Run all backend tests

```bash
cd E:\009workspace\DiagnoseToolPy
uv run pytest tests/ -v
```

**Expected**: All tests pass, including new ones. No regression in existing tests.

---

### TASK 5.2 — Run linter

```bash
cd E:\009workspace\DiagnoseToolPy
uv run ruff check diagnose_tool/
```

**Expected**: No errors.

---

### TASK 5.3 — Run frontend build

```bash
cd frontend && npm run build
```

**Expected**: Build succeeds. No TypeScript errors.

---

### TASK 5.4 — Smoke test (manual)

```powershell
# Start the backend
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080

# In another terminal, call the API with a known task_id that has evidence-pack.md
curl -X POST http://localhost:18080/api/diagnosis -H "Content-Type: application/json" -d '{"task_id": "test-task"}'

# Expected: 200 with diagnosis text, or 404/503 as appropriate
```

---

### TASK 5.5 — Update `docs/00-project/current-state.md`

**Goal**: Mark V0.3 AI Diagnosis tasks as in-progress or completed.

Add checkboxes for the new features.

---

### TASK 5.6 — Update `openspec/changes/add-ai-diagnosis-module/.openspec.yaml`

**Change status**:
```yaml
status: implemented
```

---

## Completion Criteria

All of the following must be true before the change is considered complete:

1. `uv run pytest tests/` passes with no failures.
2. `uv run ruff check diagnose_tool/` reports no errors.
3. `cd frontend && npm run build` succeeds.
4. `POST /api/diagnosis` with valid task_id returns HTTP 200 and a non-empty diagnosis string.
5. `POST /api/diagnosis` with `llm.enabled=false` returns HTTP 503.
6. `POST /api/diagnosis` with unknown task_id returns HTTP 404.
7. `ai-diagnosis.md` is written to `data/cases/{case_id}/` with the preliminary disclaimer header.
8. `docs/00-project/current-state.md` is updated.
9. No new mandatory external database dependencies introduced.
10. `add-ai-diagnosis-module` OpenSpec change is archived (`status: implemented`).

---

## Appendix: File Change Summary

| File | Action |
|------|--------|
| `diagnose_tool/core/llm_config.py` | Create |
| `diagnose_tool/core/llm_client.py` | Create |
| `diagnose_tool/analyzer/diagnosis.py` | Create |
| `diagnose_tool/api/routes_diagnosis.py` | Create |
| `diagnose_tool/main.py` | Modify |
| `config/app.yaml` | Modify |
| `tests/test_llm_config.py` | Create |
| `tests/test_llm_client.py` | Create |
| `tests/test_diagnosis.py` | Create |
| `tests/test_diagnosis_api.py` | Create |
| `frontend/src/api/diagnosisApi.ts` | Create |
| `frontend/src/types/api.ts` | Modify |
| `frontend/src/pages/AIDiagnosisPage.tsx` | Create |
| `frontend/src/App.tsx` | Modify |
| `docs/00-project/current-state.md` | Modify |
| `openspec/changes/add-ai-diagnosis-module/.openspec.yaml` | Modify |