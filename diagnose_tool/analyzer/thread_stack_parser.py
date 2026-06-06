"""JVM thread dump parser — pure Python, FastAPI-independent.

Parses HotSpot/OpenJDK thread dump blocks into structured thread content.
Separate from ``stack_parser`` which handles exception stack traces.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field


# --- Data Models --------------------------------------------------------


class ParseStatus(enum.Enum):
    """Parse completeness status."""
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    RAW = "RAW"


@dataclass
class ThreadFrame:
    """A single stack frame from a thread dump."""
    raw_text: str
    class_name: str | None = None
    method: str | None = None
    file_name: str | None = None
    line_number: int | None = None
    is_native: bool = False
    is_unknown_source: bool = False


@dataclass
class LockHint:
    """Lock or wait information from a thread dump line."""
    raw_text: str
    hint_type: str = ""  # "waiting_to_lock", "locked", "parking", etc.
    lock_address: str | None = None
    lock_class: str | None = None


@dataclass
class ThreadDumpResult:
    """Result of parsing a single thread dump block."""
    thread_name: str | None = None
    thread_state: str | None = None
    frames: list[ThreadFrame] = field(default_factory=list)
    lock_hints: list[LockHint] = field(default_factory=list)
    raw_text: str = ""
    parse_status: ParseStatus = ParseStatus.RAW


# --- Parser -------------------------------------------------------------

# Thread header: "thread-name" #42 daemon prio=5 os_prio=0 tid=0x... nid=0x... waiting on condition [0x...]
_THREAD_HEADER_RE = re.compile(
    r'^"(.+?)"'           # quoted thread name
    r"\s+#(\d+)"          # thread number
    r"(?:\s+\w+)*"        # optional words (daemon, etc.)
    r".*$",
)

# java.lang.Thread.State: WAITING (parking)
_THREAD_STATE_RE = re.compile(
    r"^\s*java\.lang\.Thread\.State:\s*(\S+)(?:\s*\((.+?)\))?\s*$",
)

# at com.demo.Class.method(File.java:42)
_FRAME_WITH_LINE_RE = re.compile(
    r"^\s*at\s+([\w.$]+)\.([\w$]+)\(([^:]+):(\d+)\)\s*$",
)

# at com.demo.Class.method(Native Method) / (Unknown Source)
_FRAME_SOURCE_RE = re.compile(
    r"^\s*at\s+([\w.$]+)\.([\w$]+)\(([^)]+)\)\s*$",
)

# Lock hint lines
_LOCK_HINT_RE = re.compile(r"^\s*-\s+(.+)$")

# Known lock hint patterns
_WAITING_TO_LOCK_RE = re.compile(
    r"waiting to lock\s+<(0x[0-9a-f]+)>\s+\(a\s+([\w.$]+)\)",
    re.IGNORECASE,
)
_LOCKED_RE = re.compile(
    r"locked\s+<(0x[0-9a-f]+)>\s+\(a\s+([\w.$]+)\)",
    re.IGNORECASE,
)
_PARKING_RE = re.compile(
    r"parking to wait for\s+<(0x[0-9a-f]+)>\s+\(a\s+([\w.$]+)\)",
    re.IGNORECASE,
)


def _parse_frame(line: str) -> ThreadFrame | None:
    """Parse a single ``at ...`` frame line."""
    # Try line-number variant first
    if m := _FRAME_WITH_LINE_RE.match(line):
        class_name, method, file_name, line_no = m.groups()
        is_native = file_name.lower() == "native method"
        is_unknown = file_name.lower() == "unknown source"
        return ThreadFrame(
            raw_text=line.rstrip(),
            class_name=class_name,
            method=method,
            file_name=file_name if not is_native and not is_unknown else None,
            line_number=int(line_no) if not is_native and not is_unknown else None,
            is_native=is_native,
            is_unknown_source=is_unknown,
        )

    # Source-only variant (Native Method, Unknown Source, or other parenthesised source)
    if m := _FRAME_SOURCE_RE.match(line):
        class_name, method, source = m.groups()
        is_native = source.lower() == "native method"
        is_unknown = source.lower() == "unknown source"
        return ThreadFrame(
            raw_text=line.rstrip(),
            class_name=class_name,
            method=method,
            file_name=source if not is_native and not is_unknown else None,
            is_native=is_native,
            is_unknown_source=is_unknown,
        )

    return None


def _parse_lock_hint(line: str) -> LockHint | None:
    """Parse a lock hint line (``- waiting to lock ...``, ``- locked ...``, etc.)."""
    m = _LOCK_HINT_RE.match(line)
    if not m:
        return None

    content = m.group(1)
    hint = LockHint(raw_text=line.rstrip())

    if pm := _PARKING_RE.search(content):
        hint.hint_type = "parking"
        hint.lock_address = pm.group(1)
        hint.lock_class = pm.group(2)
    elif wm := _WAITING_TO_LOCK_RE.search(content):
        hint.hint_type = "waiting_to_lock"
        hint.lock_address = wm.group(1)
        hint.lock_class = wm.group(2)
    elif lm := _LOCKED_RE.search(content):
        hint.hint_type = "locked"
        hint.lock_address = lm.group(1)
        hint.lock_class = lm.group(2)
    else:
        # Generic hint — e.g. "- None", "- waiting on <...>"
        hint.hint_type = "other"

    return hint


def parse_thread_dump(raw_text: str) -> ThreadDumpResult:
    """Parse a JVM thread dump block into structured data.

    Conservative parser: recognises the common HotSpot/OpenJ9 thread dump
    header, ``java.lang.Thread.State`` line, ordered ``at ...`` frames, and
    optional lock/wait hints.  Malformed or unsupported input returns RAW or
    PARTIAL output instead of raising.

    Args:
        raw_text: Multi-line thread dump text.

    Returns:
        ``ThreadDumpResult`` with parsed fields and status.
    """
    result = ThreadDumpResult(raw_text=raw_text)

    if not raw_text or not raw_text.strip():
        return result

    lines = raw_text.strip().splitlines()

    # --- Phase 1: find thread header ---
    header_idx: int | None = None
    for idx, line in enumerate(lines):
        if m := _THREAD_HEADER_RE.match(line):
            result.thread_name = m.group(1)
            header_idx = idx
            break

    if header_idx is None:
        # No recognisable thread header — raw
        result.parse_status = ParseStatus.RAW
        return result

    # --- Phase 2: parse body after header ---
    found_state = False
    found_frames = False

    for line in lines[header_idx + 1:]:
        stripped = line.rstrip()
        if not stripped:
            continue

        # Thread state line
        if sm := _THREAD_STATE_RE.match(stripped):
            result.thread_state = sm.group(1)
            found_state = True
            continue

        # Stack frame
        frame = _parse_frame(stripped)
        if frame:
            result.frames.append(frame)
            found_frames = True
            continue

        # Lock hint
        hint = _parse_lock_hint(stripped)
        if hint:
            result.lock_hints.append(hint)
            continue

        # "Locked ownable synchronizers:" / "None" — skip section headers
        # Other unrecognised lines are silently ignored.

    # --- Phase 3: determine status ---
    if found_state and found_frames:
        result.parse_status = ParseStatus.FULL
    elif found_state or found_frames:
        result.parse_status = ParseStatus.PARTIAL
    else:
        # Header found but nothing else parsed
        result.parse_status = ParseStatus.PARTIAL

    return result


# --- Convenience: parse multiple threads --------------------------------


def parse_thread_dump_all(raw_text: str) -> list[ThreadDumpResult]:
    """Parse all thread blocks from a full thread dump.

    Splits on thread header lines and delegates each block to
    ``parse_thread_dump``.

    Args:
        raw_text: Full thread dump text (may contain many threads).

    Returns:
        List of ``ThreadDumpResult``, one per detected thread block.
    """
    if not raw_text or not raw_text.strip():
        return [ThreadDumpResult(raw_text=raw_text, parse_status=ParseStatus.RAW)]

    lines = raw_text.strip().splitlines()

    # Find all header line indices
    header_indices: list[int] = []
    for idx, line in enumerate(lines):
        if _THREAD_HEADER_RE.match(line):
            header_indices.append(idx)

    if not header_indices:
        return [ThreadDumpResult(raw_text=raw_text, parse_status=ParseStatus.RAW)]

    results: list[ThreadDumpResult] = []
    for i, start in enumerate(header_indices):
        end = header_indices[i + 1] if i + 1 < len(header_indices) else len(lines)
        block = "\n".join(lines[start:end])
        results.append(parse_thread_dump(block))

    return results
