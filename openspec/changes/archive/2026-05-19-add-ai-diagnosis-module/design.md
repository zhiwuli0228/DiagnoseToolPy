# Design: add-ai-diagnosis-module

## Overview

This change adds one-click AI preliminary diagnosis to DiagnoseToolPy. A user can call `POST /api/diagnosis` with a task ID and receive an AI-generated preliminary diagnosis, which is saved as `ai-diagnosis.md` in the case directory.

**Design principle**: AI diagnosis is assistive. The result is always marked preliminary and is never the confirmed root cause.

---

## Module Design

### New Files

```
diagnose_tool/core/llm_config.py    — AppLLMConfig dataclass + YAML loading
diagnose_tool/core/llm_client.py    — OpenAICompatibleClient (httpx)
diagnose_tool/analyzer/diagnosis.py — DiagnosisOrchestrator (pure Python)
diagnose_tool/api/routes_diagnosis.py — FastAPI router
tests/test_llm_config.py
tests/test_llm_client.py
tests/test_diagnosis.py
tests/test_diagnosis_api.py
frontend/src/api/diagnosisApi.ts
frontend/src/pages/AIDiagnosisPage.tsx
frontend/src/types/api.ts
```

### Modified Files

```
diagnose_tool/main.py              — register routes_diagnosis router
config/app.yaml                   — add llm: { enabled, model, base_url, api_key, timeout }
frontend/src/App.tsx              — add /diagnosis route
```

---

## Configuration Schema

### config/app.yaml — `llm` section (new)

```yaml
llm:
  enabled: false                          # default: false (safe default)
  model: "gpt-4o-mini"                    # OpenAI model name
  base_url: "https://api.openai.com/v1"   # OpenAI-compatible base URL
  api_key: ""                              # API key; empty = no auth
  timeout: 60                              # seconds
```

**Backward compatibility**: If the `llm` section is missing entirely, the app starts with `llm.enabled = false`. No crash.

---

## API Contract

### `POST /api/diagnosis`

**Request body**:
```json
{ "task_id": "string" }
```

**Response 200**:
```json
{
  "case_id": "string",
  "diagnosis": "string (markdown)"
}
```

**Response 400** — malformed request (missing/empty task_id):
```json
{ "detail": "task_id is required" }
```

**Response 404** — task directory not found:
```json
{ "detail": "Task not found" }
```

**Response 503** — LLM not enabled or not configured:
```json
{ "detail": "AI diagnosis is not enabled. Set llm.enabled to true in config/app.yaml" }
```

**Response 500** — LLM API error:
```json
{ "detail": "AI diagnosis failed: <safe error message>" }
```

---

## Data Flow

```
User calls POST /api/diagnosis { task_id }
    │
    ▼
routes_diagnosis.validate_task_id(task_id)
    │  → checks data/output/{task_id}/ exists
    ▼
DiagnosisOrchestrator.run(task_id)
    │
    ├── reads data/output/{task_id}/evidence-pack.md
    ├── reads data/output/{task_id}/retrieval-query.json  (optional)
    │    └── if missing: uses empty retrieval context
    │
    ├── RetrievalQuery.from_task_output(...)  → RetrievalQuery
    ├── retrieval.query_cases(query)          → list[case tuples]
    ├── prompt_context.generate_prompt_context(query, cases)  → context string
    │
    ├── reads docs/05-domain/prompt-template.md
    │    → fills {evidence_pack}, {similar_cases} placeholders
    │
    ├── LLMClient.chat(messages, model, base_url, api_key, timeout)
    │    → returns str (full response)
    │
    └── writes data/cases/{case_id}/ai-diagnosis.md
         └── case_id derived from task_id
    │
    ▼
returns { case_id, diagnosis }
```

---

## Class / Function Design

### `diagnose_tool/core/llm_config.py`

```python
@dataclass(frozen=True)
class AppLLMConfig:
    enabled: bool
    model: str
    base_url: str
    api_key: str
    timeout: int  # seconds

def load_llm_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> AppLLMConfig:
    """Load LLM config from app.yaml. Returns AppLLMConfig with safe defaults if absent."""
    # If 'llm' section missing → AppLLMConfig(enabled=False, ...)
    # If 'enabled' missing in yaml → treat as False
```

### `diagnose_tool/core/llm_client.py`

```python
class LLMClientError(RuntimeError):
    """Raised on LLM API errors."""

class LLMClient:
    def __init__(self, config: AppLLMConfig):
        self._config = config
        self._semaphore = Semaphore(5)  # max 5 concurrent calls

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Call OpenAI-compatible /chat/completions endpoint. Returns assistant message."""
        # Uses httpx sync client
        # Respects per-call overrides; falls back to config
        # Raises LLMClientError on non-200 or timeout
```

### `diagnose_tool/analyzer/diagnosis.py`

```python
class DiagnosisError(RuntimeError):
    """Base exception for diagnosis errors."""

class TaskNotFoundError(DiagnosisError):
    """Raised when task output directory not found."""

class EvidenceNotFoundError(DiagnosisError):
    """Raised when evidence-pack.md not found."""

class DiagnosisOrchestrator:
    def __init__(self, llm_config: AppLLMConfig, cases_dir: Path):
        self._llm = LLMClient(llm_config)
        self._cases_dir = cases_dir

    def run(self, task_id: str) -> tuple[str, str]:
        """Run AI diagnosis for a task.
        Returns (case_id, diagnosis_text).
        Writes ai-diagnosis.md to the case directory.
        Raises DiagnosisError on failure."""
```

**FastAPI independence**: `DiagnosisOrchestrator` has no imports from `fastapi`, `pydantic` (for request/response), or `starlette`. It only depends on standard library + `httpx`.

### `diagnose_tool/api/routes_diagnosis.py`

```python
router = APIRouter(prefix="/api", tags=["diagnosis"])

class DiagnosisRequest(BaseModel):
    task_id: str = Field(min_length=1)

class DiagnosisResponse(BaseModel):
    case_id: str
    diagnosis: str

@router.post("/diagnosis", response_model=DiagnosisResponse)
def diagnose(request: DiagnosisRequest) -> DiagnosisResponse:
    """One-click AI preliminary diagnosis."""
    # Loads config, creates orchestrator, calls run()
    # Maps exceptions to appropriate HTTP responses (404, 503, 500)
```

---

## Storage Contract

### `ai-diagnosis.md` Format

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

[Full LLM response body]
```

The file is written to `data/cases/{case_id}/ai-diagnosis.md`.

---

## Security

1. **API key**: Only used for outbound LLM API calls. Never logged. Never in response body.
2. **Log sanitization**: If an error message contains an API key or URL with credentials, it must be masked before logging.
3. **task_id validation**: `task_id` is validated against `data/output/` directory. Path traversal attempts (`../`) are rejected.
4. **base_url validation**: The base_url must be a valid HTTPS URL (or localhost for dev). Arbitrary URL injection is prevented.
5. **No user input to LLM prompt**: The evidence-pack content comes from the server-side file system, not from user input, so prompt injection risk is minimal. However, evidence-pack content is treated as untrusted and escaped before insertion into the prompt.

---

## Concurrency

- `LLMClient` uses a `Semaphore(5)` to limit concurrent LLM API calls.
- This prevents exhausting the API rate limit or local file descriptors.
- The semaphore is per-client instance; the FastAPI app creates one client at startup.

---

## Error Handling

| Error | HTTP Status | Response |
|-------|-------------|----------|
| task_id not found | 404 | `{"detail": "Task not found"}` |
| evidence-pack.md missing | 404 | `{"detail": "Evidence pack not found for task"}` |
| LLM not enabled | 503 | `{"detail": "AI diagnosis is not enabled..."}` |
| LLM API returns error | 500 | `{"detail": "AI diagnosis failed: <safe msg>"}` |
| LLM API timeout | 500 | `{"detail": "AI diagnosis timed out"}` |
| Invalid request body | 400 | `{"detail": "task_id is required"}` |

---

## Dependencies

- `httpx` — already in dev dependencies. Production code uses `httpx` (sync client) for LLM API calls.
- No new production dependencies beyond `httpx`.

---

## Backward Compatibility

1. If `llm` section is absent from `config/app.yaml`, the app starts normally with `llm.enabled = false`.
2. If `llm.enabled = false`, `POST /api/diagnosis` returns 503. No crash.
3. Existing API routes (`/api/sources`, `/api/cases`) are unaffected.
4. Existing tests pass without modification.