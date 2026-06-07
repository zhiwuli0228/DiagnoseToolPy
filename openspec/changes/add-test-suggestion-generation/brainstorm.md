## Context

`diagnose_tool/analyzer/diagnosis.py` already produces a per-task AI diagnosis written to `data/cases/{task_id}/ai-diagnosis.md`. `current-state.md` lists "Implement test suggestion generation (V0.4 extended)" as a Known Gap. The user-facing need is concrete: after a diagnosis lands, the on-call engineer needs a small, executable set of verification / reproduction scenarios that map the diagnosis text into a few `curl` / shell / Python / JUnit snippets they can paste into a terminal or a test file.

The current diagnosis prompt is long and focused on root-cause analysis; it does not request test scenarios. The new capability adds a thin, independent "TestSuggester" that reads the diagnosis and the evidence pack and produces a Markdown file with executable suggestions. The diagnosis flow stays unchanged for V0.4; the test suggestion generation is wired as an auto-call at the end of `DiagnosisOrchestrator.run()` (configurable, default on) and as a manual endpoint.

## Goals

- A new analyzer module `analyzer/test_suggester.py` exposing `TestSuggester.run(task_id) -> str` that reads `ai-diagnosis.md` + `evidence-pack.md` from `data/cases/{task_id}/` and `data/output/{task_id}/`, calls the LLM with a focused prompt, and returns the test-suggestion markdown.
- A version-tracked prompt template at `docs/05-domain/test-suggestion-template.md`, with an in-module fallback when the file is absent.
- A new `POST /api/diagnosis/test-suggestions` API endpoint that wraps the suggester.
- An optional auto-generation step at the end of `DiagnosisOrchestrator.run()` (controlled by an app setting, default on).
- The output is written to `data/output/{task_id}/test-suggestions.md` and is the durable evidence for the suggestion.
- A new `TestSuggestionsPanel` frontend component and a fifth Tab on `TaskDetailPage`. The panel parses `### Test:` headings, renders each suggestion as a card with `Type` / `Goal` / `Code` / `Expected`, and offers a one-click "Copy" button per code block.
- A new "Generate test suggestions" button in the Actions Tab that triggers a manual regeneration.
- i18n keys for the new tab and button.
- Backend tests (`tests/test_test_suggester.py`) and frontend tests for the new component.
- Playwright MCP browser verification per CLAUDE.md.

## Non-Goals

- Do not change the existing `DiagnosisOrchestrator.run()` prompt or output format. The suggester is a separate LLM call, not a piggyback field.
- Do not execute the generated test code. The output is suggestions only; whether the on-call runs them is up to them.
- Do not modify the casebase storage (`data/cases/{case_id}/`) — the suggester writes only to the task output directory.
- Do not add a new external dependency. The LLM client and YAML/JSON readers already cover what is needed.
- Do not change `DiagnosisOrchestrator.run_with_context` (the conversational diagnosis path). The auto-generation hook only fires from the synchronous `run()` path.

## Approach Selection

Three approaches were considered:

- **A. Independent `TestSuggester` module + separate LLM call (chosen)** — small, mirrors the existing `DiagnosisOrchestrator` style (pure Python, FastAPI-independent). Reusable from both the auto-hook and the manual endpoint. Failure of the suggester does not affect the diagnosis.
- **B. Piggyback a `test_suggestions` field onto the diagnosis prompt** — one LLM call, but bloats the diagnosis prompt and entangles the two output schemas; a regeneration of tests means re-running the whole diagnosis.
- **C. Template + rules** — limited to known failure modes; does not generalize.

A is the natural choice given the existing `DiagnosisOrchestrator` pattern. The fallback template and the version-tracked template keep the prompt maintainable.

## Key Design Decisions

1. **A new module, not a method on `DiagnosisOrchestrator`.** Keeps the prompt focused and the call sites independent. The auto-hook is a single line at the end of `run()`.

2. **Read `ai-diagnosis.md` from `data/cases/{task_id}/`, not from in-memory state.** This decouples the suggester from the diagnosis call: the user can re-run it any time after the diagnosis lands, and the manual endpoint does not need the orchestrator to be in scope.

3. **The output is a Markdown file under `data/output/{task_id}/`**, not a new casebase artifact. It is task-scoped evidence, not a confirmed case. The file is the durable record; regenerating it overwrites.

4. **The frontend parses the Markdown on the client** using a lightweight splitter on `### Test:` headings. No `react-markdown` dependency required (consistent with `complete-log-analysis-ui`).

5. **Auto-generation is on by default but configurable** via an app setting (`auto_generate_tests: bool` in `config/app.yaml`). If the LLM is down, the diagnosis still succeeds and the suggester is a best-effort follow-up.

6. **The Actions Tab adds a "Generate test suggestions" button** that calls the manual endpoint. This makes the capability usable on older tasks that were diagnosed before this change shipped.

## Open Questions

- Should the suggester also include a "test the test" pattern (e.g., a negative test for the fix)? Deferred — the LLM can suggest them naturally; we do not pre-shape the output.
- Should the test-suggestions be a hint to `case_draft.md` rather than a separate file? Deferred — separate file is easier to re-run and to point at from the UI.
