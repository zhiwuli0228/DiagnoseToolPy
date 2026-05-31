# Bugfix Prompt Export Tasks

- [x] Implement the bugfix prompt exporter
  - Files: `diagnose_tool/exporter/bugfix_prompt_exporter.py`, `tests/test_bugfix_prompt_exporter.py`
  - Behavior: build `bugfix-prompt.md` from task output artifacts and write it atomically
  - Tests: success path, missing artifact path, overwrite path
  - Verification: `uv run pytest tests/test_bugfix_prompt_exporter.py`

- [x] Add the bugfix prompt export API
  - Files: `diagnose_tool/api/routes_diagnosis.py`, `tests/test_diagnosis_api.py`
  - Behavior: expose an endpoint that generates the prompt and returns a safe response
  - Tests: valid task, missing task, unreadable artifact, safe error handling
  - Verification: `uv run pytest tests/test_diagnosis_api.py`

- [x] Add frontend entry points for bugfix prompt export
  - Files: `frontend/src/pages/DiagnosisStudioPage.tsx`, `frontend/src/api/diagnosisApi.ts`, `frontend/src/pages/AnalysisTasksPage.tsx`, related frontend tests
  - Behavior: let the user generate or preview the bugfix prompt from the diagnosis workflow
  - Tests: button/action visibility, success modal, copy/preview behavior, error state
  - Verification: `npm test` for the affected frontend suite

- [x] Update docs and project continuity snapshot
  - Files: `docs/04-development/api-documentation.md`, `docs/05-domain/workspace-export-guide.md`, `docs/00-project/current-state.md`
  - Behavior: document the new artifact, endpoint, and workflow; mark the capability as implemented
  - Tests: manual documentation review
  - Verification: docs reviewed and current-state updated
