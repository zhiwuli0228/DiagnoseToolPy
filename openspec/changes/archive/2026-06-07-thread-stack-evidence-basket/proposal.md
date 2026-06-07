## Why

The thread stack parser already exists and has been validated, but its output is not yet part of the shared diagnosis evidence flow. Today, a user who wants to use a JVM thread dump in diagnosis has no first-class way to select parsed thread blocks and pass them into the existing preview, diagnosis, and workspace export paths. That forces manual copying and makes the parser less useful than the rest of the evidence basket system.

## What Changes

**Thread stack evidence selection**
- From: thread stack parsing exists as a standalone capability, but parsed thread blocks are not selectable as diagnosis evidence.
- To: parsed thread blocks from an analysis task can be added to the existing evidence basket, either individually or in bulk.
- Reason: users need a direct path from parsed thread evidence to diagnosis.
- Impact: non-breaking, but it adds a new evidence type to the diagnosis payload.

**Task-scoped thread evidence artifacts**
- From: no dedicated thread evidence artifact is available for the frontend to render and for the exporter to resolve.
- To: thread stack results are stored as rebuildable task artifacts under `data/output/{task_id}/artifacts/`.
- Reason: the frontend needs a durable, file-backed source of truth.
- Impact: non-breaking storage extension.

**Diagnosis and export handoff**
- From: diagnosis preview and workspace export only know about log, group, and cluster selections.
- To: these flows also resolve thread evidence selections and include them in the generated prompt/workspace.
- Reason: selected thread evidence must reach the downstream diagnosis step.
- Impact: non-breaking API payload extension.

## Capabilities

### New Capabilities
- `thread-stack-evidence`: selectable thread stack results, add-one/add-all actions, and downstream diagnosis/export handoff for thread evidence.

### Modified Capabilities
- None

## Affected Modules

- `analyzer`
- `api`
- `exporter`
- `docs`
- Frontend pages and components in `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/context/`, and `frontend/src/types/`

## Storage Impact

- New rebuildable task artifacts are expected for thread stack results, including `data/output/{task_id}/artifacts/thread-stack-results.jsonl` and `data/output/{task_id}/thread-stack-summary.md`.
- Existing analysis task outputs remain in place and continue to be rebuildable from source logs.
- No durable case storage changes are required.

## Constraints

- No mandatory database is introduced.
- No full log file is loaded into memory.
- No browser-first large log upload flow is added.
- File-based source of truth remains unchanged.

## Risks

- Thread evidence references can become unstable if they are generated from non-deterministic ordering.
- Large thread dumps can create sizable result sets, so the UI needs pagination or lazy rendering.
- Export resolution can fail if thread refs are forged or if a task artifact is missing.

## Verification

- Analyzer tests should verify artifact generation and parsing status handling.
- API tests should verify task result loading and reference validation.
- Frontend tests should verify add-one, add-all, remove, and empty-state behavior.
- Exporter tests should verify selected thread evidence appears in generated prompts and workspaces.

## Impact

- `analyzer`: write and summarize thread-stack result artifacts from parsed output.
- `api`: expose thread-stack results for task-scoped rendering and accept thread evidence selections.
- `exporter`: resolve thread evidence references into evidence markdown and workspace prompts.
- `docs`: update the storage contract and current-state snapshot after implementation.
- Frontend files expected to change include `frontend/src/pages/AnalysisTasksPage.tsx`, `frontend/src/components/EvidenceBasket.tsx`, `frontend/src/context/DiagnosisContext.tsx`, and `frontend/src/types/api.ts`.

## Storage Impact

- New rebuildable task artifacts are expected under `data/output/{task_id}/artifacts/`, including thread-stack result data and a human-readable summary.
- No durable database is introduced.
- Existing case storage, retrieval storage, and log-analysis outputs remain unchanged.

## Constraints

- No mandatory database is introduced.
- No full log file is loaded into memory.
- No browser-first large-log upload flow is added.
- File-based source of truth remains unchanged.

## Risks

- Thread refs can become unstable if they are derived from non-deterministic ordering.
- Large dumps can create large result sets, so the UI needs pagination or lazy rendering.
- Exporters can fail if thread refs are forged or reference missing artifacts.
- If the backend resolver ignores thread evidence, the UI will appear to work but the prompt will be incomplete.

## Verification

- Parse and selection tests should pass for thread evidence and existing log/group/cluster evidence.
- Frontend tests should cover add-one, add-all, remove, and empty-state behavior.
- Export/prompt tests should confirm thread evidence is present in generated output.
- The current-state snapshot should be updated after implementation.
