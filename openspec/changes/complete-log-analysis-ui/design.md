## Context

`frontend/src/pages/AnalysisTasksPage.tsx` has grown to 1,302 lines and concentrates every "log analysis" interaction: source check, scan, search, cluster, thread results, diagnosis drawer, workspace export, preview prompt, bugfix prompt. The companion `frontend/src/pages/TaskDetailPage.tsx` is a 26-line stub rendering an "Under Development" placeholder. `current-state.md` lists "Complete log analysis UI" as a Known Gap.

This change introduces a real drill-down: a historical task table on `AnalysisTasksPage` whose rows navigate to a fully-implemented `TaskDetailPage` with four sections, plus the minimal backend read endpoints needed to feed it. The change is intentionally narrow: it does not refactor the rest of `AnalysisTasksPage`, does not add real-time polling, and does not change the storage contract.

## Goals / Non-Goals

**Goals**
- Historical task list table on `AnalysisTasksPage` (task_id, source path, status, started, processed/total bytes); row click navigates to `/analysis/{task_id}`.
- `TaskDetailPage` with four sections, rendered as Ant Design Tabs:
  1. **Overview** — status, source path, started/finished, runtime, processed/total bytes, current file, failure message.
  2. **Evidence & Threads** — `evidence-pack.md` rendered; a `ThreadResultsPanel` extracted from `AnalysisTasksPage` with add-one / add-all / dedupe / remove / empty-state.
  3. **Key Logs & Case Draft** — key logs list with "add to evidence basket" buttons; `case-draft.md` rendered.
  4. **Actions** — Start diagnosis, Export workspace, Re-run scan, Delete.
- Five new read-only backend endpoints under `diagnose_tool/api/routes_source.py` to serve the data.
- A thin `diagnose_tool/analyzer/task_reader.py` service that owns path validation and file IO.
- A reusable `frontend/src/components/ThreadResultsPanel.tsx` extracted from `AnalysisTasksPage`.
- New frontend API client `frontend/src/api/taskApi.ts`.
- i18n keys for the new UI.
- Backend tests and frontend tests.
- Playwright E2E verification per CLAUDE.md.

The Overview tab in the design shows only the fields actually present in the current `progress.json` (status, progress, current_step, updated_at). Fields like started/finished/processed_bytes/total_bytes are forward-compatible: if a future analyzer change adds them, the Overview tab renders them automatically. The detail page does not invent values for fields that are not on disk.

**Non-Goals**
- No refactor of the rest of `AnalysisTasksPage.tsx`. The 1,302 lines outside the new table addition stay as-is.
- No real-time progress polling on the detail page.
- No change to the write-side endpoints in `routes_source.py`.
- No change to `thread_stack_parser.py` or `thread_artifact.py`.
- No rename / duplicate / move task features.
- No new dependency. If `react-markdown` is not already a project dep, fall back to `<pre>` rendering.
- No change to the on-disk storage contract.
- No new database, cache, or index.

## Decisions

### 1. Service layer at `analyzer/task_reader.py`, thin routes in `routes_source.py`

A new `diagnose_tool/analyzer/task_reader.py` exposes:

```python
def list_tasks() -> list[TaskSummary]
def read_progress(task_id: str) -> dict | None
def read_evidence_pack(task_id: str) -> str | None
def read_key_logs(task_id: str) -> list[dict] | None
def read_case_draft(task_id: str) -> str | None
```

All five functions run `task_id` through a single validator:

```python
_TASK_ID_RE = re.compile(r"[A-Za-z0-9_-]+")
def _validate_task_id(task_id: str) -> str:
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError(f"invalid task_id {task_id!r}")
    return task_id
```

The service is the only module that constructs `data/output/{task_id}/...` paths. The routes call the service and wrap results in HTTP responses. This matches the project's "thin API" rule and is unit-testable without spinning up FastAPI.

### 2. List endpoint reads only `progress.json` per task

`list_tasks()` enumerates the configured output root (`Path("data/output")` per `diagnose_tool/analyzer/output_context.py:24`) and, for each subdirectory:

- Skips it if it has no `progress.json` (filters out unrelated dirs like `bench-full/` or `bench-single/`).
- Reads `progress.json`; the current schema has only `status`, `progress` (0-100), `current_step`, `updated_at`. The service passes the full parsed object through so the frontend can render whatever fields exist.
- Returns a `TaskSummary` with `task_id` (directory name), `status`, plus the raw `progress` payload (so the frontend can show `progress`, `current_step`, `updated_at`).

Bounded IO. The `data/output/` root is shared with the storage contract docs and is not re-derived anywhere else.

### 3. Missing artifacts return `None`, not 404

A task may have been partially analyzed (e.g., no `key-logs.json` because the analyzer did not produce one, or no `case-draft.md` because no case was drafted). The service returns `None` for those. The routes return:

- `200` with the data, or
- `200` with an empty list for `key-logs`, or
- `200` with `null` for `evidence-pack` / `case-draft` so the frontend can render a "not produced" state.

`progress.json` is the only file required for a task to appear in the list. If `progress.json` is missing, the directory is skipped (defensive — keeps `data/output/` clean even if other tools drop files there).

### 4. `ThreadResultsPanel` is extracted, not duplicated

The existing thread results rendering in `AnalysisTasksPage` is moved to `frontend/src/components/ThreadResultsPanel.tsx`. The component takes:

```ts
interface ThreadResultsPanelProps {
  taskId: string;
  onSelectionChange?: (count: number) => void;
}
```

It internally calls `getThreadResults(taskId)` and uses `useDiagnosis().setSelections` to add thread items. Both `AnalysisTasksPage` and `TaskDetailPage` consume the same component.

### 5. Actions on the detail page compose existing flows

- **Start diagnosis**: navigate to `/diagnosis?taskId={id}` (or a new `DiagnosisStudio` deep-link with the task preselected and one thread or one log line pre-added to the basket). The detail page does not start the diagnosis inline; it deep-links.
- **Export workspace**: open the existing workspace-directory picker, then call `exportWorkspace` with the task_id and the current basket selections.
- **Re-run scan**: navigate back to `AnalysisTasksPage` with the source path prefilled (via a `?path=...` query string the page reads on mount). The user clicks "Scan" again.
- **Delete**: confirm modal, then call `deleteTempDir(taskId)`. After success, navigate back to `AnalysisTasksPage`.

No new backend endpoints for these actions; the detail page is a coordinator.

### 6. Minimal slice on `AnalysisTasksPage`

A new subcomponent `TaskHistoryTable` is added at the bottom of the page, with its own state (loading + table rows + error). It calls `getTasks()` on mount. Row click navigates to `/analysis/{task_id}`. The existing top-of-page scan / search / cluster section is untouched.

### 7. No real-time polling

The detail page is a snapshot view. If the user wants to see fresh data, they click refresh or navigate away and back. Polling would require a backend stream (SSE or WebSocket) and is out of scope.

## Architecture

```text
  +----------------------------+         +---------------------------------+
  | AnalysisTasksPage.tsx      |  click  | TaskDetailPage.tsx              |
  |  - existing top section    |  row    |  - Overview tab                 |
  |  - new TaskHistoryTable    |-------->|  - Evidence & Threads tab       |
  +----------------------------+         |  - Key Logs & Case Draft tab    |
                                         |  - Actions tab                  |
                                         +---------------------------------+
                                                        |
                                  Promise.all (5 calls) |
                                                        v
                                         +---------------------------------+
                                         | taskApi.ts (frontend)           |
                                         +---------------------------------+
                                                        |
                                                        v
                                         +---------------------------------+
                                         | routes_source.py (5 new GET)    |
                                         +---------------------------------+
                                                        |
                                                        v
                                         +---------------------------------+
                                         | analyzer/task_reader.py         |
                                         |  - validate task_id             |
                                         |  - read files in data/output/   |
                                         +---------------------------------+
```

## Data Flow

### Listing (AnalysisTasksPage)

1. Mount → `getTasks()` → `GET /api/source/tasks`.
2. `routes_source.list_tasks_route()` calls `task_reader.list_tasks()`.
3. `task_reader.list_tasks()` enumerates `data/output/`, reads `task.yaml` + `progress.json` per subdir, filters out dirs without `progress.json`, returns `list[TaskSummary]`.
4. Frontend renders the table. Each row carries the `task_id`; click → `navigate('/analysis/{task_id}')`.

### Detail Page

1. Mount → URL param `taskId`.
2. `Promise.all([getProgress(taskId), getEvidencePack(taskId), getKeyLogs(taskId), getCaseDraft(taskId), getThreadResults(taskId)])` fires five (or six, including the existing thread endpoint) concurrent reads.
3. Each section renders independently with its own loading / error / empty state. If a section's data is `null`, the section shows an "Not produced" message.
4. The Actions tab is always enabled; its buttons drive the existing flows.

### Add to Evidence Basket (Thread / Key Log)

- **Thread**: `ThreadResultsPanel` already does this in `AnalysisTasksPage`; the same component does it on the detail page. It calls `useDiagnosis().setSelections(prev => ...)` with a dedupe pass on `type === 'thread' && id === ...`.
- **Key Log**: a new tiny `KeyLogsList` component takes a `LogKeyItem[]`, renders each as a row with a "+" button. The button calls `useDiagnosis().setSelections` with a `SelectionItem` of type `'log'`. The exact key-log shape is decided during implementation; the spec is `Record<string, unknown>` for now (the service returns the raw JSON if present).

## Module Responsibilities

### `diagnose_tool/analyzer/task_reader.py`
- `_validate_task_id(task_id)` — central path-component validator.
- `list_tasks()` — read `data/output/`, return `list[TaskSummary]`.
- `read_progress(task_id)`, `read_evidence_pack(task_id)`, `read_key_logs(task_id)`, `read_case_draft(task_id)` — read the named file, return parsed content or `None` if missing.
- `TaskSummary` Pydantic / dataclass.

### `diagnose_tool/api/routes_source.py`
- Five new `GET` routes that call the service. The existing write-side routes are untouched.
- `GET /api/source/tasks` → `list[TaskSummary]` (each carries `task_id`, `status`, plus the raw `progress.json` payload)
- `GET /api/source/task/{task_id}/progress` → `dict | null`
- `GET /api/source/task/{task_id}/evidence-pack` → `{ content: str | null }`
- `GET /api/source/task/{task_id}/key-logs` → `{ content: str | null }` (text, since `key-logs.txt` is plain text)
- `GET /api/source/task/{task_id}/case-draft` → `{ content: str | null }`

### `frontend/src/api/taskApi.ts`
- `getTasks()`, `getTaskProgress(taskId)`, `getTaskEvidencePack(taskId)`, `getTaskKeyLogs(taskId)`, `getTaskCaseDraft(taskId)`.
- Same axios / typing style as `sourceApi.ts` and `diagnosisApi.ts`.

### `frontend/src/components/ThreadResultsPanel.tsx`
- Props: `taskId`, `onSelectionChange?`.
- Renders the table from `getThreadResults`, the add-one / add-all buttons, the parse status tag, and the dedupe behavior.

### `frontend/src/components/KeyLogsList.tsx`
- Props: `keyLogs: LogKeyItem[]`, `onAdd?`.
- Renders each key log as a row with a "+" button. Empty state: "No key logs in this task".

### `frontend/src/components/TaskOverview.tsx`
- Props: `progress`, `task`.
- Renders status, source, started/finished, runtime, processed/total bytes, current file, failure message.

### `frontend/src/pages/TaskDetailPage.tsx`
- Reads `:taskId` from URL.
- Calls all five reads in `Promise.all`; renders the four Tabs.
- The Actions tab wires to existing flows.

### `frontend/src/pages/AnalysisTasksPage.tsx` (slice only)
- Imports `TaskHistoryTable` and renders it below the existing top section.
- The existing state for the top section is untouched.

## Storage

- On-disk: unchanged. The new endpoints are read-only over the existing `data/output/{task_id}/` layout.
- In-memory: nothing new in the backend beyond the per-request response.
- Frontend: adds `useTasks` and `useTaskDetail` hooks (state per page). No global state added beyond what `DiagnosisContext` already exposes.

## Error Handling

- `_validate_task_id` raises `ValueError`; the route catches it and returns `HTTPException(400, "invalid task_id")`.
- Missing files: service returns `None`; route returns `200` with `null` (or empty list for `key-logs`); frontend renders an "Not produced" / "No key logs" state.
- Backend unreachable: each frontend call has its own `try/catch`; the section shows an error message with a "Retry" button.
- Delete failure: the existing `deleteTempDir` flow already surfaces a `message.error`. The detail page reuses it.

## Memory Behavior

- `list_tasks()` reads at most two small files per directory and is bounded by the number of task directories. No streaming needed.
- `read_evidence_pack` and `read_case_draft` read the full file into a string. These are small (markdown; KB range). If they grow into the MB range, a future change can add a `?from=&to=` range read; not in scope.
- The frontend does not load the full `evidence-pack.md` into a global store; it lives in the per-section state.

## Tests

### Backend
- `tests/test_task_reader.py`
  - `test_validate_task_id_accepts_safe_inputs`
  - `test_validate_task_id_rejects_traversal`
  - `test_list_tasks_skips_dirs_without_progress`
  - `test_list_tasks_reads_task_yaml_and_progress`
  - `test_read_evidence_pack_missing_returns_none`
  - `test_read_key_logs_invalid_json_returns_none` (or raises; we choose `None` and document it)
- `tests/test_task_routes.py`
  - Five happy-path tests (one per route) using a tmp task directory.
  - 404/400 tests for missing or invalid task_id.

### Frontend
- `frontend/src/components/__tests__/ThreadResultsPanel.test.tsx`
  - add-one, add-all, dedupe, remove, empty state.
- `frontend/src/components/__tests__/KeyLogsList.test.tsx`
  - render rows, click "+", empty state.
- `frontend/src/components/__tests__/TaskOverview.test.tsx`
  - render with progress, render with failure message.
- `frontend/src/pages/__tests__/TaskDetailPage.test.tsx`
  - 4 sections render after Promise.all resolves.
  - Empty / not-produced states for missing files.
  - Click "Start diagnosis" navigates correctly.

### E2E (per CLAUDE.md)
- `tests/e2e/analysis_task_detail.spec.ts` (Playwright)
  - Start the backend (`uv run uvicorn ...`) and frontend (`npm run dev`).
  - Run a real scan on a fixture directory.
  - Click the resulting row in the historical table.
  - Assert: URL is `/analysis/{task_id}`; all 4 Tabs render; "Evidence & Threads" shows the evidence-pack header; clicking "Add All Threads" updates the evidence basket count.
  - Capture a screenshot at the end.

## Compatibility

- The existing write-side routes and analysis flows are untouched.
- The `evidence-pack.md`, `case-draft.md`, and `progress.json` formats are unchanged.
- Frontend: the new `TaskHistoryTable` is additive; users who never click a row see no change.
- `TaskDetailPage` URL `/analysis/{task_id}` is new; the old stub at the same URL is replaced.

## Open Questions

- Should the historical task table support filtering? Deferred.
- Should `TaskDetailPage` deep-link to a specific tab? Deferred.
- Should `summary.html` be rendered anywhere? Deferred.
