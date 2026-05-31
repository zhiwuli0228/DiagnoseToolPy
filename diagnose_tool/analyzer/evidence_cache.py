"""Evidence cache: store and retrieve matched log lines with context."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


CONTEXT_EVENTS = 5


@dataclass
class LogEvent:
    timestamp: str
    level: str
    thread: str
    message: str
    raw: str
    file_path: str
    line_no: int


@dataclass
class CachedLogEntry:
    id: str
    group_key: str
    event: LogEvent
    context_before: list[LogEvent]
    context_after: list[LogEvent]


def generate_entry_id(file_path: str, line_no: int, timestamp: str) -> str:
    """Generate a stable hash ID for a log entry."""
    data = f"{file_path}:{line_no}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


class EvidenceCacheManager:
    """Manages evidence cache for search and cluster results."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = Path(data_dir)

    def create_search_cache(
        self,
        source_path: str,
        matched_lines: list[dict],
        group_keys: dict[int, str],
    ) -> str:
        """Create a new search cache and return the cache key.

        Args:
            source_path: The source directory path that was searched.
            matched_lines: List of matched log line dicts from search.
            group_keys: Map of line index to aggregation group key.

        Returns:
            cache_key in format 'search-{timestamp}-{uuid}'
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cache_key = f"search-{timestamp}-{uuid.uuid4().hex[:6]}"
        cache_dir = self._data_dir / "output" / cache_key
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Store source path metadata
        meta = {
            "cache_key": cache_key,
            "source_path": source_path,
            "created_at": datetime.now().isoformat(),
            "type": "search",
        }
        (cache_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8"
        )

        # Build event buffer for context calculation (just use the matched_lines list)
        all_events = matched_lines

        # Write matched-lines.jsonl with context
        entries = []
        for idx, line in enumerate(matched_lines):
            entry = self._build_cache_entry(
                line, group_keys.get(idx, ""), all_events, idx
            )
            entries.append(entry)

        matched_lines_path = cache_dir / "matched-lines.jsonl"
        with matched_lines_path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

        return cache_key

    def _build_event_index(self, matched_lines: list[dict]) -> dict[str, int]:
        """Build an index of all events by their IDs for context lookup."""
        index = {}
        for i, line in enumerate(matched_lines):
            ts = line.get("timestamp") or ""
            fp = line.get("file_path") or ""
            ln = line.get("line_no") or 0
            entry_id = generate_entry_id(fp, ln, ts)
            index[entry_id] = i
        return index

    def _build_cache_entry(
        self,
        line: dict,
        group_key: str,
        all_events: list[dict],
        current_idx: int,
    ) -> CachedLogEntry:
        """Build a cache entry with context events."""
        ts = line.get("timestamp") or ""
        fp = line.get("file_path") or ""
        ln = line.get("line_no") or 0
        entry_id = generate_entry_id(fp, ln, ts)

        event = LogEvent(
            timestamp=ts,
            level=line.get("level") or "",
            thread=line.get("thread") or "",
            message=line.get("message") or "",
            raw=line.get("raw") or "",
            file_path=fp,
            line_no=ln,
        )

        # Get context events (simple index-based for now)
        context_before = self._get_context_events(
            all_events, current_idx, CONTEXT_EVENTS, direction=-1
        )
        context_after = self._get_context_events(
            all_events, current_idx, CONTEXT_EVENTS, direction=1
        )

        return CachedLogEntry(
            id=entry_id,
            group_key=group_key,
            event=event,
            context_before=context_before,
            context_after=context_after,
        )

    def _get_context_events(
        self,
        all_events: list[dict],
        current_idx: int,
        count: int,
        direction: int,
    ) -> list[LogEvent]:
        """Get context events in a direction from a list of event dicts."""
        result = []
        pos = current_idx + direction
        for _ in range(count):
            if 0 <= pos < len(all_events):
                line = all_events[pos]
                result.append(LogEvent(
                    timestamp=line.get("timestamp") or "",
                    level=line.get("level") or "",
                    thread=line.get("thread") or "",
                    message=line.get("message") or "",
                    raw=line.get("raw") or "",
                    file_path=line.get("file_path") or "",
                    line_no=line.get("line_no") or 0,
                ))
                pos += direction
            else:
                break
        return result

    def get_cache(self, cache_key: str) -> Path | None:
        """Get cache directory path if exists."""
        cache_dir = self._data_dir / "output" / cache_key
        if not cache_dir.exists():
            return None
        matched_path = cache_dir / "matched-lines.jsonl"
        if not matched_path.exists():
            return None
        return cache_dir

    def load_matched_lines(self, cache_key: str) -> list[CachedLogEntry]:
        """Load all cached entries from a cache key."""
        cache_dir = self.get_cache(cache_key)
        if cache_dir is None:
            return []
        matched_path = cache_dir / "matched-lines.jsonl"
        if not matched_path.exists():
            return []
        entries = []
        with matched_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entries.append(
                    CachedLogEntry(
                        id=data["id"],
                        group_key=data["group_key"],
                        event=LogEvent(**data["event"]),
                        context_before=[
                            LogEvent(**e) for e in data.get("context_before", [])
                        ],
                        context_after=[
                            LogEvent(**e) for e in data.get("context_after", [])
                        ],
                    )
                )
        return entries

    def get_entries_by_group(
        self, cache_key: str, group_key: str
    ) -> list[CachedLogEntry]:
        """Get all entries for a specific group key."""
        all_entries = self.load_matched_lines(cache_key)
        return [e for e in all_entries if e.group_key == group_key]

    def get_entry_by_id(
        self, cache_key: str, entry_id: str
    ) -> CachedLogEntry | None:
        """Get a single entry by ID."""
        all_entries = self.load_matched_lines(cache_key)
        for entry in all_entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_entries_by_ids(
        self, cache_key: str, entry_ids: list[str]
    ) -> list[CachedLogEntry]:
        """Get multiple entries by their IDs."""
        all_entries = self.load_matched_lines(cache_key)
        id_set = set(entry_ids)
        return [e for e in all_entries if e.id in id_set]

    def list_caches(self, cache_type: str | None = None) -> list[str]:
        """List all cache keys, optionally filtered by type."""
        output_dir = self._data_dir / "output"
        if not output_dir.exists():
            return []
        cache_keys = []
        for d in output_dir.iterdir():
            if not d.is_dir():
                continue
            meta_path = d / "meta.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    if cache_type is None or meta.get("type") == cache_type:
                        cache_keys.append(d.name)
                except Exception:
                    pass
        return sorted(cache_keys)
