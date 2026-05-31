"""JVM stack trace parser and formatter — pure Python, FastAPI-independent."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# --- Data Models --------------------------------------------------------


@dataclass
class StackFrame:
    """A single stack frame."""
    class_name: str
    method: str
    file_name: str | None
    line_number: int | None
    is_native: bool = False

    def to_short_string(self) -> str:
        """Short representation: com.demo.Class.method(File.java:42)"""
        location = f"{self.file_name}"
        if self.line_number is not None:
            location += f":{self.line_number}"
        return f"{self.class_name}.{self.method}({location})"

    def to_string(self) -> str:
        """Full representation: at com.demo.Class.method(File.java:42)"""
        prefix = "at " if not self.is_native else "at (native) "
        return prefix + self.to_short_string()


@dataclass
class ParsedStack:
    """Result of stack parsing."""
    total_lines: int
    display_lines: int
    exception_type: str | None
    entry_point: str | None
    frames: list[StackFrame]
    truncated: bool = False
    truncated_count: int = 0
    repeat_groups: list[tuple[str, int]] = field(default_factory=list)
    package_groups: list[tuple[str, int]] = field(default_factory=list)

    def to_display_string(self) -> str:
        """Render as multi-line string."""
        lines = []
        for frame in self.frames:
            lines.append(frame.to_string())

        if self.truncated:
            lines.append(f"...（{self.truncated_count} 行已省略）...")

        return "\n".join(lines)


@dataclass
class StackParserOptions:
    """Configuration for stack parser."""
    max_lines: int = 50
    merge_repeated: bool = True
    merge_package: bool = True
    show_suggestion: bool = True
    suggestion_threshold: int = 30


# --- Parser ------------------------------------------------------------


class StackParser:
    """Parser for JVM stack traces."""

    # Regex for stack frame lines
    FRAME_PATTERNS = [
        # HotSpot format: at com.demo.Class.method(File.java:42)
        re.compile(
            r"^\s*at\s+([\w.$]+)\.([\w$]+)\(([^:]+):(\d+)\)$"
        ),
        # Native method: at com.demo.Class.method(Native Method)
        re.compile(
            r"^\s*at\s+([\w.$]+)\.([\w$]+)\(([^)]+)\)$"
        ),
        # Unknown/unknown source
        re.compile(
            r"^\s*at\s+([\w.$]+)\.([\w$]+)\(([^)]*)\)$"
        ),
        # Anonymous/classload
        re.compile(
            r"^\s*---\s+([\w.$]+)\.([\w$]+)\(([^:]+)\+(\d+)\)$"
        ),
    ]

    CAUSED_BY_PATTERN = re.compile(r"^\s*Caused by:\s*(.+)$", re.IGNORECASE)

    ENTRY_POINT_CLASSES = {
        "Controller", "RestController", "ApiController",
        "Servlet", "DispatcherServlet", "HttpServlet",
        "Filter", "Interceptor",
        "Application", "SpringApplication",
        "Main", "Runnable", "Thread",
    }

    def __init__(self, options: StackParserOptions | None = None) -> None:
        self._opts = options or StackParserOptions()

    def parse(self, raw_stack: str) -> ParsedStack:
        """Parse a raw stack trace string.

        Args:
            raw_stack: Multi-line stack trace text.

        Returns:
            ParsedStack with parsed frames and metadata.
        """
        lines = raw_stack.strip().splitlines()
        total_lines = len(lines)

        frames: list[StackFrame] = []
        exception_type: str | None = None
        entry_point: str | None = None

        # First pass: extract exception type
        for line in lines:
            if match := self.CAUSED_BY_PATTERN.match(line):
                exception_type = match.group(1)
                break

        # Second pass: parse frames
        for line in lines:
            frame = self._parse_frame(line)
            if frame:
                frames.append(frame)
                if entry_point is None and self._is_entry_point(frame):
                    entry_point = frame.to_short_string()

        # Apply transformations
        if self._opts.merge_repeated:
            frames, repeat_groups = self._merge_repeated_frames(frames)
        else:
            repeat_groups = []

        if self._opts.merge_package:
            frames, package_groups = self._merge_package_frames(frames)
        else:
            package_groups = []

        # Truncate if needed
        truncated = False
        truncated_count = 0
        if len(frames) > self._opts.max_lines:
            truncated = True
            truncated_count = len(frames) - self._opts.max_lines
            frames = self._truncate_frames(frames)

        return ParsedStack(
            total_lines=total_lines,
            display_lines=len(frames),
            exception_type=exception_type,
            entry_point=entry_point,
            frames=frames,
            truncated=truncated,
            truncated_count=truncated_count,
            repeat_groups=repeat_groups,
            package_groups=package_groups,
        )

    def needs_suggestion(self, raw_stack: str) -> bool:
        """Check if stack is long enough to suggest simplification.

        Args:
            raw_stack: Raw stack trace.

        Returns:
            True if lines exceed suggestion_threshold.
        """
        return len(raw_stack.strip().splitlines()) > self._opts.suggestion_threshold

    def _parse_frame(self, line: str) -> StackFrame | None:
        """Parse a single stack frame line."""
        for pattern in self.FRAME_PATTERNS:
            if match := pattern.match(line):
                class_name = match.group(1)
                method = match.group(2)
                file_part = match.group(3)

                is_native = file_part.lower() in ("native method", "unknown source")
                line_number: int | None = None
                if match.lastindex == 4 and not is_native:
                    try:
                        line_number = int(match.group(4))
                    except ValueError:
                        pass

                return StackFrame(
                    class_name=class_name,
                    method=method,
                    file_name=file_part if not is_native else None,
                    line_number=line_number,
                    is_native=is_native,
                )
        return None

    def _is_entry_point(self, frame: StackFrame) -> bool:
        """Check if frame looks like an entry point."""
        class_name = frame.class_name.split(".")[-1]
        return class_name in self.ENTRY_POINT_CLASSES

    def _merge_repeated_frames(
        self,
        frames: list[StackFrame],
    ) -> tuple[list[StackFrame], list[tuple[str, int]]]:
        """Merge consecutive identical frames."""
        if not frames:
            return frames, []

        merged: list[StackFrame] = []
        repeat_groups: list[tuple[str, int]] = []

        current: StackFrame | None = None
        count = 0

        for frame in frames:
            if current and frame.to_short_string() == current.to_short_string():
                count += 1
            else:
                if current and count > 1:
                    repeat_groups.append((current.to_short_string(), count))
                    merged.append(current)
                elif current:
                    merged.append(current)
                current = frame
                count = 1

        if current:
            if count > 1:
                repeat_groups.append((current.to_short_string(), count))
                merged.append(current)
            else:
                merged.append(current)

        return merged, repeat_groups

    def _merge_package_frames(
        self,
        frames: list[StackFrame],
    ) -> tuple[list[StackFrame], list[tuple[str, int]]]:
        """Merge consecutive frames from the same package."""
        if not frames:
            return frames, []

        merged: list[StackFrame] = []
        package_groups: list[tuple[str, int]] = []

        i = 0
        while i < len(frames):
            frame = frames[i]
            package = self._get_package(frame.class_name)

            if package:
                j = i + 1
                while j < len(frames) and self._get_package(frames[j].class_name) == package:
                    j += 1

                count = j - i
                if count > 1:
                    package_groups.append((package, count))
                    merged.append(frame)
                    i = j
                    continue

            merged.append(frame)
            i += 1

        return merged, package_groups

    def _get_package(self, class_name: str) -> str | None:
        """Extract package prefix from fully qualified class name."""
        parts = class_name.rsplit(".", 2)
        if len(parts) >= 2:
            return ".".join(parts[:-1])
        return None

    def _truncate_frames(self, frames: list[StackFrame]) -> list[StackFrame]:
        """Truncate to max_lines, keeping head and tail."""
        if len(frames) <= self._opts.max_lines:
            return frames

        keep_head = self._opts.max_lines // 2
        keep_tail = self._opts.max_lines - keep_head

        return frames[:keep_head] + frames[-keep_tail:]


# --- Convenience function ----------------------------------------------


def parse_stack(
    stack: str,
    max_lines: int = 50,
    merge_repeated: bool = True,
    merge_package: bool = True,
    show_suggestion: bool = True,
) -> ParsedStack:
    """Convenience function for quick parsing.

    Args:
        stack: Raw stack trace text.
        max_lines: Maximum frames to display.
        merge_repeated: Whether to merge repeated frames.
        merge_package: Whether to merge same-package frames.
        show_suggestion: Whether to include simplification suggestions.

    Returns:
        ParsedStack with parsed and formatted frames.
    """
    options = StackParserOptions(
        max_lines=max_lines,
        merge_repeated=merge_repeated,
        merge_package=merge_package,
        show_suggestion=show_suggestion,
    )
    return StackParser(options).parse(stack)
