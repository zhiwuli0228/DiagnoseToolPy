"""Tests for session_store module."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from diagnose_tool.analyzer.session_store import (
    SessionCorruptedError,
    SessionMetadata,
    SessionNotFoundError,
    SessionStore,
    SessionError,
    TurnRecord,
)


class TestTurnRecord:
    def test_turn_record_to_dict(self):
        turn = TurnRecord(
            turn_id="001",
            user_context={"phenomenon": "high cpu"},
            evidence_refs=["log-1", "log-2"],
            ai_question="What was the thread count?",
            mode="user-priority",
        )
        result = turn.to_dict()
        assert result["turn_id"] == "001"
        assert result["user_context"] == {"phenomenon": "high cpu"}
        assert result["evidence_refs"] == ["log-1", "log-2"]
        assert result["ai_question"] == "What was the thread count?"
        assert result["ai_diagnosis"] is None
        assert result["mode"] == "user-priority"
        assert "timestamp" in result

    def test_turn_record_from_dict(self):
        data = {
            "turn_id": "002",
            "user_context": {"stack": "NullPointerException"},
            "evidence_refs": [],
            "ai_question": None,
            "ai_diagnosis": "Memory leak detected",
            "mode": "log-priority",
            "timestamp": "2026-05-24T10:00:00Z",
        }
        turn = TurnRecord.from_dict(data)
        assert turn.turn_id == "002"
        assert turn.user_context == {"stack": "NullPointerException"}
        assert turn.evidence_refs == []
        assert turn.ai_question is None
        assert turn.ai_diagnosis == "Memory leak detected"
        assert turn.mode == "log-priority"
        assert turn.timestamp == "2026-05-24T10:00:00Z"

    def test_turn_record_from_dict_with_defaults(self):
        data = {"turn_id": "003", "user_context": {}, "evidence_refs": []}
        turn = TurnRecord.from_dict(data)
        assert turn.turn_id == "003"
        assert turn.ai_question is None
        assert turn.ai_diagnosis is None
        assert turn.mode == "user-priority"


class TestSessionMetadata:
    def test_session_metadata_to_dict(self):
        metadata = SessionMetadata(
            session_id="test-123",
            created_at="2026-05-24T10:00:00Z",
            last_active="2026-05-24T11:00:00Z",
            mode="log-priority",
            turns=["001", "002"],
            status="active",
        )
        result = metadata.to_dict()
        assert result["session_id"] == "test-123"
        assert result["created_at"] == "2026-05-24T10:00:00Z"
        assert result["last_active"] == "2026-05-24T11:00:00Z"
        assert result["mode"] == "log-priority"
        assert result["turns"] == ["001", "002"]
        assert result["status"] == "active"

    def test_session_metadata_from_dict(self):
        data = {
            "session_id": "test-456",
            "created_at": "2026-05-24T09:00:00Z",
            "last_active": "2026-05-24T12:00:00Z",
            "mode": "user-priority",
            "turns": ["001"],
            "status": "completed",
        }
        metadata = SessionMetadata.from_dict(data)
        assert metadata.session_id == "test-456"
        assert metadata.created_at == "2026-05-24T09:00:00Z"
        assert metadata.last_active == "2026-05-24T12:00:00Z"
        assert metadata.mode == "user-priority"
        assert metadata.turns == ["001"]
        assert metadata.status == "completed"


class TestSessionStore:
    @pytest.fixture
    def sessions_dir(self, tmp_path):
        return tmp_path / "sessions"

    @pytest.fixture
    def store(self, sessions_dir):
        sessions_dir.mkdir()
        return SessionStore(sessions_dir)

    def test_create_session(self, store):
        session_id = str(uuid.uuid4())
        metadata = store.create_session(session_id, mode="user-priority")

        assert metadata.session_id == session_id
        assert metadata.mode == "user-priority"
        assert metadata.status == "active"
        assert metadata.turns == []
        assert metadata.created_at != ""
        assert metadata.last_active != ""

        # Verify directory structure
        session_dir = store._session_dir(session_id)
        assert session_dir.exists()
        assert (session_dir / "metadata.yaml").exists()
        assert (session_dir / "conversation").is_dir()

    def test_create_session_with_log_priority(self, store):
        session_id = str(uuid.uuid4())
        metadata = store.create_session(session_id, mode="log-priority")
        assert metadata.mode == "log-priority"

    def test_create_session_duplicate_raises(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)
        with pytest.raises(SessionError, match="Session already exists"):
            store.create_session(session_id)

    def test_get_session(self, store):
        session_id = str(uuid.uuid4())
        created = store.create_session(session_id)
        retrieved = store.get_session(session_id)

        assert retrieved.session_id == created.session_id
        assert retrieved.created_at == created.created_at
        assert retrieved.mode == created.mode
        assert retrieved.status == created.status

    def test_get_session_not_found(self, store):
        with pytest.raises(SessionNotFoundError, match="Session not found"):
            store.get_session("nonexistent-id")

    def test_update_session(self, store):
        session_id = str(uuid.uuid4())
        metadata = store.create_session(session_id)

        metadata.status = "completed"
        store.update_session(metadata)

        retrieved = store.get_session(session_id)
        assert retrieved.status == "completed"
        # last_active should be updated
        assert retrieved.last_active >= metadata.last_active

    def test_update_session_not_found(self, store):
        metadata = SessionMetadata(
            session_id="nonexistent",
            created_at="2026-05-24T10:00:00Z",
            last_active="2026-05-24T10:00:00Z",
        )
        with pytest.raises(SessionNotFoundError, match="Session not found"):
            store.update_session(metadata)

    def test_add_turn(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        turn = TurnRecord(
            turn_id="001",
            user_context={"phenomenon": "slow response"},
            evidence_refs=["log-1"],
            ai_question="What is the error code?",
            mode="user-priority",
        )
        stored_turn = store.add_turn(session_id, turn)

        assert stored_turn.turn_id == "001"
        assert stored_turn.ai_question == "What is the error code?"

        # Verify metadata was updated
        metadata = store.get_session(session_id)
        assert "001" in metadata.turns

        # Verify turn file was created
        turn_path = store._session_dir(session_id) / "conversation" / "turn-001.json"
        assert turn_path.exists()

    def test_add_turn_updates_last_active(self, store):
        session_id = str(uuid.uuid4())
        metadata = store.create_session(session_id)
        original_last_active = metadata.last_active

        import time
        time.sleep(0.01)

        turn = TurnRecord(
            turn_id="001",
            user_context={},
            evidence_refs=[],
        )
        store.add_turn(session_id, turn)

        updated = store.get_session(session_id)
        assert updated.last_active > original_last_active

    def test_add_turn_session_not_found(self, store):
        turn = TurnRecord(
            turn_id="001",
            user_context={},
            evidence_refs=[],
        )
        with pytest.raises(SessionNotFoundError, match="Session not found"):
            store.add_turn("nonexistent", turn)

    def test_get_turn(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        turn = TurnRecord(
            turn_id="002",
            user_context={"params": "timeout=30"},
            evidence_refs=["log-a", "log-b"],
            ai_diagnosis="Connection pool exhausted",
            mode="log-priority",
        )
        store.add_turn(session_id, turn)

        retrieved = store.get_turn(session_id, "002")
        assert retrieved.turn_id == "002"
        assert retrieved.user_context == {"params": "timeout=30"}
        assert retrieved.evidence_refs == ["log-a", "log-b"]
        assert retrieved.ai_diagnosis == "Connection pool exhausted"
        assert retrieved.mode == "log-priority"

    def test_get_turn_not_found(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        with pytest.raises(FileNotFoundError, match="Turn not found"):
            store.get_turn(session_id, "999")

    def test_get_turn_session_not_found(self, store):
        with pytest.raises(SessionNotFoundError, match="Session not found"):
            store.get_turn("nonexistent", "001")

    def test_get_conversation_history(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        turn1 = TurnRecord(turn_id="001", user_context={}, evidence_refs=[])
        turn2 = TurnRecord(
            turn_id="002",
            user_context={},
            evidence_refs=[],
            ai_question="Any stack trace?",
        )
        turn3 = TurnRecord(
            turn_id="003",
            user_context={},
            evidence_refs=[],
            ai_diagnosis="Final diagnosis",
        )

        store.add_turn(session_id, turn1)
        store.add_turn(session_id, turn2)
        store.add_turn(session_id, turn3)

        history = store.get_conversation_history(session_id)
        assert len(history) == 3
        assert history[0].turn_id == "001"
        assert history[1].turn_id == "002"
        assert history[1].ai_question == "Any stack trace?"
        assert history[2].turn_id == "003"
        assert history[2].ai_diagnosis == "Final diagnosis"

    def test_get_conversation_history_empty(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        history = store.get_conversation_history(session_id)
        assert history == []


class TestSessionStoreCleanup:
    @pytest.fixture
    def sessions_dir(self, tmp_path):
        return tmp_path / "sessions"

    @pytest.fixture
    def store(self, sessions_dir):
        sessions_dir.mkdir()
        return SessionStore(sessions_dir)

    def test_cleanup_inactive_removes_old_sessions(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        # Manually modify the metadata to make it old
        session_dir = store._session_dir(session_id)
        metadata_path = session_dir / "metadata.yaml"
        metadata = yaml.safe_load(metadata_path.read_text())
        # Set last_active to 10 days ago
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        metadata["last_active"] = old_date
        metadata_path.write_text(yaml.safe_dump(metadata), encoding="utf-8")

        removed = store.cleanup_inactive(max_age_days=7)
        assert removed == 1
        assert not session_dir.exists()

    def test_cleanup_inactive_keeps_recent_sessions(self, store):
        session_id = str(uuid.uuid4())
        store.create_session(session_id)

        removed = store.cleanup_inactive(max_age_days=7)
        assert removed == 0
        assert store._session_dir(session_id).exists()

    def test_cleanup_inactive_nonexistent_dir(self, store):
        # sessions_dir doesn't exist - should return 0
        store._sessions_dir.rmdir()
        removed = store.cleanup_inactive(max_age_days=7)
        assert removed == 0

    def test_cleanup_inactive_multiple_sessions(self, store):
        # Create 3 sessions, make 2 old
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        id3 = str(uuid.uuid4())

        store.create_session(id1)
        store.create_session(id2)
        store.create_session(id3)

        # Make id1 and id3 old
        for sid in [id1, id3]:
            session_dir = store._session_dir(sid)
            metadata_path = session_dir / "metadata.yaml"
            metadata = yaml.safe_load(metadata_path.read_text())
            old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            metadata["last_active"] = old_date
            metadata_path.write_text(yaml.safe_dump(metadata), encoding="utf-8")

        removed = store.cleanup_inactive(max_age_days=7)
        assert removed == 2
        assert store._session_dir(id2).exists()
        assert not store._session_dir(id1).exists()
        assert not store._session_dir(id3).exists()
