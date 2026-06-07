## 1. Backend Suggester And Template

- [x] 1.1 Implement `diagnose_tool/analyzer/test_suggester.py` with `TestSuggester.run` and `run_and_save`, plus `DiagnosisNotFoundError`
  - Files: `diagnose_tool/analyzer/test_suggester.py`, `docs/05-domain/test-suggestion-template.md`
  - Behavior: reads `ai-diagnosis.md` + `evidence-pack.md`; calls LLM with focused prompt; writes `data/output/{task_id}/test-suggestions.md`; uses fallback when the template is missing
  - Tests: `tests/test_test_suggester.py` covers happy path, missing diagnosis, missing task, fallback, overwrite
  - Verification: `uv run pytest tests/test_test_suggester.py -q`
- [x] 1.2 Add `POST /api/diagnosis/test-suggestions` route
  - Files: `diagnose_tool/api/routes_diagnosis.py`
  - Behavior: thin wrapper around `TestSuggester.run_and_save`; 404 for missing diagnosis/task, 502 for LLM errors
  - Tests: covered by `tests/test_test_suggester.py` plus an end-to-end check in the full backend suite
  - Verification: `uv run pytest -q`
- [x] 1.3 Add `read_test_suggestions` to `task_reader.py` and `GET /api/source/task/{task_id}/test-suggestions` route
  - Files: `diagnose_tool/analyzer/task_reader.py`, `diagnose_tool/api/routes_source.py`
  - Behavior: returns `{ content }` for the file; 400 for invalid task_id; same shape as `evidence-pack`
  - Tests: extend the existing route tests
  - Verification: `uv run pytest tests/test_task_routes.py -q`

## 2. Auto-Generation Hook

- [x] 2.1 Wire the auto-call at the end of `DiagnosisOrchestrator.run()`
  - Files: `diagnose_tool/analyzer/diagnosis.py`, `config/app.yaml`
  - Behavior: best-effort call after writing `ai-diagnosis.md`; logs and continues on failure; controlled by `diagnosis.auto_generate_tests` (default `true`)
  - Tests: a unit test that the suggester is invoked (and a failure does not raise) when the setting is on
  - Verification: `uv run pytest -q`

## 3. Frontend Tab And Manual Button

- [x] 3.1 Add the API client functions
  - Files: `frontend/src/api/diagnosisApi.ts`, `frontend/src/api/taskApi.ts`
  - Behavior: `generateTestSuggestions(taskId)` and `getTaskTestSuggestions(taskId)`
  - Tests: indirect via component tests
  - Verification: `npx tsc --noEmit`
- [x] 3.2 Add `TestSuggestionsPanel` and the fifth Tab
  - Files: `frontend/src/components/TestSuggestionsPanel.tsx`, `frontend/src/pages/TaskDetailPage.tsx`
  - Behavior: parses `### Test:` headings, renders cards with Type / Goal / Code / Expected, Copy button; empty state when missing
  - Tests: `frontend/src/components/__tests__/TestSuggestionsPanel.test.tsx`
  - Verification: `npm test -- --run TestSuggestionsPanel`
- [x] 3.3 Add the manual "Generate test suggestions" button in Actions
  - Files: `frontend/src/pages/TaskDetailPage.tsx`
  - Behavior: calls the endpoint on click; on success, bumps a `key` to refresh the panel; on failure, shows an error
  - Tests: extend `TaskDetailPage.test.tsx` if present
  - Verification: `npm test -- --run TaskDetailPage`
- [x] 3.4 Add i18n keys
  - Files: `frontend/src/locales/en.json`, `frontend/src/locales/zh.json`
  - Behavior: keys under `taskDetail.testSuggestions.*` and `taskDetail.actions.generateTests.*`
  - Tests: review only
  - Verification: keys are present in both English and Chinese

## 4. Verification And Project Hygiene

- [x] 4.1 Run the full regression suite
  - Files: `tests/`, `frontend/src/`
  - Behavior: full backend suite passes; full Vitest suite passes
  - Tests: `uv run pytest -q`, `npm test -- --run`
  - Verification: terminal output reports all green
- [x] 4.2 Playwright MCP browser verification
  - Files: `frontend/src/pages/TaskDetailPage.tsx` and the new component
  - Behavior: open the detail page for a task, click the fifth Tab, click "Generate test suggestions" in Actions, confirm the file content is rendered
  - Tests: the manual flow described in apply.md
  - Verification: Playwright MCP confirms no console errors and the new Tab renders
- [x] 4.3 Update durable docs
  - Files: `docs/00-project/current-state.md`
  - Behavior: move "Implement test suggestion generation" from Known Gap to Implemented
  - Tests: review only
  - Verification: `git diff docs/00-project/current-state.md` shows the move
