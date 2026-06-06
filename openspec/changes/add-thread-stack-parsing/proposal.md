## Why

DiagnoseToolPy can already preserve multiline logs and parse JVM exception stack traces, but it still treats thread dump blocks as unstructured text. That is a gap for real diagnostics: blocked workers, deadlocks, and thread-state snapshots often carry the most useful evidence, yet they remain hard to query, compare, and reuse without a dedicated parser.

We should add this capability now because it fits the existing streaming, file-based analyzer architecture and does not require any new infrastructure. A bounded, pure parser also keeps the change low risk while creating a reusable foundation for later evidence and diagnosis integration.

## What Changes

**Thread dump parsing capability**
- From: Thread dump blocks are preserved only as raw text.
- To: The analyzer can parse common JVM thread dump blocks into structured thread metadata and stack frames while preserving raw input on malformed blocks.
- Reason: Thread-state evidence is currently invisible to machines even when it is present in the log content.
- Impact: New analyzer capability; no mandatory storage or infrastructure changes.

**Failure handling**
- From: Unrecognized or partially formed stack content is handled only as raw text.
- To: The parser returns RAW or PARTIAL results for malformed inputs instead of failing the analysis flow.
- Reason: Diagnostic inputs are messy, and the parser must be safe to use on real-world logs.
- Impact: Non-breaking behavior change.

## Capabilities

### New Capabilities
- `thread-stack-parsing`: Parse JVM thread dump blocks into structured thread metadata, stack frames, and parse status while preserving raw content on failure.

### Modified Capabilities
- None.

## Impact

- **Affected modules**:
  - `diagnose_tool/analyzer/` for the parser implementation
  - `tests/` for parser coverage
  - `docs/00-project/current-state.md` after implementation is complete
- **Storage impact**:
  - No new durable files or schema changes in the first version
  - No changes to case storage, retrieval indexes, or task output contracts required
- **Risks**:
  - Thread dump formats vary across JVMs and vendors, so the first parser must stay conservative
  - Overlapping stack grammars could introduce regression risk if the parser is merged into the existing exception-stack module
  - Consumer integration may still be needed later if parsed thread dumps should appear in evidence or prompts
- **Verification**:
  - Unit tests for standard thread dump formats, malformed inputs, and partial parses
  - Regression tests to confirm existing exception-stack parsing is unchanged
  - `uv run pytest` or the targeted parser test subset after implementation
