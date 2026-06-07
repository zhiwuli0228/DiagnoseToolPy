## 1. Thread Artifact and Resolver

- [x] 1.1 Define the thread evidence artifact schema and stable `thread_ref` contract
  - Files: `diagnose_tool/analyzer/*` and `docs/01-architecture/storage-contract.md`
  - Behavior: persist parsed thread blocks as rebuildable task artifacts and define how a thread is referenced later
  - Tests: artifact schema round-trip and stable reference generation tests
  - Verification: `uv run pytest` for analyzer tests covering thread artifact output
- [x] 1.2 Add backend resolution for thread evidence references
  - Files: `diagnose_tool/exporter/workspace_exporter.py`, `diagnose_tool/api/routes_diagnosis.py`
  - Behavior: resolve `thread_ref` into thread evidence during preview, diagnosis, and export
  - Tests: valid ref, missing ref, forged ref, empty artifact
  - Verification: `uv run pytest` for exporter and diagnosis route tests

## 2. API And Frontend Selection UI

- [x] 2.1 Expose thread result metadata to the frontend
  - Files: `diagnose_tool/api/*`, `frontend/src/api/*`, `frontend/src/types/api.ts`
  - Behavior: return task-scoped thread metadata for rendering and selection without loading raw dumps into the browser
  - Tests: route success, missing task, malformed artifact
  - Verification: API tests plus frontend API contract tests
- [x] 2.2 Render thread results in the analysis task view
  - Files: `frontend/src/pages/AnalysisTasksPage.tsx`, `frontend/src/components/*`
  - Behavior: show thread rows, parse status, and add-one/add-all actions
  - Tests: add one, add all, dedupe, empty state, disabled state
  - Verification: `uv run` frontend unit tests for the new thread panel

## 3. Evidence Basket Integration

- [x] 3.1 Extend the evidence basket selection model for thread evidence
  - Files: `frontend/src/context/DiagnosisContext.tsx`, `frontend/src/components/EvidenceBasket.tsx`, `frontend/src/components/AIDiagnosisButton.tsx`, `frontend/src/types/api.ts`
  - Behavior: render thread evidence labels, preserve removal/clear behavior, and pass selections through existing diagnosis flows
  - Tests: label rendering, dedupe, remove, clear, and mixed evidence selection
  - Verification: frontend component tests for diagnosis basket behavior
- [x] 3.2 Carry thread evidence through preview and workspace export
  - Files: `frontend/src/pages/DiagnosisStudioPage.tsx`, `frontend/src/pages/AnalysisTasksPage.tsx`, `diagnose_tool/exporter/workspace_exporter.py`
  - Behavior: include thread evidence in prompt preview, diagnosis, and exported workspace output
  - Tests: prompt content contains selected thread evidence; export contains selected thread evidence
  - Verification: end-to-end smoke test with one selected thread and one selected log item

## 4. Documentation And Regression Coverage

- [x] 4.1 Add regression tests for thread evidence and existing evidence types
  - Files: `tests/*`, `frontend/src/**/__tests__/*`
  - Behavior: verify thread evidence works without breaking log/group/cluster evidence
  - Tests: analyzer, API, exporter, and frontend regression suites
  - Verification: `uv run pytest` and frontend unit test run
- [x] 4.2 Update durable docs and project continuity notes
  - Files: `docs/00-project/current-state.md`, `docs/01-architecture/storage-contract.md`, relevant OpenSpec artifacts
  - Behavior: document the new thread evidence artifacts and the updated diagnosis flow
  - Tests: documentation review only
  - Verification: manual review of updated docs and OpenSpec status
