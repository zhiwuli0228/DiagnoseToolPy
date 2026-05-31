"""Log content search with filtering by time, thread, keywords, and exclusion."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from diagnose_tool.analyzer.header_parser import parse_log_record
from diagnose_tool.analyzer.reader import read_log_lines
from diagnose_tool.analyzer.scanner import scan_directory
from diagnose_tool.analyzer.multiline import is_continuation_line, is_log_start
from diagnose_tool.core.security import PathValidationError, validate_server_directory
from diagnose_tool.core.config import load_config

logger = logging.getLogger(__name__)

# Stack trace continuation lines start with these patterns
_STACK_LINE_RE = re.compile(r"^\s+at\s+|^\s*\.\.\.\s+\d+\s+more|^\s+Caused by:|^\s+Suppressed:")


def search_log_content(
    path: str,
    time_start: str | None = None,
    time_end: str | None = None,
    thread: str | None = None,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    max_lines: int = 1000,
    include_stack: bool = True,
) -> dict:
    """Search log content with filters.

    Args:
        path: Server directory path to search.
        time_start: ISO timestamp lower bound (inclusive).
        time_end: ISO timestamp upper bound (inclusive).
        thread: Thread name substring to match.
        keywords: All keywords must be present in the line (AND logic).
        exclude_keywords: Any keyword present excludes the line.
        max_lines: Maximum matched lines to return.
        include_stack: Whether to include Java stack trace lines in display output.
            When False, stack trace lines are hidden from raw/message but still
            used for keyword matching.

    Returns:
        dict with matched_count, total_scanned_lines, files_scanned, results.
    """
    config = load_config()
    validated_path = validate_server_directory(path, config.allowed_input_roots)

    keywords = keywords or []
    exclude_keywords = exclude_keywords or []

    scan_result = scan_directory(validated_path)
    files = [f for f in scan_result.files if f.type != "unsupported"]

    results: list[dict] = []
    total_lines = 0
    matched_count = 0

    for scanned_file in files:
        file_path = Path(scanned_file.path)
        try:
            event_buffer: list[dict] = []

            for log_line in read_log_lines(file_path):
                total_lines += 1

                if is_log_start(log_line.raw):
                    if event_buffer:
                        matched_count, truncated = _flush_event_buffer(
                            event_buffer, results,
                            time_start, time_end, thread,
                            keywords, exclude_keywords,
                            matched_count, max_lines,
                            include_stack,
                        )
                        if truncated:
                            return {
                                "matched_count": matched_count,
                                "total_scanned_lines": total_lines,
                                "files_scanned": len(files),
                                "results": results,
                                "truncated": True,
                            }
                        event_buffer = []

                event_buffer.append({
                    "log_line": log_line,
                    "record": parse_log_record(log_line.raw, log_line.file_path, log_line.line_no),
                })

            if event_buffer:
                matched_count, truncated = _flush_event_buffer(
                    event_buffer, results,
                    time_start, time_end, thread,
                    keywords, exclude_keywords,
                    matched_count, max_lines,
                    include_stack,
                )
                if truncated:
                    return {
                        "matched_count": matched_count,
                        "total_scanned_lines": total_lines,
                        "files_scanned": len(files),
                        "results": results,
                        "truncated": True,
                    }

        except Exception as e:
            logger.warning("Failed to read file %s: %s", scanned_file.path, e)
            continue

    return {
        "matched_count": matched_count,
        "total_scanned_lines": total_lines,
        "files_scanned": len(files),
        "results": results,
        "truncated": False,
    }


def _passes_time_filter(record, time_start: str | None, time_end: str | None) -> bool:
    if not time_start and not time_end:
        return True
    if not record.timestamp:
        return False

    ts = record.timestamp
    ts_clean = ts.replace(" ", "T")
    if time_start and ts_clean < time_start:
        return False
    if time_end and ts_clean > time_end:
        return False
    return True


def _passes_thread_filter(record, thread: str) -> bool:
    if not record.thread:
        return False
    return thread.lower() in record.thread.lower()


def _passes_keyword_filter(record, keywords: list[str]) -> bool:
    text = record.raw.lower()
    return all(kw.lower() in text for kw in keywords)


def _has_any_keyword(record, exclude_keywords: list[str]) -> bool:
    text = record.raw.lower()
    return any(kw.lower() in text for kw in exclude_keywords)


def _find_matched_keywords(record, keywords: list[str]) -> list[str]:
    text = record.raw.lower()
    return [kw for kw in keywords if kw.lower() in text]


def _flush_event_buffer(
    event_buffer: list[dict],
    results: list[dict],
    time_start: str | None,
    time_end: str | None,
    thread: str | None,
    keywords: list[str],
    exclude_keywords: list[str],
    matched_count: int,
    max_lines: int,
    include_stack: bool,
) -> tuple[int, bool]:
    """Flush buffered multiline event to results if it passes filters.

    Returns (matched_count, truncated).
    """
    if not event_buffer:
        return matched_count, False

    first = event_buffer[0]
    header_record = first["record"]
    header_line = first["log_line"]

    # Build merged raw text
    raw_lines = [header_line.raw]
    for entry in event_buffer[1:]:
        raw_lines.append(entry["log_line"].raw)
    merged_raw = "\n".join(raw_lines)

    # Apply filters using header's metadata and full merged text
    if not _passes_time_filter(header_record, time_start, time_end):
        return matched_count, False
    if thread and not _passes_thread_filter(header_record, thread):
        return matched_count, False
    if keywords and not _passes_keyword_filter_by_raw(merged_raw, keywords):
        return matched_count, False
    if exclude_keywords and _has_any_keyword_by_raw(merged_raw, exclude_keywords):
        return matched_count, False

    matched_keyword = _find_matched_keywords_by_raw(merged_raw, keywords) if keywords else None

    # Build display raw and message
    if include_stack:
        display_raw = merged_raw
    else:
        # Strip stack trace lines from display
        display_raw = _strip_stack_traces(merged_raw)

    msg = header_record.message if header_record.message is not None else display_raw.split("\n")[0]

    results.append({
        "file_path": header_line.file_path,
        "line_no": header_line.line_no,
        "timestamp": header_record.timestamp or "",
        "level": header_record.level or "",
        "thread": header_record.thread or "",
        "logger": header_record.logger if header_record.logger is not None else "",
        "message": msg if include_stack else _strip_stack_traces(msg) if "\n" in msg else msg,
        "raw": display_raw,
        "matched_keyword": matched_keyword,
    })
    matched_count += 1

    return matched_count, matched_count >= max_lines


def _strip_stack_traces(text: str) -> str:
    """Remove stack trace lines from text, keeping only the first line(s) before the stack."""
    lines = text.split("\n")
    stripped = []
    for line in lines:
        if _STACK_LINE_RE.match(line):
            break
        stripped.append(line)
    return "\n".join(stripped).rstrip("\n")


def _passes_keyword_filter_by_raw(raw: str, keywords: list[str]) -> bool:
    text = raw.lower()
    return all(kw.lower() in text for kw in keywords)


def _has_any_keyword_by_raw(raw: str, exclude_keywords: list[str]) -> bool:
    text = raw.lower()
    return any(kw.lower() in text for kw in exclude_keywords)


def _find_matched_keywords_by_raw(raw: str, keywords: list[str]) -> list[str]:
    text = raw.lower()
    return [kw for kw in keywords if kw.lower() in text]