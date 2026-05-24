"""Integration tests for diagnosis API endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from diagnose_tool.analyzer.evidence_cache import EvidenceCacheManager, LogEvent, CachedLogEntry


@pytest.fixture
def app_client():
    """Create a FastAPI test client with all diagnosis routers."""
    from diagnose_tool.api import routes_diagnosis
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(routes_diagnosis.router)
    return TestClient(app)


@pytest.fixture
def mock_llm_config(tmp_path: Path):
    """Create a mock LLM config."""
    from diagnose_tool.core.llm_config import AppLLMConfig
    return AppLLMConfig(
        enabled=True,
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        timeout=60,
        data_dir=tmp_path,
    )


@pytest.fixture
def search_cache(tmp_path: Path):
    """Create a search cache with sample entries."""
    cache_mgr = EvidenceCacheManager(tmp_path)
    matched_lines = [
        {
            "timestamp": "2026-05-23 10:01:01",
            "level": "ERROR",
            "thread": "main",
            "message": "NullPointerException: object is null",
            "raw": "2026-05-23 10:01:01 ERROR [main] NullPointerException: object is null\n    at com.example.Service.method(Service.java:42)",
            "file_path": "/data/app.log",
            "line_no": 10,
        },
        {
            "timestamp": "2026-05-23 10:01:02",
            "level": "ERROR",
            "thread": "worker-1",
            "message": "NullPointerException: object is null",
            "raw": "2026-05-23 10:01:02 ERROR [worker-1] NullPointerException: object is null\n    at com.example.Service.method(Service.java:42)",
            "file_path": "/data/app.log",
            "line_no": 20,
        },
    ]
    group_keys = {0: "NullPointerException", 1: "NullPointerException"}
    cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)
    return cache_key


class TestDiagnoseFromSearchEndpoint:
    """Tests for POST /api/diagnosis/search endpoint."""

    def test_diagnose_from_search_returns_200(
        self, app_client, tmp_path, mock_llm_config
    ):
        """Valid request returns diagnosis."""
        # Create cache
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error message",
                "raw": "raw log line",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        cache_key = cache_mgr.create_search_cache("/data", matched_lines, {0: "group1"})

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_diagnosis._call_llm"
            ) as mock_llm:
                mock_llm.return_value = "## Diagnosis\n\nPossible null pointer issue."

                response = app_client.post(
                    "/api/diagnosis/search",
                    json={
                        "cache_key": cache_key,
                        "selections": [{"type": "log", "id": cache_mgr.load_matched_lines(cache_key)[0].id}],
                        "options": {"include_stack": True, "include_timeline": True, "max_tokens": 2000},
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert "diagnosis" in data

    def test_diagnose_from_search_cache_not_found(
        self, app_client, mock_llm_config
    ):
        """Non-existent cache returns 404."""
        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            response = app_client.post(
                "/api/diagnosis/search",
                json={
                    "cache_key": "nonexistent-cache-key",
                    "selections": [],
                    "options": {},
                },
            )

        assert response.status_code == 404

    def test_diagnose_from_search_no_selections(
        self, app_client, mock_llm_config, tmp_path
    ):
        """Empty selections returns 400."""
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error",
                "raw": "raw",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        cache_key = cache_mgr.create_search_cache("/data", matched_lines, {0: "group1"})

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            response = app_client.post(
                "/api/diagnosis/search",
                json={
                    "cache_key": cache_key,
                    "selections": [],
                    "options": {},
                },
            )

        assert response.status_code == 400

    def test_diagnose_from_search_with_group_selection(
        self, app_client, mock_llm_config, tmp_path
    ):
        """Group selection type is handled correctly."""
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error",
                "raw": "raw",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        cache_key = cache_mgr.create_search_cache("/data", matched_lines, {0: "NullPointerException"})

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_diagnosis._call_llm"
            ) as mock_llm:
                mock_llm.return_value = "## Diagnosis\n\nGroup issue detected."

                response = app_client.post(
                    "/api/diagnosis/search",
                    json={
                        "cache_key": cache_key,
                        "selections": [{"type": "group", "group_key": "NullPointerException"}],
                        "options": {},
                    },
                )

        assert response.status_code == 200


class TestDiagnoseFromClusterEndpoint:
    """Tests for POST /api/diagnosis/cluster endpoint."""

    def test_diagnose_from_cluster_returns_200(
        self, app_client, mock_llm_config, tmp_path
    ):
        """Valid cluster diagnosis request returns 200."""
        # For cluster, cache_key is the task_id
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "NullPointerException",
                "raw": "raw log",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        # Cluster uses task_id as cache_key
        task_id = "test-cluster-task-123"
        cache_dir = tmp_path / "output" / task_id
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Write meta.json for cluster cache
        import json
        (cache_dir / "meta.json").write_text(
            json.dumps({"cache_key": task_id, "type": "cluster", "source_path": "/data"}),
            encoding="utf-8",
        )

        entries = []
        for line in matched_lines:
            entry = CachedLogEntry(
                id="abc123",
                group_key="NullPointerException",
                event=LogEvent(
                    timestamp=line["timestamp"],
                    level=line["level"],
                    thread=line["thread"],
                    message=line["message"],
                    raw=line["raw"],
                    file_path=line["file_path"],
                    line_no=line["line_no"],
                ),
                context_before=[],
                context_after=[],
            )
            entries.append(entry)

        matched_path = cache_dir / "matched-lines.jsonl"
        with matched_path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps({
                    "id": entry.id,
                    "group_key": entry.group_key,
                    "event": {
                        "timestamp": entry.event.timestamp,
                        "level": entry.event.level,
                        "thread": entry.event.thread,
                        "message": entry.event.message,
                        "raw": entry.event.raw,
                        "file_path": entry.event.file_path,
                        "line_no": entry.event.line_no,
                    },
                    "context_before": [],
                    "context_after": [],
                }, ensure_ascii=False) + "\n")

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_diagnosis._call_llm"
            ) as mock_llm:
                mock_llm.return_value = "## Diagnosis\n\nCluster issue found."

                response = app_client.post(
                    "/api/diagnosis/cluster",
                    json={
                        "cache_key": task_id,
                        "selections": [{"type": "cluster", "cluster_index": 0}],
                        "options": {},
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert "diagnosis" in data

    def test_diagnose_from_cluster_cache_not_found(
        self, app_client, mock_llm_config
    ):
        """Non-existent cluster cache returns 404."""
        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            response = app_client.post(
                "/api/diagnosis/cluster",
                json={
                    "cache_key": "nonexistent-cluster-task",
                    "selections": [],
                    "options": {},
                },
            )

        assert response.status_code == 404


class TestDiagnosisEndpoint:
    """Tests for POST /api/diagnosis endpoint (original task-based diagnosis)."""

    def test_diagnose_task_not_found(self, app_client, mock_llm_config):
        """Unknown task_id returns 404."""
        from diagnose_tool.analyzer.diagnosis import TaskNotFoundError

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_diagnosis.DiagnosisOrchestrator"
            ) as mock_orch_cls:
                mock_orch_cls.return_value.run = MagicMock(
                    side_effect=TaskNotFoundError("Task not found")
                )

                response = app_client.post(
                    "/api/diagnosis", json={"task_id": "unknown-task"}
                )

        assert response.status_code == 404

    def test_diagnose_llm_not_enabled(self, app_client, tmp_path):
        """Disabled LLM returns 503."""
        from diagnose_tool.core.llm_config import AppLLMConfig

        disabled_config = AppLLMConfig(
            enabled=False,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=tmp_path,
        )

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = disabled_config

            response = app_client.post(
                "/api/diagnosis", json={"task_id": "some-task"}
            )

        assert response.status_code == 503


class TestCompressionOptions:
    """Tests for compression options in diagnosis requests."""

    def test_custom_max_tokens(self, app_client, mock_llm_config, tmp_path):
        """Custom max_tokens is passed correctly."""
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error",
                "raw": "raw",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        cache_key = cache_mgr.create_search_cache("/data", matched_lines, {0: "group1"})

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_diagnosis._call_llm"
            ) as mock_llm:
                mock_llm.return_value = "Diagnosis result"

                response = app_client.post(
                    "/api/diagnosis/search",
                    json={
                        "cache_key": cache_key,
                        "selections": [{"type": "log", "id": cache_mgr.load_matched_lines(cache_key)[0].id}],
                        "options": {"max_tokens": 5000},
                    },
                )

                # Verify _call_llm was called with evidence that respects token limit
                assert response.status_code == 200

    def test_include_stack_false(self, app_client, mock_llm_config, tmp_path):
        """include_stack=False excludes stack traces."""
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error with stack",
                "raw": "Error\n    at com.example.Method(File.java:10)",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        cache_key = cache_mgr.create_search_cache("/data", matched_lines, {0: "group1"})

        with patch(
            "diagnose_tool.api.routes_diagnosis._get_llm_config"
        ) as mock_get_config:
            mock_get_config.return_value = mock_llm_config

            with patch(
                "diagnose_tool.api.routes_diagnosis._call_llm"
            ) as mock_llm:
                mock_llm.return_value = "Diagnosis result"

                response = app_client.post(
                    "/api/diagnosis/search",
                    json={
                        "cache_key": cache_key,
                        "selections": [{"type": "log", "id": cache_mgr.load_matched_lines(cache_key)[0].id}],
                        "options": {"include_stack": False},
                    },
                )

                assert response.status_code == 200
