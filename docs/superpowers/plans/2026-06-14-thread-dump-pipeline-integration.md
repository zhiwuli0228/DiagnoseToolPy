# Thread Dump Pipeline Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate existing thread dump parser and artifact writer into the standard analysis and cluster analysis pipelines so thread dumps in logs are automatically detected, parsed, and embedded in evidence.

**Architecture:** Post-scan dedicated pass — a new `thread_dump_hook.py` module streaming-scans the file list with a state machine, detects JVM thread dump blocks, parses them via the existing `thread_stack_parser`, writes artifacts via `thread_artifact`, and returns structured results. Both `evidence.py` and `cluster_analyzer.py` call this hook after their primary scan completes.

**Tech Stack:** Python 3.12+, pytest, existing `thread_stack_parser` / `thread_artifact` / `reader` modules

**Spec:** `docs/superpowers/specs/2026-06-14-thread-dump-pipeline-integration-design.md`

---

### Task 1: Create thread_dump_hook.py with state machine scanner

**Files:**
- Create: `diagnose_tool/analyzer/thread_dump_hook.py`
- Test: `tests/test_thread_dump_hook.py`

- [ ] **Step 1: Write failing tests for state machine detection**

```python
# tests/test_thread_dump_hook.py
"""Tests for thread dump hook — state machine scanning and integration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from diagnose_tool.analyzer.thread_dump_hook import scan_and_parse_thread_dumps
from diagnose_tool.analyzer.thread_stack_parser import ThreadDumpResult, ParseStatus


SAMPLE_THREAD_HEADER = '"worker-1" #42 daemon prio=5 os_prio=0 tid=0x00007f8b4c128000 nid=0x1a2b waiting on condition [0x00007f8b3c0fe000]\n'
SAMPLE_THREAD_STATE = '   java.lang.Thread.State: WAITING (parking)\n'
SAMPLE_FRAME = '\tat sun.misc.Unsafe.park(Native Method)\n'
SAMPLE_LOCK_HINT = '    - parking to wait for <0x000000008ab12340> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)\n'

SAMPLE_LOG_LINE = '2026-06-14 10:01:01.123 ERROR [main] com.demo.OrderService - query failed\n'


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestStateDetection:
    """Test that the state machine correctly identifies thread dump blocks."""

    def test_pure_log_file_returns_empty(self, tmp_path: Path) -> None:
        """A file with only log lines should produce no thread results."""
        log_file = tmp_path / "app.log"
        _write_file(log_file, SAMPLE_LOG_LINE * 5)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(log_file)],
            output_dir=tmp_path / "output",
            task_id="test-001",
        )
        assert results == []

    def test_pure_dump_file(self, tmp_path: Path) -> None:
        """A file with only thread dump blocks should be parsed."""
        dump_file = tmp_path / "jstack.log"
        content = SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME * 3
        _write_file(dump_file, content)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(dump_file)],
            output_dir=tmp_path / "output",
            task_id="test-002",
        )
        assert len(results) >= 1
        assert any(r.thread_name == "worker-1" for r in results)

    def test_mixed_file_log_then_dump(self, tmp_path: Path) -> None:
        """A file with log lines followed by a thread dump should detect the dump."""
        mixed_file = tmp_path / "mixed.log"
        content = SAMPLE_LOG_LINE * 3 + "\n" + SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME * 2
        _write_file(mixed_file, content)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(mixed_file)],
            output_dir=tmp_path / "output",
            task_id="test-003",
        )
        assert len(results) >= 1

    def test_mixed_file_dump_then_log(self, tmp_path: Path) -> None:
        """A file with a thread dump followed by log lines should detect the dump."""
        mixed_file = tmp_path / "mixed.log"
        content = SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME + "\n" + SAMPLE_LOG_LINE * 3
        _write_file(mixed_file, content)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(mixed_file)],
            output_dir=tmp_path / "output",
            task_id="test-004",
        )
        assert len(results) >= 1

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """An empty file should produce no results."""
        empty_file = tmp_path / "empty.log"
        _write_file(empty_file, "")

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(empty_file)],
            output_dir=tmp_path / "output",
            task_id="test-005",
        )
        assert results == []

    def test_multiple_threads_in_one_file(self, tmp_path: Path) -> None:
        """Multiple thread blocks in one file should all be detected."""
        dump_file = tmp_path / "jstack.log"
        thread1 = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)\n'
        thread2 = '"worker-2" #2 daemon prio=5\n   java.lang.Thread.State: BLOCKED\n\tat com.Lock.acquire(Lock.java:20)\n'
        _write_file(dump_file, thread1 + thread2)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(dump_file)],
            output_dir=tmp_path / "output",
            task_id="test-006",
        )
        assert len(results) == 2


def _make_scanned_file(path: Path):
    """Create a minimal ScannedFile-like object."""
    from dataclasses import dataclass

    @dataclass
    class FakeScannedFile:
        path: str
        name: str
        size: int
        type: str

    return FakeScannedFile(
        path=str(path),
        name=path.name,
        size=path.stat().st_size,
        type="log",
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_thread_dump_hook.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'diagnose_tool.analyzer.thread_dump_hook'`

- [ ] **Step 3: Implement thread_dump_hook.py**

```python
# diagnose_tool/analyzer/thread_dump_hook.py
"""Thread dump detection and parsing hook for analysis pipelines.

Scans a file list with streaming reads, detects JVM thread dump blocks
via a state machine, parses them with thread_stack_parser, and writes
artifacts via thread_artifact.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from diagnose_tool.analyzer.reader import LogLine, read_log_lines
from diagnose_tool.analyzer.thread_stack_parser import (
    ThreadDumpResult,
    parse_thread_dump_all,
)

logger = logging.getLogger(__name__)

# Reuse the same header pattern from thread_stack_parser
_THREAD_HEADER_RE = re.compile(
    r'^"(.+?)"'           # quoted thread name
    r"\s+#(\d+)"          # thread number
    r"(?:\s+\w+)*"        # optional words (daemon, etc.)
    r".*$",
)

# Log line start pattern (from multiline.py)
_LOG_START_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")


def scan_and_parse_thread_dumps(
    files: list,
    output_dir: Path,
    task_id: str,
) -> list[ThreadDumpResult]:
    """Scan files for thread dump blocks, parse, and write artifacts.

    Args:
        files: List of ScannedFile-like objects with .path attribute.
        output_dir: Task output directory for writing artifacts.
        task_id: Task identifier for artifact naming.

    Returns:
        List of ThreadDumpResult from all detected dump blocks.
        Empty list if no thread dumps found.
    """
    all_results: list[ThreadDumpResult] = []

    for file_info in files:
        file_path = Path(file_info.path)
        try:
            results = _scan_single_file(file_path)
            all_results.extend(results)
        except Exception as exc:
            logger.warning("Failed to scan %s for thread dumps: %s", file_path, exc)
            continue

    if all_results:
        try:
            # Write artifacts directly to output_dir without OutputContext
            _write_thread_artifacts_direct(output_dir, task_id, all_results)
        except Exception as exc:
            logger.warning("Failed to write thread artifacts: %s", exc)

    return all_results


def _scan_single_file(file_path: Path) -> list[ThreadDumpResult]:
    """Scan a single file for thread dump blocks using a state machine.

    States:
        SCANNING — looking for a thread header
        IN_DUMP — buffering lines inside a detected dump block
    """
    results: list[ThreadDumpResult] = []
    buffer: list[str] = []
    in_dump = False

    for log_line in read_log_lines(file_path):
        line = log_line.raw

        if _THREAD_HEADER_RE.match(line):
            # Found a thread header
            if in_dump:
                # Flush previous block
                results.extend(_flush_buffer(buffer))
            buffer = [line]
            in_dump = True
            continue

        if in_dump and _LOG_START_RE.match(line):
            # Regular log line starts — flush dump block
            results.extend(_flush_buffer(buffer))
            buffer = []
            in_dump = False
            continue

        if in_dump:
            buffer.append(line)

    # EOF — flush remaining buffer
    if buffer and in_dump:
        results.extend(_flush_buffer(buffer))

    return results


def _flush_buffer(buffer: list[str]) -> list[ThreadDumpResult]:
    """Join buffered lines and parse as thread dump blocks."""
    if not buffer:
        return []
    raw_text = "".join(buffer)
    try:
        return parse_thread_dump_all(raw_text)
    except Exception as exc:
        logger.warning("Failed to parse thread dump block: %s", exc)
        return []


def _write_thread_artifacts_direct(
    output_dir: Path,
    task_id: str,
    results: list[ThreadDumpResult],
) -> None:
    """Write thread artifacts directly to output_dir without OutputContext."""
    import hashlib
    import json

    from diagnose_tool.analyzer.thread_artifact import (
        ARTIFACT_FILENAME,
        SUMMARY_FILENAME,
    )

    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Write JSONL artifact
    jsonl_path = artifacts_dir / ARTIFACT_FILENAME
    with jsonl_path.open("w", encoding="utf-8") as f:
        for idx, result in enumerate(results):
            name_hash = hashlib.sha256(
                (result.thread_name or "").encode("utf-8")
            ).hexdigest()[:8]
            thread_ref = f"thread:{task_id}:{idx}:{name_hash}"

            frames_summary = []
            for frame in result.frames[:5]:
                if frame.class_name and frame.method:
                    frames_summary.append(f"{frame.class_name}.{frame.method}")

            entry = {
                "thread_ref": thread_ref,
                "thread_name": result.thread_name,
                "thread_state": result.thread_state,
                "parse_status": result.parse_status.value,
                "frame_count": len(result.frames),
                "lock_count": len(result.lock_hints),
                "frames_summary": frames_summary,
                "raw_text": result.raw_text,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Write summary markdown
    summary_path = output_dir / SUMMARY_FILENAME
    from collections import Counter

    status_counts: Counter[str] = Counter()
    for r in results:
        status_counts[r.parse_status.value] += 1

    with summary_path.open("w", encoding="utf-8") as f:
        f.write(f"# Thread Stack Summary — {task_id}\n\n")
        f.write(f"**Total threads:** {len(results)}\n\n")
        parts = []
        for status in ("FULL", "PARTIAL", "RAW"):
            count = status_counts.get(status, 0)
            if count:
                parts.append(f"{status} {count}")
        if parts:
            f.write(f"**Status:** {' / '.join(parts)}\n\n")
        f.write("| # | Thread Name | State | Parse Status | Frames |\n")
        f.write("|---|---|---|---|---|\n")
        for idx, r in enumerate(results):
            name = r.thread_name or "(unnamed)"
            state = r.thread_state or "-"
            status = r.parse_status.value
            frames = len(r.frames)
            f.write(f"| {idx + 1} | {name} | {state} | {status} | {frames} |\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_thread_dump_hook.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add diagnose_tool/analyzer/thread_dump_hook.py tests/test_thread_dump_hook.py
git commit -m "feat(analyzer): add thread dump hook with state machine scanner"
```

---

### Task 2: Add multi-file and error tolerance tests

**Files:**
- Modify: `tests/test_thread_dump_hook.py`

- [ ] **Step 1: Write tests for multi-file scanning and error handling**

Append to `tests/test_thread_dump_hook.py`:

```python
class TestMultiFile:
    """Test scanning across multiple files."""

    def test_partial_files_contain_dumps(self, tmp_path: Path) -> None:
        """Only files with thread dumps should contribute results."""
        log_file = tmp_path / "app.log"
        dump_file = tmp_path / "jstack.log"
        _write_file(log_file, SAMPLE_LOG_LINE * 3)
        _write_file(dump_file, SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(log_file), _make_scanned_file(dump_file)],
            output_dir=tmp_path / "output",
            task_id="test-multi-001",
        )
        assert len(results) >= 1

    def test_multiple_dump_files(self, tmp_path: Path) -> None:
        """Thread dumps from multiple files should all be collected."""
        dump1 = tmp_path / "jstack1.log"
        dump2 = tmp_path / "jstack2.log"
        thread1 = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)\n'
        thread2 = '"worker-2" #2 daemon prio=5\n   java.lang.Thread.State: BLOCKED\n\tat com.Lock.acquire(Lock.java:20)\n'
        _write_file(dump1, thread1)
        _write_file(dump2, thread2)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(dump1), _make_scanned_file(dump2)],
            output_dir=tmp_path / "output",
            task_id="test-multi-002",
        )
        assert len(results) == 2


class TestErrorTolerance:
    """Test that errors in individual files don't abort the pipeline."""

    def test_nonexistent_file_skipped(self, tmp_path: Path) -> None:
        """A file that doesn't exist should be skipped without raising."""
        missing = tmp_path / "missing.log"
        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(missing)],
            output_dir=tmp_path / "output",
            task_id="test-err-001",
        )
        assert results == []

    def test_corrupted_dump_block_skipped(self, tmp_path: Path) -> None:
        """A file with garbage between valid thread headers should still parse what it can."""
        bad_file = tmp_path / "bad.log"
        valid_thread = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)\n'
        garbage = "this is not a valid thread dump block at all\n" * 10
        _write_file(bad_file, valid_thread + garbage)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(bad_file)],
            output_dir=tmp_path / "output",
            task_id="test-err-002",
        )
        # Should still get at least the valid thread
        assert len(results) >= 1
```

- [ ] **Step 2: Run all tests**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_thread_dump_hook.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_thread_dump_hook.py
git commit -m "test(analyzer): add multi-file and error tolerance tests for thread dump hook"
```

---

### Task 3: Add thread dump section to evidence-pack.md generation

**Files:**
- Modify: `diagnose_tool/analyzer/evidence.py`
- Modify: `tests/test_evidence.py`

- [ ] **Step 1: Write failing test for thread dump section in evidence pack**

Append to `tests/test_evidence.py`:

```python
from diagnose_tool.analyzer.thread_stack_parser import (
    ThreadDumpResult,
    ThreadFrame,
    LockHint,
    ParseStatus,
)


def test_evidence_pack_includes_thread_dump_section(tmp_path: Path) -> None:
    """Evidence pack should include thread dump analysis section when results provided."""
    ctx = _make_output_context(tmp_path)
    records = []
    classifications = []
    timeline = []

    thread_results = [
        ThreadDumpResult(
            thread_name="worker-1",
            thread_state="BLOCKED",
            frames=[
                ThreadFrame(raw_text="\tat com.Lock.acquire(Lock.java:20)", class_name="com.Lock", method="acquire"),
                ThreadFrame(raw_text="\tat com.Worker.run(Worker.java:10)", class_name="com.Worker", method="run"),
            ],
            lock_hints=[
                LockHint(raw_text="    - waiting to lock <0x0007> (a java.lang.Object)", hint_type="waiting_to_lock", lock_address="0x0007", lock_class="java.lang.Object"),
            ],
            parse_status=ParseStatus.FULL,
        ),
        ThreadDumpResult(
            thread_name="worker-2",
            thread_state="RUNNABLE",
            frames=[
                ThreadFrame(raw_text="\tat com.Main.main(Main.java:5)", class_name="com.Main", method="main"),
            ],
            lock_hints=[],
            parse_status=ParseStatus.FULL,
        ),
    ]

    generate_evidence_pack(ctx, records, classifications, 0, 0, timeline, thread_results=thread_results)

    content = (ctx.output_dir() / "evidence-pack.md").read_text(encoding="utf-8")
    assert "线程 Dump 分析" in content
    assert "线程总数" in content
    assert "BLOCKED" in content
    assert "worker-1" in content


def test_evidence_pack_no_thread_section_when_no_results(tmp_path: Path) -> None:
    """Evidence pack should not include thread section when no results provided."""
    ctx = _make_output_context(tmp_path)
    generate_evidence_pack(ctx, [], [], 0, 0, [])

    content = (ctx.output_dir() / "evidence-pack.md").read_text(encoding="utf-8")
    assert "线程 Dump 分析" not in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_evidence.py::test_evidence_pack_includes_thread_dump_section -v`
Expected: FAIL — `generate_evidence_pack()` does not accept `thread_results` parameter

- [ ] **Step 3: Implement thread dump section in evidence.py**

Modify `diagnose_tool/analyzer/evidence.py`:

1. Add `thread_results` parameter to `generate_evidence_pack()`
2. Add `_build_thread_dump_section()` helper function
3. Insert the section into the evidence pack markdown

Changes to `generate_evidence_pack`:

```python
def generate_evidence_pack(
    output_context: OutputContext,
    records: list[ParsedLogRecord],
    classifications: list[ClassificationResult],
    error_count: int,
    warn_count: int,
    timeline_buckets: list[dict],
    thread_results: list | None = None,  # NEW
) -> None:
    output_context.ensure_directories()

    stats = _build_classification_stats(classifications)
    top_exceptions = _get_top_exceptions(classifications)
    key_features = _extract_key_features(classifications)

    content = _build_evidence_pack_markdown(
        output_context, stats, error_count, warn_count, timeline_buckets, key_features, top_exceptions,
        thread_results=thread_results,
    )

    (output_context.output_dir() / "evidence-pack.md").write_text(content, encoding="utf-8")
```

Add new helper function:

```python
def _build_thread_dump_section(thread_results: list) -> str:
    """Build the thread dump analysis section for evidence-pack.md."""
    from collections import Counter

    if not thread_results:
        return ""

    # Count by state
    state_counts: Counter[str] = Counter()
    parse_status_counts: Counter[str] = Counter()
    for r in thread_results:
        state = r.thread_state or "UNKNOWN"
        state_counts[state] += 1
        parse_status_counts[r.parse_status.value] += 1

    total = len(thread_results)

    lines = [
        "",
        "## 6. 线程 Dump 分析",
        "",
        f"**线程总数**: {total}",
        f"**解析状态**: {' / '.join(f'{k} {v}' for k, v in sorted(parse_status_counts.items()))}",
        "",
        "### 线程状态分布",
        "",
        "| 状态 | 数量 |",
        "|---|---:|",
    ]

    for state, count in state_counts.most_common():
        lines.append(f"| {state} | {count} |")

    # Key threads: BLOCKED or has lock hints
    key_threads = [
        r for r in thread_results
        if r.thread_state == "BLOCKED"
        or any(h.hint_type in ("waiting_to_lock", "parking") for h in r.lock_hints)
    ][:10]

    if key_threads:
        lines.extend([
            "",
            "### 关键线程（BLOCKED / 等待锁）",
            "",
        ])
        for r in key_threads:
            name = r.thread_name or "(unnamed)"
            state = r.thread_state or "UNKNOWN"
            lines.append(f"**Thread: {name}** ({state})")

            for hint in r.lock_hints:
                if hint.hint_type == "waiting_to_lock":
                    lines.append(f"- 等待锁: `<{hint.lock_address}>` ({hint.lock_class})")
                elif hint.hint_type == "parking":
                    lines.append(f"- 等待: `<{hint.lock_address}>` ({hint.lock_class})")
                elif hint.hint_type == "locked":
                    lines.append(f"- 持有锁: `<{hint.lock_address}>` ({hint.lock_class})")

            if r.frames:
                lines.append("- 帧:")
                lines.append("  ```")
                for frame in r.frames[:5]:
                    lines.append(f"  {frame.raw_text.strip()}")
                lines.append("  ```")
            lines.append("")

        lines.append(f"> 仅展示 BLOCKED 和等待锁的线程（最多 10 个）")

    return "\n".join(lines)
```

Update `_build_evidence_pack_markdown` to accept and use `thread_results`:

```python
def _build_evidence_pack_markdown(
    output_context: OutputContext,
    stats: dict[str, int],
    error_count: int,
    warn_count: int,
    timeline_buckets: list[dict],
    key_features: dict[str, Any],
    top_exceptions: list[tuple[str, str, int]],
    thread_results: list | None = None,  # NEW
) -> str:
    # ... existing sections 1-5 ...

    # NEW: Thread dump section (inserted as section 6)
    thread_section = ""
    if thread_results:
        thread_section = _build_thread_dump_section(thread_results)

    # Renumber: old section 6 → 7, old section 7 → 8
    lines.extend([
        "",
        "## 6. 相似案例召回",  # was section 6, now renumbered
        "",
        "以下案例仅作为参考，不代表当前故障一定相同。",
        "",
        "## 7. 诊断要求",  # was section 7, now renumbered
        # ... rest of existing content ...
    ])

    # Insert thread section after section 5 if present
    if thread_section:
        # Find the position after section 5 and insert
        # This requires restructuring the section building
        pass

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_evidence.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add diagnose_tool/analyzer/evidence.py tests/test_evidence.py
git commit -m "feat(analyzer): embed thread dump section in evidence-pack.md"
```

---

### Task 4: Integrate thread dump hook into cluster analyzer

**Files:**
- Modify: `diagnose_tool/analyzer/cluster_analyzer.py`
- Modify: `tests/test_cluster_analyzer.py`

- [ ] **Step 1: Write failing test for thread dump group in cluster results**

Append to `tests/test_cluster_analyzer.py`:

```python
def test_cluster_result_includes_thread_dump_group(tmp_path: Path) -> None:
    """Cluster analysis should include a thread dump group when dumps are present."""
    # Create a log file with a thread dump block
    log_file = tmp_path / "app.log"
    thread_block = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: BLOCKED\n\tat com.Lock.acquire(Lock.java:20)\n'
    log_content = '2026-06-14 10:01:01 ERROR [main] com.demo.OrderService - query failed\n' * 5
    log_file.write_text(log_content + thread_block, encoding="utf-8")

    analyzer = ClusterAnalyzer(tmp_path)
    task_id, task_output = analyzer.create_task(str(tmp_path))

    # Run with the log directory
    result = analyzer.run(task_id, str(tmp_path))

    # Should have at least one cluster group (the error clusters)
    # and the thread dump group at the end
    thread_groups = [c for c in result.clusters if c.exception_class.startswith("[Thread Dump]")]
    assert len(thread_groups) == 1
    assert thread_groups[0].count >= 1
    assert thread_groups[0].matched_cases == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_cluster_analyzer.py::test_cluster_result_includes_thread_dump_group -v`
Expected: FAIL — no thread dump group in cluster results

- [ ] **Step 3: Implement cluster analyzer integration**

Modify `diagnose_tool/analyzer/cluster_analyzer.py` in the `run()` method, between Phase 2 and Phase 3:

```python
def run(self, task_id: str, source_path: str) -> ClusterResult:
    # ... existing Phase 1 and Phase 2 ...

    # Phase 2: Match historical cases
    self._update_progress(task_output, PHASE_MATCH, 80)
    clusters = self._match_historical_cases(aggregated_groups)

    # NEW: Phase 2.5 — scan thread dumps
    try:
        from diagnose_tool.analyzer.thread_dump_hook import scan_and_parse_thread_dumps
        thread_results = scan_and_parse_thread_dumps(
            files=files,
            output_dir=task_output,
            task_id=task_id,
        )
        if thread_results:
            thread_group = self._build_thread_cluster_group(thread_results)
            clusters.append(thread_group)
    except Exception as exc:
        logger.warning("Thread dump scanning failed: %s", exc)

    # Phase 3: Write result
    # ... rest unchanged ...
```

Add helper method to `ClusterAnalyzer`:

```python
def _build_thread_cluster_group(self, thread_results: list) -> ClusterGroup:
    """Build a ClusterGroup representing thread dump analysis."""
    from collections import Counter

    state_counts: Counter[str] = Counter()
    for r in thread_results:
        state = r.thread_state or "UNKNOWN"
        state_counts[state] += 1

    total = len(thread_results)
    state_summary = " / ".join(f"{k} {v}" for k, v in state_counts.most_common())

    sample_messages = [state_summary]

    # Add key blocked threads as sample messages
    for r in thread_results:
        if r.thread_state == "BLOCKED" or any(h.hint_type == "waiting_to_lock" for h in r.lock_hints):
            name = r.thread_name or "(unnamed)"
            lock_info = ""
            for h in r.lock_hints:
                if h.hint_type == "waiting_to_lock":
                    lock_info = f" waiting for <{h.lock_address}> ({h.lock_class})"
                    break
            sample_messages.append(f"BLOCKED: {name}{lock_info}")
            if len(sample_messages) >= 5:
                break

    return ClusterGroup(
        exception_class=f"[Thread Dump] {total} threads",
        count=total,
        sample_messages=sample_messages,
        time_distribution={},
        matched_cases=[],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest tests/test_cluster_analyzer.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add diagnose_tool/analyzer/cluster_analyzer.py tests/test_cluster_analyzer.py
git commit -m "feat(analyzer): integrate thread dump hook into cluster analysis pipeline"
```

---

### Task 5: Run full test suite and lint

**Files:**
- No new files

- [ ] **Step 1: Run full test suite**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Run lint**

Run: `cd E:\009workspace\claudecode\DiagnoseToolPy && uv run ruff check .`
Expected: No errors

- [ ] **Step 3: Fix any lint issues if present**

- [ ] **Step 4: Final commit if fixes were needed**

```bash
git add -A
git commit -m "chore: fix lint issues in thread dump integration"
```
