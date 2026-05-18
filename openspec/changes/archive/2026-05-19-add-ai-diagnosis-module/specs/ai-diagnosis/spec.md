# Spec: ai-diagnosis

## Spec ID

`ai-diagnosis`

## Change ID

`add-ai-diagnosis-module`

## Overview

The AI diagnosis module adds a one-click preliminary AI diagnosis feature to DiagnoseToolPy. The system accepts a completed analysis task, builds an AI prompt from the evidence pack and similar cases, calls a configurable OpenAI-compatible LLM, and saves the result as `ai-diagnosis.md` in the case directory.

---

## Functionality

### F1: LLM Configuration Loading

**Module**: `diagnose_tool/core/llm_config.py`

The system SHALL load LLM provider settings from the `llm` section of `config/app.yaml`.

Config fields:
- `enabled` (bool, default: `false`)
- `model` (string, default: `"gpt-4o-mini"`)
- `base_url` (string, default: `"https://api.openai.com/v1"`)
- `api_key` (string, default: `""`)
- `timeout` (int, default: `60`)

**Rules**:
- If the `llm` section is entirely absent, the system SHALL start with `enabled = false` (no crash).
- If `llm.enabled` is absent in YAML, it SHALL be treated as `false`.
- The config dataclass SHALL be frozen (immutable).
- The config loader SHALL raise `ConfigError` on invalid YAML structure, not crash silently.

### F2: OpenAI-Compatible LLM Client

**Module**: `diagnose_tool/core/llm_client.py`

The system SHALL provide an `LLMClient` class that calls an OpenAI-compatible `/chat/completions` endpoint via HTTP.

**Rules**:
- The client SHALL use `httpx` synchronous client.
- The client SHALL send a `POST` request with `model`, `messages`, and standard OpenAI request body.
- If `api_key` is non-empty, the client SHALL include `Authorization: Bearer <api_key>` header.
- The client SHALL respect the configured `timeout`.
- The client SHALL raise `LLMClientError` on non-200 responses, network errors, and timeouts.
- The client SHALL limit concurrent calls to 5 per instance via semaphore.
- The client SHALL NOT log the API key or full request/response bodies.

**Request format**:
```json
{
  "model": "<model>",
  "messages": [
    { "role": "system", "content": "<system prompt>" },
    { "role": "user", "content": "<user prompt>" }
  ]
}
```

**Response**: The client SHALL return the `content` field of the first assistant message.

### F3: Diagnosis Orchestrator

**Module**: `diagnose_tool/analyzer/diagnosis.py`

The system SHALL provide a `DiagnosisOrchestrator` class that orchestrates the full diagnosis flow.

**Rules**:
- The orchestrator SHALL be independent of FastAPI (no FastAPI imports).
- The orchestrator SHALL read `data/output/{task_id}/evidence-pack.md`.
- If `retrieval-query.json` exists, the orchestrator SHALL use it to retrieve similar cases via the existing retrieval module.
- The orchestrator SHALL build the prompt using `docs/05-domain/prompt-template.md` as the base template.
- The orchestrator SHALL inject the evidence pack content and retrieval context (from `prompt_context.py`) into the template.
- The orchestrator SHALL call `LLMClient.chat()` with the constructed messages.
- The orchestrator SHALL write the LLM response to `data/cases/{case_id}/ai-diagnosis.md`.
- The orchestrator SHALL derive `case_id` from the task output directory name.
- The `ai-diagnosis.md` content SHALL start with a prominent "PRELIMINARY AI DIAGNOSIS — NOT CONFIRMED ROOT CAUSE" header and a disclaimer.
- The orchestrator SHALL raise `TaskNotFoundError` if `data/output/{task_id}` does not exist.
- The orchestrator SHALL raise `EvidenceNotFoundError` if `evidence-pack.md` does not exist.
- The orchestrator SHALL propagate `LLMClientError` as `DiagnosisError`.

### F4: `POST /api/diagnosis` Endpoint

**Module**: `diagnose_tool/api/routes_diagnosis.py`

The system SHALL provide a FastAPI route `POST /api/diagnosis`.

**Request**:
```json
{ "task_id": "string" }
```

**Response 200**:
```json
{
  "case_id": "string",
  "diagnosis": "string"
}
```

**Error responses**:
- `400 Bad Request`: `task_id` is missing or empty.
- `404 Not Found`: Task output directory not found.
- `503 Service Unavailable`: LLM is not enabled (`llm.enabled = false`) or not configured.
- `500 Internal Server Error`: LLM API error or unexpected failure.

**Rules**:
- The endpoint SHALL create one `DiagnosisOrchestrator` per request (or reuse a shared one).
- The endpoint SHALL map `TaskNotFoundError` → 404, `EvidenceNotFoundError` → 404, `LLMClientError` → 500, `DiagnosisError` → 500.
- The endpoint SHALL return safe error messages without exposing internal paths, API keys, or stack traces.
- The endpoint SHALL load the LLM config once at startup (not per request).

### F5: Router Registration

**Module**: `diagnose_tool/main.py`

The system SHALL register `routes_diagnosis` router in the FastAPI app.

**Rules**:
- Registration happens at app creation time.
- If LLM is not enabled, the `/api/diagnosis` endpoint still exists but returns 503 on request.

### F6: Configuration File Update

**File**: `config/app.yaml`

The `llm` section SHALL be added to the config file.

```yaml
llm:
  enabled: false
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"
  api_key: ""
  timeout: 60
```

### F7: Frontend AI Diagnosis Page

**Module**: `frontend/src/pages/AIDiagnosisPage.tsx`

The system SHALL provide a React page that:
- Accepts a task_id input.
- Calls `POST /api/diagnosis`.
- Displays the returned `diagnosis` markdown.
- Displays a prominent warning that the diagnosis is preliminary and not confirmed root cause.
- Handles error states (404, 503, 500) with user-friendly messages.

**Rules**:
- The page SHALL use existing `api/client.ts` (axios wrapper) or a new `diagnosisApi.ts`.
- The page SHALL NOT display raw API key or internal paths.
- The page SHALL handle loading and error states.

### F8: Frontend API Client

**Module**: `frontend/src/api/diagnosisApi.ts`

The system SHALL provide a TypeScript function:
```typescript
async function diagnose(taskId: string): Promise<{ case_id: string; diagnosis: string }>
```

**Rules**:
- Calls `POST /api/diagnosis` with `{ task_id: taskId }`.
- Throws on HTTP error responses (non-2xx), letting callers handle error UI.
- Returns parsed JSON response.

### F9: Frontend Routing

**Module**: `frontend/src/App.tsx`

The system SHALL add a route for `/diagnosis` rendering `AIDiagnosisPage`.

### F10: TypeScript Types

**Module**: `frontend/src/types/api.ts`

The system SHALL add:
```typescript
interface DiagnosisRequest { task_id: string }
interface DiagnosisResponse { case_id: string; diagnosis: string }
```

---

## Data Formats

### `ai-diagnosis.md`

```markdown
# PRELIMINARY AI DIAGNOSIS — NOT CONFIRMED ROOT CAUSE

> **Disclaimer**: This diagnosis was generated by an AI model and represents a
> preliminary hypothesis. It is **NOT** the confirmed root cause.
> A human engineer must review, validate, and confirm before treating this as fact.

## Generated At

{timestamp}

## Task ID

{task_id}

## Source Evidence

- Evidence pack: `data/output/{task_id}/evidence-pack.md`
- Retrieval query: `data/output/{task_id}/retrieval-query.json`

---

[LLM response content]
```

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | `llm` section absent from app.yaml → app starts with `enabled=false` | Manual: remove llm section, start app, check no crash |
| AC2 | `POST /api/diagnosis` with unknown task_id → 404 | `pytest tests/test_diagnosis_api.py` |
| AC3 | `POST /api/diagnosis` with `llm.enabled=false` → 503 | `pytest tests/test_diagnosis_api.py` |
| AC4 | `POST /api/diagnosis` with valid task_id and LLM enabled → 200 with diagnosis text | `pytest tests/test_diagnosis_api.py` (mocked LLM) |
| AC5 | `ai-diagnosis.md` written with preliminary header | `pytest tests/test_diagnosis.py` |
| AC6 | API key never appears in response body | `pytest tests/test_diagnosis_api.py` |
| AC7 | LLM API error → 500 with safe message | `pytest tests/test_diagnosis_api.py` (mock error) |
| AC8 | Frontend `npm run build` succeeds | CI/CD or manual |
| AC9 | All new Python modules have pytest tests | `pytest tests/test_llm_config.py tests/test_llm_client.py tests/test_diagnosis.py tests/test_diagnosis_api.py` |
| AC10 | `uv run ruff check` passes | Manual |

---

## Dependencies

- Python: `httpx` (already in dev dependencies)
- Frontend: no new production dependencies (React + axios already present)

---

## Non-Goals

- Streaming LLM responses (v1 is non-streaming)
- Multiple LLM providers or dynamic switching
- Bugfix prompt / test suggestion / monitoring suggestion generation
- Vector retrieval