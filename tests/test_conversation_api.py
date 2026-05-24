"""Tests for diagnose_tool/api/routes_conversation.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client():
    """Create a FastAPI test client with the conversation router."""
    from diagnose_tool.api.routes_conversation import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_llm_config(tmp_path):
    """Create a mock LLM config."""
    from dataclasses import replace
    from diagnose_tool.core.llm_config import AppLLMConfig

    base_config = AppLLMConfig(
        enabled=True,
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        timeout=60,
        data_dir=tmp_path / "data",
    )
    return replace(base_config, enabled=True)


class TestConversationStartEndpoint:
    """Tests for POST /api/diagnosis/conversation endpoint."""

    def test_start_conversation_new_session(self, app_client, mock_llm_config, tmp_path):
        """Start new conversation with user context."""
        mock_metadata = MagicMock()
        mock_metadata.session_id = "test-session-123"
        mock_metadata.status = "active"
        mock_metadata.mode = "user-priority"
        mock_metadata.turns = []

        mock_turn = MagicMock()
        mock_turn.to_record.return_value = MagicMock(turn_id="001")

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_conversation_manager"
            ) as mock_mgr_factory:
                mock_manager = MagicMock()
                mock_manager.create_or_continue.return_value = (
                    mock_metadata,
                    mock_turn,
                    True,  # is_new
                )
                mock_mgr_factory.return_value = mock_manager

                with patch(
                    "diagnose_tool.api.routes_conversation._get_question_generator"
                ) as mock_qgen_factory:
                    mock_qgen = MagicMock()
                    mock_sufficiency = MagicMock()
                    mock_sufficiency.sufficient = True
                    mock_qgen.evaluate_sufficiency.return_value = mock_sufficiency

                    mock_diag_result = MagicMock()
                    mock_diag_result.diagnosis = "Database connection pool exhausted."
                    mock_qgen.generate_diagnosis.return_value = mock_diag_result
                    mock_qgen_factory.return_value = mock_qgen

                    response = app_client.post(
                        "/api/diagnosis/conversation",
                        json={
                            "user_context": {
                                "phenomenon": "Service responding slowly",
                                "stack": "",
                                "params": "",
                            },
                            "mode": "user-priority",
                            "max_follow_up_rounds": 3,
                        },
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["is_new_session"] is True
        assert data["state"] == "diagnosis_complete"
        assert "Database connection pool exhausted" in data["ai_diagnosis"]

    def test_start_conversation_insufficient_info_asks_question(
        self, app_client, mock_llm_config, tmp_path
    ):
        """When info is insufficient, AI should ask a follow-up question."""
        mock_metadata = MagicMock()
        mock_metadata.session_id = "test-session-456"
        mock_metadata.status = "active"
        mock_metadata.mode = "user-priority"
        mock_metadata.turns = []

        mock_turn = MagicMock()
        mock_turn.to_record.return_value = MagicMock(turn_id="001")

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_conversation_manager"
            ) as mock_mgr_factory:
                mock_manager = MagicMock()
                mock_manager.create_or_continue.return_value = (
                    mock_metadata,
                    mock_turn,
                    True,
                )
                mock_mgr_factory.return_value = mock_manager

                with patch(
                    "diagnose_tool.api.routes_conversation._get_question_generator"
                ) as mock_qgen_factory:
                    mock_qgen = MagicMock()
                    mock_sufficiency = MagicMock()
                    mock_sufficiency.sufficient = False
                    mock_sufficiency.missing = ["stack trace"]
                    mock_qgen.evaluate_sufficiency.return_value = mock_sufficiency

                    mock_q_result = MagicMock()
                    mock_q_result.question = "请提供完整的堆栈信息以便进一步分析。"
                    mock_qgen.generate_question.return_value = mock_q_result
                    mock_qgen_factory.return_value = mock_qgen

                    response = app_client.post(
                        "/api/diagnosis/conversation",
                        json={
                            "user_context": {
                                "phenomenon": "Service down",
                                "stack": "",
                                "params": "",
                            },
                            "mode": "user-priority",
                        },
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "awaiting_user_reply"
        assert data["ai_question"] is not None
        assert "堆栈" in data["ai_question"]

    def test_start_conversation_llm_disabled(self, app_client, mock_llm_config):
        """When LLM is disabled, should return 503."""
        from dataclasses import replace

        disabled_config = replace(mock_llm_config, enabled=False)

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = disabled_config

            response = app_client.post(
                "/api/diagnosis/conversation",
                json={
                    "user_context": {
                        "phenomenon": "Error",
                        "stack": "",
                        "params": "",
                    },
                },
            )

        assert response.status_code == 503


class TestConversationGetEndpoint:
    """Tests for GET /api/diagnosis/conversation/{session_id} endpoint."""

    def test_get_conversation_returns_history(self, app_client, mock_llm_config):
        """Get existing conversation history."""
        mock_metadata = MagicMock()
        mock_metadata.session_id = "session-123"
        mock_metadata.status = "active"
        mock_metadata.mode = "user-priority"

        mock_turn = MagicMock()
        mock_turn.to_dict.return_value = {
            "turn_id": "001",
            "user_context": {"phenomenon": "Error", "stack": "", "params": ""},
            "evidence_refs": [],
            "ai_question": None,
            "ai_diagnosis": "Memory leak detected",
        }

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_session_store"
            ) as mock_store_factory:
                mock_store = MagicMock()
                mock_store.get_session.return_value = mock_metadata
                mock_store.get_conversation_history.return_value = [mock_turn]
                mock_store_factory.return_value = mock_store

                response = app_client.get(
                    "/api/diagnosis/conversation/session-123"
                )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session-123"
        assert data["status"] == "active"
        assert len(data["turns"]) == 1

    def test_get_conversation_not_found(self, app_client, mock_llm_config):
        """Non-existent session returns 404."""
        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_session_store"
            ) as mock_store_factory:
                mock_store = MagicMock()
                mock_store.get_session.side_effect = Exception("Not found")
                mock_store_factory.return_value = mock_store

                response = app_client.get(
                    "/api/diagnosis/conversation/nonexistent"
                )

        assert response.status_code == 404


class TestConversationContinueEndpoint:
    """Tests for POST /api/diagnosis/conversation/{session_id}/continue endpoint."""

    def test_continue_conversation_with_reply(self, app_client, mock_llm_config):
        """User's reply to follow-up question."""
        mock_history = [
            MagicMock(
                user_context={"phenomenon": "Slow", "stack": "", "params": ""},
                evidence_refs=[],
                ai_question="请提供堆栈信息",
            )
        ]

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_conversation_manager"
            ) as mock_mgr_factory:
                mock_manager = MagicMock()
                mock_mgr_factory.return_value = mock_manager

                with patch(
                    "diagnose_tool.api.routes_conversation._get_session_store"
                ) as mock_store_factory:
                    mock_store = MagicMock()
                    mock_store.get_session.return_value = MagicMock()
                    mock_store.get_conversation_history.return_value = mock_history
                    mock_store_factory.return_value = mock_store

                    with patch(
                        "diagnose_tool.api.routes_conversation._get_question_generator"
                    ) as mock_qgen_factory:
                        mock_qgen = MagicMock()
                        mock_sufficiency = MagicMock()
                        mock_sufficiency.sufficient = True
                        mock_qgen.evaluate_sufficiency.return_value = mock_sufficiency

                        mock_diag = MagicMock()
                        mock_diag.diagnosis = "Thread pool exhausted."
                        mock_qgen.generate_diagnosis.return_value = mock_diag
                        mock_qgen_factory.return_value = mock_qgen

                        response = app_client.post(
                            "/api/diagnosis/conversation/session-123/continue",
                            json={"user_reply": "堆栈信息: java.lang.ThreadPool..."},
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session-123"
        assert data["state"] == "diagnosis_complete"

    def test_continue_conversation_no_history(self, app_client, mock_llm_config):
        """Continue without conversation history returns 400."""
        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_conversation_manager"
            ) as mock_mgr_factory:
                mock_manager = MagicMock()
                mock_mgr_factory.return_value = mock_manager

                with patch(
                    "diagnose_tool.api.routes_conversation._get_session_store"
                ) as mock_store_factory:
                    mock_store = MagicMock()
                    mock_store.get_session.return_value = MagicMock()
                    mock_store.get_conversation_history.return_value = []
                    mock_store_factory.return_value = mock_store

                    response = app_client.post(
                        "/api/diagnosis/conversation/session-123/continue",
                        json={"user_reply": "some reply"},
                    )

        assert response.status_code == 400


class TestConversationSkipEndpoint:
    """Tests for POST /api/diagnosis/conversation/{session_id}/skip endpoint."""

    def test_skip_follow_up(self, app_client, mock_llm_config):
        """Skip follow-up and force diagnosis."""
        mock_history = [
            MagicMock(
                user_context={"phenomenon": "Error", "stack": "", "params": ""},
                evidence_refs=[],
                ai_question="请提供更多信息",
            )
        ]

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_session_store"
            ) as mock_store_factory:
                mock_store = MagicMock()
                mock_store.get_session.return_value = MagicMock()
                mock_store.get_conversation_history.return_value = mock_history
                mock_store_factory.return_value = mock_store

                with patch(
                    "diagnose_tool.api.routes_conversation._get_question_generator"
                ) as mock_qgen_factory:
                    mock_qgen = MagicMock()
                    mock_diag = MagicMock()
                    mock_diag.diagnosis = "Possible deadlock detected."
                    mock_qgen.generate_diagnosis.return_value = mock_diag
                    mock_qgen_factory.return_value = mock_qgen

                    with patch(
                        "diagnose_tool.api.routes_conversation._get_conversation_manager"
                    ) as mock_mgr_factory:
                        mock_manager = MagicMock()
                        mock_mgr_factory.return_value = mock_manager

                        response = app_client.post(
                            "/api/diagnosis/conversation/session-123/skip"
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "skipped"
        assert "Possible deadlock" in data["ai_diagnosis"]


class TestConversationEndEndpoint:
    """Tests for POST /api/diagnosis/conversation/{session_id}/end endpoint."""

    def test_end_conversation_promotes_to_case(self, app_client, mock_llm_config, tmp_path):
        """High quality diagnosis should be promoted to case."""
        mock_metadata = MagicMock()
        mock_metadata.status = "active"

        mock_turn1 = MagicMock()
        mock_turn1.user_context = {
            "phenomenon": "Error",
            "stack": "java.lang.NullPointerException",
            "params": "id=123",
        }
        mock_turn1.evidence_refs = ["log-1"]
        mock_turn1.ai_question = None
        mock_turn1.ai_diagnosis = "Database connection failed."
        mock_turn1.to_dict.return_value = {
            "turn_id": "001",
            "user_context": {"phenomenon": "Error", "stack": "java.lang.NullPointerException", "params": "id=123"},
            "evidence_refs": ["log-1"],
            "ai_question": None,
            "ai_diagnosis": "Database connection failed.",
        }

        mock_turn2 = MagicMock()
        mock_turn2.user_context = {
            "phenomenon": "Error",
            "stack": "java.lang.NullPointerException",
            "params": "id=123",
        }
        mock_turn2.evidence_refs = ["log-1"]
        mock_turn2.ai_question = "What was the timeout?"
        mock_turn2.ai_diagnosis = None
        mock_turn2.to_dict.return_value = {
            "turn_id": "002",
            "user_context": {"phenomenon": "Error", "stack": "java.lang.NullPointerException", "params": "id=123"},
            "evidence_refs": ["log-1"],
            "ai_question": "What was the timeout?",
            "ai_diagnosis": None,
        }

        mock_history = [mock_turn1, mock_turn2]

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_session_store"
            ) as mock_store_factory:
                mock_store = MagicMock()
                mock_store.get_session.return_value = mock_metadata
                mock_store.get_conversation_history.return_value = mock_history
                mock_store_factory.return_value = mock_store

                with patch(
                    "diagnose_tool.api.routes_conversation._get_case_scorer"
                ) as mock_scorer_factory:
                    mock_scorer = MagicMock()
                    mock_score = MagicMock()
                    mock_score.to_dict.return_value = {
                        "total": 8.5,
                        "conversation_rounds": 10.0,
                        "user_questions": 8.0,
                        "completeness": 7.0,
                        "ai_confidence": 8.0,
                    }
                    mock_scorer.score_diagnosis.return_value = mock_score
                    mock_scorer.should_promote.return_value = True
                    mock_scorer_factory.return_value = mock_scorer

                    response = app_client.post(
                        "/api/diagnosis/conversation/session-123/end"
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["is_draft"] is False
        assert data["quality_score"]["total"] == 8.5

    def test_end_conversation_creates_draft(self, app_client, mock_llm_config, tmp_path):
        """Low quality diagnosis should be saved as draft."""
        mock_metadata = MagicMock()
        mock_metadata.status = "active"

        mock_turn = MagicMock()
        mock_turn.user_context = {"phenomenon": "Error", "stack": "", "params": ""}
        mock_turn.evidence_refs = []
        mock_turn.ai_question = None
        mock_turn.ai_diagnosis = "Possible issue."
        mock_turn.to_dict.return_value = {
            "turn_id": "001",
            "user_context": {"phenomenon": "Error", "stack": "", "params": ""},
            "evidence_refs": [],
            "ai_question": None,
            "ai_diagnosis": "Possible issue.",
        }

        mock_history = [mock_turn]

        with patch(
            "diagnose_tool.api.routes_conversation._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_conversation._get_session_store"
            ) as mock_store_factory:
                mock_store = MagicMock()
                mock_store.get_session.return_value = mock_metadata
                mock_store.get_conversation_history.return_value = mock_history
                mock_store_factory.return_value = mock_store

                with patch(
                    "diagnose_tool.api.routes_conversation._get_case_scorer"
                ) as mock_scorer_factory:
                    mock_scorer = MagicMock()
                    mock_score = MagicMock()
                    mock_score.to_dict.return_value = {
                        "total": 5.0,
                        "conversation_rounds": 2.0,
                        "user_questions": 2.0,
                        "completeness": 3.0,
                        "ai_confidence": 5.0,
                    }
                    mock_scorer.score_diagnosis.return_value = mock_score
                    mock_scorer.should_promote.return_value = False
                    mock_scorer_factory.return_value = mock_scorer

                    response = app_client.post(
                        "/api/diagnosis/conversation/session-123/end"
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["is_draft"] is True
        assert data["quality_score"]["total"] == 5.0
