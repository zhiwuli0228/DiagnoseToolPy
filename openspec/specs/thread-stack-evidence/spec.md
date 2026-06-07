# Thread Stack Evidence

## Purpose

Make parsed thread stack results first-class diagnosis evidence: persist them as rebuildable task artifacts, expose a read-only task result API for the frontend, and carry selected thread evidence through diagnosis preview, preliminary diagnosis, and workspace export using the existing selection-based flow.

## Requirements

### Requirement: Thread Evidence Artifacts
The system MUST persist parsed thread dump results for each analysis task as rebuildable files under `data/output/{task_id}/artifacts/` so that the frontend and exporter can reload thread evidence without rerunning the parser.

The thread evidence artifacts MUST include a machine-readable result file named `thread-stack-results.jsonl` under `data/output/{task_id}/artifacts/` and a human-readable summary file named `thread-stack-summary.md` under `data/output/{task_id}/`. Re-running the same task MAY overwrite these files, and the files MUST be considered rebuildable rather than durable truth.

#### Scenario: Thread results are available after analysis
- **WHEN** an analysis task produces parsed thread dump blocks
- **THEN** the task output directory contains thread evidence artifacts that can be reloaded later

#### Scenario: Missing thread artifact does not break diagnosis
- **WHEN** a completed task has no thread evidence artifact
- **THEN** the rest of the diagnosis workflow still works and the thread panel shows an empty state

### Requirement: Thread Evidence Selection
The system MUST allow a user to add one parsed thread block or all parsed thread blocks from a task result into the diagnosis evidence basket.

The selection model MUST preserve thread identity with a stable `thread_ref` and MUST NOT require the browser to store raw thread dump text as the selection source of truth.

#### Scenario: Add one parsed thread
- **WHEN** the user selects a single parsed thread block in the thread result view
- **THEN** the thread is added to the evidence basket as a thread evidence item

#### Scenario: Add all parsed threads
- **WHEN** the user chooses the add-all action for a task that contains parsed thread blocks
- **THEN** every parsed thread block is added to the evidence basket exactly once

#### Scenario: Duplicate selections are prevented
- **WHEN** the user adds the same thread evidence item more than once
- **THEN** the evidence basket keeps only one selection for that thread

### Requirement: Thread Evidence Uses The Existing Diagnosis Flow
The system MUST carry selected thread evidence through diagnosis preview, preliminary diagnosis, and workspace export using the existing selection-based flow.

Thread evidence MUST appear in the generated prompt or exported workspace content when it is selected, and invalid thread references MUST fail with a clear error instead of being silently dropped.

#### Scenario: Preview prompt includes thread evidence
- **WHEN** the user previews the diagnosis prompt with thread evidence selected
- **THEN** the generated prompt includes the selected thread evidence

#### Scenario: Export workspace includes thread evidence
- **WHEN** the user exports a diagnosis workspace with thread evidence selected
- **THEN** the exported workspace includes the selected thread evidence content

#### Scenario: Forged thread reference is rejected
- **WHEN** a request contains a thread reference that does not exist in the task artifact
- **THEN** the server rejects the request with a clear client error

### Requirement: Thread Evidence Preserves Parse Status And Safe Failure Modes
The system MUST preserve the parse status and source metadata for each thread evidence item, including FULL, PARTIAL, and RAW states when they exist in the parser output.

Malformed artifact entries or partial parser failures MUST NOT crash the UI or the backend; the system SHOULD skip invalid entries or surface them as unavailable while keeping other valid thread evidence usable.

#### Scenario: Partial thread remains selectable
- **WHEN** the parser produces a PARTIAL thread result with usable metadata
- **THEN** the UI shows the thread and allows it to be selected as evidence

#### Scenario: Malformed entry is isolated
- **WHEN** one entry in the thread artifact is malformed
- **THEN** the UI still renders the remaining valid thread entries

#### Scenario: Empty thread result is safe
- **WHEN** a task produces no parsed thread blocks
- **THEN** the thread evidence view shows an empty state and does not block other diagnosis actions
