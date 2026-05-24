"""Session filesystem storage — pure Python, FastAPI-independent."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# --- Exceptions ---------------------------------------------------------


class SessionError(RuntimeError):
    """Base exception for session errors."""
    pass


class SessionNotFoundError(SessionError):
    """Raised when session directory not found."""
    pass


class SessionCorruptedError(SessionError):
    """Raised when session metadata is corrupted."""
    pass


# --- Data Models --------------------------------------------------------


@dataclass
class TurnRecord:
    """A single conversation turn."""

    turn_id: str
    user_context: dict[str, str]
    evidence_refs: list[str]
    ai_question: str | None = None
    ai_diagnosis: str | None = None
    mode: str = "user-priority"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_context": self.user_context,
            "evidence_refs": self.evidence_refs,
            "ai_question": self.ai_question,
            "ai_diagnosis": self.ai_diagnosis,
            "mode": self.mode,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TurnRecord:
        return cls(
            turn_id=data["turn_id"],
            user_context=data.get("user_context", {}),
            evidence_refs=data.get("evidence_refs", []),
            ai_question=data.get("ai_question"),
            ai_diagnosis=data.get("ai_diagnosis"),
            mode=data.get("mode", "user-priority"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class SessionMetadata:
    """Session metadata stored in metadata.yaml."""

    session_id: str
    created_at: str
    last_active: str
    mode: str = "user-priority"
    turns: list[str] = field(default_factory=list)
    status: str = "active"  # active, completed, abandoned

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "mode": self.mode,
            "turns": self.turns,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMetadata:
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            last_active=data["last_active"],
            mode=data.get("mode", "user-priority"),
            turns=data.get("turns", []),
            status=data.get("status", "active"),
        )


# --- Session Store ------------------------------------------------------


class SessionStore:
    """Filesystem-based session storage.

    Storage structure:
        data/sessions/{session_id}/
        ├── metadata.yaml       # SessionMetadata
        ├── conversation/
        │   ├── turn-001.json  # TurnRecord
        │   ├── turn-002.json
        │   └── ...
        └── draft_case/         # temporary draft if quality is low
    """

    def __init__(self, sessions_dir: Path) -> None:
        self._sessions_dir = Path(sessions_dir)

    def create_session(self, session_id: str, mode: str = "user-priority") -> SessionMetadata:
        """Create a new session.

        Args:
            session_id: UUID session identifier.
            mode: Initial diagnosis mode.

        Returns:
            The created SessionMetadata.

        Raises:
            SessionError: If session already exists.
        """
        session_dir = self._session_dir(session_id)
        if session_dir.exists():
            raise SessionError(f"Session already exists: {session_id}")

        now = datetime.now(timezone.utc).isoformat()
        metadata = SessionMetadata(
            session_id=session_id,
            created_at=now,
            last_active=now,
            mode=mode,
            turns=[],
            status="active",
        )

        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "conversation").mkdir(exist_ok=True)

        self._write_metadata(session_dir, metadata)
        logger.info("Created session: %s", session_id)
        return metadata

    def get_session(self, session_id: str) -> SessionMetadata:
        """Load session metadata.

        Args:
            session_id: Session identifier.

        Returns:
            The SessionMetadata.

        Raises:
            SessionNotFoundError: If session does not exist.
            SessionCorruptedError: If metadata.yaml is invalid.
        """
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")

        try:
            return self._read_metadata(session_dir)
        except Exception as exc:
            raise SessionCorruptedError(f"Corrupted session {session_id}: {exc}") from exc

    def update_session(self, metadata: SessionMetadata) -> None:
        """Update session metadata.

        Args:
            metadata: Updated metadata to persist.
        """
        session_dir = self._session_dir(metadata.session_id)
        if not session_dir.exists():
            raise SessionNotFoundError(f"Session not found: {metadata.session_id}")

        metadata.last_active = datetime.now(timezone.utc).isoformat()
        self._write_metadata(session_dir, metadata)
        logger.debug("Updated session: %s", metadata.session_id)

    def add_turn(self, session_id: str, turn: TurnRecord) -> TurnRecord:
        """Add a turn to the session conversation history.

        Args:
            session_id: Session identifier.
            turn: Turn to add.

        Returns:
            The added TurnRecord.

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")

        turn_path = session_dir / "conversation" / f"turn-{turn.turn_id}.json"
        turn_path.write_text(
            _json_dumps(turn.to_dict()), encoding="utf-8"
        )

        # Update metadata with new turn
        metadata = self.get_session(session_id)
        if turn.turn_id not in metadata.turns:
            metadata.turns.append(turn.turn_id)
        metadata.last_active = datetime.now(timezone.utc).isoformat()
        self._write_metadata(session_dir, metadata)

        logger.debug("Added turn %s to session %s", turn.turn_id, session_id)
        return turn

    def get_turn(self, session_id: str, turn_id: str) -> TurnRecord:
        """Load a specific turn.

        Args:
            session_id: Session identifier.
            turn_id: Turn identifier (e.g., "001").

        Returns:
            The TurnRecord.

        Raises:
            SessionNotFoundError: If session does not exist.
            FileNotFoundError: If turn file does not exist.
        """
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")

        turn_path = session_dir / "conversation" / f"turn-{turn_id}.json"
        if not turn_path.exists():
            raise FileNotFoundError(f"Turn not found: {turn_path}")

        data = _json_loads(turn_path.read_text(encoding="utf-8"))
        return TurnRecord.from_dict(data)

    def get_conversation_history(self, session_id: str) -> list[TurnRecord]:
        """Load all conversation turns in order.

        Args:
            session_id: Session identifier.

        Returns:
            List of TurnRecords in chronological order.

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        metadata = self.get_session(session_id)
        turns = []
        for turn_id in metadata.turns:
            try:
                turns.append(self.get_turn(session_id, turn_id))
            except FileNotFoundError:
                logger.warning("Turn %s missing for session %s", turn_id, session_id)
        return turns

    def cleanup_inactive(self, max_age_days: int = 7) -> int:
        """Remove sessions inactive for more than max_age_days.

        Args:
            max_age_days: Sessions inactive longer than this are removed.

        Returns:
            Number of sessions removed.
        """
        if not self._sessions_dir.exists():
            return 0

        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
        removed = 0

        for session_path in self._sessions_dir.iterdir():
            if not session_path.is_dir():
                continue
            try:
                metadata = self._read_metadata(session_path)
                last_active = datetime.fromisoformat(metadata.last_active)
                if last_active.timestamp() < cutoff:
                    _rmtree(session_path)
                    removed += 1
                    logger.info("Removed inactive session: %s", metadata.session_id)
            except Exception as exc:
                logger.warning("Failed to check session %s: %s", session_path, exc)

        return removed

    def _session_dir(self, session_id: str) -> Path:
        return self._sessions_dir / session_id

    def _read_metadata(self, session_dir: Path) -> SessionMetadata:
        metadata_path = session_dir / "metadata.yaml"
        if not metadata_path.exists():
            raise SessionCorruptedError(f"Missing metadata.yaml in {session_dir}")

        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        if data is None:
            raise SessionCorruptedError(f"Empty metadata.yaml in {session_dir}")
        return SessionMetadata.from_dict(data)

    def _write_metadata(self, session_dir: Path, metadata: SessionMetadata) -> None:
        metadata_path = session_dir / "metadata.yaml"
        metadata_path.write_text(
            yaml.safe_dump(metadata.to_dict(), allow_unicode=True),
            encoding="utf-8",
        )


# --- Helpers ------------------------------------------------------------


def _json_dumps(data: dict[str, Any]) -> str:
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)


def _json_loads(text: str) -> dict[str, Any]:
    import json
    return json.loads(text)


def _rmtree(path: Path) -> None:
    """Remove directory recursively."""
    import shutil
    shutil.rmtree(path)
