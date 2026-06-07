## Why

`diagnose_tool/analyzer/diagnosis.py` already produces a per-task AI diagnosis written to `data/cases/{task_id}/ai-diagnosis.md`. `current-state.md` lists "Implement test suggestion generation (V0.4 extended)" as a Known Gap. The on-call engineer needs a small, executable set of verification / reproduction scenarios that map the diagnosis text into `curl` / shell / Python / JUnit snippets they can paste into a terminal or a test file.

Today, after a diagnosis lands, the engineer has to read the diagnosis prose and write the test cases by hand. That is error-prone and slow, and it is the missing link between "AI says X is the cause" and "I have a script that proves X is the cause". The new capability closes this gap with a thin, independent `TestSuggester` that consumes the existing diagnosis and emits a Markdown file with executable suggestions.

## What Changes

**Independent `TestSuggester` module**
- From: no automated test suggestion; the engineer writes snippets by hand.
- To: `diagnose_tool/analyzer/test_suggester.py` reads the existing diagnosis and evidence pack, calls the LLM with a focused prompt, and returns a Markdown file with reproduction / verification / negative test cases.
- Reason: a thin, independent module is the smallest change that adds a durable, regenerable artifact.
- Impact: non-breaking addition; the existing diagnosis flow stays unchanged.

**Version-tracked prompt template**
- From: no template; the LLM is asked ad-hoc.
- To: `docs/05-domain/test-suggestion-template.md` carries the prompt with `{diagnosis}` and `{evidence_pack}` placeholders; an in-module fallback when the file is absent.
- Reason: a version-tracked template is maintainable; the fallback keeps the suggester working even in minimal deployments.
- Impact: new tracked file.

**New `POST /api/diagnosis/test-suggestions` endpoint**
- From: no API to request test suggestions.
- To: a thin route that wraps `TestSuggester.run_and_save(task_id)` and returns `{ content, path }`.
- Reason: a manual endpoint is needed for tasks diagnosed before this change shipped and for re-generation.
- Impact: non-breaking addition.

**Optional auto-generation hook at the end of `DiagnosisOrchestrator.run()`**
- From: no test suggestions are produced automatically.
- To: when `diagnosis.auto_generate_tests: bool` is true (default), `DiagnosisOrchestrator.run()` calls `TestSuggester.run_and_save(task_id)` after writing the diagnosis. A failure is logged and does NOT affect the diagnosis return.
- Reason: most users want the suggestions by default; the failure mode must not regress diagnosis.
- Impact: additive; the existing diagnosis return is unchanged.

**New `GET /api/source/task/{task_id}/test-suggestions` endpoint**
- From: no read endpoint for the new file.
- To: a thin route that returns `{ content: str | null }` for the file (mirrors `evidence-pack` and friends).
- Reason: the new TaskDetailPage Tab needs the data; reusing the existing read pattern keeps the surface uniform.
- Impact: non-breaking addition.

**Frontend fifth Tab and "Generate test suggestions" button**
- From: no place in the UI to see test suggestions.
- To: `TaskDetailPage` adds a fifth Tab "Test Suggestions" with a `TestSuggestionsPanel` that renders parsed `### Test:` cards with one-click Copy. The Actions Tab adds a "Generate test suggestions" button.
- Reason: the file alone is not useful; the UI is the place where the on-call actually pastes the snippets.
- Impact: additive slice of the existing TaskDetailPage.

**i18n, tests, and E2E**
- From: no i18n keys, no regression tests, no browser verification.
- To: i18n keys for the new tab and button; backend tests for the suggester; frontend tests for the panel; Playwright MCP browser verification per CLAUDE.md.
- Reason: keep the project hygiene.
- Impact: additive.

## Capabilities

### New Capabilities
- `test-suggestion-generation`: independent `TestSuggester`, prompt template, two new API endpoints, an auto-generation hook on the diagnosis flow, a fifth Tab on `TaskDetailPage` with copy-to-clipboard, and a manual regenerate button. With regression tests and Playwright MCP browser verification.

### Modified Capabilities
- None. The existing `complete-log-analysis-ui` capability (which provides `TaskDetailPage`) gains one new Tab and one new button; no capability-level behavior change.

## Affected Modules

- `diagnose_tool/analyzer/test_suggester.py` — new module.
- `diagnose_tool/analyzer/diagnosis.py` — single best-effort auto-call at the end of `run()`.
- `diagnose_tool/analyzer/task_reader.py` — `read_test_suggestions` and a constant for the filename.
- `diagnose_tool/api/routes_diagnosis.py` — new `POST /api/diagnosis/test-suggestions` route.
- `diagnose_tool/api/routes_source.py` — new `GET /api/source/task/{task_id}/test-suggestions` route.
- `config/app.yaml` — new `diagnosis.auto_generate_tests` setting.
- `docs/05-domain/test-suggestion-template.md` — new tracked template.
- `tests/test_test_suggester.py` — new tests.
- `frontend/src/api/diagnosisApi.ts` — new client function.
- `frontend/src/api/taskApi.ts` — new client function.
- `frontend/src/components/TestSuggestionsPanel.tsx` — new component.
- `frontend/src/pages/TaskDetailPage.tsx` — fifth Tab and new Actions button.
- `frontend/src/components/__tests__/TestSuggestionsPanel.test.tsx` — new tests.
- `frontend/src/locales/en.json`, `frontend/src/locales/zh.json` — new i18n keys.
- `docs/00-project/current-state.md` — move "Test suggestion generation" from Known Gap to Implemented.

## Storage Impact

- New tracked file: `docs/05-domain/test-suggestion-template.md`.
- New per-run output: `data/output/{task_id}/test-suggestions.md` (rebuildable from the diagnosis and the evidence pack).
- No new durable database, no new index, no new cache.

## Constraints

- No mandatory database.
- No new external dependency.
- The auto-generation hook MUST NOT affect the diagnosis return value or the `ai-diagnosis.md` write.
- The LLM call uses the existing `LLMClient` and configuration.
- The frontend parses the Markdown on the client (no new `react-markdown` dependency, consistent with `complete-log-analysis-ui`).
- All new tracked files use LF line endings and UTF-8.

## Risks

- The LLM might produce non-executable or low-quality suggestions. Mitigation: the output is suggestions only; the on-call reviews before running. The Markdown is structured so that a missing or unparseable suggestion is at least visible.
- The auto-generation hook adds an LLM call to the diagnosis latency. Mitigation: it runs after the diagnosis is written; the diagnosis return is not blocked. If latency is a concern, the setting can be turned off.
- The new file `test-suggestions.md` may not exist for older tasks. Mitigation: the empty state is rendered, and the "Generate test suggestions" button backfills it.

## Verification

- `uv run pytest tests/test_test_suggester.py -q` — new backend tests pass.
- `uv run pytest` — full backend suite still passes.
- `npm test -- --run` — Vitest passes for the new component test; the existing suite still passes.
- Playwright MCP: navigate to a task detail page; the new Tab is visible; clicking it shows the parsed cards (or the empty state). Click "Generate test suggestions" in Actions; the file is regenerated and the Tab is re-rendered.
- Manual: trigger a diagnosis; confirm `data/output/{task_id}/test-suggestions.md` is written and contains three sections (Reproduction, Verification, Negative / Edge).

## Impact

- `diagnose_tool/`: +1 module (`test_suggester.py`); +1 route in `routes_diagnosis.py`; +1 route in `routes_source.py`; +1 best-effort call in `diagnosis.py`; +1 function in `task_reader.py`; +1 setting in `config/app.yaml`.
- `docs/05-domain/`: +1 template file.
- `tests/`: +1 backend test file.
- `frontend/`: +1 component; +1 Tab; +1 button; +1 client function in 2 files; 1 new test file; i18n key additions.
- `docs/00-project/current-state.md`: one line moves from Known Gap to Implemented.
- No casebase, no retrieval, no cluster analyzer, no thread stack changes.
