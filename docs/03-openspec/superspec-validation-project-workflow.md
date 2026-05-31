# SuperSpec Validation Project Workflow

DiagnoseToolPy is a validation-grade project. The active workflow is the standard SuperSpec lifecycle:

```text
brainstorm → proposal → specs → tasks → plan → apply → verify → finalize → archive
```

## Why this is enabled

- The project already uses `schema: superspec`.
- The repository has the required backend, frontend, and evidence-generation flow in place.
- Validation-grade changes are allowed to move through the normal lifecycle without a separate Phase 3 approval gate.

## Standard feature flow

1. Create or update the change artifacts.
2. Use `apply` to implement the approved scope.
3. Run tests and `verify` the result.
4. Use `finalize` to close out the change.
5. Use `archive` to sync living specs and archive the change when supported by the repository workflow.

## Small bugfix flow

For small, low-risk fixes that do not change API contracts, storage contracts, or architecture boundaries:

1. Reproduce the issue.
2. Apply the minimal fix.
3. Add a regression test.
4. Verify the result.
5. Finalize and archive using the same repository workflow.

## Still enforced

- File system remains the source of truth.
- No mandatory external database.
- Large logs remain streamed, not bulk loaded.
- Retrieval works without embeddings by default.
- AI diagnosis stays assistive and does not auto-confirm root cause.
- Git safety still matters: no destructive history rewrites, no accidental inclusion of unrelated files.

## Historical gates

Older Phase 3 / Gate B / Gate D restriction reports remain in `docs/rectification/` as historical evidence. They are not the current execution rules for this validation-grade workflow.
