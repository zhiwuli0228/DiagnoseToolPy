"""Integration tests for the five new task-detail read routes."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_client(tmp_path: Path) -> TestClient:
    """Build a TestClient with the task routes mounted and the output
    root pointed at ``tmp_path``."""

    # Load the routes_source module and patch the task_reader._OUTPUT_ROOT
    # so the new endpoints read from the test tmp dir.
    routes_path = (
        Path(__file__).resolve().parent.parent
        / "diagnose_tool"
        / "api"
        / "routes_source.py"
    )
    task_reader_path = (
        Path(__file__).resolve().parent.parent
        / "diagnose_tool"
        / "analyzer"
        / "task_reader.py"
    )

    # Load task_reader first so we can patch its _OUTPUT_ROOT before
    # routes_source imports it.
    tr_spec = importlib.util.spec_from_file_location("_task_reader_test", task_reader_path)
    assert tr_spec and tr_spec.loader
    task_reader = importlib.util.module_from_spec(tr_spec)
    sys.modules[tr_spec.name] = task_reader
    tr_spec.loader.exec_module(task_reader)
    task_reader._OUTPUT_ROOT = tmp_path

    # Load routes_source and remap its task_reader import to the patched module.
    rs_spec = importlib.util.spec_from_file_location("_routes_source_test", routes_path)
    assert rs_spec and rs_spec.loader
    routes_source = importlib.util.module_from_spec(rs_spec)
    sys.modules[rs_spec.name] = routes_source
    sys.modules["diagnose_tool.api.routes_source"] = routes_source
    rs_spec.loader.exec_module(routes_source)
    routes_source.task_reader = task_reader  # type: ignore[attr-defined]

    app = FastAPI()
    app.include_router(routes_source.router)
    return TestClient(app)


def _seed_task(tmp_path: Path, task_id: str, *, with_progress: bool = True) -> None:
    d = tmp_path / task_id
    d.mkdir()
    if with_progress:
        (d / "progress.json").write_text(
            json.dumps(
                {
                    "status": "done",
                    "progress": 100,
                    "current_step": "分析完成",
                    "updated_at": "2026-06-01T10:00:00Z",
                }
            ),
            encoding="utf-8",
        )
    (d / "evidence-pack.md").write_text("# evidence", encoding="utf-8")
    (d / "key-logs.txt").write_text("[error] foo\n", encoding="utf-8")
    (d / "case-draft.md").write_text("## case", encoding="utf-8")


def test_list_tasks_returns_seeded_tasks(tmp_path: Path) -> None:
    _seed_task(tmp_path, "task-a")
    _seed_task(tmp_path, "task-b")
    _seed_task(tmp_path, "no-progress", with_progress=False)

    client = _build_client(tmp_path)
    response = client.get("/api/source/tasks")
    assert response.status_code == 200
    body = response.json()
    ids = [t["task_id"] for t in body["tasks"]]
    assert "task-a" in ids
    assert "task-b" in ids
    assert "no-progress" not in ids
    for entry in body["tasks"]:
        assert "task_id" in entry
        assert "status" in entry
        assert "progress" in entry


def test_get_task_progress_returns_payload(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    client = _build_client(tmp_path)
    response = client.get("/api/source/task/t1/progress")
    assert response.status_code == 200
    body = response.json()
    assert body["progress"]["status"] == "done"
    assert body["progress"]["current_step"] == "分析完成"


def test_get_task_progress_missing_returns_null(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    client = _build_client(tmp_path)
    response = client.get("/api/source/task/empty/progress")
    assert response.status_code == 200
    assert response.json()["progress"] is None


def test_get_task_evidence_pack_returns_text(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    client = _build_client(tmp_path)
    response = client.get("/api/source/task/t1/evidence-pack")
    assert response.status_code == 200
    assert response.json()["content"] == "# evidence"


def test_get_task_evidence_pack_missing_returns_null(tmp_path: Path) -> None:
    (tmp_path / "t1").mkdir()
    client = _build_client(tmp_path)
    response = client.get("/api/source/task/t1/evidence-pack")
    assert response.status_code == 200
    assert response.json()["content"] is None


def test_get_task_key_logs_returns_text(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    client = _build_client(tmp_path)
    response = client.get("/api/source/task/t1/key-logs")
    assert response.status_code == 200
    assert response.json()["content"] == "[error] foo\n"


def test_get_task_case_draft_returns_text(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    client = _build_client(tmp_path)
    response = client.get("/api/source/task/t1/case-draft")
    assert response.status_code == 200
    assert response.json()["content"] == "## case"


@pytest.mark.parametrize(
    "bad_id",
    ["..", "../etc", "abc/def", ""],
)
def test_invalid_task_id_returns_400_or_404(tmp_path: Path, bad_id: str) -> None:
    """Bad task_ids are rejected with 400 (validator) or 404 (framework).

    FastAPI's path matcher itself rejects ``..`` and ``/`` with 404
    before the handler runs, which is the stronger guarantee. The
    service-level validator (covered in ``test_task_reader.py``) raises
    ``InvalidTaskIdError`` which the route translates to 400 for any
    other inputs that do reach it (e.g., unicode).
    """

    _seed_task(tmp_path, "t1")
    client = _build_client(tmp_path)
    for path in (
        "/api/source/task/{t}/progress",
        "/api/source/task/{t}/evidence-pack",
        "/api/source/task/{t}/key-logs",
        "/api/source/task/{t}/case-draft",
    ):
        response = client.get(path.format(t=bad_id))
        assert response.status_code in (400, 404), (
            f"{path} for {bad_id!r} should 400 or 404, got {response.status_code}"
        )
