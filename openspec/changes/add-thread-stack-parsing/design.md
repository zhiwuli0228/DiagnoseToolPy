## Design Summary

Add a dedicated parser for JVM thread dump blocks so DiagnoseToolPy can structure thread-state evidence that is currently only available as raw text. The parser will live in the analyzer layer, remain FastAPI-independent, and return a structured result that preserves raw content on partial or malformed inputs.

The first implementation targets common HotSpot/OpenJDK thread dump formats. It focuses on the fields most useful for diagnosis workflows: thread identity, thread state, stack frames, and lock/monitor hints when present. The parser is intentionally separate from the existing JVM exception stack parser so each capability keeps a narrow contract.

## Alternatives Considered

### Alternative A: No dedicated parser
- **Approach**: Continue storing thread dumps as raw multiline text only.
- **Pros**: Zero implementation cost.
- **Cons**: No machine-readable thread-state metadata; poor reusability; manual inspection stays mandatory.
- **Why not chosen**: Does not solve the core diagnostic gap.

### Alternative B: Dedicated thread dump parser module
- **Approach**: Add a new pure-Python parser module that consumes a raw thread dump block and emits structured metadata.
- **Pros**: Clear boundary; good testability; minimal coupling; preserves existing exception-stack behavior.
- **Cons**: Requires new parser tests and later consumer integration if the result should appear in reports.
- **Why not chosen**: Chosen approach.

### Alternative C: Merge thread dump parsing into the existing exception stack parser
- **Approach**: Expand `stack_parser.py` to parse both exception traces and thread dumps.
- **Pros**: Reuses frame parsing helpers.
- **Cons**: Two unrelated grammars in one module; higher regression risk; harder to maintain exact output contracts.
- **Why not chosen**: The formats are different enough to warrant separate parsers.

## Agreed Approach

Implement a new `diagnose_tool/analyzer/thread_stack_parser.py` module with a `parse_thread_dump(...)` entry point and a small set of dataclasses for structured results. Keep the parser pure and deterministic. Preserve raw input on failures, and return a partial result when some fields are parsed but others are missing.

The analyzer pipeline remains streaming-first. This change only parses bounded raw thread-dump blocks that are already in memory as event candidates or user-provided stack text. No new mandatory storage or infrastructure is introduced.

## Data Flow

1. A caller passes a raw thread dump block to the parser.
2. The parser identifies the thread header line, state line, frame lines, and optional lock/monitor hints.
3. The parser returns a structured result containing parsed metadata and the original raw block.
4. Downstream consumers can later use that result for evidence text, diagnosis prompts, or retrieval hints.

## Module Responsibilities

- `diagnose_tool/analyzer/thread_stack_parser.py`
  - Parse thread dump blocks into structured data.
  - Extract thread name, state, frames, and optional lock hints.
  - Preserve raw input and parse status on malformed inputs.
- `diagnose_tool/analyzer/stack_parser.py`
  - Remains the existing JVM exception-stack parser.
  - Does not take on thread dump grammar in this change.
- `tests/test_thread_stack_parser.py`
  - Cover happy-path formats, malformed inputs, and partial parses.

## File Outputs

- No new durable files are introduced in this change.
- The parser operates on in-memory strings and returns Python objects.
- Any later report or export integration will be handled in a follow-up change if needed.

## Error Handling

- If the input is not a recognizable thread dump block, the parser returns a RAW result.
- If the block has a recognizable header but incomplete body, the parser returns a PARTIAL result.
- The parser never raises for a malformed thread dump block unless the caller passes an invalid type.

## Security Considerations

- The parser does not execute code, open files, or make network calls.
- Raw text is preserved as input only; no path expansion or dynamic evaluation is involved.
- The module must remain independent from FastAPI and other runtime layers.

## Memory Behavior

- Parsing is bounded to the provided raw block string.
- The implementation should avoid recursive unbounded structures and keep frame lists limited to parsed content only.
- No whole-directory or whole-file buffering is introduced by this capability.

## Tests

- Parse a standard HotSpot/OpenJDK thread dump block.
- Parse a block with blocked/waiting states and lock hints.
- Parse a malformed block and confirm RAW/PARTIAL behavior.
- Preserve raw input and file-independent behavior.

## Compatibility

- Existing exception stack parsing remains unchanged.
- Existing multiline log event merging remains unchanged in this change.
- No storage contract changes are required for the first implementation.
