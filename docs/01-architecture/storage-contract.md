# Storage Contract

## Principle

The file system is the source of truth.

No mandatory external database is allowed.

## Analysis Task Output

```text
data/output/{task_id}/
├── task.yaml
├── progress.json
├── summary.html
├── evidence-pack.md
├── key-logs.txt
├── case-draft.md
├── case-metadata-draft.yaml
├── retrieval-query.json
├── thread-stack-summary.md          # NEW: human-readable thread summary
└── artifacts/
    ├── timeline.json
    ├── raw-samples.jsonl
    └── thread-stack-results.jsonl   # NEW: machine-readable thread results
```

### thread-stack-results.jsonl

One JSON object per parsed thread block. Each line contains:

```json
{
  "thread_ref": "thread:<task_id>:<index>:<name_hash8>",
  "thread_name": "http-nio-8080-exec-1",
  "thread_state": "WAITING",
  "parse_status": "FULL",
  "frame_count": 8,
  "lock_count": 1,
  "frames_summary": ["com.demo.Service.process", "com.demo.Controller.handle"],
  "raw_text": "..."
}
```

- ``thread_ref``: stable opaque reference for downstream resolution. Encodes task scope and a name-derived hash.
- ``parse_status``: one of ``FULL``, ``PARTIAL``, ``RAW``.
- ``raw_text``: complete raw thread dump block for this thread.
- Rebuildable from source logs and parser output. Overwritten on task rerun.

### thread-stack-summary.md

Human-readable markdown summary of parsed threads. Contains a table of thread names, states, parse statuses, and frame counts. Used for UI/debugging display.

## task.yaml

Required fields:

```yaml
task_id: task-20260516-100103
source_type: SERVER_DIRECTORY
source_path: /data/diagnose/input/DTS-001
mode: STANDARD
status: SUCCESS

created_at: "2026-05-16 10:01:03"
started_at: "2026-05-16 10:01:04"
finished_at: "2026-05-16 10:05:22"

total_files: 28
processed_files: 28
total_bytes: 7340032000
processed_bytes: 7340032000

error_count: 1203
warn_count: 3892

outputs:
  summary: summary.html
  evidence_pack: evidence-pack.md
  key_logs: key-logs.txt
  case_draft: case-draft.md
```

## progress.json

Required fields:

```json
{
  "status": "RUNNING",
  "processed_files": 12,
  "total_files": 28,
  "processed_bytes": 2147483648,
  "total_bytes": 7340032000,
  "message": "analyzing app.log"
}
```

## Fault Case

```text
data/cases/{case_id}_{slug}/
├── case.md
├── metadata.yaml
├── evidence-pack.md
├── key-logs.txt
├── ai-diagnosis.md
├── review.md
├── actions.md
└── artifacts/
```

## metadata.yaml Required Fields

```yaml
case_id: CASE-20260516-001
title: Redis连接池耗尽导致任务失败
slug: redis-pool-exhausted
source_type: auto
status: archived
confidence: confirmed
tags: []
components: []
fault_modes: []
exception_classes: []
key_phrases: []
```

## Indexes

Indexes are rebuildable caches.

Allowed index files:

```text
data/cases/index.yaml
data/indexes/fulltext/index.jsonl
data/indexes/bm25/corpus.jsonl
data/indexes/lancedb/
```

Indexes must not be treated as durable truth.
