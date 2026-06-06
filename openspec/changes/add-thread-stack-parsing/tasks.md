## 1. Thread Dump Parser Core

- [ ] 1.1 Add `diagnose_tool/analyzer/thread_stack_parser.py` with a pure parser for common JVM thread dump blocks
  - Files: `diagnose_tool/analyzer/thread_stack_parser.py`
  - Behavior: parse thread name, thread state, ordered stack frames, optional lock/wait hints, raw text, and parse status
  - Tests: parse a standard HotSpot/OpenJDK dump, a blocked/waiting dump, and a truncated dump
  - Verification: `uv run pytest tests/test_thread_stack_parser.py`

- [ ] 1.2 Keep the parser conservative on malformed or unsupported vendor formats
  - Files: `diagnose_tool/analyzer/thread_stack_parser.py`, `tests/test_thread_stack_parser.py`
  - Behavior: return RAW or PARTIAL instead of raising for unsupported or truncated input
  - Tests: malformed header, missing stack frames, unsupported format
  - Verification: `uv run pytest tests/test_thread_stack_parser.py`

## 2. Regression Coverage

- [ ] 2.1 Add focused parser tests for metadata and frame ordering
  - Files: `tests/test_thread_stack_parser.py`
  - Behavior: verify thread name/state extraction, frame order preservation, and native/unknown frame retention
  - Tests: metadata extraction, ordered frames, Native Method, Unknown Source
  - Verification: `uv run pytest tests/test_thread_stack_parser.py`

- [ ] 2.2 Confirm the existing JVM exception stack parser remains unchanged
  - Files: `tests/test_stack_parser.py`
  - Behavior: no regression in the existing `parse_stack` contract
  - Tests: rerun the existing stack parser suite unchanged
  - Verification: `uv run pytest tests/test_stack_parser.py`

## 3. Documentation And Continuity

- [ ] 3.1 Document thread dump parsing support in the log format guide
  - Files: `docs/05-domain/log-format-guide.md`
  - Behavior: describe supported thread dump input and the parser’s raw/partial/full behavior
  - Verification: manual review against the implemented parser contract

- [ ] 3.2 Update the project continuity snapshot after implementation
  - Files: `docs/00-project/current-state.md`
  - Behavior: record thread stack parsing as implemented and list any remaining follow-up work
  - Verification: manual review of current-state entry consistency
