# Implementation Plan: add-test-suggestion-generation

## Goal

Implement the test suggestion generation capability: a thin `TestSuggester` module, two new API endpoints, an auto-generation hook on `DiagnosisOrchestrator.run()`, a new fifth Tab on `TaskDetailPage` with copy-to-clipboard, and a manual "Generate test suggestions" button. With backend and frontend tests and Playwright MCP browser verification per CLAUDE.md.

## Pre-conditions

- Branch `claude_master` is clean and ahead of `origin/claude_master` by 23 commits (after `complete-log-analysis-ui`).
- `diagnose_tool/analyzer/diagnosis.py` writes `data/cases/{task_id}/ai-diagnosis.md`.
- `docs/05-domain/prompt-template.md` is the existing diagnosis prompt template; the new template lives next to it.
- `frontend/src/pages/TaskDetailPage.tsx` already has 4 Tabs; the 5th Tab is added.
- `diagnose_tool/analyzer/task_reader.py` and `routes_source.py` provide the read pattern for task artifacts; the new endpoint mirrors them.
- `uv` and `npm` are available on the developer's machine.

## Steps

### Step 1 — Prompt template

1. Create `docs/05-domain/test-suggestion-template.md` with the two placeholders (`{diagnosis}`, `{evidence_pack}`) and the three-section structure.
2. The structure: a Reproduction section, a Verification section, and a Negative / Edge section. Each test is a `### Test:` heading with `**Type**`, `**Goal**`, `**Code**` block, `**Expected**`.

### Step 2 — `TestSuggester` service

1. Create `diagnose_tool/analyzer/test_suggester.py` with:
   - `class DiagnosisNotFoundError(DiagnosisError)` (or reuse if a base class exists)
   - `class TestSuggester` with `__init__(llm_config, data_dir)`, `run(task_id)`, `run_and_save(task_id)`
   - `_find_test_template(data_dir) -> Path | None`
   - `_fallback_test_template() -> str` (in-module constant matching the file's structure)
2. The service reads `data/cases/{task_id}/ai-diagnosis.md` and `data/output/{task_id}/evidence-pack.md`, builds the prompt, calls `self._llm.chat(messages=[...])`, and returns the result text.
3. `run_and_save` writes the result to `data/output/{task_id}/test-suggestions.md` (overwriting any prior content).

**Validation**: `uv run pytest tests/test_test_suggester.py -q` (5+ tests).

### Step 3 — `POST /api/diagnosis/test-suggestions` route

1. Add the route in `routes_diagnosis.py`:
   ```python
   class TestSuggestionsRequest(BaseModel):
       task_id: str
   class TestSuggestionsResponse(BaseModel):
       content: str
       path: str
   @router.post("/diagnosis/test-suggestions", response_model=TestSuggestionsResponse)
   def generate_test_suggestions(request: TestSuggestionsRequest) -> TestSuggestionsResponse:
       ...
   ```
2. The route resolves the LLM config and data dir from the same places the existing diagnosis route does. Translate `DiagnosisNotFoundError` / `TaskNotFoundError` to `404`; `LLMClientError` to `502`.

**Validation**: existing test suite still passes; new tests cover the route indirectly via the suggester tests.

### Step 4 — `read_test_suggestions` and the read route

1. Add `TEST_SUGGESTIONS_FILENAME = "test-suggestions.md"` and `read_test_suggestions(task_id) -> str | None` to `task_reader.py`.
2. Add `GET /api/source/task/{task_id}/test-suggestions` to `routes_source.py`, returning `{ content: str | null }` and rejecting invalid `task_id` with `400`.

**Validation**: `uv run pytest tests/test_task_routes.py -q` (existing + new).

### Step 5 — Auto-generation hook

1. In `DiagnosisOrchestrator.run()`, after writing `ai-diagnosis.md`, add:
   ```python
   if self._settings.auto_generate_tests:
       try:
           TestSuggester(self._llm_config, self._data_dir).run_and_save(task_id)
       except Exception as exc:
           logger.warning("test suggestion auto-generation failed for %s: %s", task_id, exc)
   ```
2. Add `auto_generate_tests: bool = True` to the settings (via a small helper that reads from `config/app.yaml` or via the `LLMClient` settings).
3. A unit test verifies that a failure in the suggester does not raise out of `run()`.

**Validation**: `uv run pytest -q` (full backend suite green).

### Step 6 — Frontend API clients

1. Add `generateTestSuggestions(taskId)` to `frontend/src/api/diagnosisApi.ts`.
2. Add `getTaskTestSuggestions(taskId)` to `frontend/src/api/taskApi.ts`.

**Validation**: `npx tsc --noEmit` clean.

### Step 7 — `TestSuggestionsPanel` and the fifth Tab

1. Create `frontend/src/components/TestSuggestionsPanel.tsx`:
   - `props: { taskId: string }`
   - Calls `getTaskTestSuggestions(taskId)` on mount.
   - Parses the content on `### Test:` headings into cards with Type / Goal / Code / Expected.
   - Each code block has a Copy button that uses `navigator.clipboard.writeText`.
   - Renders an empty state when content is `null` and a loading / error state per the existing pattern.
2. Add the fifth Tab to `TaskDetailPage`. Use `Promise.all`-style load via the existing `usePromise` hook, parallel with the other tabs.

**Validation**: `npm test -- --run TestSuggestionsPanel` (3+ tests).

### Step 8 — Manual generate button

1. Add a "Generate test suggestions" button to the Actions Tab.
2. The button calls `generateTestSuggestions(taskId)`, then bumps a `key` on `TestSuggestionsPanel` (or refreshes its internal state) to fetch the new content.
3. On success, show a success message; on failure, show the error.

**Validation**: `npm test -- --run TaskDetailPage` if the test exists.

### Step 9 — i18n

1. Add keys to `frontend/src/locales/en.json` and `zh.json`:
   - `taskDetail.tabs.testSuggestions`
   - `taskDetail.testSuggestions.title`, `.empty`, `.notProduced`, `.copy`, `.copied`
   - `taskDetail.actions.generateTests.label`, `.success`, `.failed`

**Validation**: review only.

### Step 10 — Update `current-state.md`

1. Move "Implement test suggestion generation (V0.4 extended)" from Known Gap to Implemented in `docs/00-project/current-state.md`. Cross-link to the `add-test-suggestion-generation` change.

**Validation**: `git diff docs/00-project/current-state.md` shows the move.

### Step 11 — Commit and archive

1. Stage files by explicit path (no `git add -A`).
2. Use a `feat(...)` commit for the implementation, plus a `chore(openspec)` archive commit, plus a `docs(current-state)` cross-link commit.
3. `openspec archive add-test-suggestion-generation -y --skip-specs` (consistent with the prior `add-requirement-acceptance`, `add-thread-stack-bench`, and `complete-log-analysis-ui` archive commands in this session).

## Out of scope (deferred)

- Modifying the existing `DiagnosisOrchestrator.run_with_context` (the conversational path) to also auto-generate tests.
- Persisting test-suggestions to the casebase (the file is task-scoped, not case-scoped).
- Executing the generated test code automatically.

## Validation checkpoints

| Checkpoint | Command | Pass criterion |
|------------|---------|----------------|
| Suggester service | `uv run pytest tests/test_test_suggester.py -q` | 5+ passed |
| Full backend | `uv run pytest -q` | all green (no regression) |
| Frontend types | `npx tsc --noEmit` | exit 0 |
| Component test | `npm test -- --run TestSuggestionsPanel` | all green |
| Full frontend | `npm test -- --run` | all green |
| Playwright MCP | open detail page; click the new Tab; click "Generate" | Tab renders; file content is fetched |
| Status complete | `openspec status --change add-test-suggestion-generation --json` | `isComplete: true` |
