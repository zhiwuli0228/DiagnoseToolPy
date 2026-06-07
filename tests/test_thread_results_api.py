"""Tests for the thread results API endpoint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from diagnose_tool.analyzer.thread_artifact import write_thread_artifacts
from diagnose_tool.analyzer.thread_stack_parser import (
    ParseStatus,
    ThreadDumpResult,
    ThreadFrame,
)
from diagnose_tool.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_ctx(tmp_path: Path, task_id: str = "test-task-001"):
    """Create a mock OutputContext that writes to tmp_path/output/task_id."""
    output_dir = tmp_path / "output" / task_id

    class _Ctx:
        def __init__(self):
            self.task_id = task_id

        def output_dir(self):
            return output_dir

        def artifacts_dir(self):
            return output_dir / "artifacts"

        def ensure_directories(self):
            self.output_dir().mkdir(parents=True, exist_ok=True)
            self.artifacts_dir().mkdir(parents=True, exist_ok=True)

    return _Ctx()


def _sample_results():
    return [
        ThreadDumpResult(
            thread_name="main",
            thread_state="RUNNABLE",
            frames=[
                ThreadFrame(raw_text="\tat com.Main.run(Main.java:10)",
                            class_name="com.Main", method="run",
                            file_name="Main.java", line_number=10),
            ],
            lock_hints=[],
            raw_text='"main" #1 prio=5\n   java.lang.Thread.State: RUNNABLE',
            parse_status=ParseStatus.FULL,
        ),
        ThreadDumpResult(
            thread_name="worker-1",
            thread_state="BLOCKED",
            frames=[],
            lock_hints=[],
            raw_text='"worker-1" #2 prio=5\n   java.lang.Thread.State: BLOCKED',
            parse_status=ParseStatus.FULL,
        ),
    ]


class TestGetThreadResults:
    def test_returns_thread_results(self, client, tmp_path):
        ctx = _make_ctx(tmp_path)
        write_thread_artifacts(ctx, _sample_results())

        with patch("diagnose_tool.api.routes_diagnosis._get_llm_config") as mock_cfg:
            mock_cfg.return_value = type("Cfg", (), {"data_dir": tmp_path})()
            resp = client.get("/api/diagnosis/thread-results/test-task-001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "test-task-001"
        assert data["total_threads"] == 2
        assert len(data["threads"]) == 2

    def test_thread_item_fields(self, client, tmp_path):
        ctx = _make_ctx(tmp_path)
        write_thread_artifacts(ctx, _sample_results())

        with patch("diagnose_tool.api.routes_diagnosis._get_llm_config") as mock_cfg:
            mock_cfg.return_value = type("Cfg", (), {"data_dir": tmp_path})()
            resp = client.get("/api/diagnosis/thread-results/test-task-001")

        thread = resp.json()["threads"][0]
        assert "thread_ref" in thread
        assert "thread_name" in thread
        assert "thread_state" in thread
        assert "parse_status" in thread
        assert "frame_count" in thread
        assert "frames_summary" in thread

    def test_no_raw_text_in_response(self, client, tmp_path):
        ctx = _make_ctx(tmp_path)
        write_thread_artifacts(ctx, _sample_results())

        with patch("diagnose_tool.api.routes_diagnosis._get_llm_config") as mock_cfg:
            mock_cfg.return_value = type("Cfg", (), {"data_dir": tmp_path})()
            resp = client.get("/api/diagnosis/thread-results/test-task-001")

        thread = resp.json()["threads"][0]
        assert "raw_text" not in thread

    def test_missing_task_returns_404(self, client, tmp_path):
        with patch("diagnose_tool.api.routes_diagnosis._get_llm_config") as mock_cfg:
            mock_cfg.return_value = type("Cfg", (), {"data_dir": tmp_path})()
            resp = client.get("/api/diagnosis/thread-results/nonexistent")

        assert resp.status_code == 404

    def test_no_artifact_returns_empty(self, client, tmp_path):
        (tmp_path / "output" / "empty-task").mkdir(parents=True)

        with patch("diagnose_tool.api.routes_diagnosis._get_llm_config") as mock_cfg:
            mock_cfg.return_value = type("Cfg", (), {"data_dir": tmp_path})()
            resp = client.get("/api/diagnosis/thread-results/empty-task")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_threads"] == 0
        assert data["threads"] == []

    def test_status_counts(self, client, tmp_path):
        results = [
            ThreadDumpResult(thread_name="t1", thread_state="RUNNABLE",
                             frames=[ThreadFrame(raw_text="\tat com.A.b(A.java:1)", class_name="com.A", method="b")],
                             parse_status=ParseStatus.FULL),
            ThreadDumpResult(thread_name="t2", thread_state="RUNNABLE",
                             frames=[], parse_status=ParseStatus.PARTIAL),
            ThreadDumpResult(thread_name="t3", thread_state="RUNNABLE",
                             frames=[], parse_status=ParseStatus.RAW),
        ]
        ctx = _make_ctx(tmp_path)
        write_thread_artifacts(ctx, results)

        with patch("diagnose_tool.api.routes_diagnosis._get_llm_config") as mock_cfg:
            mock_cfg.return_value = type("Cfg", (), {"data_dir": tmp_path})()
            resp = client.get("/api/diagnosis/thread-results/test-task-001")

        data = resp.json()
        assert data["status_counts"]["FULL"] == 1
        assert data["status_counts"]["PARTIAL"] == 1
        assert data["status_counts"]["RAW"] == 1
