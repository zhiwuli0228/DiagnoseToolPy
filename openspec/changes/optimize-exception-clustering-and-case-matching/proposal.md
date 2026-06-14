## Why

Large-log scanning is already acceptable, but exception categorization remains slow when many error groups are produced. The current cluster flow can fragment one exception into many time-suffixed groups and repeatedly scan `data/cases/` for each group. This change bounds grouping and historical case matching work so large-log diagnosis remains usable without changing the file-based architecture.

## What Changes

**Exception Grouping**
- From: Cluster group keys may include time fragments, increasing group cardinality for the same exception pattern.
- To: Group keys classify by exception class or normalized message template only; time remains separate distribution metadata.
- Reason: Time belongs to analysis context, not category identity.
- Impact: Non-breaking result shape; fewer duplicate-looking clusters.

**Historical Case Matching**
- From: Each group can trigger fresh case directory iteration, YAML parsing, and case body extraction.
- To: A task-local case match index is loaded once and reused across group matching.
- Reason: Matching cost should scale with top groups and casebase size, not repeated filesystem scans per group.
- Impact: Non-breaking; matching still uses file-backed case data and works without embeddings.

**Bounded Matching**
- From: All groups may attempt historical matching.
- To: Only top-N significant groups perform historical case matching by default; all groups are still counted and returned.
- Reason: Low-frequency groups should not dominate runtime.
- Impact: Some low-frequency groups may have no matched cases, but their counts and samples remain available.

**Phase Metrics**
- From: Users can see broad progress but not which post-scan phase is slow.
- To: Progress and benchmark evidence expose aggregation, case matching, and cache-writing phase costs.
- Reason: Future tuning needs actionable evidence.
- Impact: Adds observability fields without replacing existing progress behavior.

## Capabilities

### New Capabilities

- `exception-cluster-matching-performance`: Defines bounded exception grouping, top-N historical case matching, task-local case match indexing, and post-scan phase metrics.

### Modified Capabilities

- None.

## Impact

Affected modules:

- `analyzer`: cluster grouping, group cardinality control, time distribution, phase metrics, matched-lines cache timing.
- `retrieval`: reusable case match loading/scoring helpers that do not require embeddings.
- `tests/load`: benchmark evidence for post-scan categorization and matching time.
- `docs`: current-state and architecture notes after implementation.

Storage impact:

- `progress.json`: may include additional phase, timing, group-count, and top-N matching fields.
- `cluster-result.json`: existing shape remains compatible; group keys become more stable.
- `matched-lines.jsonl`: remains bounded and rebuildable.
- Optional `data/indexes/fulltext/index.jsonl`: may be reused or rebuilt as a cache, never durable truth.

Constraints:

- No mandatory database introduced.
- No full log file read into memory.
- No browser-first large-log upload flow.
- File system remains the source of truth.
- Retrieval continues to work with embeddings disabled.

Risks:

- Removing time from group keys may merge events that previously appeared as separate time buckets.
- Top-N matching may omit historical matches for rare groups.
- Case match index loading must handle malformed `metadata.yaml` or missing `case.md` without failing the whole task.

Verification:

- Unit tests must prove stable grouping without time-key fragmentation.
- Unit tests must prove case files are loaded once per task-level matcher, not once per group.
- Regression tests must cover empty casebase, malformed metadata, and embedding-disabled matching.
- Load benchmarks must report scan, aggregation, matching, and cache-writing timing separately.
