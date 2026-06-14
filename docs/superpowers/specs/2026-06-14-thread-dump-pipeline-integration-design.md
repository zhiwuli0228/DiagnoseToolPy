# Thread Dump Pipeline Integration Design

## Purpose

Integrate the existing thread dump parser (`thread_stack_parser.py`) and artifact writer (`thread_artifact.py`) into the main analysis and cluster analysis pipelines. Currently these modules are implemented and tested but never called from the production analysis flow — thread dumps in logs are silently ignored.

## Requirements

1. **Standard analysis flow** — scan files for thread dump blocks, parse them, embed summary + key thread frames into `evidence-pack.md`.
2. **Cluster analysis flow** — same scanning, but present thread dumps as an independent `ClusterGroup` appended to cluster results.
3. **Auto-detection** — no configuration needed; thread dumps are identified by the existing `_THREAD_HEADER_RE` pattern (`"thread-name" #42 daemon ...`).
4. **Evidence format** — summary (thread state distribution) + key threads (BLOCKED / waiting for lock, max 10, max 5 frames each).
5. **Error tolerance** — single dump block or file failures log warnings and skip, never abort the pipeline.

## Non-Goals

- Thread dump historical case matching (thread state is not matchable across cases).
- New configuration options or feature flags.
- Changes to `diagnosis.py` prompt logic (evidence-pack already carries the info).
- Frontend changes (existing `ThreadResultsPanel` and cluster card rendering already handle the data shape).

## Architecture

### Integration Strategy: Post-Scan Dedicated Pass (Approach B)

The main scan/classify/aggregate logic is unchanged. After the primary scan completes, a dedicated thread dump pass reads the same file list with streaming, detects thread dump blocks via a state machine, and feeds them to the existing parser.

```
Standard:  scan → classify → [NEW: thread dump pass] → update evidence-pack → diagnosis
Cluster:   scan → aggregate → match → [NEW: thread dump pass] → append thread group → write result
```

### New Module

**`analyzer/thread_dump_hook.py`** — single entry point for both flows.

### Existing Module Changes

| Module | Change |
|---|---|
| `analyzer/evidence.py` | `generate_evidence_pack()` accepts optional `thread_results: list[ThreadDumpResult]`; inserts "线程 Dump 分析" section |
| `analyzer/cluster_analyzer.py` | `run()` calls thread dump hook between Phase 2 and Phase 3; appends thread ClusterGroup |

### No Changes Required

| Module | Reason |
|---|---|
| `analyzer/diagnosis.py` | Evidence-pack already contains thread dump info |
| `analyzer/thread_stack_parser.py` | Already complete |
| `analyzer/thread_artifact.py` | Already complete |
| `api/routes_diagnosis.py` | `GET /thread-results/{task_id}` already works |

## Data Flow

### thread_dump_hook.scan_and_parse_thread_dumps()

```
Input:  files (list[ScannedFile]), output_context (OutputContext)
Output: list[ThreadDumpResult]

1. For each file:
   a. Streaming read via reader.read_log_lines() or read_log_lines_from_zip_streaming()
   b. State machine detects thread dump blocks
   c. Buffered blocks sent to parse_thread_dump_all()
   d. Results accumulated
2. write_thread_artifacts(output_context, all_results)
3. Return all_results
```

### State Machine

```
State: SCANNING → IN_DUMP → SCANNING

SCANNING:
  line matches _THREAD_HEADER_RE → buffer = [line], state = IN_DUMP
  other line → skip

IN_DUMP:
  line matches _THREAD_HEADER_RE → flush buffer to parser, buffer = [line]
  line matches LOG_START_RE → flush buffer to parser, state = SCANNING
  EOF → flush buffer to parser
  other line → append to buffer
```

### Flushing

When a buffer is flushed:
1. Join buffered lines into raw text
2. Call `parse_thread_dump_all(raw_text)` → `list[ThreadDumpResult]`
3. Append results to accumulator

## Evidence-Pack Embedding

### Section Format

Inserted after "5. Top 关键异常样例", before "6. 相似案例召回" (which renumbers to 7).

```markdown
## 6. 线程 Dump 分析

**线程总数**: 42
**解析状态**: FULL 35 / PARTIAL 5 / RAW 2

### 线程状态分布

| 状态 | 数量 |
|---|---:|
| RUNNABLE | 15 |
| WAITING | 12 |
| BLOCKED | 8 |
| TIMED_WAITING | 7 |

### 关键线程（BLOCKED / 等待锁）

**Thread: worker-1** (BLOCKED)
- 等待锁: `<0x0007f8b4>` (java.util.concurrent.LinkedBlockingQueue)
- 帧:
  ```
  at com.demo.QueueConsumer.take(QueueConsumer.java:42)
  at com.demo.Worker.run(Worker.java:18)
  ```

> 仅展示 BLOCKED 和等待锁的线程（最多 10 个）
```

### Filtering Rules

- **Summary**: count all threads by state
- **Key threads**: only BLOCKED or threads with `waiting_to_lock` / `parking` lock hints
- **Frame limit**: top 5 frames per key thread
- **Thread limit**: max 10 key threads

### Code Changes in evidence.py

```python
def generate_evidence_pack(
    output_context,
    records,
    classifications,
    error_count,
    warn_count,
    timeline_buckets,
    thread_results=None,  # NEW optional parameter
):
    ...
    if thread_results:
        thread_section = _build_thread_dump_section(thread_results)
        # Insert after section 5, renumber sections 6→7, 7→8
```

## Cluster Integration

### Integration Point

In `ClusterAnalyzer.run()`, between Phase 2 (match historical cases) and Phase 3 (write result):

```python
# Phase 2: match historical cases
clusters = self._match_historical_cases(aggregated_groups)

# NEW: Phase 2.5 — scan thread dumps
from diagnose_tool.analyzer.thread_dump_hook import scan_and_parse_thread_dumps
thread_results = scan_and_parse_thread_dumps(files, output_context)
if thread_results:
    thread_group = self._build_thread_cluster_group(thread_results)
    clusters.append(thread_group)

# Phase 3: write result
self._write_result(task_output, ClusterResult(...))
```

### Thread ClusterGroup Shape

```python
ClusterGroup(
    exception_class="[Thread Dump] 42 threads",
    count=42,
    sample_messages=[
        "RUNNABLE 15 / WAITING 12 / BLOCKED 8 / TIMED_WAITING 7",
        "BLOCKED: worker-1 waiting for <0x0007f8b4> (LinkedBlockingQueue)",
        "BLOCKED: worker-2 holding <0x0007f8b4> (LinkedBlockingQueue)",
    ],
    time_distribution={},
    matched_cases=[],
)
```

## Error Handling

| Scenario | Behavior |
|---|---|
| Single dump block parse failure | `logger.warning()`, skip block, continue |
| Single file I/O failure | `logger.warning()`, skip file, continue |
| No thread dumps found | evidence-pack omits thread section; cluster has no thread group |
| `write_thread_artifacts()` failure | `logger.warning()`, hook still returns results |

All errors are best-effort — the main pipeline never aborts due to thread dump issues.

## Testing

| Test File | Coverage |
|---|---|
| `tests/test_thread_dump_hook.py` | State machine: pure log file, pure dump file, mixed file, empty file |
| `tests/test_thread_dump_hook.py` | Multi-file: partial files contain dumps |
| `tests/test_thread_dump_hook.py` | ZIP streaming with dump detection |
| `tests/test_thread_dump_hook.py` | Error tolerance: corrupted dump block, I/O failure |
| `tests/test_evidence.py` | evidence-pack thread dump section format and filtering |
| `tests/test_cluster_analyzer.py` | Cluster result contains independent thread dump group |

## File Summary

| File | Action |
|---|---|
| `diagnose_tool/analyzer/thread_dump_hook.py` | **NEW** — unified thread dump scanning hook |
| `diagnose_tool/analyzer/evidence.py` | **MODIFY** — add `thread_results` parameter, insert thread section |
| `diagnose_tool/analyzer/cluster_analyzer.py` | **MODIFY** — call hook, append thread ClusterGroup |
| `tests/test_thread_dump_hook.py` | **NEW** — hook tests |
| `tests/test_evidence.py` | **MODIFY** — thread section tests |
| `tests/test_cluster_analyzer.py` | **MODIFY** — thread group tests |
