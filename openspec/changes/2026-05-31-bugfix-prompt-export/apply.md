# Bugfix Prompt Export Apply Receipt

## Authorization

- Change: `2026-05-31-bugfix-prompt-export`
- Authorized by: `21-superspec-final-bugfix-prompt-export-end-to-end-delivery-closure-operation.md`
- Execution mode: controlled implementation within the approved feature scope
- Implementation executor: Codex

## Scope Implemented

- Added `data/output/{task_id}/bugfix-prompt.md` exporter logic.
- Added API endpoint for bugfix prompt export.
- Added frontend entry points and preview/copy flow for bugfix prompt export.
- Added backend and frontend tests for the new workflow.
- Updated project continuity and feature documentation.

## Modified Files

- `diagnose_tool/exporter/bugfix_prompt_exporter.py`
- `diagnose_tool/exporter/__init__.py`
- `diagnose_tool/api/routes_diagnosis.py`
- `frontend/src/api/diagnosisApi.ts`
- `frontend/src/pages/AnalysisTasksPage.tsx`
- `frontend/src/pages/DiagnosisStudioPage.tsx`
- `frontend/src/mocks/handlers.ts`
- `frontend/src/locales/en.json`
- `frontend/src/locales/zh.json`
- `frontend/src/pages/__tests__/AnalysisTasksPage.test.tsx`
- `frontend/src/pages/__tests__/DiagnosisStudioPage.test.tsx`
- `tests/test_bugfix_prompt_exporter.py`
- `tests/test_diagnosis_api.py`
- `openspec/changes/2026-05-31-bugfix-prompt-export/tasks.md`

## Implementation Notes

- The exporter writes `bugfix-prompt.md` atomically under the task output directory.
- The API returns a safe prompt preview plus the output path.
- The UI exposes generation/preview actions without requiring raw log reads in memory.
- The prompt content preserves AI diagnosis as preliminary and highlights human confirmation requirements.
