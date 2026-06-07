## Context

`frontend/src/pages/AnalysisTasksPage.tsx` has grown to 1,302 lines and is the god component for the entire "log analysis" flow: source check, scan, search, cluster, thread results, diagnosis drawer, workspace export, preview prompt, bugfix prompt. The companion detail page `frontend/src/pages/TaskDetailPage.tsx` is a 26-line stub that renders an "Under Development" placeholder.

`current-state.md` lists "Complete log analysis UI" as a Known Gap. The user-facing pain is: after a scan or cluster finishes, the user has no first-class place to (1) review the task's overview, (2) inspect its evidence pack and thread stack results, (3) see key logs and the case draft, and (4) take the next action (start diagnosis, export, re-run, delete). All of this currently lives in modal/tab chaos on `AnalysisTasksPage`.

This change introduces a real drill-down: a historical task table on `AnalysisTasksPage` whose rows navigate to a fully-implemented `TaskDetailPage` with four sections, plus the minimal backend read endpoints needed to feed it.

## Goals

- A historical task list table on `AnalysisTasksPage` that lists all known analysis tasks with task_id, source path, status, started timestamp, and processed/total bytes. Row click navigates to `/analysis/{task_id}`.
- A real `TaskDetailPage` with four sections, rendered as Ant Design Tabs (or a single column for very small screens):
  1. **Overview** — status tag, source path, started/finished timestamps, runtime, processed/total bytes, current file, failure message if any.
  2. **Evidence & Threads** — `evidence-pack.md` rendered as Markdown; a thread results panel extracted from `AnalysisTasksPage` with add-one / add-all / dedupe / remove / empty-state.
  3. **Key Logs & Case Draft** — key logs list (each row has an "add to evidence basket" button); `case-draft.md` rendered as Markdown.
  4. **Actions** — Start diagnosis (navigates to `DiagnosisStudioPage` with the task preselected), Export workspace (reuses the existing `exportWorkspace` flow), Re-run scan (refills the path and starts a new scan), Delete (confirms then calls `deleteTempDir`).
- Five new read-only backend endpoints under `diagnose_tool/api/routes_source.py` to serve the data the detail page needs.
- A thin `diagnose_tool/analyzer/task_reader.py` service that does path validation and file IO in one place, called by all five routes.
- A reusable `frontend/src/components/ThreadResultsPanel.tsx` extracted from `AnalysisTasksPage`.
- New frontend API client `frontend/src/api/taskApi.ts`.
- i18n keys for the new UI.
- Backend tests (`tests/test_task_reader.py`, `tests/test_task_routes.py`) and frontend tests for the new components and the detail page.
- Playwright E2E verification per CLAUDE.md's Frontend E2E Verification Rule.

## Non-Goals

- Do not refactor the rest of `AnalysisTasksPage.tsx`. The 1,302 lines outside of the new "historical task table" addition stay as-is. A future change can split it; that is out of scope here.
- Do not add real-time progress polling to `TaskDetailPage`. The detail page loads each section once on mount; if a future change wants polling, that is separate.
- Do not change the existing `routes_source.py` write-side endpoints (`check`, `scan`, `search`, `upload`, `delete_temp`).
- Do not change `diagnose_tool/analyzer/thread_stack_parser.py` or `thread_artifact.py`.
- Do not add a "rename task" or "duplicate task" feature.
- Do not add a new dependency. If `react-markdown` is not already a dependency, fall back to rendering markdown as `<pre>` text.
- Do not change the storage contract on disk. The new endpoints are read-only over the existing `data/output/{task_id}/` layout.
- Do not introduce a new database, cache, or index.

## Approach Selection

Three approaches were considered for the backend side:

- **A. Pure routes (minimum)** — five new routes directly read files from `data/output/`. Easiest to write, but path validation and error handling get duplicated, and the routes become a thin shell over filesystem paths.
- **A+. Routes + thin service (chosen)** — five new routes call a small `task_reader.py` service that owns path validation, file existence checks, and typed returns. The routes stay thin (matching CLAUDE.md's "thin API" rule); the service is unit-testable in isolation.
- **C. Aggregate endpoint** — one new `GET /api/source/task/{id}/summary` returns all four sections. Fewer requests, but the response body is large and changes to the sections require backend changes. The user's explicit choice in the brainstorm was "multiple read endpoints" for this reason.

The chosen approach is A+: minimal new abstractions, but the abstraction that does exist is at the right layer (the analyzer service module, not the routes). The frontend makes five concurrent reads on detail-page mount via `Promise.all`; the latency is dominated by the largest response (`evidence-pack.md`), which is already what the current `AnalysisTasksPage` loads.

## Key Design Decisions

1. **Path validation is centralized in `task_reader.py`.** A regex like `re.fullmatch(r"[A-Za-z0-9_-]+", task_id)` rejects `..`, `/`, and any other traversal vectors. The routes forward the same error to the client as `HTTPException(400)` with a clear message. Tests cover this directly.

2. **Missing artifacts return None, not 404, where the file is optional for the page.** A task may not have `key-logs.json` if the analyzer did not produce one. The service returns `None` in that case; the route returns `200` with an empty list, and the frontend renders an empty state. `progress.json` is the only file that is required for the task to be in the list at all (the list endpoint filters out directories with no `progress.json`).

3. **The list endpoint reads only `task.yaml` and `progress.json` per task.** This is bounded IO: two small files per task, no full artifact scan. If the directory has neither, it is silently skipped (defensive against the `data/output/` directory containing unrelated subfolders like `bench-full/` or `bench-single/` that we saw at the time of writing).

4. **`ThreadResultsPanel` is extracted, not duplicated.** The existing thread results rendering in `AnalysisTasksPage` is moved verbatim into `frontend/src/components/ThreadResultsPanel.tsx` with a small prop surface (`taskId`, `onAddToBasket` callback). The detail page passes its own `DiagnosisContext` updater; `AnalysisTasksPage` does the same. No copy-paste.

5. **Actions reuse existing flows.** Start diagnosis reuses the existing `previewPrompt` + `DiagnosisStudio` route. Export workspace reuses `exportWorkspace`. Delete reuses `deleteTempDir`. The detail page does not introduce new backend actions; it composes the existing ones. This keeps the change small and reuses tested code paths.

6. **The 1,302-line `AnalysisTasksPage.tsx` gets a minimal slice, not a refactor.** A new `TaskHistoryTable` subcomponent is added at the bottom of the existing page. The existing top-of-page scan/search/cluster section is untouched.

7. **No real-time polling.** The detail page is a snapshot view. If the user wants live updates, they refresh or click "Re-run".

## Open Questions

- Should the historical task table support filtering (by status, by source path) on `AnalysisTasksPage`? Deferred — a basic table is the minimum. A future change can add a filter row.
- Should `TaskDetailPage` deep-link to a specific section via URL hash (`/analysis/{id}#threads`)? Deferred — the Tab default selection is good enough; deep-linking is a separate change.
- Should we render `summary.html` somewhere? Deferred — `evidence-pack.md` is the source of truth for the page; `summary.html` is a separate render target.
