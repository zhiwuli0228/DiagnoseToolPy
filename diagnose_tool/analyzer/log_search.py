"""Log content search with filtering by time, thread, keywords, and exclusion."""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from diagnose_tool.analyzer.header_parser import parse_log_record
from diagnose_tool.analyzer.reader import read_log_lines
from diagnose_tool.analyzer.scanner import scan_directory
from diagnose_tool.core.security import PathValidationError, validate_server_directory
from diagnose_tool.core.config import load_config

logger = logging.getLogger(__name__)


def search_log_content(
    path: str,
    time_start: str | None = None,
    time_end: str | None = None,
    thread: str | None = None,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    max_lines: int = 1000,
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
            for log_line in read_log_lines(file_path):
                total_lines += 1
                record = parse_log_record(log_line.raw, log_line.file_path, log_line.line_no)

                # Time filter
                if not _passes_time_filter(record, time_start, time_end):
                    continue

                # Thread filter
                if thread and not _passes_thread_filter(record, thread):
                    continue

                # Keyword filter (AND — all must be present)
                if keywords and not _passes_keyword_filter(record, keywords):
                    continue

                # Exclude filter
                if exclude_keywords and _has_any_keyword(record, exclude_keywords):
                    continue

                matched_keyword = _find_matched_keywords(record, keywords) if keywords else None
                results.append({
                    "file_path": log_line.file_path,
                    "line_no": log_line.line_no,
                    "timestamp": record.timestamp or "",
                    "level": record.level or "",
                    "thread": record.thread or "",
                    "logger": record.logger or "",
                    "message": record.message or "",
                    "raw": record.raw,
                    "matched_keyword": matched_keyword,
                })
                matched_count += 1

                if matched_count >= max_lines:
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
    # Handle both 'T' and space separator formats
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