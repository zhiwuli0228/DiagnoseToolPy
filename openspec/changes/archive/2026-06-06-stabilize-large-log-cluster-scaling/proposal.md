## Why

Real benchmark evidence now shows that large-directory clustering is not operationally viable: a verified `directory_concurrency_baseline` run on a prepared `10 GB` directory completed metadata scan in milliseconds but left both cluster tasks stuck in `scanning` until the 30-minute timeout. This change is needed now because the system cannot claim large-log readiness while duplicate requests can trigger repeated full scans of the same source.

## What Changes

**Cluster task admission and execution**
- From: Every `POST /api/cluster` request starts an independent background scan of the requested source path.
- To: The system coordinates cluster requests by normalized source path, prevents duplicate same-source full scans from running concurrently, and publishes byte-based progress while scanning.
- Reason: Current behavior duplicates `10 GB` scans under concurrency and produces timeouts without useful progress visibility.
- Impact: Non-breaking API surface with changed runtime behavior and richer task progress files.

**Benchmark validation contract**
- From: Benchmark automation exists, but large-directory readiness is not a formal acceptance contract for the clustering feature.
- To: The system defines benchmark-backed acceptance criteria for smoke, baseline, and large-directory cluster validation, including prepared dataset handling and required artifacts.
- Reason: The current bottleneck was only discovered through benchmark evidence and must stay continuously verifiable.
- Impact: Non-breaking operational and test workflow change; benchmark artifacts remain local/generated.

## Capabilities

### New Capabilities
- `cluster-task-scaling`: Coordinate large-log cluster execution so duplicate same-source requests do not start redundant full scans, publish byte-based progress, and fail safely when limits are exceeded.
- `large-log-benchmarking`: Provide benchmark automation and acceptance rules that validate large-log clustering against prepared datasets and required runtime evidence.

### Modified Capabilities
- `server-directory-scan`: Extend scan-related observable behavior for cluster workflows so progress reporting and source-path normalization expectations are explicit for large-directory task execution.

## Impact

- **Affected modules**: `api`, `analyzer`, `core`, `config`, `docs`, `tests`
- **Storage impact**:
  - `progress.json` gains byte-based and current-file fields for cluster tasks
  - `task.yaml` may gain source fingerprint / coordination fields if needed for runtime continuity
  - benchmark artifacts remain generated under `tests/load/artifacts/` and are not durable truth
- **Constraints confirmed**:
  - No mandatory database introduced
  - No full log file read into memory
  - No browser-first large log upload flow
  - File-based source of truth remains unchanged
- **Risks**:
  - Admission control bugs could strand tasks if runtime state is not updated atomically
  - Byte-based progress may require additional reader hooks and tests
  - Single-task protection may reduce concurrency for unrelated sources if scoping is too coarse
- **Verification**:
  - Unit coverage for task coordination and progress persistence
  - Smoke benchmark profile must pass
  - Real `directory_concurrency_baseline` must complete or fail with explicit bounded reasons instead of silent 30-minute scan hangs
