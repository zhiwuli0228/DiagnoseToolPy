## ADDED Requirements

### Requirement: Stable Exception Cluster Identity

The system MUST group exception clusters by exception class when available, otherwise by normalized message template, and MUST NOT include timestamp buckets or minute/hour fragments in the cluster identity.

#### Scenario: Same exception across different minutes

- **WHEN** a cluster task processes two log events with the same exception class at different minutes
- **THEN** the task produces one exception cluster for that exception class

#### Scenario: Time distribution remains available

- **WHEN** a cluster contains events from multiple time buckets
- **THEN** the cluster result includes time distribution data separate from the cluster identity

---

### Requirement: Bounded Historical Case Matching

The system MUST perform historical case matching only for a bounded set of the most significant exception clusters while preserving counts and samples for all clusters.

#### Scenario: Groups exceed matching limit

- **WHEN** a cluster task produces more groups than the configured matching limit
- **THEN** only the top groups up to the limit include historical case matches
- **THEN** groups outside the limit remain present with counts, samples, and empty matched case lists

#### Scenario: Groups within matching limit

- **WHEN** a cluster task produces groups within the configured matching limit
- **THEN** every produced group is eligible for historical case matching

---

### Requirement: Task-local Case Matching Source

The system MUST load case metadata and relevant case text once for a cluster task matching phase and MUST reuse that loaded representation across group matching.

#### Scenario: Multiple groups match against casebase

- **WHEN** a cluster task matches multiple exception groups against the same casebase
- **THEN** the task does not re-read each case file independently for each group

#### Scenario: Empty casebase

- **WHEN** the casebase directory is empty or missing
- **THEN** the cluster task succeeds and returns empty matched case lists

#### Scenario: Malformed case metadata

- **WHEN** a case contains malformed `metadata.yaml`
- **THEN** that case is skipped for matching and the cluster task continues processing other cases

#### Scenario: Metadata-only matching

- **WHEN** a case has valid `metadata.yaml` but missing `case.md`
- **THEN** the case remains eligible for metadata-based matching

---

### Requirement: Embedding-disabled Matching Compatibility

The system MUST match historical cases without requiring embeddings or vector indexes.

#### Scenario: Embeddings disabled

- **WHEN** embedding or vector retrieval is disabled
- **THEN** exception cluster matching uses local metadata, keywords, exception classes, key phrases, components, tags, fault modes, and optional BM25 when available

---

### Requirement: Post-scan Phase Observability

The system MUST expose post-scan phase evidence for exception aggregation, historical case matching, and cache/result writing.

#### Scenario: Successful cluster task

- **WHEN** a cluster task completes successfully
- **THEN** task output includes timing or metric evidence for aggregation, case matching, and cache/result writing phases

#### Scenario: Matching phase failure

- **WHEN** historical case matching fails after exception aggregation succeeds
- **THEN** progress output records a safe failure reason or degraded matching state without leaving the task indefinitely in a scanning or matching status

---

### Requirement: File-based Storage Compatibility

The system MUST preserve `case.md` and `metadata.yaml` as durable case truth and MUST treat any generated match index as a rebuildable cache.

#### Scenario: Rebuildable index unavailable

- **WHEN** a rebuildable fulltext or BM25 index is missing
- **THEN** exception cluster matching still works by reading the file-backed casebase

#### Scenario: Metrics output written

- **WHEN** post-scan metrics are written to `progress.json` or `data/output/{task_id}/artifacts/performance-metrics.json`
- **THEN** the metrics are task output evidence and may be overwritten on task rerun
