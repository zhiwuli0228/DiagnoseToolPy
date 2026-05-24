"""Intelligent evidence compression for LLM diagnosis."""

from __future__ import annotations

import re
from dataclasses import dataclass


# Stack trace pattern to extract first line (the most specific code location)
_STACK_FIRST_LINE_RE = re.compile(r"^\s+at\s+([^\(]+)")


@dataclass
class CompressionOptions:
    include_stack: bool = True
    include_timeline: bool = True
    max_tokens: int = 2000


@dataclass
class StackPatternGroup:
    pattern: str  # Normalized stack first line
    count: int
    first_occurrence: str
    last_occurrence: str
    peak_window: str
    sample_entry: dict


@dataclass
class CompressedEvidence:
    group_key: str
    total_count: int
    first_occurrence: str
    last_occurrence: str
    peak_window: str
    stack_groups: list[StackPatternGroup]
    raw_sample: str


def compress_log_entries(
    entries: list[dict],
    options: CompressionOptions | None = None,
) -> list[CompressedEvidence]:
    """Compress log entries into structured evidence for LLM.

    Args:
        entries: List of log entry dicts or CachedLogEntry-like dicts.
        options: Compression options.

    Returns:
        List of CompressedEvidence, one per unique group_key.
    """
    if options is None:
        options = CompressionOptions()

    if not entries:
        return []

    # Group entries by group_key
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        if isinstance(entry, dict):
            group_key = entry.get("group_key", "unknown")
        else:
            # CachedLogEntry object
            group_key = entry.group_key if hasattr(entry, "group_key") else "unknown"

        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(entry)

    results = []
    for group_key, group_entries in groups.items():
        compressed = _compress_group(group_key, group_entries, options)
        results.append(compressed)

    return results


def _compress_group(group_key: str, entries: list[dict], options: CompressionOptions) -> CompressedEvidence:
    """Compress a group of entries into one CompressedEvidence."""
    # Extract events and timestamps
    events = []
    timestamps = []
    for entry in entries:
        if isinstance(entry, dict):
            event = entry.get("event", entry)
        else:
            event = entry.event if hasattr(entry, "event") else entry
        events.append(event)
        ts = event.get("timestamp", "") if isinstance(event, dict) else getattr(event, "timestamp", "")
        if ts:
            timestamps.append(ts)

    # Compute statistics
    timestamps_sorted = sorted(timestamps)
    first_occurrence = timestamps_sorted[0] if timestamps_sorted else "N/A"
    last_occurrence = timestamps_sorted[-1] if timestamps_sorted else "N/A"
    peak_window = _compute_peak_window(timestamps)

    # Group by stack pattern
    stack_groups = _group_by_stack_pattern(events, options)

    # Get sample raw for reference
    sample_entry = events[0] if events else {}
    raw_sample = sample_entry.get("raw", "") if isinstance(sample_entry, dict) else ""

    return CompressedEvidence(
        group_key=group_key,
        total_count=len(entries),
        first_occurrence=first_occurrence,
        last_occurrence=last_occurrence,
        peak_window=peak_window,
        stack_groups=stack_groups,
        raw_sample=raw_sample,
    )


def _group_by_stack_pattern(
    events: list[dict],
    options: CompressionOptions,
) -> list[StackPatternGroup]:
    """Group events by stack trace pattern."""
    pattern_groups: dict[str, list[dict]] = {}

    for event in events:
        raw = event.get("raw", "") if isinstance(event, dict) else getattr(event, "raw", "")
        stack_pattern = _extract_stack_pattern(raw, options.include_stack)

        if stack_pattern not in pattern_groups:
            pattern_groups[stack_pattern] = []
        pattern_groups[stack_pattern].append(event)

    results = []
    for pattern, group_events in pattern_groups.items():
        timestamps = []
        for e in group_events:
            ts = e.get("timestamp", "") if isinstance(e, dict) else getattr(e, "timestamp", "")
            if ts:
                timestamps.append(ts)

        timestamps_sorted = sorted(timestamps)
        first = timestamps_sorted[0] if timestamps_sorted else "N/A"
        last = timestamps_sorted[-1] if timestamps_sorted else "N/A"
        peak = _compute_peak_window(timestamps)

        results.append(StackPatternGroup(
            pattern=pattern,
            count=len(group_events),
            first_occurrence=first,
            last_occurrence=last,
            peak_window=peak,
            sample_entry=group_events[0] if group_events else {},
        ))

    # Sort by count descending
    results.sort(key=lambda g: g.count, reverse=True)
    return results


def _extract_stack_pattern(raw: str, include_stack: bool) -> str:
    """Extract the first stack line as pattern identifier."""
    if not include_stack:
        return "no_stack"

    # Find first "at ..." pattern in stack trace
    match = _STACK_FIRST_LINE_RE.search(raw)
    if match:
        return match.group(1).strip()

    # If no stack, return first line of message
    lines = raw.split("\n")
    first_line = lines[0] if lines else raw
    # Truncate if too long
    if len(first_line) > 100:
        first_line = first_line[:100] + "..."
    return first_line


def _compute_peak_window(timestamps: list[str]) -> str:
    """Compute the peak hour window from timestamps."""
    if not timestamps:
        return "N/A"

    hours: dict[str, int] = {}
    for ts in timestamps:
        # Extract hour from timestamp (format: "2026-05-23 10:01:01" or "2026-05-23T10:01:01")
        if "T" in ts:
            hour = ts[11:13]
        elif " " in ts:
            hour = ts[11:13]
        else:
            continue

        window = f"{hour}:00-{hour}:59"
        hours[window] = hours.get(window, 0) + 1

    if not hours:
        return "N/A"

    peak = max(hours.items(), key=lambda x: x[1])[0]
    total = sum(hours.values())
    percentage = (hours[peak] / total) * 100 if total > 0 else 0
    return f"{peak} ({percentage:.0f}%)"


def build_evidence_markdown(
    compressed_evidence: list[CompressedEvidence],
    options: CompressionOptions | None = None,
) -> str:
    """Build markdown evidence pack from compressed evidence.

    Args:
        compressed_evidence: List of CompressedEvidence from compress_log_entries.
        options: Compression options.

    Returns:
        Markdown string suitable for LLM input.
    """
    if options is None:
        options = CompressionOptions()

    if not compressed_evidence:
        return "No evidence to display."

    lines = [
        "# 日志诊断证据包 (压缩版)",
        "",
    ]

    for i, evidence in enumerate(compressed_evidence, 1):
        lines.append(f"## {i}. {evidence.group_key}")
        lines.append("")

        # Statistics
        lines.append(f"**总计**: {evidence.total_count} 次")
        lines.append(f"**首次**: {evidence.first_occurrence}")
        lines.append(f"**末次**: {evidence.last_occurrence}")
        lines.append(f"**峰值**: {evidence.peak_window}")
        lines.append("")

        # Stack patterns
        if evidence.stack_groups and options.include_stack:
            lines.append("### 堆栈模式")
            lines.append("")
            for j, sg in enumerate(evidence.stack_groups, 1):
                lines.append(f"**模式 {j}** ({sg.count}次):")
                lines.append("```")
                lines.append(f"  {sg.pattern}")
                lines.append(f"  首次: {sg.first_occurrence}")
                lines.append(f"  末次: {sg.last_occurrence}")
                lines.append("```")
                lines.append("")
        elif options.include_stack:
            lines.append("### 堆栈模式")
            lines.append("(无堆栈信息)")
            lines.append("")

        # Timeline
        if options.include_timeline:
            lines.append("### 时间分布")
            lines.append(f"- 首次出现: {evidence.first_occurrence}")
            lines.append(f"- 末次出现: {evidence.last_occurrence}")
            lines.append(f"- 峰值时段: {evidence.peak_window}")
            lines.append("")

    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count for text."""
    # Rough estimate: 1 token ≈ 4 characters for Chinese/English mixed
    return len(text) // 2


def truncate_to_token_budget(
    evidence_markdown: str,
    max_tokens: int,
) -> str:
    """Truncate evidence markdown to fit within token budget.

    Args:
        evidence_markdown: The full evidence markdown.
        max_tokens: Maximum tokens allowed.

    Returns:
        Truncated markdown that fits within budget.
    """
    current_tokens = estimate_tokens(evidence_markdown)
    if current_tokens <= max_tokens:
        return evidence_markdown

    # Binary search for truncation point
    lines = evidence_markdown.split("\n")
    low = 0
    high = len(lines)

    while low < high:
        mid = (low + high + 1) // 2
        truncated = "\n".join(lines[:mid])
        if estimate_tokens(truncated) <= max_tokens:
            low = mid
        else:
            high = mid - 1

    return "\n".join(lines[:low]) + "\n\n*[内容已截断以符合token限制]*"
