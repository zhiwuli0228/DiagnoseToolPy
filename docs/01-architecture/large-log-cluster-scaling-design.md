# Large Log Cluster Scaling Design

## Overview

This document defines the end-to-end requirement for making DiagnoseToolPy’s cluster workflow operationally viable on multi-gigabyte log directories. The immediate trigger is a verified large-directory benchmark failure: a prepared directory extracted from `E:\006tooldevelop\logsearch\out-final-expanded.zip` produced about `10 GB` of logs across 24 supported files, and `directory_concurrency_baseline` showed that two concurrent cluster tasks for the same source remained in `scanning` until the 30-minute timeout.

The design covers:
- request admission for large cluster tasks
- scan-stage execution and progress telemetry
- runtime state and file outputs
- benchmark-driven acceptance
- future evolution beyond the first stabilization pass

It does **not** introduce a database, queue service, or external worker dependency.

## Problem Statement

Current behavior has three operational flaws:

1. `POST /api/cluster` starts independent full scans even when multiple requests target the same source path.
2. Cluster progress is reported by file count rather than byte count, which is misleading when a few files are hundreds of megabytes each.
3. Benchmark evidence exists, but large-directory completion is not yet a formal implementation gate.

The result is that metadata scan looks healthy while the expensive cluster scan silently burns CPU and IO for long periods without completing under concurrency.

## Goals

- Prevent redundant concurrent same-source cluster scans.
- Preserve streaming reads and bounded in-memory grouping.
- Make progress observable and trustworthy on multi-gigabyte inputs.
- Turn benchmark evidence into a formal acceptance contract.
- Keep the design implementable within current FastAPI + file-state architecture.

## Non-Goals

- External worker queues or mandatory infrastructure.
- Full rewrite of clustering logic.
- Frontend redesign.
- Embedding-based or ML-based clustering changes.

## Data Flow

1. Client submits `POST /api/cluster` with `source_path`.
2. API resolves and normalizes the source path.
3. API checks local runtime state for an active same-source cluster task.
4. If an active same-source task exists:
   - return existing task identity, or
   - return a clear reused/serialized response
5. If no active same-source task exists:
   - create `data/output/{task_id}/`
   - write initial `progress.json`
   - start background cluster execution
6. Analyzer scans files line-by-line, updates byte-based progress, and incrementally builds bounded cluster groups.
7. On success:
   - write `cluster-result.json`
   - write bounded `matched-lines.jsonl`
   - mark `progress.json` terminal success
8. On failure or timeout:
   - write terminal failure state to `progress.json`
   - keep partial observability without pretending success

## Module Responsibilities

### `api`

- Normalize source path
- Coordinate same-source admission
- Return task identity and status safely
- Never perform log parsing or directory scanning directly

### `core`

- Hold runtime coordination helpers if needed
- Normalize path identity safely
- Provide atomic file update helpers where useful

### `analyzer`

- Perform streaming cluster scan
- Track processed bytes and current file
- Keep memory bounded
- Emit task outputs and terminal state

### `tests/load`

- Prepare large benchmark datasets
- Run smoke and baseline profiles
- Produce machine-readable and markdown evidence

## File Outputs

### Cluster Runtime Output

`data/output/{task_id}/progress.json` SHALL include:

```json
{
  "status": "scanning",
  "progress": 42,
  "processed_files": 7,
  "total_files": 24,
  "processed_bytes": 4286578688,
  "total_bytes": 10001887403,
  "current_file": "E:/.../myservice10/root/myservice10.log",
  "message": "scanning myservice10.log",
  "updated_at": "2026-06-06T11:14:36.071007"
}
```

`data/output/{task_id}/cluster-result.json` remains the success artifact.

`data/output/{task_id}/matched-lines.jsonl` remains a bounded cache, not durable truth.

### Benchmark Evidence Output

Each benchmark run writes:

```text
tests/load/artifacts/{run_id}/
├── {profile}.json
├── {profile}.md
├── process-stats.csv
├── run-meta.json
└── index.json
```

## Error Handling

- Duplicate same-source request:
  - do not start a second full scan
  - return existing task identity or explicit reuse status
- Scan timeout:
  - write terminal failed state to `progress.json`
  - preserve last known byte progress
- Background exception:
  - do not leave the task in `scanning`
  - emit safe failure reason
- Partial artifact generation:
  - no success result may be written unless clustering actually completes

## Security Considerations

- Source path normalization must use resolved server paths only.
- Same-source coordination must not widen path access beyond existing validation.
- Dataset preparation from ZIP must continue using safe extraction that rejects traversal members.

## Memory Behavior

- Full log files MUST NOT be read into memory.
- Group state remains bounded by count and bounded sample lists.
- Duplicate same-source scans are prevented because they multiply both IO and memory pressure.
- Progress updates should be frequent enough for observability but not so frequent that they dominate runtime.

## Benchmark-Driven Acceptance

### Smoke Acceptance

`smoke_scan_sample` MUST pass and produce:
- profile markdown/json
- `process-stats.csv`
- `run-meta.json`

### Functional Large-Directory Acceptance

Using the prepared directory extracted from `out-final-expanded.zip`:

- `directory_concurrency_baseline` MUST complete without leaving all cluster tasks stuck in `scanning`
- same-source concurrent requests MUST NOT trigger redundant independent full scans
- task progress MUST expose `processed_bytes`, `total_bytes`, and `current_file`

### Performance Acceptance

The first implementation pass is accepted when:

- scan metadata path still passes benchmark thresholds
- at least one same-source large-directory baseline run completes within configured timeout, or
- if timeout still occurs, it must happen with explicit terminal failure semantics and evidence showing the remaining bottleneck

This is intentionally staged: Phase 1 prioritizes safe execution and observability before deeper optimization.

## Evolution Plan

### Phase 1: Stabilization

- same-source task admission control
- byte-based progress
- terminal timeout/failure semantics
- benchmark metric correctness

### Phase 2: Reuse

- source fingerprinting based on path + file count + total bytes + mtimes
- reuse of prior cluster outputs for unchanged sources
- explicit stale-result invalidation rules

### Phase 3: Throughput Tuning

- per-source and cross-source concurrency policies
- deeper parser cost reductions
- optional staged scan summaries for faster repeated diagnosis paths

## Tests

- Unit tests for duplicate same-source admission
- Unit tests for byte-based progress persistence
- Unit tests for timeout terminal-state persistence
- Unit tests for benchmark summary correctness when cluster runs fail
- Smoke benchmark run
- Large-directory baseline benchmark run

## Compatibility

- No database migration required
- Existing API route shape can be preserved
- Existing benchmark artifacts remain local/generated
- Existing casebase and retrieval contracts are unchanged

## Acceptance Checklist

- [ ] OpenSpec change artifacts are complete through `plan`
- [ ] Wrapper can run smoke profile without manual benchmark setup
- [ ] Prepared large directory is benchmarked from a declared ZIP source
- [ ] Same-source concurrent cluster requests do not launch redundant full scans
- [ ] Cluster progress becomes byte-based and file-aware
- [ ] Terminal timeout/failure states are explicit in `progress.json`
- [ ] `directory_concurrency_baseline` is rerun and evidence is attached
