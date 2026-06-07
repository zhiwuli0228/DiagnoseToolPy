# Implementation Plan: complete-log-analysis-ui

## Goal

Implement the complete log analysis UI: a real four-section `TaskDetailPage` reached from a historical task table on `AnalysisTasksPage`, backed by five new read-only API endpoints and a thin `task_reader` service. Includes unit tests, frontend tests, and a Playwright E2E spec that runs against a real backend and frontend per CLAUDE.md.

## Pre-conditions

- Branch `claude_master` is clean and ahead of `origin/claude_master` by 21 commits (the three prior closeouts).
- `frontend/src/pages/AnalysisTasksPage.tsx` is 1,302 lines and `TaskDetailPage.tsx` is a 26-line stub.
- Backend: `diagnose_tool/api/routes_source.py` has `check`, `scan`, `search`, `upload`, `delete_temp`; the analyzer has `thread_artifact.py` but no `task_reader.py`.
- The configured output root is `data/output/` (per `docs/01-architecture/storage-contract.md` and CLAUDE.md). The plan reads this from settings, not as a hard-coded path.
- The frontend has `react-i18next` already in use; `react-markdown` may or may not be a dependency. The plan falls back to `<pre>` rendering if `react-markdown` is unavailable.
- `uv` and `npm` are available on the developer's machine.

## Steps

### Step 1 — Backend: `task_reader.py` service

1. Create `diagnose_tool/analyzer/task_reader.py` with:
   - `_TASK_ID_RE = re.compile(r"[A-Za-z0-9_-]+")`
   - `_validate_task_id(task_id: str) -> str` (raise `ValueError` for invalid)
   - `@dataclass class TaskSummary(task_id, source_path, status, started_at, finished_at, processed_bytes, total_bytes, current_file)`
   - `list_tasks() -> list[TaskSummary]`
   - `read_progress(task_id) -> dict | None`
   - `read_evidence_pack(task_id) -> str | None`
   - `read_key_logs(task_id) -> list[dict] | None`
   - `read_case_draft(task_id) -> str | None`
2. Use the configured output root from settings (read once at module import time or per call — per call is fine since settings are cheap).
3. Files inside a task directory may be missing; return `None` for missing optional artifacts.

**Validation**: `uv run pytest tests/test_task_reader.py -q` (5+ tests).

### Step 2 — Backend: routes in `routes_source.py`

1. Add 5 `GET` routes. Each route calls the service and wraps exceptions:
   - `GET /api/source/tasks` → 200 with `list[TaskSummary]`
   - `GET /api/source/task/{task_id}/progress` → 200 with parsed JSON or `null`
   - `GET /api/source/task/{task_id}/evidence-pack` → 200 with `{ "content": str | null }`
   - `GET /api/source/task/{task_id}/key-logs` → 200 with `list[dict] | null`
   - `GET /api/source/task/{task_id}/case-draft` → 200 with `{ "content": str | null }`
2. Catch `ValueError` from the validator; raise `HTTPException(400, "invalid task_id")`.
3. Use FastAPI's `Path` for `task_id` (so Swagger docs are clean).

**Validation**: `uv run pytest tests/test_task_routes.py -q` (5+ tests).

### Step 3 — Frontend: `taskApi.ts`

1. Create `frontend/src/api/taskApi.ts` with the five functions, typed with `Record<string, unknown> | null` and `unknown[] | null`.
2. Use the same axios import path as `sourceApi.ts` and `diagnosisApi.ts`.

**Validation**: `npx tsc --noEmit` passes for the frontend.

### Step 4 — Frontend: `ThreadResultsPanel` extraction

1. Create `frontend/src/components/ThreadResultsPanel.tsx`. The component takes:
   ```ts
   interface ThreadResultsPanelProps {
     taskId: string;
   }
   ```
2. Move the thread results state + render from `AnalysisTasksPage` (lines around the existing `getThreadResults` call) into the component. Use `useDiagnosis()` for basket state.
3. In `AnalysisTasksPage.tsx`, replace the inline block with `<ThreadResultsPanel taskId={...} />`.
4. Add `ThreadResultsPanel.test.tsx` covering add-one / add-all / dedupe / empty.

**Validation**: `npm test -- --run ThreadResultsPanel` passes; the existing `AnalysisTasksPage` tests still pass.

### Step 5 — Frontend: `KeyLogsList` and `TaskOverview`

1. `KeyLogsList.tsx`: `props: { keyLogs: Array<Record<string, unknown>> }`. Each row shows a label (filename or first 80 chars) and a "+" button that calls `useDiagnosis().setSelections`.
2. `TaskOverview.tsx`: `props: { progress: Record<string, unknown> | null, task: { source_path: string } }`. Renders status tag, source path, started/finished, runtime, processed/total bytes, current file, failure message.
3. Add tests for both.

**Validation**: `npm test -- --run KeyLogsList TaskOverview` passes.

### Step 6 — Frontend: rewrite `TaskDetailPage.tsx`

1. Replace the 26-line stub with a real page.
2. Use Ant Design `Tabs` with 4 items.
3. `Promise.all` the 5 reads on mount.
4. Each section has its own loading / error / not-produced state.
5. Actions tab wires to the existing flows:
   - "Start diagnosis" → `navigate('/diagnosis', { state: { taskId } })` (or query string — pick one; document the choice in the page).
   - "Export workspace" → open the existing workspace-dir picker modal, then call `exportWorkspace`.
   - "Re-run scan" → `navigate('/analysis?path=' + encodeURIComponent(source_path))`.
   - "Delete" → confirm modal → `deleteTempDir(taskId)` → on success `navigate('/analysis')`.
6. Add `TaskDetailPage.test.tsx` with mocks for all 5 reads.

**Validation**: `npm test -- --run TaskDetailPage` passes; manual visual check via Playwright E2E.

### Step 7 — Frontend: `TaskHistoryTable` on `AnalysisTasksPage`

1. Create `frontend/src/components/TaskHistoryTable.tsx`. Renders a list, empty state, error state with retry.
2. Add `<TaskHistoryTable />` at the bottom of `AnalysisTasksPage`.
3. Row click → `navigate('/analysis/{task_id}')`.

**Validation**: existing AnalysisTasksPage tests still pass; manual check.

### Step 8 — i18n

1. Add keys to the existing i18n resource files. Both English and Chinese values.
2. The detail page and table must not contain hard-coded English strings in JSX.

**Validation**: a code search for the new keys in the resource files succeeds.

### Step 9 — Playwright E2E

1. Create `tests/e2e/analysis_task_detail.spec.ts` per the spec.
2. The spec starts the backend (`uv run uvicorn`) and frontend (`npm run dev`); uses Playwright's `webServer` config or assumes the developer has them running locally.
3. Runs a scan on a fixture directory (`tests/e2e/fixtures/...`).
4. Clicks the row in the historical table.
5. Asserts the URL is `/analysis/{task_id}`; the four Tabs render; "Add All Threads" updates the basket count.
6. Captures a screenshot.
7. Fails on any console error.

**Validation**: spec passes locally; screenshot is committed as evidence.

### Step 10 — Update `current-state.md`

1. Move "Complete log analysis UI" from Known Gaps to Implemented in `docs/00-project/current-state.md`.

**Validation**: `git diff docs/00-project/current-state.md` shows the move.

### Step 11 — Commit and archive

1. Stage files by explicit path (no `git add -A`).
2. Use a single `feat(...)` commit for the implementation, plus a small `chore(openspec)` archive commit, plus a `docs(current-state)` cross-link commit.
3. `openspec archive complete-log-analysis-ui -y --skip-specs`.

## Out of scope (deferred)

- Refactoring the rest of `AnalysisTasksPage.tsx`.
- Real-time progress polling on the detail page.
- Filtering or sorting on the historical task table.
- Deep-linking to a specific tab via URL hash.
- Rendering `summary.html`.
- Renaming / duplicating tasks.

## Validation checkpoints

| Checkpoint | Command | Pass criterion |
|------------|---------|----------------|
| Backend service | `uv run pytest tests/test_task_reader.py -q` | 5+ passed |
| Backend routes | `uv run pytest tests/test_task_routes.py -q` | 5+ passed |
| Full backend | `uv run pytest -q` | 526+ passed (we add more) |
| Frontend types | `npx tsc --noEmit` | exit 0 |
| ThreadResultsPanel | `npm test -- --run ThreadResultsPanel` | all green |
| KeyLogsList + TaskOverview | `npm test -- --run KeyLogsList TaskOverview` | all green |
| TaskDetailPage | `npm test -- --run TaskDetailPage` | all green |
| AnalysisTasksPage | `npm test -- --run AnalysisTasksPage` | all green |
| E2E | `npx playwright test tests/e2e/analysis_task_detail.spec.ts` | exit 0 |
| Status complete | `openspec status --change complete-log-analysis-ui --json` | `isComplete: true` |
