# Thread Stack Evidence Basket Implementation Plan

> **For agentic workers:** Use `superpowers:subagent-driven-development`
> to implement this plan task-by-task.

**Goal:** Make parsed thread stack results selectable as diagnosis evidence and carry them through the existing preview, diagnosis, and workspace export flow.

**Architecture:** Keep thread evidence file-backed and task-scoped under `data/output/{task_id}/artifacts/`. Extend the shared selection model so thread items can join the existing evidence basket without creating a separate diagnosis pipeline. The backend resolves opaque thread references at request time, and the frontend only renders metadata plus selection controls.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, React, TypeScript, pytest, Vite, Ant Design.

---

## Task 1: Thread artifact and resolver

- [ ] **Step 1:** Read `openspec/changes/thread-stack-evidence-basket/design.md`, `proposal.md`, `specs/thread-stack-evidence/spec.md`, and `tasks.md` to confirm the thread evidence contract and failure cases.
- [ ] **Step 2:** Inspect `diagnose_tool/analyzer/thread_stack_parser.py`, `diagnose_tool/analyzer/output_context.py`, `diagnose_tool/api/routes_diagnosis.py`, and `diagnose_tool/exporter/workspace_exporter.py` to identify the smallest place to persist and resolve thread evidence.
- [ ] **Step 3:** Add or adjust tests first for thread evidence artifact shape, stable `thread_ref` generation, missing artifact handling, and forged reference rejection.
- [ ] **Step 4:** Implement the artifact writer and resolver logic, keeping the output rebuildable and file-backed.
- [ ] **Step 5:** Run the targeted backend tests and confirm the new artifact files can be read back without loading unrelated task data.

**Validation checkpoint:** `uv run pytest` on the new analyzer, API, and exporter tests for thread evidence.

**Commit point:** Commit once thread artifacts can be generated and resolved end-to-end by the backend.

## Task 2: API and frontend selection UI

- [ ] **Step 1:** Inspect `frontend/src/pages/AnalysisTasksPage.tsx`, `frontend/src/types/api.ts`, and the relevant API wrapper files to map the current analysis-task and selection flow.
- [ ] **Step 2:** Add contract tests for the new thread result metadata response and the corresponding frontend types before changing UI code.
- [ ] **Step 3:** Implement the thread result metadata endpoint or extend the current analysis-task response so the frontend can render parsed thread rows without pulling raw dumps into browser state.
- [ ] **Step 4:** Add a thread results panel to `AnalysisTasksPage.tsx` with row-level add-one controls, an add-all action, parse status display, and an empty state.
- [ ] **Step 5:** Verify the panel works with a completed task, a task with partial thread results, and a task with no parsed thread evidence.

**Validation checkpoint:** Frontend unit tests for the thread panel and API contract tests pass.

**Commit point:** Commit once the UI can display thread evidence and add it to the shared selection state.

## Task 3: Evidence basket integration

- [ ] **Step 1:** Update `frontend/src/context/DiagnosisContext.tsx`, `frontend/src/components/EvidenceBasket.tsx`, `frontend/src/components/AIDiagnosisButton.tsx`, and `frontend/src/types/api.ts` to recognize the new thread evidence type.
- [ ] **Step 2:** Add tests for label rendering, deduplication, removal, clear behavior, and mixed evidence sets containing logs, clusters, and threads.
- [ ] **Step 3:** Extend the preview and export request paths in `frontend/src/pages/DiagnosisStudioPage.tsx` and `frontend/src/pages/AnalysisTasksPage.tsx` so thread selections are forwarded with the existing evidence payload.
- [ ] **Step 4:** Update `diagnose_tool/exporter/workspace_exporter.py` so thread references resolve into prompt and workspace content alongside existing evidence types.
- [ ] **Step 5:** Verify the generated prompt and workspace artifacts contain the selected thread evidence and that invalid references fail clearly.

**Validation checkpoint:** Mixed-evidence smoke test passes for preview, diagnosis, and workspace export.

**Commit point:** Commit once thread evidence survives the full selection-to-export pipeline.

## Task 4: Documentation and regression coverage

- [ ] **Step 1:** Add regression tests that prove thread evidence does not break log, group, or cluster evidence behavior.
- [ ] **Step 2:** Update `docs/01-architecture/storage-contract.md` with the new thread evidence artifact paths and rebuild behavior.
- [ ] **Step 3:** Update `docs/00-project/current-state.md` after implementation so the continuity snapshot reflects the new capability.
- [ ] **Step 4:** Review the final OpenSpec artifacts for consistency with the implemented behavior and recorded storage contract.
- [ ] **Step 5:** Run the full targeted test set and capture any non-blocking gaps that remain for follow-up.

**Validation checkpoint:** Backend tests, frontend tests, and documentation updates are all complete.

**Commit point:** Commit once the change is fully verified and the durable docs are synchronized.
