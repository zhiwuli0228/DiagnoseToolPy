## 1. Backend Service And Routes

- [x] 1.1 Add `diagnose_tool/analyzer/task_reader.py` with the central `task_id` validator and the five read functions
  - Files: `diagnose_tool/analyzer/task_reader.py`
  - Behavior: `_validate_task_id` rejects anything not matching `[A-Za-z0-9_-]+`; `list_tasks` enumerates the configured output root and skips dirs without `progress.json`; `read_progress` / `read_evidence_pack` / `read_key_logs` / `read_case_draft` return parsed content or `None`
  - Tests: `tests/test_task_reader.py` covers accept-safe, reject `..`, reject empty, reject slash, reject unicode, list-skips-bench-dirs, missing-file-returns-none
  - Verification: `uv run pytest tests/test_task_reader.py -q`
- [x] 1.2 Add the five `GET` routes to `routes_source.py`
  - Files: `diagnose_tool/api/routes_source.py`
  - Behavior: `/api/source/tasks` returns `list[TaskSummary]` sorted by `started_at` desc; the four `/api/source/task/{task_id}/*` routes call the service and return JSON; invalid `task_id` returns `400`
  - Tests: `tests/test_task_routes.py` covers happy path, missing artifact, invalid task_id, list endpoint shape
  - Verification: `uv run pytest tests/test_task_routes.py -q`

## 2. Frontend API Client And Components

- [x] 2.1 Add `frontend/src/api/taskApi.ts`
  - Files: `frontend/src/api/taskApi.ts`
  - Behavior: `getTasks`, `getTaskProgress`, `getTaskEvidencePack`, `getTaskKeyLogs`, `getTaskCaseDraft` typed with `Record<string, unknown> | null` / `unknown[] | null`
  - Tests: API contract is exercised indirectly through component tests
  - Verification: TypeScript build passes
- [x] 2.2 Extract `frontend/src/components/ThreadResultsPanel.tsx`
  - Files: `frontend/src/components/ThreadResultsPanel.tsx`, `frontend/src/pages/AnalysisTasksPage.tsx` (replace inline render with the component)
  - Behavior: same behavior as the inline block on `AnalysisTasksPage`: add-one, add-all, dedupe, remove, empty state
  - Tests: `frontend/src/components/__tests__/ThreadResultsPanel.test.tsx`
  - Verification: `npm test -- --run ThreadResultsPanel`
- [x] 2.3 Add `frontend/src/components/KeyLogsList.tsx` and `TaskOverview.tsx`
  - Files: `frontend/src/components/KeyLogsList.tsx`, `frontend/src/components/TaskOverview.tsx`
  - Behavior: `KeyLogsList` renders rows with "+" buttons; `TaskOverview` renders status, source, started/finished, runtime, processed/total bytes, current file, failure message
  - Tests: `KeyLogsList.test.tsx`, `TaskOverview.test.tsx`
  - Verification: `npm test -- --run KeyLogsList TaskOverview`

## 3. TaskDetailPage And Historical Table

- [x] 3.1 Rewrite `frontend/src/pages/TaskDetailPage.tsx`
  - Files: `frontend/src/pages/TaskDetailPage.tsx`
  - Behavior: 4-section Tabs page; `Promise.all` for the 5 reads; per-section loading / error / not-produced states; Actions tab wires to existing flows
  - Tests: `frontend/src/pages/__tests__/TaskDetailPage.test.tsx`
  - Verification: `npm test -- --run TaskDetailPage`
- [x] 3.2 Add `TaskHistoryTable` slice to `AnalysisTasksPage.tsx`
  - Files: `frontend/src/pages/AnalysisTasksPage.tsx`, `frontend/src/components/TaskHistoryTable.tsx` (new)
  - Behavior: list table at the bottom of the page; row click → `navigate('/analysis/{task_id}')`; empty / error / loading states
  - Tests: extend `frontend/src/pages/__tests__/AnalysisTasksPage.test.tsx` if present
  - Verification: `npm test -- --run AnalysisTasksPage`
- [x] 3.3 Add i18n keys
  - Files: existing i18n resource files
  - Behavior: keys for `analysisTasks.taskTable.*` (empty, error, retry, columns) and `taskDetail.*` (overview, evidence, threads, keyLogs, caseDraft, actions, startDiagnosis, export, rerun, delete, confirmDelete, notProduced, etc.)
  - Tests: review only
  - Verification: keys are present in both English and Chinese

## 4. E2E And Final Verification

- [x] 4.1 Add Playwright E2E spec
  - Files: `tests/e2e/analysis_task_detail.spec.ts`
  - Behavior: full drill-down flow with real backend + frontend; capture screenshot; assert no console errors
  - Tests: spec passes locally
  - Verification: `npx playwright test tests/e2e/analysis_task_detail.spec.ts`
- [x] 4.2 Run the full regression suite
  - Files: `tests/`, `frontend/src/`
  - Behavior: 526/526 backend tests pass; Vitest suite passes
  - Tests: `uv run pytest -q`, `npm test -- --run`
  - Verification: terminal output reports all green
- [x] 4.3 Update durable docs
  - Files: `docs/00-project/current-state.md`
  - Behavior: move "Complete log analysis UI" from Known Gap to Implemented
  - Tests: review only
  - Verification: `git diff docs/00-project/current-state.md` shows the move
