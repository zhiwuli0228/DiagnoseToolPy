## Design Summary

The user reports that large-log scanning is acceptable, but exception categorization is slow. Code inspection shows the likely bottleneck is not raw file reading; it is the post-scan path where clustered exception groups are generated and each group performs repeated historical case matching.

The current cluster flow can multiply work in two ways:

- group keys include minute-level time suffixes, so one exception class can fragment into many groups
- each group can trigger fresh scans of `data/cases/`, repeated YAML parsing, and repeated `case.md` extraction

The validated direction is to optimize exception clustering and case matching without changing the source-of-truth model:

```text
streamed log lines
  -> fast exception candidate extraction
  -> stable exception grouping without time in the key
  -> bounded group list with top-N matching
  -> task-local case match index loaded once
  -> cluster result + progress metrics
```

This change keeps scanning streaming-based, keeps case files as durable truth, and treats any in-memory or JSONL retrieval index as a rebuildable cache.

## Alternatives Considered

### Alternative A: Add More Parallelism

- **Approach**: Run exception grouping and historical case matching across multiple workers.
- **Pros**:
  - Can improve throughput when CPU is the bottleneck
  - Keeps the visible behavior mostly unchanged
- **Cons**:
  - Multiplies file reads when matching still scans cases per group
  - Raises memory and disk contention risk
  - Does not fix group explosion from time-fragmented keys
- **Why not chosen**: Parallelism would hide, not remove, the repeated work. It is better as a later step after the algorithmic cost is bounded.

### Alternative B: Use a Mandatory Database or Search Service

- **Approach**: Store cases and match indexes in SQLite, Elasticsearch, Redis, or another query service.
- **Pros**:
  - Fast lookups and ranking are easy to model
  - Mature indexing features are available
- **Cons**:
  - Violates the project constraint against mandatory databases or infrastructure
  - Increases deployment complexity for a lightweight diagnostic tool
  - Moves durable knowledge away from file documents
- **Why not chosen**: The project requires Markdown/YAML files as source of truth and retrieval without mandatory external services.

### Alternative C: Bound Clustering and Cache Case Matching

- **Approach**: Remove time from group keys, keep time as distribution metadata, cap historical matching to top-N groups, and load case metadata/body summaries once per task into a task-local matcher.
- **Pros**:
  - Directly addresses repeated work
  - Preserves file-based source of truth
  - Improves worst-case behavior even on a large casebase
  - Keeps scanning and analyzer module boundaries intact
- **Cons**:
  - Requires careful compatibility with existing cluster result shape
  - Needs metrics to prove the bottleneck moved or was reduced
- **Why chosen**: It targets the slow stage reported by the user while staying within current architecture and governance constraints.

## Agreed Approach

Choose Alternative C.

The change will optimize exception clustering and historical case matching by:

1. Using stable exception group keys that do not include minute/hour time fragments.
2. Preserving time information as separate `time_distribution` data.
3. Loading case metadata and relevant case text once per cluster task.
4. Matching historical cases only for the top-N most significant groups by default.
5. Recording phase timings and cardinality metrics so future validation can distinguish scan, grouping, matching, and output-writing costs.

The design explicitly excludes mandatory databases, vector retrieval, frontend redesign, and broad analyzer rewrites.

## Key Decisions

- Exception grouping MUST classify by exception class or normalized message template, not by timestamp bucket.
- Time distribution MUST remain available for diagnosis, but MUST NOT increase group cardinality.
- Historical case matching SHOULD be performed through a task-local case match index loaded once from `data/cases/`.
- Matching MUST continue to work when embeddings are disabled.
- Top-N matching SHOULD default to a conservative bound such as 50 groups, with all groups still counted and returned.
- Progress and benchmark output SHOULD expose `aggregating`, `matching_cases`, and `writing_cache` phase timings.
- Rebuildable indexes MAY be used under `data/indexes/`, but case files remain the source of truth.

## Open Questions

- What default top-N value should be used for historical matching: 20, 50, or configurable through app config?
- Should low-frequency groups beyond a maximum group count be preserved individually or collapsed into an `other` summary group?
- Should task-level phase metrics live only in `progress.json`, or also be written to a dedicated artifact such as `artifacts/performance-metrics.json`?
