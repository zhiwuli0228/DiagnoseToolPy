# Thread Stack Parsing Implementation Plan

> **For agentic workers:** Implement this plan task-by-task and stop if a step
> reveals out-of-scope behavior.

**Goal:** Add structured JVM thread dump parsing without changing the existing exception stack parser contract.

**Architecture:** Keep the new capability inside `diagnose_tool/analyzer/` as a pure parser module that accepts a raw thread dump block and returns structured metadata plus raw preservation fields. Do not merge thread dump grammar into `stack_parser.py`; keep the existing exception-stack parser untouched and verify that its tests still pass.

**Tech Stack:** Python 3.11+, `pytest`, `uv`, existing analyzer dataclasses, file-based docs.

---

## Task 1: Add the thread dump parser module

- [ ] **Step 1:** Read `openspec/changes/add-thread-stack-parsing/specs/thread-stack-parsing/spec.md` and `openspec/changes/add-thread-stack-parsing/design.md` before coding.
- [ ] **Step 2:** Create `diagnose_tool/analyzer/thread_stack_parser.py` with dataclasses for parsed thread dumps and a pure `parse_thread_dump(...)` entry point.
- [ ] **Step 3:** Implement conservative parsing for a common HotSpot/OpenJDK thread dump header, thread state line, ordered `at ...` frames, and optional lock/wait hints.
- [ ] **Step 4:** Ensure malformed or unsupported input returns RAW or PARTIAL output instead of raising.
- [ ] **Step 5:** Run `uv run pytest tests/test_thread_stack_parser.py` after the first parser draft.

**Commit point:** parser module exists, passes focused parser tests, and preserves raw input on failures.

## Task 2: Add regression coverage

- [ ] **Step 1:** Create `tests/test_thread_stack_parser.py` with fixtures for a standard dump, a blocked/waiting dump, and a truncated dump.
- [ ] **Step 2:** Add assertions for thread name extraction, state extraction, frame ordering, native/unknown source retention, and parse status.
- [ ] **Step 3:** Add malformed-input cases that must stay safe and must not crash.
- [ ] **Step 4:** Re-run `uv run pytest tests/test_thread_stack_parser.py tests/test_stack_parser.py`.
- [ ] **Step 5:** Confirm the existing exception stack parser contract remains unchanged.

**Commit point:** new thread dump tests pass and the existing stack parser suite still passes unchanged.

## Task 3: Update docs and continuity state

- [ ] **Step 1:** Update `docs/05-domain/log-format-guide.md` to document supported thread dump parsing behavior and raw/partial/full outcomes.
- [ ] **Step 2:** Update `docs/00-project/current-state.md` to record thread stack parsing as implemented only after the code and tests are complete.
- [ ] **Step 3:** Review the updated docs for consistency with the new spec and analyzer boundary rules.
- [ ] **Step 4:** Run `uv run pytest tests/test_thread_stack_parser.py tests/test_stack_parser.py` again if any doc-driven code comment or fixture change was needed.

**Commit point:** docs and continuity snapshot match the delivered capability.
