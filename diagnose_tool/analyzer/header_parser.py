"""Complex log header parser with balanced bracket scanning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterator


class ParseStatus(Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    RAW = "RAW"


@dataclass(frozen=True)
class ParsedLogRecord:
    timestamp: str | None
    level: str | None
    module: str | None
    thread: str | None
    logger: str | None
    message: str | None
    raw: str
    file_path: str | None
    line_no: int | None
    parse_status: ParseStatus


TIMESTAMP_LEVEL_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,3})?)\s+(ERROR|WARN|WARNING|INFO|DEBUG|TRACE|FATAL)\s+"
)


def parse_log_record(raw: str, file_path: str | None = None, line_no: int | None = None) -> ParsedLogRecord:
    """Parse a raw log event into a structured record.

    Uses regex for timestamp/level and balanced bracket scanning for
    module/thread and logger groups. Preserves raw content on any failure.
    """

    ts_match = TIMESTAMP_LEVEL_RE.match(raw)
    if not ts_match:
        return ParsedLogRecord(
            timestamp=None,
            level=None,
            module=None,
            thread=None,
            logger=None,
            message=None,
            raw=raw,
            file_path=file_path,
            line_no=line_no,
            parse_status=ParseStatus.RAW,
        )

    timestamp = ts_match.group(1)
    level = ts_match.group(2)
    remaining = raw[ts_match.end():]

    bracket_groups = list(scan_balanced_bracket_groups(remaining))
    if not bracket_groups:
        return ParsedLogRecord(
            timestamp=timestamp,
            level=level,
            module=None,
            thread=None,
            logger=None,
            message=remaining.strip() or None,
            raw=raw,
            file_path=file_path,
            line_no=line_no,
            parse_status=ParseStatus.PARTIAL,
        )

    module_thread_raw = bracket_groups[0] if bracket_groups else None
    module, thread = _parse_module_thread(module_thread_raw)

    logger = None
    message = None
    if len(bracket_groups) > 1:
        # Find the logger group in remaining text and extract message from what follows.
        # This avoids misinterpreting ']' characters inside the message as delimiters.
        logger_raw = bracket_groups[1]
        logger_pos = remaining.find(logger_raw)
        if logger_pos >= 0:
            msg_start = logger_pos + len(logger_raw)
            message = remaining[msg_start:].strip() or None
            # Extract logger name by stripping outer brackets only
            inner = _strip_brackets(logger_raw)
            # If there are more ']' characters, split on the first to separate logger from message
            if message and "]" in inner:
                parts = inner.split("]", 1)
                logger = parts[0].strip()
                message = (parts[1].strip() + (" " + message if message else "")).strip() or None
            else:
                logger = inner or None
        else:
            # Fallback: strip outer brackets and split on remaining ']'
            bracket_content = _strip_brackets(logger_raw)
            if "]" in bracket_content:
                idx = bracket_content.index("]")
                logger = bracket_content[:idx].strip()
                message = bracket_content[idx + 1 :].strip() or None
            else:
                logger = bracket_content
                logger_end = remaining.find(logger_raw)
                if logger_end >= 0:
                    msg_start = logger_end + len(logger_raw)
                    message = remaining[msg_start:].strip() or None
                else:
                    message = None
    if len(bracket_groups) > 2:
        # Only join additional groups as continuation if the message from
        # remaining is empty or blank — meaning there was no message text
        # after the logger. If a message already exists, nested brackets
        # in the message body produced spurious groups; don't overwrite.
        if not message:
            message = " ".join(bracket_groups[2:]).strip() or message

    if message is None and len(bracket_groups) == 1:
        first_group_end = remaining.find(bracket_groups[0])
        if first_group_end >= 0:
            msg_start = first_group_end + len(bracket_groups[0])
            message = remaining[msg_start:].strip() or None

    if module is None or logger is None or message is None:
        return ParsedLogRecord(
            timestamp=timestamp,
            level=level,
            module=module,
            thread=thread,
            logger=logger,
            message=message,
            raw=raw,
            file_path=file_path,
            line_no=line_no,
            parse_status=ParseStatus.PARTIAL,
        )

    return ParsedLogRecord(
        timestamp=timestamp,
        level=level,
        module=module,
        thread=thread,
        logger=logger,
        message=message,
        raw=raw,
        file_path=file_path,
        line_no=line_no,
        parse_status=ParseStatus.FULL,
    )


def _parse_module_thread(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    if not (raw.startswith("[") and raw.endswith("]")):
        return None, None
    depth = 0
    module_start = 1
    module_end = -1
    for i, ch in enumerate(raw):
        if ch == "[":
            if depth == 1:
                module_start = i + 1
            depth += 1
        elif ch == "]":
            prev = depth
            depth -= 1
            if prev == 2 and module_end < 0:
                module_end = i
            elif prev == 1 and module_end < 0:
                module_end = i
    if module_end >= 0:
        module = raw[module_start:module_end]
        if module_end == len(raw) - 1:
            return module.strip() or None, None
        thread = raw[module_end + 1 : -1].strip()
        return module.strip() or None, thread or None
    return None, None


def _strip_brackets(text: str) -> str:
    """Remove outermost matched brackets from text like '[content]' or '[[content]]'.

    - '[x]' -> 'x'
    - '[[order-core]worker-1]' -> '[order-core]worker-1'
    """
    if len(text) >= 2 and text.startswith("[") and text.endswith("]"):
        return text[1:-1]
    return text


def scan_balanced_bracket_groups(text: str) -> Iterator[str]:
    """Scan text for balanced bracket groups like '[x]' or '[[y]z]'."""
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "[":
            start = i
            depth = 1
            i += 1
            while i < n and depth > 0:
                if text[i] == "[":
                    depth += 1
                elif text[i] == "]":
                    depth -= 1
                i += 1
            if depth == 0:
                group = text[start:i]
                # Skip empty groups [] that are placeholders in real log formats
                if group != "[]":
                    yield group
        else:
            i += 1