"""Tests for diagnose_tool/api/routes_diagnosis.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from diagnose_tool.analyzer.diagnosis import (
    TaskNotFoundError,
)
from diagnose_tool.core.llm_client import LLMClientError


@pytest.fixture
def app_client():
    """Create a FastAPI test client with the diagnosis router."""
    from diagnose_tool.api.routes_diagnosis import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestDiagnosisAPI:
    """Tests for POST /api/diagnosis endpoint."""

    def test_valid_task_id_returns_200_with_case_id_and_diagnosis(
        self, app_client
    ) -> None:
        """Valid task_id → 200 with case_id and diagnosis fields."""
        mock_orchestrator_run = MagicMock(
            return_value=("task-001", "## Diagnosis\n\nDatabase timeout detected.")
        )

        with patch(
            "diagnose_tool.api.routes_diagnosis.DiagnosisOrchestrator"
        ) as mock_orch_cls:
            mock_orch_cls.return_value.run = mock_orchestrator_run

            # Also need to patch the llm_config loader to avoid file system dependency
            with patch(
                "diagnose_tool.api.routes_diagnosis._get_llm_config"
            ) as mock_get_config:
                from diagnose_tool.core.llm_config import AppLLMConfig

                mock_config = AppLLMConfig(
                    enabled=True,
                    model="gpt-4o-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="test-key",
                    timeout=60,
                    data_dir=Path("/tmp/data"),
                )
                mock_get_config.return_value = mock_config

                response = app_client.post(
                    "/api/diagnosis", json={"task_id": "task-001"}
                )

        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert "diagnosis" in data
        assert data["case_id"] == "task-001"
        assert "Database timeout detected" in data["diagnosis"]

    def test_unknown_task_id_returns_404(self, app_client) -> None:
        """Unknown task_id → 404."""
        with patch(
            "diagnose_tool.api.routes_diagnosis.DiagnosisOrchestrator"
        ) as mock_orch_cls:
            mock_orch_cls.return_value.run = MagicMock(
                side_effect=TaskNotFoundError("Task not found")
            )

            with patch(
                "diagnose_tool.api.routes_diagnosis._get_llm_config"
            ) as mock_get_config:
                from diagnose_tool.core.llm_config import AppLLMConfig

                mock_config = AppLLMConfig(
                    enabled=True,
                    model="gpt-4o-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="test-key",
                    timeout=60,
                    data_dir=Path("/tmp/data"),
                )
                mock_get_config.return_value = mock_config

                response = app_client.post(
                    "/api/diagnosis", json={"task_id": "nonexistent-task"}
                )

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_llm_disabled_returns_503(self, app_client) -> None:
        """llm.enabled=false → 503."""
        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            from diagnose_tool.core.llm_config import AppLLMConfig

            mock_config = AppLLMConfig(
                enabled=False,
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                api_key="",
                timeout=60,
                data_dir=Path("/tmp/data"),
            )
            mock_get_config.return_value = mock_config

            response = app_client.post(
                "/api/diagnosis", json={"task_id": "any-task"}
            )

        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"]

    def test_empty_task_id_returns_400(self, app_client) -> None:
        """Empty task_id → 400."""
        response = app_client.post(
            "/api/diagnosis", json={"task_id": ""}
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_llm_api_error_returns_500_safe_message(self, app_client) -> None:
        """LLM API error → 500 with safe message (no API key leaked)."""
        with patch(
            "diagnose_tool.api.routes_diagnosis.DiagnosisOrchestrator"
        ) as mock_orch_cls:
            mock_orch_cls.return_value.run = MagicMock(
                side_effect=LLMClientError("LLM API returned 500")
            )

            with patch(
                "diagnose_tool.api.routes_diagnosis._get_llm_config"
            ) as mock_get_config:
                from diagnose_tool.core.llm_config import AppLLMConfig

                mock_config = AppLLMConfig(
                    enabled=True,
                    model="gpt-4o-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="super-secret-key-12345",
                    timeout=60,
                    data_dir=Path("/tmp/data"),
                )
                mock_get_config.return_value = mock_config

                response = app_client.post(
                    "/api/diagnosis", json={"task_id": "task-001"}
                )

        assert response.status_code == 500
        detail = response.json()["detail"]
        # Ensure API key doesn't appear in response
        assert "super-secret-key-12345" not in detail
        assert "test-key" not in detail
        assert "api_key" not in detail.lower()

    def test_response_body_contains_case_id_and_diagnosis_fields(
        self, app_client
    ) -> None:
        """200 response body contains case_id and diagnosis string fields."""
        mock_orchestrator_run = MagicMock(
            return_value=("case-123", "Root cause: database pool exhaustion.")
        )

        with patch(
            "diagnose_tool.api.routes_diagnosis.DiagnosisOrchestrator"
        ) as mock_orch_cls:
            mock_orch_cls.return_value.run = mock_orchestrator_run

            with patch(
                "diagnose_tool.api.routes_diagnosis._get_llm_config"
            ) as mock_get_config:
                from diagnose_tool.core.llm_config import AppLLMConfig

                mock_config = AppLLMConfig(
                    enabled=True,
                    model="gpt-4o-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="test-key",
                    timeout=60,
                    data_dir=Path("/tmp/data"),
                )
                mock_get_config.return_value = mock_config

                response = app_client.post(
                    "/api/diagnosis", json={"task_id": "task-001"}
                )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("case_id"), str)
        assert isinstance(data.get("diagnosis"), str)
        assert len(data["case_id"]) > 0
        assert len(data["diagnosis"]) > 0