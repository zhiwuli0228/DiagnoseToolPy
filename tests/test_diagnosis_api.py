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

    def test_llm_api_error_returns_degraded_response(self, app_client) -> None:
        """LLM API error → 503 with degraded response including workspace export option."""
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

        assert response.status_code == 503
        data = response.json()
        detail = data.get("detail", {})
        # Verify degraded response structure
        assert detail.get("degraded") is True
        assert detail.get("error_type") == "llm_error"
        assert "workspace_export_url" in detail
        assert "workspace_export_options" in detail
        # Ensure API key doesn't appear in response
        response_str = str(detail)
        assert "super-secret-key-12345" not in response_str
        assert "test-key" not in response_str

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


class TestCheckResultEndpoint:
    """Tests for GET /api/diagnosis/check-result endpoint."""

    def test_check_result_returns_not_found_when_directory_missing(self, app_client: TestClient) -> None:
        """Non-existent directory returns exists: false."""
        response = app_client.get("/api/diagnosis/check-result?workspace_dir=/nonexistent/path")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert data["content"] is None

    def test_check_result_returns_not_found_when_result_md_missing(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Directory without result.md returns exists: false."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        response = app_client.get(f"/api/diagnosis/check-result?workspace_dir={workspace}")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False

    def test_check_result_rejects_empty_result_md(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Empty result.md returns exists: true but content: null."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "result.md").write_text("", encoding="utf-8")

        response = app_client.get(f"/api/diagnosis/check-result?workspace_dir={workspace}")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["content"] is None
        assert data["validation"]["is_empty"] is True

    def test_check_result_rejects_too_short_content(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Content less than 100 chars returns content: null."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "result.md").write_text("Too short", encoding="utf-8")

        response = app_client.get(f"/api/diagnosis/check-result?workspace_dir={workspace}")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["content"] is None
        assert data["validation"]["is_too_short"] is True

    def test_check_result_rejects_prompt_template(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Content that looks like prompt template returns content: null."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        prompt_content = """# Role
You are an experienced backend stability engineer.
# Current Fault Evidence
{evidence_pack}
# Diagnosis Instructions
Please analyze and provide a diagnosis.
"""
        (workspace / "result.md").write_text(prompt_content, encoding="utf-8")

        response = app_client.get(f"/api/diagnosis/check-result?workspace_dir={workspace}")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["content"] is None
        assert data["validation"]["is_prompt_template"] is True

    def test_check_result_accepts_valid_diagnosis(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Valid diagnosis content is returned."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        valid_content = """# Diagnosis Result

## Root Cause
Database connection pool exhaustion due to slow queries.

## Evidence
- Connection pool size: 10
- Active connections: 10
- Wait queue: 50+

## Solution
1. Increase pool size to 50
2. Optimize slow queries
3. Add connection timeout
"""
        (workspace / "result.md").write_text(valid_content, encoding="utf-8")

        response = app_client.get(f"/api/diagnosis/check-result?workspace_dir={workspace}")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["content"] == valid_content
        assert data["validation"]["is_empty"] is False
        assert data["validation"]["is_too_short"] is False
        assert data["validation"]["is_prompt_template"] is False


class TestExportWorkspaceEndpoint:
    """Tests for POST /api/diagnosis/export-workspace endpoint."""

    def test_export_workspace_requires_source(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Request without task_id, session_id, or cache_key returns 400."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

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
                data_dir=tmp_path,
            )
            mock_get_config.return_value = mock_config

            response = app_client.post(
                "/api/diagnosis/export-workspace",
                json={"workspace_dir": str(workspace)},
            )

        assert response.status_code == 400
        assert "At least one of task_id, session_id, or cache_key must be provided" in response.json()["detail"]

    def test_export_workspace_rejects_nonexistent_directory(
        self, app_client: TestClient
    ) -> None:
        """Non-existent workspace_dir returns 400."""
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
                data_dir=tmp_path,
            )
            mock_get_config.return_value = mock_config

            response = app_client.post(
                "/api/diagnosis/export-workspace",
                json={"workspace_dir": "/nonexistent/path", "task_id": "task-001"},
            )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_export_workspace_with_cache_key_and_selections(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Export with cache_key and selections succeeds."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create data directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create evidence cache
        cache_dir = data_dir / "cache" / "test-cache-key"
        cache_dir.mkdir(parents=True)
        (cache_dir / "matched-lines.jsonl").write_text(
            '{"id": "log-1", "event": {"timestamp": "2026-05-23 10:00:00", "level": "ERROR", "thread": "main", "message": "Connection failed"}, "group_key": "error"}',
            encoding="utf-8"
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
                data_dir=data_dir,
            )
            mock_get_config.return_value = mock_config

            response = app_client.post(
                "/api/diagnosis/export-workspace",
                json={
                    "workspace_dir": str(workspace),
                    "cache_key": "test-cache-key",
                    "selections": [{"type": "log", "id": "log-1"}],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workspace_dir"] == str(workspace)
        assert "files_written" in data
        assert len(data["files_written"]) > 0

    def test_export_workspace_response_structure(
        self, app_client: TestClient, tmp_path: Path
    ) -> None:
        """Response contains success, workspace_dir, files_written, and detection_hint."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create data directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create evidence cache
        cache_dir = data_dir / "cache" / "test-cache-key-2"
        cache_dir.mkdir(parents=True)
        (cache_dir / "matched-lines.jsonl").write_text(
            '{"id": "log-1", "event": {"timestamp": "2026-05-23 10:00:00", "level": "ERROR", "thread": "main", "message": "Connection failed"}, "group_key": "error"}',
            encoding="utf-8"
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
                data_dir=data_dir,
            )
            mock_get_config.return_value = mock_config

            response = app_client.post(
                "/api/diagnosis/export-workspace",
                json={
                    "workspace_dir": str(workspace),
                    "cache_key": "test-cache-key-2",
                    "selections": [{"type": "log", "id": "log-1"}],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["success"], bool)
        assert isinstance(data["workspace_dir"], str)
        assert isinstance(data["files_written"], list)
        assert "detection_hint" in data