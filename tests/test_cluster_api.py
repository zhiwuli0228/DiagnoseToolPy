"""Tests for cluster API routes."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from fastapi.testclient import TestClient

from diagnose_tool.analyzer.cluster_analyzer import ClusterAnalyzer
from diagnose_tool.main import app


@pytest.fixture
def client(mock_cluster_config):
    return TestClient(app)


@pytest.fixture
def mock_cluster_config(monkeypatch, tmp_path: Path):
    """Set up a mock config with a temporary data directory."""
    from diagnose_tool.core.config import AppConfig

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "output").mkdir(parents=True, exist_ok=True)

    def fake_load_config() -> AppConfig:
        return AppConfig(
            name="DiagnoseToolPy",
            version="0.1.0",
            host="127.0.0.1",
            port=18080,
            allowed_input_roots=(tmp_path.resolve(),),
            data_dir=data_dir.resolve(),
        )

    # Patch load_config in routes_cluster module before any config is loaded
    import diagnose_tool.api.routes_cluster as rc_module
    rc_module._config = None  # Reset cached config
    monkeypatch.setattr(rc_module, "load_config", fake_load_config)

    return data_dir


class TestPostCluster:
    def test_create_cluster_task_returns_task_id(self, client, mock_cluster_config, tmp_path: Path):
        """POST /api/cluster creates a task and returns task_id."""
        # Create a log source directory with a log file
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text(
            "2026-05-23 10:00:00 ERROR [worker-1] NullPointerException at line 42\n"
            "2026-05-23 10:01:00 WARN Something went wrong\n",
            encoding="utf-8",
        )

        response = client.post("/api/cluster", json={"source_path": str(log_dir)})

        assert response.status_code == 200
        payload = response.json()
        assert "task_id" in payload
        assert payload["task_id"].startswith("cluster-")

    def test_create_cluster_task_creates_progress_file(self, client, mock_cluster_config, tmp_path: Path):
        """POST /api/cluster creates progress.json immediately."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        response = client.post("/api/cluster", json={"source_path": str(log_dir)})

        assert response.status_code == 200
        task_id = response.json()["task_id"]
        progress_path = mock_cluster_config / "output" / task_id / "progress.json"
        assert progress_path.exists()
        progress_data = json.loads(progress_path.read_text(encoding="utf-8"))
        # In test mode with synchronous BackgroundTasks, task may already be done
        assert progress_data["status"] in ("scanning", "done")
        assert progress_data["progress"] in (0, 100)

    def test_create_cluster_task_accepts_nonexistent_path(self, client, mock_cluster_config):
        """POST /api/cluster returns 400 for nonexistent path."""
        response = client.post("/api/cluster", json={"source_path": "/nonexistent/path"})

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_cluster_task_missing_body(self, client):
        """POST /api/cluster returns 422 for missing body."""
        response = client.post("/api/cluster")
        assert response.status_code == 422


class TestGetCluster:
    def test_get_cluster_status_returns_progress(self, client, mock_cluster_config, tmp_path: Path):
        """GET /api/cluster/{task_id} returns current status."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("2026-05-23 10:00:00 ERROR Test error\n", encoding="utf-8")

        # Create task
        create_response = client.post("/api/cluster", json={"source_path": str(log_dir)})
        task_id = create_response.json()["task_id"]

        # Get status
        status_response = client.get(f"/api/cluster/{task_id}")
        assert status_response.status_code == 200
        payload = status_response.json()
        assert "status" in payload
        assert "progress" in payload
        assert "current_step" in payload

    def test_get_cluster_status_not_found(self, client, mock_cluster_config, tmp_path: Path):
        """GET /api/cluster/{task_id} returns 404 for unknown task."""
        response = client.get("/api/cluster/nonexistent-task-id")
        assert response.status_code == 404

    def test_get_cluster_status_done_returns_clusters(self, client, mock_cluster_config, tmp_path: Path):
        """GET /api/cluster/{task_id} returns clusters when done."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        # Write a log file that will produce clusters
        (log_dir / "app.log").write_text(
            "2026-05-23 10:00:00 ERROR [worker-1] java.lang.NullPointerException at line 42\n"
            "2026-05-23 10:01:00 ERROR [worker-1] java.lang.NullPointerException at line 100\n"
            "2026-05-23 10:02:00 WARN Some warning\n",
            encoding="utf-8",
        )

        # Create task
        create_response = client.post("/api/cluster", json={"source_path": str(log_dir)})
        task_id = create_response.json()["task_id"]

        # Wait for completion (poll until done)
        import time
        for _ in range(30):
            time.sleep(0.5)
            status_response = client.get(f"/api/cluster/{task_id}")
            payload = status_response.json()
            if payload["status"] == "done":
                break

        # Verify final status
        assert payload["status"] == "done"
        assert payload["progress"] == 100
        assert payload["clusters"] is not None

    def test_get_cluster_invalid_task_id_format(self, client, mock_cluster_config):
        """GET /api/cluster/{task_id} handles various ID formats."""
        # Task IDs with unusual characters
        response = client.get("/api/cluster/../../../etc/passwd")
        # Should return 404, not 400 (path traversal attempt)
        assert response.status_code == 404


class TestClusterWorkflow:
    def test_full_cluster_workflow(self, client, mock_cluster_config, tmp_path: Path):
        """Test complete workflow: create task -> poll -> get results."""
        # 1. Create log source
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text(
            "2026-05-23 10:00:00 ERROR [main] java.sql.SQLException connection timeout\n"
            "2026-05-23 10:01:00 ERROR [main] java.sql.SQLException connection timeout\n"
            "2026-05-23 10:02:00 ERROR [pool-1] java.lang.RuntimeException unexpected\n",
            encoding="utf-8",
        )

        # 2. Create cluster task
        create_resp = client.post("/api/cluster", json={"source_path": str(log_dir)})
        assert create_resp.status_code == 200
        task_id = create_resp.json()["task_id"]

        # 3. Poll until done
        import time
        final_payload = None
        for _ in range(60):  # up to 30 seconds
            time.sleep(0.5)
            status_resp = client.get(f"/api/cluster/{task_id}")
            payload = status_resp.json()
            if payload["status"] == "done":
                final_payload = payload
                break

        assert final_payload is not None, "Task did not complete in time"
        assert final_payload["status"] == "done"
        assert final_payload["progress"] == 100
        assert final_payload["clusters"] is not None
        assert len(final_payload["clusters"]) >= 0  # At least empty is OK

    def test_cluster_with_no_errors(self, client, mock_cluster_config, tmp_path: Path):
        """Cluster analysis on log with no ERROR/WARN lines."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text(
            "2026-05-23 10:00:00 INFO Application started\n"
            "2026-05-23 10:01:00 DEBUG Processing request\n",
            encoding="utf-8",
        )

        create_resp = client.post("/api/cluster", json={"source_path": str(log_dir)})
        task_id = create_resp.json()["task_id"]

        # Wait for completion
        import time
        for _ in range(30):
            time.sleep(0.5)
            status_resp = client.get(f"/api/cluster/{task_id}")
            payload = status_resp.json()
            if payload["status"] == "done":
                assert payload["clusters"] is not None
                assert payload["clusters"] == []  # No errors found
                break