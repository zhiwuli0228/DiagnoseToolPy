## Design Summary

DiagnoseToolPy already has streaming log reading, multiline event merging, and a JVM exception stack parser, but it still lacks structured parsing for thread dump blocks. In practice that means deadlock dumps, blocked worker snapshots, and JVM thread-state reports are preserved only as raw text, which is hard to compare, classify, and reuse in diagnosis flows.

The agreed direction is to add a dedicated thread dump parser that can extract thread identity, state, lock/monitor hints, and stack frames from a bounded raw block while preserving the original text on failure. The parser should stay analyzer-only, reuse the project's existing streaming and file-based workflow, and avoid changing storage contracts in the first pass.

## Alternatives Considered

### Alternative A: Keep thread dumps as raw text only
- **Approach**: Leave the current multiline pipeline unchanged and let downstream consumers inspect thread dumps manually.
- **Pros**: No code changes; no new parsing edge cases.
- **Cons**: No structured metadata; thread-state and lock information stay buried in text; poor reuse across evidence, retrieval, and diagnosis.
- **Why not chosen**: This preserves the current limitation and does not add any durable diagnostic value.

### Alternative B: Add a dedicated thread dump parser module
- **Approach**: Introduce a pure parser for thread dump blocks that extracts thread name, state, frames, and lock hints, while preserving raw content and handling malformed blocks safely.
- **Pros**: Clean module boundary; can be tested independently; can evolve without disturbing the existing exception stack parser.
- **Cons**: Requires new tests and later integration work if the parsed structure should appear in reports or prompts.
- **Why not chosen**: Chosen approach.

### Alternative C: Extend the existing JVM exception stack parser
- **Approach**: Fold thread dump parsing into the current `stack_parser.py` implementation.
- **Pros**: Reuses some frame parsing logic.
- **Cons**: Conflates two different formats; makes the parser harder to reason about; increases regression risk for the existing exception-stack capability.
- **Why not chosen**: The current stack parser already has a clear contract for exception traces, and mixing thread dumps into it would blur the boundaries.

## Agreed Approach

Use **Alternative B**. Add a standalone thread dump parser that accepts a raw thread dump block and returns structured metadata plus parsed frames. Keep the parser independent from FastAPI and from any file-writing responsibility. Preserve the existing multiline reader and exception stack parser unchanged in this change.

## Key Decisions

- Thread dump parsing is a new analyzer capability, not a storage or deployment change.
- Parsing must preserve raw input and return a partial/RAW result instead of throwing on malformed blocks.
- The first version should focus on common HotSpot/OpenJDK thread dump formats.
- The parser should be bounded and testable on in-memory block strings; it must not require any new mandatory infrastructure.
- Any later report/prompt integration should consume the parser output after this capability is stable.

## Open Questions

- Whether the first release should include thread monitor ownership details beyond `state` and stack frames.
- Whether the parser should normalize thread names and ids or preserve their raw form only.
- Whether a later change should expose the parsed thread dump in evidence packs or diagnosis prompts.
