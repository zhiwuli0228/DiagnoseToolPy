# Complete Log Analysis UI

## Purpose

Make every analysis task a first-class, drill-downable object on the analysis page. The analyzer, parser, and evidence pack writers already produce a stable `data/output/{task_id}/` layout; this capability adds the read endpoints, the service that owns the task_id validator, the historical task table on `AnalysisTasksPage`, and a real four-section `TaskDetailPage` so a reviewer can audit any past task in one place.

## Requirements

### Requirement: Task Listing Endpoint
The system MUST provide `GET /api/source/tasks` that returns a JSON array of historical task summaries, sorted by `updated_at` descending. Each entry MUST contain at least `task_id` and `status` (read from `progress.json`); when present in `progress.json`, the entry MUST also expose `progress` (0-100), `current_step`, and `updated_at`. Directories under the configured output root that do not contain a `progress.json` MUST be silently skipped.

The endpoint MUST NOT include any file content beyond the summary fields above.

#### Scenario: List returns tasks sorted by updated_at desc
- **WHEN** the configured output root contains tasks A, B, C with `updated_at` values such that B is the most recent
- **THEN** the response array's first element is B and every entry has at least `task_id` and `status`

#### Scenario: List skips directories without progress.json
- **WHEN** the configured output root contains a subdirectory `bench-full/` that has no `progress.json`
- **THEN** the response array does not contain an entry for `bench-full`

#### Scenario: List is bounded
- **WHEN** the configured output root contains N task directories
- **THEN** the response contains exactly N entries (no duplicates, no extras)

### Requirement: Task Detail Read Endpoints
The system MUST provide four `GET /api/source/task/{task_id}/*` endpoints, each returning one artifact for the given task. The endpoints MUST be:

- `GET /api/source/task/{task_id}/progress` → the parsed `progress.json` content as a JSON object, or `null` if the file is missing.
- `GET /api/source/task/{task_id}/evidence-pack` → `{ "content": string | null }` where `content` is the full text of `evidence-pack.md`, or `null` if the file is missing.
- `GET /api/source/task/{task_id}/key-logs` → `{ "content": string | null }` where `content` is the full text of `key-logs.txt`, or `null` if the file is missing.
- `GET /api/source/task/{task_id}/case-draft` → `{ "content": string | null }` where `content` is the full text of `case-draft.md`, or `null` if the file is missing.

The endpoints MUST reject any `task_id` that does not match `[A-Za-z0-9_-]+` with `HTTP 400`. The endpoints MUST NOT read any file outside the configured output root.

#### Scenario: Valid task_id returns the artifact
- **WHEN** the operator requests `/api/source/task/{valid_id}/progress` and `data/output/{valid_id}/progress.json` exists
- **THEN** the response is `200` with the parsed JSON object

#### Scenario: Missing artifact returns null
- **WHEN** the operator requests `/api/source/task/{valid_id}/evidence-pack` and `data/output/{valid_id}/evidence-pack.md` does not exist
- **THEN** the response is `200` with `{ "content": null }`

#### Scenario: Invalid task_id is rejected
- **WHEN** the operator requests `/api/source/task/..%2Fetc/progress`
- **THEN** the response is `400` (or `404` from the framework) with a clear error message and no filesystem read occurs

### Requirement: Task Reader Service
The system MUST provide a Python module `diagnose_tool/analyzer/task_reader.py` that exposes `list_tasks()`, `read_progress(task_id)`, `read_evidence_pack(task_id)`, `read_key_logs(task_id)`, and `read_case_draft(task_id)`. Each function MUST validate `task_id` against the regex `[A-Za-z0-9_-]+` and raise `ValueError` for any other input.

The service is the only module in the project that constructs `data/output/{task_id}/...` paths for the read side. The five routes call this service.

#### Scenario: Validator accepts safe task_ids
- **WHEN** the validator is called with `task_id = "cluster-20260523-215842-038e9b"`
- **THEN** it returns the same string without raising

#### Scenario: Validator rejects path traversal
- **WHEN** the validator is called with `task_id = ".."`
- **THEN** it raises `ValueError`

### Requirement: Historical Task Table
`AnalysisTasksPage` MUST render a historical task table. The table MUST list every entry returned by `GET /api/source/tasks`, with at least these columns: `task_id`, `status`, `progress`, `current_step`, and `updated_at`. Row click MUST navigate to `/analysis/{task_id}`. The table MUST render an empty state when the list endpoint returns an empty array, and an error state with a "Retry" button when the call fails.

#### Scenario: Empty list shows empty state
- **WHEN** the list endpoint returns an empty array
- **THEN** the table renders an empty-state message instead of rows

#### Scenario: Row click navigates to the detail page
- **WHEN** the user clicks a row whose `task_id` is `abc-123`
- **THEN** the router navigates to `/analysis/abc-123`

### Requirement: Task Detail Page Sections
`TaskDetailPage` MUST render four sections, organized as Ant Design Tabs:

1. **Overview** — status tag, source path, `updated_at` timestamp, progress (0-100), `current_step`, and failure message when present.
2. **Evidence & Threads** — `evidence-pack.md` rendered (Markdown if `react-markdown` is available, otherwise `<pre>`); a `ThreadResultsPanel` with add-one / add-all / dedupe / remove behavior.
3. **Key Logs & Case Draft** — `key-logs.txt` rendered as a `<pre>` block with a single "Add all to evidence basket" button; `case-draft.md` rendered (Markdown or `<pre>`).
4. **Actions** — four buttons: "Start diagnosis" (navigates to `DiagnosisStudioPage` with the task preselected), "Export workspace" (uses the existing `exportWorkspace` flow), "Re-run scan" (navigates back to `AnalysisTasksPage`), and "Delete" (confirm modal then `deleteTempDir`).

The page MUST load the four backend resources in parallel.

#### Scenario: Overview renders status and timestamps
- **WHEN** `progress.json` contains `status: "done"`, `progress: 100`, `current_step: "分析完成"`, and `updated_at: "2026-06-01T10:05:30Z"`
- **THEN** the Overview tab shows the "done" tag, the progress bar at 100%, the `current_step` text, and the `updated_at` timestamp

#### Scenario: Evidence section renders evidence-pack.md
- **WHEN** `evidence-pack.md` exists and is non-empty
- **THEN** the Evidence & Threads tab shows the rendered content (or `<pre>` fallback) and a `ThreadResultsPanel` below

#### Scenario: Missing evidence-pack shows not-produced state
- **WHEN** `evidence-pack.md` is missing
- **THEN** the Evidence & Threads tab shows a not-produced message and still renders the `ThreadResultsPanel`

#### Scenario: Missing key-logs shows empty state
- **WHEN** `key-logs.txt` is missing
- **THEN** the Key Logs section renders "No key logs in this task"

### Requirement: Reusable Thread Results Panel
The system MUST provide a `frontend/src/components/ThreadResultsPanel.tsx` component that renders the thread results for a given `taskId` and supports add-one, add-all, dedupe, remove, and empty-state behaviors. The component MUST consume `useDiagnosis` for basket state. Both `AnalysisTasksPage` and `TaskDetailPage` MUST use this component instead of duplicating the rendering.

#### Scenario: Add all dedupes against existing selections
- **WHEN** the basket already contains one thread and the user clicks "Add all"
- **THEN** the basket ends with all unique threads (no duplicates)

#### Scenario: Empty thread results show empty state
- **WHEN** the thread results endpoint returns `threads: []`
- **THEN** the component renders a not-found message and disables the "Add all" button

### Requirement: Frontend API Client
The system MUST provide `frontend/src/api/taskApi.ts` exporting `getTasks()`, `getTaskProgress(taskId)`, `getTaskEvidencePack(taskId)`, `getTaskKeyLogs(taskId)`, and `getTaskCaseDraft(taskId)`.

### Requirement: i18n Keys
The system MUST add i18n keys for the historical task table and the detail page. The detail page and table MUST NOT contain hard-coded English strings in JSX.

#### Scenario: New keys are present in the i18n bundle
- **WHEN** a reviewer searches the i18n resource files for `taskDetail.overview.status` and `analysisTasks.taskTable.empty`
- **THEN** both keys exist with English and Chinese values

### Requirement: Backend And Frontend Tests
The system MUST provide regression tests covering the new backend service, the new routes, the new components, and the new detail page. The tests MUST pass under `uv run pytest` and `npm test` respectively.

#### Scenario: All acceptance tests pass
- **WHEN** the test suite is run with the new tests included
- **THEN** every test passes
