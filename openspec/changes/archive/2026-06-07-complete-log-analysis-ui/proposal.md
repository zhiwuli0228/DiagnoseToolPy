## Why

`frontend/src/pages/AnalysisTasksPage.tsx` has grown to 1,302 lines and concentrates every "log analysis" interaction in one place. The companion `frontend/src/pages/TaskDetailPage.tsx` is a 26-line stub that renders "Under Development". `current-state.md` lists "Complete log analysis UI" as a Known Gap, and the user-facing pain is concrete: after a scan or cluster finishes, the reviewer has no first-class place to inspect a task's overview, evidence pack, thread results, key logs, case draft, or to take the obvious next action (start diagnosis, export workspace, re-run, delete). Everything currently lives in modal/tab chaos on `AnalysisTasksPage`.

This change introduces a real drill-down: a historical task table on `AnalysisTasksPage` whose rows navigate to a fully-implemented `TaskDetailPage` with four sections, plus the minimal backend read endpoints needed to feed it. The change is intentionally narrow — it does not refactor the rest of `AnalysisTasksPage`, does not add real-time polling, and does not change the storage contract.

## What Changes

**Historical task table on `AnalysisTasksPage`**
- From: no historical task list; the user can only interact with the most recent scan/cluster result.
- To: a table at the bottom of `AnalysisTasksPage` lists every known analysis task (task_id, source path, status, started, processed/total bytes). Row click navigates to `/analysis/{task_id}`.
- Reason: a reviewer needs a way to find and revisit any past task, not only the most recent one.
- Impact: non-breaking additive slice of `AnalysisTasksPage`; the existing top section is untouched.

**`TaskDetailPage` becomes a real page with four sections**
- From: 26-line stub showing "Under Development".
- To: four Tabs (Overview, Evidence & Threads, Key Logs & Case Draft, Actions), each backed by a small focused component.
- Reason: drill-down is the natural way to give a task its own control surface.
- Impact: replaces the stub. Existing URL `/analysis/{task_id}` now renders useful content.

**Thread results panel extracted to a reusable component**
- From: thread results rendering lives inline in `AnalysisTasksPage` (~150 lines of state + render).
- To: a new `frontend/src/components/ThreadResultsPanel.tsx` consumed by both `AnalysisTasksPage` and `TaskDetailPage`.
- Reason: keep behavior identical across the two pages; future changes touch one component.
- Impact: pure extraction; no behavior change.

**Five new read-only backend endpoints**
- From: no API to read a task's `progress.json`, `evidence-pack.md`, key logs, or `case-draft.md`; no API to list tasks.
- To: `GET /api/source/tasks` plus `GET /api/source/task/{task_id}/{progress|evidence-pack|key-logs|case-draft}`.
- Reason: the frontend detail page needs the data; existing endpoints are write-side and don't serve it.
- Impact: non-breaking additive API.

**`task_reader.py` thin service**
- From: filesystem path access is implicit in any code that touches `data/output/`.
- To: a small `diagnose_tool/analyzer/task_reader.py` owns path validation and file IO. All five new routes call it.
- Reason: centralize the `task_id` validator and the file-existence semantics in one testable module.
- Impact: pure addition; the analyzer service grows by one module.

**Frontend API client + i18n keys**
- From: no `taskApi.ts`; no i18n keys for the detail page or the historical table.
- To: `frontend/src/api/taskApi.ts`; new keys in the existing i18n bundle.
- Reason: keep the frontend code style consistent.
- Impact: non-breaking.

**Tests + Playwright E2E**
- From: no backend test for the new endpoints; no frontend test for the new components or detail page; no E2E coverage of the drill-down flow.
- To: `tests/test_task_reader.py` and `tests/test_task_routes.py`; frontend component and page tests; a new Playwright spec under `tests/e2e/`.
- Reason: match the project's "thin API" testing style and CLAUDE.md's E2E verification rule.
- Impact: non-breaking.

## Capabilities

### New Capabilities
- `complete-log-analysis-ui`: a historical task table on `AnalysisTasksPage`, a real four-section `TaskDetailPage`, a reusable `ThreadResultsPanel`, a thin `task_reader` service, and five read-only backend endpoints. With regression tests and Playwright E2E.

### Modified Capabilities
- None. The existing `react-frontend-shell` capability (which covers the page shell, Ant Design setup, i18n, and routing) gains one new page implementation, one new component, and one new API client. No capability-level behavior change.

## Affected Modules

- `diagnose_tool/analyzer/task_reader.py` — new thin service.
- `diagnose_tool/api/routes_source.py` — five new `GET` routes.
- `tests/test_task_reader.py`, `tests/test_task_routes.py` — new backend tests.
- `frontend/src/api/taskApi.ts` — new client.
- `frontend/src/components/ThreadResultsPanel.tsx` — new (extracted from `AnalysisTasksPage`).
- `frontend/src/components/KeyLogsList.tsx` — new.
- `frontend/src/components/TaskOverview.tsx` — new.
- `frontend/src/pages/TaskDetailPage.tsx` — rewritten from stub to real page.
- `frontend/src/pages/AnalysisTasksPage.tsx` — minimal slice: render `TaskHistoryTable` below the existing top section; thread results block is replaced by `<ThreadResultsPanel .../>`.
- `frontend/src/components/__tests__/ThreadResultsPanel.test.tsx` — new.
- `frontend/src/components/__tests__/KeyLogsList.test.tsx` — new.
- `frontend/src/components/__tests__/TaskOverview.test.tsx` — new.
- `frontend/src/pages/__tests__/TaskDetailPage.test.tsx` — new.
- `tests/e2e/analysis_task_detail.spec.ts` — new Playwright spec.
- i18n resource files (existing paths) — new keys.
- `docs/00-project/current-state.md` — mark "Complete log analysis UI" as implemented.

## Storage Impact

- No on-disk change. The new endpoints are read-only over the existing `data/output/{task_id}/` layout.
- No new database, no new index, no new cache.

## Constraints

- No mandatory database.
- No new Python dependency.
- No new frontend dependency. If `react-markdown` is not already a project dep, fall back to `<pre>` rendering for `evidence-pack.md` and `case-draft.md`. The detail page's other content is Ant Design primitives, which are already in the bundle.
- Existing write-side endpoints in `routes_source.py` are untouched.
- The thread stack parser, evidence compressor, cluster analyzer, and other analyzer modules are untouched.
- The on-disk storage contract is untouched.
- All new tracked files use LF line endings and UTF-8 (PowerShell files, if any, have no BOM).
- The 1,302-line `AnalysisTasksPage.tsx` is sliced, not refactored.

## Risks

- Path traversal if the `task_id` validator is buggy. Mitigation: a single regex (`[A-Za-z0-9_-]+`) checked in one place, with explicit tests for `..`, `/`, `\`, empty string, and unicode.
- The list endpoint reads two small files per task; with many tasks, IO could become a bottleneck. Mitigation: the design returns `list[TaskSummary]` with bounded per-task fields; if profiling shows this is slow, a future change can add a cached `data/output/index.json`. Not in scope here.
- A partial task (e.g., scan in progress) may have `progress.json` but no `evidence-pack.md`. The detail page must render gracefully. Mitigation: each section renders an explicit "Not produced" state, with empty lists / null payloads handled.
- `react-markdown` may not be in the project's deps. Mitigation: the design falls back to `<pre>` rendering; the markdown is still readable.
- The 1,302-line `AnalysisTasksPage.tsx` already concentrates many state hooks. Adding the new slice risks making it even longer. Mitigation: the slice is purely additive (one new component rendered at the bottom); existing hooks and renders are untouched.
- Playwright E2E depends on a running backend + frontend. The CLAUDE.md rule is firm on real-browser verification. Mitigation: the spec includes a CI-friendly invocation, and the developer can run the spec locally with `npm run dev` + `uv run uvicorn`.

## Verification

- `uv run pytest tests/test_task_reader.py tests/test_task_routes.py -q` — new backend tests pass.
- `uv run pytest` — full backend suite still passes (the change is additive).
- `npm test -- --run` — Vitest passes for the new component and page tests; the existing suite still passes.
- `npx playwright test tests/e2e/analysis_task_detail.spec.ts` — drill-down flow works in a real browser. The spec captures a screenshot and a console-error log. The verify pass requires the screenshot.
- Manual: `npm run dev` + `uv run uvicorn ...`; visit `/analysis`, run a scan, click a row, verify the four Tabs render, click "Add All Threads" and confirm the basket count updates, click "Start diagnosis" and confirm the navigation.

## Impact

- `diagnose_tool/`: +1 module (`task_reader.py`); +5 routes in `routes_source.py`.
- `tests/`: +2 backend test files; +1 Playwright E2E spec.
- `frontend/`: +1 API client; +3 components (one extracted, two new); 1 page rewrite; minimal slice on `AnalysisTasksPage`; 4 new test files; i18n key additions.
- `docs/00-project/current-state.md`: one line moves from Known Gap to Implemented.
- No casebase, no retrieval, no exporter, no LLM client changes.
