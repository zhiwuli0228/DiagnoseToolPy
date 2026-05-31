# Bugfix Prompt Export Design

## 1. Overview

The bugfix prompt export feature generates a deterministic markdown prompt that converts an analysis task into an implementation-oriented brief. The prompt is intended for Claude Code or OpenCode and is derived from already-produced task artifacts rather than from raw log files or a new LLM call.

The export is additive. It does not change current diagnosis, evidence, or casebase flows.

## 2. Data Flow

1. User completes analysis or diagnosis for a task.
2. The API reads existing task output artifacts such as `evidence-pack.md`, `case-draft.md`, and `retrieval-query.json`.
3. A bugfix prompt builder composes a markdown prompt with:
   - task metadata
   - observed evidence summary
   - diagnosis disclaimer or confirmation state
   - implementation guardrails
   - suggested fix plan
   - regression test reminders
   - human confirmation questions
4. The exporter writes `data/output/{task_id}/bugfix-prompt.md` atomically.
5. The API returns the prompt text and file path so the frontend can preview or copy it.

## 3. Module Responsibilities

### exporter

- Build bugfix prompt markdown from task output artifacts.
- Write `bugfix-prompt.md` atomically.
- Keep the logic independent from FastAPI.

### api

- Validate the request.
- Load the exporter and return a safe response.
- Map missing task artifacts to clean 404 or 400 responses.

### frontend

- Add a user action to generate or preview the bugfix prompt.
- Offer copy/open/download behavior without exposing raw internals.

### docs

- Document the new artifact, endpoint, and user workflow.
- Update `docs/00-project/current-state.md` when the feature is implemented.

## 4. File Outputs

- `data/output/{task_id}/bugfix-prompt.md`

Required content sections:

- Task metadata
- Problem summary
- Evidence summary
- Diagnosis or hypothesis state
- Fix constraints
- Suggested implementation plan
- Regression tests
- Human confirmation questions

Overwrite behavior:

- Regeneration overwrites the existing `bugfix-prompt.md` deterministically.

Partial failure behavior:

- If prompt generation fails after file creation starts, the exporter must roll back the created file and leave the task output unchanged.

## 5. Error Handling

- Missing task output directory: return not found and do not write files.
- Missing required evidence artifacts: return a clear error and do not write files.
- Invalid task id or unreadable content: return a safe error message.
- File write failure: roll back and report failure.

## 6. Security Considerations

- Do not include API keys, tokens, or secret file paths in the prompt.
- Do not claim the AI diagnosis is confirmed root cause unless human-confirmed data exists.
- Mark historical references as references only.
- Keep the prompt useful for implementation without allowing it to bypass human review.

## 7. Memory Behavior

- Reuse existing output markdown files.
- Do not load raw log files.
- Do not buffer large log content in memory.
- Keep the prompt builder bounded to the existing evidence pack and related task artifacts.

## 8. Tests

- Unit test the prompt builder content and overwrite behavior.
- Unit test missing artifact handling.
- Integration test the API endpoint.
- Frontend test the prompt export entry point and copy flow.
- Verify current-state and docs updates after implementation.

## 9. Compatibility

- Existing diagnosis, evidence export, and casebase flows remain unchanged.
- The feature is additive and can be ignored by users who do not need it.
- Future agents can extend the same pattern to test suggestion export and monitoring suggestion export without changing the storage contract again.

