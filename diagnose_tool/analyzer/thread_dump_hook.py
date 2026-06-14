"""Thread dump detection and parsing hook for analysis pipelines.

Scans a file list with streaming reads, detects JVM thread dump blocks
via a state machine, parses them with thread_stack_parser, and writes
artifacts via thread_artifact.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from diagnose_tool.analyzer.multiline import LOG_START_RE as _LOG_START_RE
from diagnose_tool.analyzer.reader import read_log_lines
from diagnose_tool.analyzer.thread_artifact import write_thread_artifacts
from diagnose_tool.analyzer.thread_stack_parser import (
    _THREAD_HEADER_RE,
    ThreadDumpResult,
    parse_thread_dump_all,
)

logger = logging.getLogger(__name__)


class _DirectOutputContext:
    """Minimal OutputContext-like object that writes directly to a given directory."""

    def __init__(self, output_dir: Path, task_id: str):
        self._output_dir = output_dir
        self.task_id = task_id

    def output_dir(self) -> Path:
        return self._output_dir

    def artifacts_dir(self) -> Path:
        return self._output_dir / "artifacts"

    def ensure_directories(self) -> None:
        self.output_dir().mkdir(parents=True, exist_ok=True)
        self.artifacts_dir().mkdir(parents=True, exist_ok=True)


def scan_and_parse_thread_dumps(
    files: list[Any],
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
            ctx = _DirectOutputContext(output_dir, task_id)
            write_thread_artifacts(ctx, all_results)
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
    raw_text = "\n".join(buffer)
    try:
        return parse_thread_dump_all(raw_text)
    except Exception as exc:
        logger.warning("Failed to parse thread dump block: %s", exc)
        return []


