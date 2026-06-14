"""Thread dump detection and parsing hook for analysis pipelines.

Scans a file list with streaming reads, detects JVM thread dump blocks
via a state machine, parses them with thread_stack_parser, and writes
artifacts via thread_artifact.
"""

from __future__ import annotations

import hashlib
import json
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
