"""In-process runtime helpers for cluster task coordination.

These helpers keep a small in-memory registry of cluster tasks keyed by the
normalized source path, so duplicate same-source requests can reuse an active
task instead of starting a redundant full scan. The registry also tracks
terminal task states (done/failed) so the API can decide whether a fresh
submission is allowed.

The registry is intentionally process-local: it is rebuilt on restart from
the `data/output/` directory if needed, and does not introduce any
mandatory infrastructure.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

TERMINAL_DONE = "done"
TERMINAL_FAILED = "failed"
ACTIVE_STATUSES = {"scanning", "aggregating", "matching"}
TERMINAL_STATUSES = {TERMINAL_DONE, TERMINAL_FAILED}


def normalize_source_key(source_path: str | Path) -> str:
    """Return a stable, absolute key for cluster task admission.

    Resolves the path and uses lowercase to absorb case-only differences on
    case-insensitive filesystems. Symlinks are resolved so two distinct
    references to the same directory are treated as the same source.
    """
    resolved = Path(source_path).resolve()
    return str(resolved).lower()


@dataclass(frozen=True)
class ClusterTaskRecord:
    task_id: str
    status: str


class ClusterTaskRegistry:
    """Thread-safe in-process registry of cluster tasks by source key."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, ClusterTaskRecord] = {}

    def get(self, source_key: str) -> ClusterTaskRecord | None:
        with self._lock:
            return self._entries.get(source_key)

    def active_task_id(self, source_key: str) -> str | None:
        record = self.get(source_key)
        if record is None:
            return None
        if record.status in ACTIVE_STATUSES:
            return record.task_id
        return None

    def register_new(self, source_key: str, task_id: str) -> None:
        with self._lock:
            self._entries[source_key] = ClusterTaskRecord(
                task_id=task_id, status="scanning"
            )

    def update_status(self, source_key: str, status: str) -> None:
        with self._lock:
            record = self._entries.get(source_key)
            if record is None:
                return
            self._entries[source_key] = ClusterTaskRecord(
                task_id=record.task_id, status=status
            )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# Single process-wide registry used by the API layer.
_registry = ClusterTaskRegistry()


def get_registry() -> ClusterTaskRegistry:
    return _registry
