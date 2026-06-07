## Context

`diagnose_tool/analyzer/diagnosis.py` already produces a per-task AI diagnosis written to `data/cases/{task_id}/ai-diagnosis.md`. `current-state.md` lists "Implement test suggestion generation (V0.4 extended)" as a Known Gap. The on-call engineer needs a small, executable set of verification / reproduction scenarios that map the diagnosis text into `curl` / shell / Python / JUnit snippets they can paste into a terminal or a test file.

This change adds a thin, independent "TestSuggester" that reads the diagnosis and the evidence pack and produces a Markdown file with executable suggestions. The diagnosis flow stays unchanged for V0.4; test suggestion generation is wired as an auto-call at the end of `DiagnosisOrchestrator.run()` (configurable, default on) and as a manual endpoint.

## Goals / Non-Goals

**Goals**
- A new analyzer module `analyzer/test_suggester.py` exposing `TestSuggester.run(task_id) -> str` that reads `ai-diagnosis.md` + `evidence-pack.md` and returns the test-suggestion markdown.
- A version-tracked prompt template at `docs/05-domain/test-suggestion-template.md`, with an in-module fallback when the file is absent.
- A new `POST /api/diagnosis/test-suggestions` API endpoint.
- An optional auto-generation step at the end of `DiagnosisOrchestrator.run()` (controlled by an app setting, default on).
- The output is written to `data/output/{task_id}/test-suggestions.md` and is the durable evidence for the suggestion.
- A new `TestSuggestionsPanel` frontend component and a fifth Tab on `TaskDetailPage`. The panel parses `### Test:` headings, renders each suggestion as a card with `Type` / `Goal` / `Code` / `Expected`, and offers a one-click "Copy" button per code block.
- A new "Generate test suggestions" button in the Actions Tab that triggers a manual regeneration.
- i18n keys for the new tab and button.
- Backend tests (`tests/test_test_suggester.py`) and frontend tests for the new component.
- Playwright MCP browser verification per CLAUDE.md.

**Non-Goals**
- No change to the existing `DiagnosisOrchestrator.run()` prompt or output format.
- No execution of the generated test code.
- No modification of the casebase storage.
- No new external dependency.
- No change to `DiagnosisOrchestrator.run_with_context`.

## Decisions

### 1. Independent `TestSuggester` module

`diagnose_tool/analyzer/test_suggester.py` exposes:

```python
class TestSuggester:
    def __init__(self, llm_config: AppLLMConfig, data_dir: Path) -> None: ...
    def run(self, task_id: str) -> str: ...  # returns the markdown text
    def run_and_save(self, task_id: str) -> str: ...  # writes to data/output/{task_id}/test-suggestions.md
```

The module reads `ai-diagnosis.md` from `data/cases/{task_id}/` and `evidence-pack.md` from `data/output/{task_id}/`. It calls the LLM with the prompt template. It raises:
- `TaskNotFoundError` if `data/output/{task_id}` is missing.
- `DiagnosisNotFoundError` if `data/cases/{task_id}/ai-diagnosis.md` is missing.

Mirrors the existing `DiagnosisOrchestrator` style: pure Python, FastAPI-independent, takes a `data_dir` and an `llm_config`.

### 2. Prompt template at `docs/05-domain/test-suggestion-template.md`

The template is a version-tracked Markdown file with two placeholders:

- `{diagnosis}` — content of `ai-diagnosis.md`
- `{evidence_pack}` — content of `evidence-pack.md`

The template asks the LLM to produce a Markdown file with the following structure:

```markdown
# Test Suggestions for Task {task_id}

## Reproduction (must be runnable as-is)

### Test: <short name>
- **Type**: shell | python | junit | curl | ...
- **Goal**: <one sentence>
- **Code**:
  ```<lang>
  <executable snippet>
  ```
- **Expected**: <what success looks like>

(3-5 reproduction tests)

## Verification (probes that the fix actually works)

### Test: <short name>
...
(2-3 verification tests)

## Negative / Edge

### Test: <short name>
...
(1-2 negative tests)
```

When the file is absent, the module falls back to an embedded constant `_FALLBACK_TEST_TEMPLATE` with the same structure. This is the same pattern `diagnosis.py` uses.

### 3. New `POST /api/diagnosis/test-suggestions` endpoint

The endpoint takes `{ "task_id": str }` and returns `{ "content": str, "path": str }`. The route is a thin wrapper:

```python
@router.post("/diagnosis/test-suggestions")
def generate_test_suggestions(request: TestSuggestionsRequest) -> TestSuggestionsResponse:
    suggester = TestSuggester(llm_config, data_dir)
    content = suggester.run_and_save(request.task_id)
    return TestSuggestionsResponse(content=content, path=...)
```

Errors:
- 400 if the LLM is not configured.
- 404 if the diagnosis file is missing.
- 502 if the LLM call fails (consistent with the existing diagnosis endpoint's `LLMClientError` handling).

### 4. Auto-generation hook

`DiagnosisOrchestrator.run()` ends with a single best-effort call:

```python
if self._settings.auto_generate_tests:
    try:
        TestSuggester(self._llm_config, self._data_dir).run_and_save(task_id)
    except Exception as e:
        logger.warning("test suggestion auto-generation failed for %s: %s", task_id, e)
```

A failure here MUST NOT affect the diagnosis return value or the `ai-diagnosis.md` write. The setting lives in `config/app.yaml` under `diagnosis.auto_generate_tests: bool` (default `true`).

### 5. Frontend: `TestSuggestionsPanel` + fifth Tab

`TestSuggestionsPanel.tsx` is a new component:

```ts
interface TestSuggestionsPanelProps {
  taskId: string;
}

interface ParsedTest {
  name: string;
  type: string | null;
  goal: string | null;
  code: string;     // code block content (without fence)
  language: string; // code block language
  expected: string | null;
}
```

The component reads `test-suggestions.md` (new endpoint `GET /api/source/task/{task_id}/test-suggestions` returns `{ content: string | null }`, mirroring the existing `evidence-pack` endpoint) and parses on `### Test:` headings. Each test becomes a card with the type as an AntD `Tag`, the goal as a sentence, the code as a `<pre>` with a one-click Copy button (using `navigator.clipboard.writeText`), and the expected as a small block.

The TaskDetailPage adds a fifth Tab labeled `Test Suggestions`. The Actions Tab gets a new "Generate test suggestions" button that calls the manual endpoint and refreshes the panel via a `key` bump.

The new endpoint `GET /api/source/task/{task_id}/test-suggestions` is added alongside the existing `evidence-pack` and friends. The `task_reader` service gains a `read_test_suggestions(task_id)` function and a `TEST_SUGGESTIONS_FILENAME` constant.

### 6. i18n

Add to `frontend/src/locales/{en,zh}.json`:

- `analysisTasks.taskTable.testSuggestions` is unnecessary; the new keys live under `taskDetail.testSuggestions` and `taskDetail.actions.generateTests`.
- `taskDetail.tabs.testSuggestions` — "Test Suggestions" / "测试建议"
- `taskDetail.testSuggestions.title` — section title
- `taskDetail.testSuggestions.empty` — "No test suggestions yet. Use the Generate button in Actions to produce them."
- `taskDetail.testSuggestions.notProduced` — empty state when not generated
- `taskDetail.testSuggestions.copy` — "Copy"
- `taskDetail.testSuggestions.copied` — "Copied"
- `taskDetail.actions.generateTests.label` — "Generate test suggestions"
- `taskDetail.actions.generateTests.success` — "Test suggestions generated"
- `taskDetail.actions.generateTests.failed` — "Failed to generate test suggestions"

## Architecture

```text
  +----------------------------------+
  | routes_diagnosis.py              |
  |  POST /diagnosis/test-suggestions|
  +----------------------------------+
                  |
                  v
  +----------------------------------+
  | analyzer/test_suggester.py       |
  |  TestSuggester.run(task_id)      |
  +----------------------------------+
                  |
                  v
  +----------------------------------+
  | LLMClient + prompt template      |
  +----------------------------------+
                  |
                  v
  +----------------------------------+
  | data/output/{task_id}/           |
  |   test-suggestions.md            |
  +----------------------------------+
                  |
                  v
  +----------------------------------+
  | routes_source.py                 |
  |  GET /task/{id}/test-suggestions |
  +----------------------------------+
                  |
                  v
  +----------------------------------+
  | TaskDetailPage (5th Tab)         |
  |  TestSuggestionsPanel            |
  +----------------------------------+
```

## Data Flow

### Auto path

1. User triggers diagnosis via `POST /api/diagnosis` (existing).
2. `DiagnosisOrchestrator.run()` runs and writes `data/cases/{task_id}/ai-diagnosis.md`.
3. The auto-hook (when enabled) calls `TestSuggester.run_and_save(task_id)`, which reads the diagnosis + evidence pack, calls the LLM, and writes `data/output/{task_id}/test-suggestions.md`. A failure here is logged and ignored.
4. The frontend already polls/awaits the diagnosis response; on next navigation to the detail page, the new Tab is populated from the file.

### Manual path

1. User opens `TaskDetailPage`, clicks "Generate test suggestions" in the Actions Tab.
2. The frontend calls `POST /api/diagnosis/test-suggestions` with `{ task_id }`.
3. The backend runs the suggester and returns `{ content, path }`.
4. The frontend shows a success message and bumps a `key` on the panel to force a re-fetch of the file.

## Module Responsibilities

### `diagnose_tool/analyzer/test_suggester.py`
- `TestSuggester.run(task_id) -> str`
- `TestSuggester.run_and_save(task_id) -> str` (writes file, returns content)
- `_find_test_template(data_dir) -> Path | None`
- `_fallback_test_template() -> str`
- `DiagnosisNotFoundError`

### `diagnose_tool/api/routes_diagnosis.py`
- New `POST /api/diagnosis/test-suggestions` route.
- `TestSuggestionsRequest` and `TestSuggestionsResponse` Pydantic models.

### `diagnose_tool/analyzer/diagnosis.py`
- Add a single best-effort auto-call at the end of `run()`.
- Read `auto_generate_tests` from settings (default `True`).

### `diagnose_tool/analyzer/task_reader.py`
- Add `TEST_SUGGESTIONS_FILENAME = "test-suggestions.md"` and `read_test_suggestions(task_id) -> str | None`.

### `diagnose_tool/api/routes_source.py`
- Add `GET /api/source/task/{task_id}/test-suggestions` route that returns `{ content }` (mirrors `evidence-pack`).

### `frontend/src/components/TestSuggestionsPanel.tsx`
- Reads the file via the new GET endpoint, parses `### Test:` headings, renders cards with copy buttons.

### `frontend/src/pages/TaskDetailPage.tsx`
- Add the fifth Tab and the new Actions button.

### `frontend/src/api/diagnosisApi.ts` and `frontend/src/api/taskApi.ts`
- New client functions.

## Storage

- New tracked file: `data/output/{task_id}/test-suggestions.md` is per-run output (regenerable; the path is consistent with other task artifacts).
- New tracked template: `docs/05-domain/test-suggestion-template.md`.
- No new database, no new cache, no new index.

## Error Handling

- `DiagnosisNotFoundError` is caught at the route layer and translated to `HTTPException(404, "Diagnosis not found for task {task_id}; run diagnosis first")`.
- `LLMClientError` is caught and translated to `HTTPException(502, "LLM call failed")`.
- The auto-hook catches any exception and logs a warning; it never raises out of `DiagnosisOrchestrator.run()`.

## Memory Behavior

- The suggester reads two small files (the diagnosis and the evidence pack) and writes one Markdown file. No streaming concerns.
- The frontend parses the Markdown in the browser; the parsed structure is small.

## Tests

- `tests/test_test_suggester.py`:
  - `test_run_returns_markdown` — happy path with a fake `LLMClient`.
  - `test_run_raises_when_diagnosis_missing`.
  - `test_run_raises_when_task_missing`.
  - `test_run_and_save_writes_file_and_overwrites`.
  - `test_fallback_template_used_when_file_missing`.
- Frontend:
  - `TestSuggestionsPanel.test.tsx` — empty state, renders parsed cards, copy button.
- Playwright MCP: navigate to a task detail page; the new Tab is visible; the panel renders whatever `test-suggestions.md` content is on disk (or shows the empty state).

## Compatibility

- No storage contract change.
- `DiagnosisOrchestrator.run()` return value is unchanged; only a new best-effort side effect is added.
- The new GET endpoint follows the same shape as `evidence-pack`, `case-draft`, and friends.
- Existing tasks that were diagnosed before this change shipped can be backfilled by clicking the new "Generate test suggestions" button.

## Open Questions

- Should the LLM include language hints (e.g., the project's language from the evidence) in the prompt? Deferred — the LLM can infer.
- Should the test-suggestions be added to the case-draft? Deferred — the standalone file is the right scope for V0.4.
