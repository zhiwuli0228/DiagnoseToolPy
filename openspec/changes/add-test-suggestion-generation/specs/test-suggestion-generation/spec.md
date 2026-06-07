## ADDED Requirements

### Requirement: Test Suggester Service
The system MUST provide a Python module `diagnose_tool/analyzer/test_suggester.py` exposing `TestSuggester.run(task_id) -> str` and `TestSuggester.run_and_save(task_id) -> str`. The module MUST read `ai-diagnosis.md` from `data/cases/{task_id}/` and `evidence-pack.md` from `data/output/{task_id}/`. It MUST call the LLM with the focused test-suggestion prompt and return the result.

The module MUST raise `DiagnosisNotFoundError` if the diagnosis file is missing and `TaskNotFoundError` if the task output directory is missing. The module MUST be FastAPI-independent and accept an `LLMClient` via the `TestSuggester` constructor.

#### Scenario: Run returns the LLM output for a valid task
- **WHEN** `TestSuggester.run(task_id)` is called and both the diagnosis and evidence pack exist
- **THEN** the return value is the LLM's response (non-empty markdown)

#### Scenario: Missing diagnosis raises DiagnosisNotFoundError
- **WHEN** `TestSuggester.run(task_id)` is called and `data/cases/{task_id}/ai-diagnosis.md` is missing
- **THEN** the call raises `DiagnosisNotFoundError`

#### Scenario: Missing task raises TaskNotFoundError
- **WHEN** `TestSuggester.run(task_id)` is called and `data/output/{task_id}` is missing
- **THEN** the call raises `TaskNotFoundError`

### Requirement: Prompt Template
The system MUST provide a version-tracked prompt template at `docs/05-domain/test-suggestion-template.md`. The template MUST contain two placeholders, `{diagnosis}` and `{evidence_pack}`, and MUST instruct the LLM to produce a Markdown file with three sections (Reproduction, Verification, Negative / Edge) using `### Test:` headings.

When the template file is missing, the module MUST fall back to an in-module constant that has the same structure.

#### Scenario: Tracked template is used when present
- **WHEN** `docs/05-domain/test-suggestion-template.md` exists
- **THEN** the suggester reads it and substitutes the placeholders

#### Scenario: Fallback template is used when the file is missing
- **WHEN** `docs/05-domain/test-suggestion-template.md` does not exist
- **THEN** the suggester uses the in-module fallback and the call still succeeds

### Requirement: Test Suggestions Endpoint
The system MUST provide `POST /api/diagnosis/test-suggestions` that takes `{ "task_id": str }` and returns `{ "content": str, "path": str }`. The endpoint MUST translate `DiagnosisNotFoundError` to `404`, `TaskNotFoundError` to `404`, and LLM errors to `502`. The endpoint MUST be a thin wrapper around `TestSuggester.run_and_save(task_id)`.

#### Scenario: Valid task returns content and path
- **WHEN** the operator calls `POST /api/diagnosis/test-suggestions` with a valid task_id
- **THEN** the response is `200` with `{ content: <markdown>, path: <output path> }`

#### Scenario: Missing diagnosis returns 404
- **WHEN** the operator calls the endpoint and the diagnosis is missing
- **THEN** the response is `404` with a clear error message

### Requirement: Auto-Generation Hook
`DiagnosisOrchestrator.run()` MUST call `TestSuggester.run_and_save(task_id)` after writing `ai-diagnosis.md` when the app setting `diagnosis.auto_generate_tests` is true (default). A failure in the suggester MUST be logged as a warning and MUST NOT affect the diagnosis return value or the `ai-diagnosis.md` write.

#### Scenario: Default behavior is on
- **WHEN** `diagnosis.auto_generate_tests` is not set or is `true`
- **THEN** after a successful diagnosis the suggester is invoked and the test-suggestions file is written

#### Scenario: Auto-generation failure does not affect the diagnosis
- **WHEN** the suggester raises an exception during auto-generation
- **THEN** the exception is logged, the diagnosis return value is unchanged, and the `ai-diagnosis.md` file is unchanged

#### Scenario: Setting off disables auto-generation
- **WHEN** `diagnosis.auto_generate_tests` is `false`
- **THEN** the suggester is NOT invoked from `DiagnosisOrchestrator.run()`

### Requirement: Test Suggestions Read Endpoint
The system MUST provide `GET /api/source/task/{task_id}/test-suggestions` that returns `{ "content": string | null }`. The endpoint MUST reject any `task_id` that does not match `[A-Za-z0-9_-]+` with `HTTP 400`. The endpoint MUST NOT read any file outside the configured output root.

The service function MUST live in `diagnose_tool/analyzer/task_reader.py` and be the only module in the project that constructs the `data/output/{task_id}/test-suggestions.md` path for the read side.

#### Scenario: Valid task_id returns the file content
- **WHEN** `data/output/{task_id}/test-suggestions.md` exists
- **THEN** the response is `200` with `{ "content": <text> }`

#### Scenario: Missing file returns null
- **WHEN** `data/output/{task_id}/test-suggestions.md` is missing
- **THEN** the response is `200` with `{ "content": null }`

### Requirement: Frontend Test Suggestions Tab
`TaskDetailPage` MUST render a fifth Tab "Test Suggestions" that displays the file content via a new `TestSuggestionsPanel` component. The component MUST parse `### Test:` headings and render each test as a card with a `Type` tag, a `Goal` sentence, a `Code` block, and a `Expected` line. The component MUST provide a one-click "Copy" button for each code block (using `navigator.clipboard.writeText`).

When the file is missing, the panel MUST render a "No test suggestions yet" message. The panel MUST use the existing `usePromise` + `Promise.all` parallel-load pattern, consistent with the other tabs.

#### Scenario: Panel renders parsed cards
- **WHEN** `test-suggestions.md` has three `### Test:` sections
- **THEN** the panel renders three cards, each with Type, Goal, Code (with a Copy button), and Expected

#### Scenario: Empty state when file is missing
- **WHEN** `test-suggestions.md` is missing
- **THEN** the panel renders "No test suggestions yet" and a Copy button is not present

#### Scenario: Copy button writes to clipboard
- **WHEN** the user clicks the Copy button on a card
- **THEN** the code block's text is written to the system clipboard

### Requirement: Manual Generate Button
`TaskDetailPage`'s Actions Tab MUST include a "Generate test suggestions" button. Clicking the button MUST call `POST /api/diagnosis/test-suggestions` with the current `task_id`. On success, the button MUST show a success message and the fifth Tab MUST re-render with the new content. On failure, the button MUST show the error.

#### Scenario: Clicking the button regenerates the suggestions
- **WHEN** the user clicks "Generate test suggestions" in the Actions Tab
- **THEN** the endpoint is called, the file is rewritten, and the Tab is re-rendered with the new content

### Requirement: i18n Keys
The system MUST add i18n keys for the new tab, the new card fields, and the new Actions button. The detail page MUST NOT contain hard-coded English strings in JSX.

#### Scenario: New keys are present in the i18n bundle
- **WHEN** a reviewer searches the i18n resource files for `taskDetail.tabs.testSuggestions` and `taskDetail.actions.generateTests.label`
- **THEN** both keys exist with English and Chinese values

### Requirement: Backend And Frontend Tests
The system MUST provide regression tests covering the new suggester service, the new routes, and the new frontend component.

#### Scenario: Suggester unit tests
- **WHEN** `tests/test_test_suggester.py` runs
- **THEN** every test passes (happy path, missing diagnosis, missing task, fallback template, file overwrite)

#### Scenario: Frontend component tests
- **WHEN** `npm test -- --run` runs against `TestSuggestionsPanel.test.tsx`
- **THEN** every test passes (empty state, parsed cards, copy interaction)
