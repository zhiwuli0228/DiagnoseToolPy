"""Read-only access to analysis task artifacts on disk.

This module is the single point in the project that constructs
``data/output/{task_id}/...`` paths for the read side. The five new
``GET /api/source/...`` routes in ``routes_source.py`` call it; no other
module is expected to read these files directly.

Every public function validates ``task_id`` against a strict regex so
that no caller can pass path-traversal vectors (``..``, ``/``, ``\\``,
empty string, unicode). The validator is intentionally narrow: tasks
are produced by the project's own code, so any non-``[A-Za-z0-9_-]``
input is a bug or an attack.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


_TASK_ID_RE = re.compile(r"[A-Za-z0-9_-]+")
_OUTPUT_ROOT = Path("data/output")
_PROGRESS_FILENAME = "progress.json"
_EVIDENCE_PACK_FILENAME = "evidence-pack.md"
_KEY_LOGS_FILENAME = "key-logs.txt"
_CASE_DRAFT_FILENAME = "case-draft.md"
_TEST_SUGGESTIONS_FILENAME = "test-suggestions.md"
_MONITOR_SUGGESTIONS_FILENAME = "monitor-suggestions.md"


class InvalidTaskIdError(ValueError):
    """Raised when a task_id fails the path-component validator."""


def _validate_task_id(task_id: str) -> str:
    """Return ``task_id`` if it is safe to use as a path component.

    Raises ``InvalidTaskIdError`` for any other input. The error type is
    a ``ValueError`` subclass so existing call sites that catch
    ``ValueError`` keep working.
    """

    if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
        raise InvalidTaskIdError(
            f"invalid task_id {task_id!r}: must match {_TASK_ID_RE.pattern}"
        )
    return task_id


@dataclass
class TaskSummary:
    """A row returned by ``list_tasks()``."""

    task_id: str
    status: str | None = None
    progress: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _output_root() -> Path:
    """Return the configured output root. Centralized for tests."""

    return _OUTPUT_ROOT


def list_tasks() -> list[TaskSummary]:
    """Return a list of historical task summaries, sorted by ``updated_at`` desc.

    Directories under the output root that do not contain a
    ``progress.json`` are silently skipped (this is defensive against
    unrelated subfolders such as ``bench-full/`` that other tools may
    create under ``data/output/``).
    """

    root = _output_root()
    if not root.exists():
        return []

    summaries: list[TaskSummary] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        progress_path = entry / _PROGRESS_FILENAME
        if not progress_path.is_file():
            continue
        try:
            raw = json.loads(progress_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {}
        status = raw.get("status") if isinstance(raw, dict) else None
        if not isinstance(status, str):
            status = None
        summaries.append(
            TaskSummary(
                task_id=entry.name,
                status=status,
                progress=raw if isinstance(raw, dict) else {},
            )
        )

    summaries.sort(
        key=lambda s: (
            s.progress.get("updated_at")
            if isinstance(s.progress.get("updated_at"), str)
            else ""
        ),
        reverse=True,
    )
    return summaries


def read_progress(task_id: str) -> dict[str, Any] | None:
    """Return the parsed ``progress.json`` for ``task_id``, or ``None`` if missing."""

    task_dir = _output_root() / _validate_task_id(task_id)
    progress_path = task_dir / _PROGRESS_FILENAME
    if not progress_path.is_file():
        return None
    try:
        raw = json.loads(progress_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def read_evidence_pack(task_id: str) -> str | None:
    """Return the text of ``evidence-pack.md`` or ``None`` if missing."""

    return _read_text(task_id, _EVIDENCE_PACK_FILENAME)


def read_key_logs(task_id: str) -> str | None:
    """Return the text of ``key-logs.txt`` or ``None`` if missing.

    The analyzer writes ``key-logs.txt`` as plain text (one log line
    per non-empty line), not JSON.
    """

    return _read_text(task_id, _KEY_LOGS_FILENAME)


def read_case_draft(task_id: str) -> str | None:
    """Return the text of ``case-draft.md`` or ``None`` if missing."""

    return _read_text(task_id, _CASE_DRAFT_FILENAME)


def read_test_suggestions(task_id: str) -> str | None:
    """Return the text of ``test-suggestions.md`` or ``None`` if missing."""

    return _read_text(task_id, _TEST_SUGGESTIONS_FILENAME)


def read_monitor_suggestions(task_id: str) -> str | None:
    """Return the text of ``monitor-suggestions.md`` or ``None`` if missing."""

    return _read_text(task_id, _MONITOR_SUGGESTIONS_FILENAME)


def _read_text(task_id: str, filename: str) -> str | None:
    task_dir = _output_root() / _validate_task_id(task_id)
    path = task_dir / filename
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
