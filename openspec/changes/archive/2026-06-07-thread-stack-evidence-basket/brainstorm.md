## Design Summary

Thread stack evidence should be a file-backed, task-scoped evidence source that plugs into the existing diagnosis evidence basket. The parser stays responsible for recognizing and structuring thread dump blocks; this change adds the selection and handoff layer so users can add one parsed thread or all parsed threads into the same diagnosis flow used for logs and clusters.

The source of truth should remain in `data/output/{task_id}/artifacts/`, so the frontend only renders and selects thread evidence. Diagnosis, prompt preview, and workspace export should resolve thread references on demand rather than storing thread bodies in browser state or introducing a database.

## Alternatives Considered

### Alternative A: Dedicated thread-diagnosis workflow
- **Approach**: Create a separate thread stack diagnosis page and a separate prompt/export pipeline.
- **Pros**:
  - Keeps thread logic isolated.
  - Can be optimized for thread-specific UI.
- **Cons**:
  - Duplicates evidence selection and export behavior.
  - Splits diagnosis UX across multiple flows.
  - Adds more surface area than needed for the first version.
- **Why not chosen**: The existing evidence basket already solves selection and prompt handoff, so a separate workflow would be redundant.

### Alternative B: Reuse the existing evidence basket with a new thread evidence type
- **Approach**: Add thread evidence as a new selection type and let the current diagnosis/export flow handle it.
- **Pros**:
  - Minimal change to the overall UX.
  - Keeps thread evidence consistent with log/group/cluster evidence.
  - Reuses existing preview, diagnosis, and workspace export paths.
- **Cons**:
  - Requires updates to selection labels, API payloads, and prompt assembly.
  - Requires a new read-only task artifact for thread results.
- **Why not chosen**: This is the chosen approach because it is the smallest change that satisfies the user-visible goal.

### Alternative C: Persist thread selections in a database-backed session
- **Approach**: Store parsed thread results and selections in a server database for later reuse.
- **Pros**:
  - Easy to share and query.
  - Can cache parsed results centrally.
- **Cons**:
  - Violates the file-system source-of-truth rule.
  - Introduces mandatory infrastructure.
  - Adds operational and migration complexity.
- **Why not chosen**: The project explicitly forbids mandatory databases, and the thread evidence is naturally rebuildable from files.

## Agreed Approach

Use the existing diagnosis evidence basket as the integration point, add a thread evidence selection type, and expose thread-stack results as task artifacts under `data/output/{task_id}/artifacts/`. The frontend will render parsed thread rows with add-one and add-all actions, while backend export and diagnosis logic resolves thread references from the task artifact at request time.

## Key Decisions

- Thread evidence is task-scoped and file-backed, not stored in a database or browser cache.
- The new flow reuses the existing diagnosis preview, diagnosis start, and workspace export APIs.
- Selection entries use stable opaque thread references rather than storing raw thread dump text in the selection payload.
- Add-all is implemented as repeated thread selection with deduplication, not as a separate storage type.
- If a task has no parsed thread blocks, the UI shows an empty state and does not block other diagnosis evidence.
- Partially parsed thread blocks remain selectable as long as the parser produced a structured thread entry.

## Open Questions

- Should the first release surface thread evidence only from completed analysis tasks, or also from standalone pasted thread dump text?
- Should the frontend show raw thread excerpts inline, or only metadata plus a truncated preview?
- Should the export prompt include a dedicated section for thread evidence, or merge it into the existing evidence pack section?
