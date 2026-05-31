from pathlib import Path

from fastapi.testclient import TestClient

from diagnose_tool.api import routes_source
from diagnose_tool.core.config import AppConfig
from diagnose_tool.main import app


def _patch_config(monkeypatch, allowed_root: Path) -> None:
    def fake_load_config() -> AppConfig:
        return AppConfig(
            name="DiagnoseToolPy",
            version="0.1.0",
            host="127.0.0.1",
            port=18080,
            allowed_input_roots=(allowed_root.resolve(),),
            data_dir=allowed_root.parent.resolve(),
        )

    monkeypatch.setattr(routes_source, "load_config", fake_load_config)


def test_check_source_directory_accepts_allowed_directory(tmp_path: Path, monkeypatch) -> None:
    allowed_root = tmp_path / "input"
    source = allowed_root / "case-001"
    source.mkdir(parents=True)
    _patch_config(monkeypatch, allowed_root)

    response = TestClient(app).post("/api/source/check", json={"path": str(source)})

    assert response.status_code == 200
    assert response.json() == {
        "allowed": True,
        "path": str(source.resolve()),
        "name": "case-001",
        "is_zip": False,
    }


def test_check_source_directory_rejects_missing_path() -> None:
    response = TestClient(app).post("/api/source/check", json={})

    assert response.status_code == 422
    assert "detail" in response.json()


def test_check_source_directory_rejects_nonexistent_path(tmp_path: Path, monkeypatch) -> None:
    allowed_root = tmp_path / "input"
    allowed_root.mkdir()
    _patch_config(monkeypatch, allowed_root)

    response = TestClient(app).post(
        "/api/source/check",
        json={"path": str(allowed_root / "missing")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Requested path does not exist"}


def test_check_source_directory_rejects_file_path(tmp_path: Path, monkeypatch) -> None:
    allowed_root = tmp_path / "input"
    allowed_root.mkdir()
    file_path = allowed_root / "app.log"
    file_path.write_text("log", encoding="utf-8")
    _patch_config(monkeypatch, allowed_root)

    response = TestClient(app).post("/api/source/check", json={"path": str(file_path)})

    assert response.status_code == 400
    assert response.json() == {"detail": "Requested path is not a directory"}


def test_scan_source_directory_returns_metadata(tmp_path: Path, monkeypatch) -> None:
    allowed_root = tmp_path / "input"
    source = allowed_root / "case-001"
    nested = source / "nested"
    nested.mkdir(parents=True)
    (source / "app.log").write_text("abc", encoding="utf-8")
    (nested / "worker.err").write_text("12345", encoding="utf-8")
    (nested / "image.png").write_text("no", encoding="utf-8")
    _patch_config(monkeypatch, allowed_root)

    response = TestClient(app).post("/api/source/scan", json={"path": str(source)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["root_path"] == str(source.resolve())
    assert payload["file_count"] == 3
    assert payload["supported_file_count"] == 2
    assert payload["unsupported_file_count"] == 1
    assert payload["total_bytes"] == 10
    assert {file["name"] for file in payload["files"]} == {
        "app.log",
        "worker.err",
        "image.png",
    }
    assert all({"path", "name", "size", "type"} <= set(file) for file in payload["files"])


