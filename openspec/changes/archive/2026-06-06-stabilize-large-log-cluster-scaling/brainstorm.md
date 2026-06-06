## Design Summary

The current cluster analysis path works for small inputs but fails for real large-directory workloads. A verified `directory_concurrency_baseline` run against a prepared `10 GB` directory completed metadata scan quickly, then left two cluster tasks stuck in `scanning` for 30 minutes until timeout. The design therefore needs to treat large-log clustering as a protected background workload rather than a fire-and-forget endpoint.

The agreed direction is to add source-aware job admission, byte-based progress reporting, and low-cost scan behavior so the system can complete a single large-directory cluster task predictably and reject or reuse duplicate work instead of re-reading the same directory concurrently. The benchmark automation remains part of the requirement so each fix can be validated against a real prepared dataset.

## Alternatives Considered

### Alternative A: Keep current flow and only increase benchmark timeout
- **Approach**: Raise `cluster_timeout_seconds` from 1800 seconds to a much larger number and accept long-running scans.
- **Pros**: Minimal code change; preserves current APIs and task model.
- **Cons**: Does not reduce duplicate scans, CPU burn, or user uncertainty; allows the same directory to be scanned repeatedly; makes progress reporting even less trustworthy.
- **Why not chosen**: This treats symptoms instead of the root cause and would still fail when multiple users submit the same large source.

### Alternative B: Introduce source-aware task coordination and byte-driven scan progress
- **Approach**: Add a cluster task registry keyed by normalized source path, deduplicate or serialize duplicate submissions, expose byte-level progress, and reduce scan-stage per-line overhead while preserving streaming reads.
- **Pros**: Directly addresses the observed timeout mode; fits file-system source-of-truth constraints; keeps implementation inside existing API/analyzer boundaries; provides observable acceptance criteria.
- **Cons**: Requires changes across API, analyzer, runtime state, and benchmark tooling; needs careful partial-failure handling.
- **Why not chosen**: Chosen approach.

### Alternative C: Introduce a separate queue service or external worker system
- **Approach**: Offload cluster tasks to Redis/Celery, Kafka, or a database-backed job queue.
- **Pros**: Stronger concurrency control and queue semantics.
- **Cons**: Violates project constraints against mandatory infrastructure; increases deployment complexity; broadens scope beyond the immediate bottleneck.
- **Why not chosen**: Incompatible with the project’s no-mandatory-database / no-mandatory-infrastructure rule.

## Agreed Approach

Use **Alternative B**. The system will keep cluster execution file-based and local, but it will stop treating every request as an independent full scan. The API layer will coordinate requests by source path and active task state. The analyzer will publish byte-based progress and reduce scan-stage work to the minimum needed for clustering. The benchmark standard will become part of the contract so each implementation step can be validated with a smoke profile and a real large-directory baseline.

## Key Decisions

- Cluster execution remains local and file-based; no external queue or database is introduced.
- Duplicate cluster submissions for the same normalized source path will not start independent full scans.
- Progress must reflect processed bytes and the current file, not only processed file count.
- Large-directory benchmark validation is part of the change scope, not a later operational concern.
- A successful fix is defined by benchmark completion behavior, not only by code structure.

## Open Questions

- Whether duplicate same-source requests should always return the existing `task_id` or optionally queue a follow-up task after the current one completes.
- Whether cluster results should be reusable across requests via a lightweight source fingerprint in a later phase.
- Whether scan-stage optimizations should stop at admission/progress improvements in this change or also include deeper parser cost reductions if the first pass is insufficient.
