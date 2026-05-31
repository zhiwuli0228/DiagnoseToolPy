# Bugfix Prompt Export

## Problem

DiagnoseToolPy can already produce evidence packs, diagnosis drafts, and workspace exports, but it does not yet produce a structured bugfix prompt that can be handed directly to Claude Code or OpenCode for implementation. Users must manually reassemble diagnosis output, evidence, and constraints before starting the fix.

## Goal

Provide a deterministic bugfix prompt export that turns an existing analysis task into a ready-to-use implementation brief. The exported prompt should help the implementation agent start from confirmed evidence, known constraints, and regression expectations without inventing new facts.

## Scope

- Generate `bugfix-prompt.md` from existing task output artifacts.
- Add an API path for generating or previewing the bugfix prompt.
- Add a UI action for exporting or copying the bugfix prompt from the diagnosis workflow.
- Document the artifact and update the project continuity snapshot.

## Out of Scope

- Real code implementation of the diagnosed fix.
- Automatic patch generation or autonomous code edits.
- Git worktree creation, merge, push, or PR closeout.
- Retrieval or storage redesign.
- Database introduction or embedding/vector search changes.

## Affected Modules

- exporter
- api
- frontend
- docs

## Storage Impact

- `data/output/{task_id}/bugfix-prompt.md` is a new task output artifact.
- `docs/00-project/current-state.md` must be updated after implementation.
- `docs/04-development/api-documentation.md` and `docs/05-domain/workspace-export-guide.md` should document the new workflow.

## Constraints

- No mandatory database introduced.
- No full log file should be read into memory.
- No browser-first large log upload flow.
- File-system source of truth must remain unchanged.
- The bugfix prompt must treat AI diagnosis as preliminary unless human-confirmed root cause is available.

## Risks

- The prompt may overfit to a preliminary diagnosis and encourage premature implementation.
- Missing task artifacts could cause incomplete prompt generation.
- The new file path could conflict with existing task output naming if overwrite behavior is not defined.
- Frontend affordances could overexpose the feature before the prompt contract is stable.

## Verification

- Unit tests for prompt generation and overwrite behavior.
- API tests for success, missing task artifact, and safe error handling.
- Frontend tests for prompt export entry points.
- Manual review of generated prompt content against the task output.
