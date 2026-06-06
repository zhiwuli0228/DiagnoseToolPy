## Context

DiagnoseToolPy currently exposes cluster analysis through `POST /api/cluster`, which creates a background task and persists progress under `data/output/{task_id}/progress.json`. Real benchmark evidence now confirms that the current design is not sufficient for large-directory workloads. A prepared directory extracted from `E:\006tooldevelop\logsearch\out-final-expanded.zip` produced a `10 GB` source tree with 24 supported files, many of them hundreds of megabytes each. Under `directory_concurrency_baseline`, metadata scan completed quickly, but two concurrent cluster tasks for the same source path both remained in `scanning` until the 1800-second timeout.

The code path shows why this happens. `routes_cluster.py` starts a new background task for every request. `ClusterAnalyzer._scan_and_aggregate_streaming()` then linearly scans each file, applying decode, severity matching, parsing, and grouping without any same-source coordination. Progress is updated by file count instead of byte count, which hides the fact that a few massive files dominate total runtime.

Stakeholders are backend developers, operations engineers, and benchmark-running agents who need predictable behavior, observable progress, and repeatable acceptance criteria without introducing a database or external worker system.

## Goals / Non-Goals

**Goals:**
- Make large-log cluster execution operationally safe for repeated and concurrent requests on the same source path.
- Ensure cluster progress is meaningful for multi-gigabyte inputs by reporting byte-based progress and current-file context.
- Keep cluster execution streaming-first and file-based.
- Preserve benchmark automation as the source of validation for this requirement.
- Define an end-to-end acceptance contract that maps directly to benchmark evidence.

**Non-Goals:**
- Introducing Redis, Celery, Kafka, or any mandatory external queueing system.
- Replacing the clustering algorithm with ML or embedding-based grouping.
- Re-architecting the entire analyzer stack or the frontend.
- Solving every possible large-log optimization in one change; the first goal is correctness, coordination, and bounded completion behavior.

## Decisions

### 1. Source-aware cluster task coordination

The API layer will normalize `source_path` and coordinate background execution by source identity. For a source path that is already being scanned or matched:
- Default behavior: return the active `task_id` rather than start a duplicate full scan.
- Optional future behavior: allow queued follow-up work after current completion.

This keeps the fix within existing FastAPI and file-based boundaries while eliminating the most expensive observed failure mode: redundant concurrent scans of the same 10 GB directory.

### 2. Byte-based progress and richer task state

Cluster progress will be reported with:
- `processed_files`
- `total_files`
- `processed_bytes`
- `total_bytes`
- `current_file`
- `status`
- `message`

This aligns cluster task state with the project’s documented storage contract and makes progress meaningful for uneven file-size distributions.

### 3. Low-cost scan-stage behavior

The analyzer will keep streaming reads but reduce per-line cost where possible:
- avoid expensive parsing for lines that do not match severity preconditions
- update progress periodically by bytes and/or time window, not only every 10 files
- retain bounded in-memory grouping and samples

The change does not require algorithm replacement; it requires scan-stage cost discipline and observability.

### 4. Benchmark automation as acceptance contract

The benchmark standard becomes part of the design:
- `smoke_scan_sample` validates wrapper, dataset prep, and artifact generation
- `directory_concurrency_baseline` validates a real prepared large directory
- later heavier profiles remain evolution steps, not the first gate

This ensures future agents can verify the change with the same dataset and scripts instead of inventing ad-hoc tests.

### 5. Evolution path is explicit

The design is staged:
- Phase 1: same-source admission control, byte progress, bounded failure semantics
- Phase 2: optional source fingerprint reuse and cached cluster result reuse
- Phase 3: optional differentiated concurrency limits for unrelated sources

This avoids overcommitting the first implementation while leaving a coherent path forward.

## Risks / Trade-offs

- **[Risk] Same-source task registry becomes stale after partial failure** → Mitigation: persist runtime state transitions carefully and treat missing/terminal task outputs as recoverable when admitting new work.
- **[Risk] Byte-based progress adds more file-stat bookkeeping** → Mitigation: compute totals once from scan metadata and update processed bytes incrementally during streaming reads.
- **[Risk] Returning an existing `task_id` may surprise callers expecting a new task per click** → Mitigation: document the behavior and include explicit response fields indicating whether work was reused or newly created.
- **[Risk] Scan-stage optimizations may still be insufficient for worst-case workloads** → Mitigation: keep benchmark evidence in-scope and define Phase 2 reuse/fingerprinting if Phase 1 still fails the large-directory baseline.
- **[Risk] Broader concurrency throttling could underutilize the system for unrelated sources** → Mitigation: scope admission control by normalized source path first, not globally.

## Migration Plan

1. Introduce source-aware admission logic and richer progress persistence behind existing cluster APIs.
2. Extend tests for duplicate submissions, byte progress, timeout behavior, and benchmark reporting.
3. Run `smoke_scan_sample` to confirm wrapper and dataset preparation remain valid.
4. Run `directory_concurrency_baseline` against the prepared large directory.
5. If baseline still fails, inspect progress and process-stat evidence before moving to Phase 2 optimizations.

Rollback remains straightforward because the change is local to API/analyzer/runtime state. Reverting the new admission logic and progress fields restores the previous one-task-per-request behavior without requiring schema rollback beyond file-based task outputs.

## Open Questions

- Should duplicate same-source requests return HTTP 200 with the existing `task_id`, or a dedicated status field such as `reused_task: true`?
- Should source identity in Phase 2 use `(resolved path, file count, total bytes, mtimes)` or a stronger fingerprint?
- Should unrelated large-source tasks be allowed to run concurrently in Phase 1, or should the first release keep cluster execution globally single-threaded until evidence shows it is safe?
