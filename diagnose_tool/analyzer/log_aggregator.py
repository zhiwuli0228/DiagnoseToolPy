"""Log aggregation: group similar log events and count occurrences."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterator


# Patterns used for message normalization
_TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?')
_NUMERIC_RE = re.compile(r'\b\d+\b')
_STRING_RE = re.compile(r'"[^"]*"')
_HEX_RE = re.compile(r'0x[0-9a-fA-F]+')
_EXCEPTION_CLASS_RE = re.compile(r'\b([A-Z]\w*(?:Exception|Error|RuntimeException))\b')
_CAUSED_BY_RE = re.compile(r'Caused by:\s*([\w.]+\.(?:Exception|Error|RuntimeException))', re.IGNORECASE)
_UNDERSCORE_NUM_RE = re.compile(r'_\d+(?=_|$)')


@dataclass
class AggregationOptions:
    group_by_exception: bool = True
    include_thread: bool = False
    include_time: bool = False
    message_only: bool = False


@dataclass
class AggregatedGroup:
    key: str
    count: int
    sample_message: str
    sample_timestamp: str
    sample_thread: str
    sample_level: str
    file_path: str
    matched_lines: list[dict] = field(default_factory=list)


def aggregate_log_lines(
    lines: list[dict],
    options: AggregationOptions,
    max_sample_lines: int = 10,
) -> list[AggregatedGroup]:
    """Aggregate log lines by exception class or message template.

    Args:
        lines: List of log result dicts from search_log_content.
        options: Aggregation options.
        max_sample_lines: Max sample lines to store per group.

    Returns:
        List of AggregatedGroup sorted by count descending.
    """
    groups: dict[str, list[dict]] = defaultdict(list)

    for line in lines:
        key = _build_group_key(line, options)
        groups[key].append(line)

    results: list[AggregatedGroup] = []
    for key, matched_lines in groups.items():
        first = matched_lines[0]
        results.append(AggregatedGroup(
            key=key,
            count=len(matched_lines),
            sample_message=_build_sample_message(first, options),
            sample_timestamp=first.get("timestamp") or "",
            sample_thread=first.get("thread") or "",
            sample_level=first.get("level") or "",
            file_path=first.get("file_path") or "",
            matched_lines=matched_lines[:max_sample_lines],
        ))

    results.sort(key=lambda g: g.count, reverse=True)
    return results


def aggregate_log_lines_streaming(
    lines_iter: Iterator[dict],
    options: AggregationOptions,
    max_sample_lines: int = 10,
) -> list[AggregatedGroup]:
    """Aggregate log lines by exception class using streaming (memory-efficient).

    Accumulates groups incrementally without storing all lines in memory.

    Args:
        lines_iter: Iterable of log line dicts (e.g., from a generator).
        options: Aggregation options.
        max_sample_lines: Max sample lines to store per group.

    Returns:
        List of AggregatedGroup sorted by count descending.
    """
    # Accumulators: key -> group data (no need to store all lines)
    group_counts: dict[str, int] = defaultdict(int)
    group_first_line: dict[str, dict] = {}
    group_samples: dict[str, list[dict]] = defaultdict(list)

    for line in lines_iter:
        key = _build_group_key(line, options)
        group_counts[key] += 1

        # Keep first line as sample (for message/timestamp/thread/level)
        if key not in group_first_line:
            group_first_line[key] = line

        # Keep samples up to max_sample_lines
        if len(group_samples[key]) < max_sample_lines:
            group_samples[key].append(line)

    results: list[AggregatedGroup] = []
    for key in group_counts:
        first = group_first_line[key]
        results.append(AggregatedGroup(
            key=key,
            count=group_counts[key],
            sample_message=_build_sample_message(first, options),
            sample_timestamp=first.get("timestamp") or "",
            sample_thread=first.get("thread") or "",
            sample_level=first.get("level") or "",
            file_path=first.get("file_path") or "",
            matched_lines=group_samples[key],
        ))

    results.sort(key=lambda g: g.count, reverse=True)
    return results


def _build_group_key(line: dict, options: AggregationOptions) -> str:
    """Build a group key from a log line dict."""
    # Try exception class first
    raw = line.get("raw", "") or ""
    exc = _extract_exception_class(raw)
    if exc and options.group_by_exception:
        key = exc
    else:
        # Fall back to normalized message template
        key = _normalize_message(line.get("message") or "", options.message_only)

    # Optionally prepend thread/time to make groups more specific
    if options.include_thread and line.get("thread"):
        key = f"{key} @ {line['thread']}"
    if options.include_time and line.get("timestamp"):
        ts = line["timestamp"]
        # Keep only hour (HH) to avoid per-minute fragmentation
        if "T" in ts:
            key = f"{key} [{ts[11:13]}]"
        elif " " in ts:
            key = f"{key} [{ts[11:13]}]"

    return key


def _build_sample_message(line: dict, options: AggregationOptions) -> str:
    """Build a human-readable sample message line."""
    parts = []
    if options.include_time and line.get("timestamp"):
        parts.append(line["timestamp"][11:13])  # HH
    if not options.message_only and line.get("level"):
        parts.append(line["level"])
    if not options.message_only and options.include_thread and line.get("thread"):
        parts.append(f"[{line['thread']}]")
    msg = line.get("message") or line.get("raw") or ""
    parts.append(msg)
    return " ".join(parts)


def _extract_exception_class(raw: str) -> str | None:
    """Extract the primary exception class name from raw log text."""
    # Try "Caused by:" first — most specific
    m = _CAUSED_BY_RE.search(raw)
    if m:
        return m.group(1).split(".")[-1]  # "JedisConnectionException"
    # Fall back to class name pattern in text
    m = _EXCEPTION_CLASS_RE.search(raw)
    if m:
        return m.group(1)
    return None


def _normalize_message(message: str, strip_context: bool = False) -> str:
    """Normalize a log message for grouping.

    Replaces dynamic values (numbers, strings, hex) with placeholders
    so similar events with different values share the same template.
    """
    text = message
    text = _TIMESTAMP_RE.sub('<TS>', text)
    text = _STRING_RE.sub('<S>', text)
    text = _HEX_RE.sub('<HEX>', text)
    text = _UNDERSCORE_NUM_RE.sub('<N>', text)
    text = _NUMERIC_RE.sub('<N>', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()