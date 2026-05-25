"""Tests for ZIP file handling in source API."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from diagnose_tool.api import routes_source
from diagnose_tool.core.config import AppConfig
from diagnose_tool.main import app


def _patch_config(monkeypatch, allowed_root: Path, data_dir: Path | None = None) -> None:
    """Patch load_config to use the given allowed_root."""
    def fake_load_config() -> AppConfig:
        return AppConfig(
            name="DiagnoseToolPy",
            version="0.1.0",
            host="127.0.0.1",
            port=18080,
            allowed_input_roots=(allowed_root.resolve(),),
            data_dir=(data_dir or allowed_root.parent).resolve(),
        )

    monkeypatch.setattr(routes_source, "load_config", fake_load_config)


def _create_test_zip(zip_path: Path, files: dict[str, str]) -> None:
    """Create a ZIP file with the given files."""
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


class TestCheckSourceDirectoryZip:
    """Tests for ZIP file detection in check endpoint."""

    def test_check_detects_zip_suffix(self, tmp_path: Path, monkeypatch) -> None:
        """check endpoint returns is_zip=True for .zip files."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        zip_path = allowed_root / "logs.zip"
        _create_test_zip(zip_path, {"app.log": "2024-01-01 ERROR test\n"})
        _patch_config(monkeypatch, allowed_root)

        response = TestClient(app).post("/api/source/check", json={"path": str(zip_path)})

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["is_zip"] is True
        assert data["name"] == "logs.zip"

    def test_check_detects_non_zip(self, tmp_path: Path, monkeypatch) -> None:
        """check endpoint returns is_zip=False for regular directories."""
        allowed_root = tmp_path / "input"
        source = allowed_root / "logs"
        source.mkdir(parents=True)
        _patch_config(monkeypatch, allowed_root)

        response = TestClient(app).post("/api/source/check", json={"path": str(source)})

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["is_zip"] is False

    def test_check_rejects_invalid_zip(self, tmp_path: Path, monkeypatch) -> None:
        """check endpoint rejects a file that ends in .zip but is not a valid ZIP."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        fake_zip = allowed_root / "fake.zip"
        fake_zip.write_text("not a zip file content", encoding="utf-8")
        _patch_config(monkeypatch, allowed_root)

        response = TestClient(app).post("/api/source/check", json={"path": str(fake_zip)})

        assert response.status_code == 400
        assert "Not a valid ZIP file" in response.json()["detail"]


class TestScanSourceDirectoryZip:
    """Tests for ZIP file handling in scan endpoint."""

    def test_scan_extracts_and_scans_zip(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """scan endpoint extracts ZIP and returns results from extracted contents."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        zip_path = allowed_root / "logs.zip"
        _create_test_zip(zip_path, {
            "app.log": "2024-01-01 10:00:00 ERROR connection failed\n",
            "worker.log": "2024-01-01 10:00:01 WARN retry attempt 1\n",
        })
        _patch_config(monkeypatch, allowed_root, data_dir)

        response = TestClient(app).post("/api/source/scan", json={"path": str(zip_path)})

        assert response.status_code == 200
        data = response.json()
        # Should have scanned extracted contents
        assert data["file_count"] == 2
        # Should return extracted_path and zip_task_id
        assert "extracted_path" in data
        assert "zip_task_id" in data
        # extracted_path should be under data_dir/temp/
        assert "zip-" in data["extracted_path"]

    def test_scan_regular_directory_no_extracted_path(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """scan endpoint does not return extracted_path for regular directories."""
        allowed_root = tmp_path / "input"
        source = allowed_root / "logs"
        source.mkdir(parents=True)
        (source / "app.log").write_text("test", encoding="utf-8")
        _patch_config(monkeypatch, allowed_root)

        response = TestClient(app).post("/api/source/scan", json={"path": str(source)})

        assert response.status_code == 200
        data = response.json()
        assert data["file_count"] == 1
        assert "extracted_path" not in data
        assert "zip_task_id" not in data

    def test_scan_rejects_invalid_zip(self, tmp_path: Path, monkeypatch) -> None:
        """scan endpoint rejects invalid ZIP files."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        fake_zip = allowed_root / "corrupt.zip"
        fake_zip.write_text("not a zip", encoding="utf-8")
        _patch_config(monkeypatch, allowed_root, data_dir)

        response = TestClient(app).post("/api/source/scan", json={"path": str(fake_zip)})

        assert response.status_code == 400
        assert "Not a valid ZIP file" in response.json()["detail"]

    def test_scan_zip_with_nested_directories(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """scan endpoint correctly handles ZIP with nested directories."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        zip_path = allowed_root / "nested.zip"
        _create_test_zip(zip_path, {
            "logs/app.log": "2024-01-01 ERROR test\n",
            "logs/nested/worker.err": "2024-01-01 WARN test\n",
        })
        _patch_config(monkeypatch, allowed_root, data_dir)

        response = TestClient(app).post("/api/source/scan", json={"path": str(zip_path)})

        assert response.status_code == 200
        data = response.json()
        assert data["file_count"] == 2


class TestCleanupTempDir:
    """Tests for temp directory cleanup endpoint."""

    def test_cleanup_deletes_extracted_directory(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """DELETE endpoint removes the extracted temp directory."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # First extract a ZIP to create a temp dir
        zip_path = allowed_root / "logs.zip"
        _create_test_zip(zip_path, {"app.log": "test\n"})
        _patch_config(monkeypatch, allowed_root, data_dir)

        # Scan to extract
        scan_response = TestClient(app).post("/api/source/scan", json={"path": str(zip_path)})
        assert scan_response.status_code == 200
        task_id = scan_response.json()["zip_task_id"]

        # Verify temp dir exists
        temp_dir = data_dir / "temp" / f"zip-{task_id}"
        assert temp_dir.exists(), f"Temp dir {temp_dir} should exist before cleanup"

        # Cleanup
        cleanup_response = TestClient(app).delete(f"/api/source/temp/{task_id}")
        assert cleanup_response.status_code == 200
        assert cleanup_response.json()["status"] == "cleaned"

        # Verify temp dir no longer exists
        assert not temp_dir.exists(), f"Temp dir {temp_dir} should not exist after cleanup"

    def test_cleanup_returns_404_for_unknown_task_id(self, tmp_path: Path, monkeypatch) -> None:
        """DELETE endpoint returns 404 for non-existent task_id."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        _patch_config(monkeypatch, allowed_root, data_dir)

        response = TestClient(app).delete("/api/source/temp/nonexistent")

        assert response.status_code == 404
        assert "Temp directory not found" in response.json()["detail"]

    def test_cleanup_idempotent(self, tmp_path: Path, monkeypatch) -> None:
        """Calling cleanup twice returns 404 on second call."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        zip_path = allowed_root / "logs.zip"
        _create_test_zip(zip_path, {"app.log": "test\n"})
        _patch_config(monkeypatch, allowed_root, data_dir)

        # Scan to extract
        scan_response = TestClient(app).post("/api/source/scan", json={"path": str(zip_path)})
        task_id = scan_response.json()["zip_task_id"]

        # First cleanup succeeds
        response1 = TestClient(app).delete(f"/api/source/temp/{task_id}")
        assert response1.status_code == 200

        # Second cleanup returns 404
        response2 = TestClient(app).delete(f"/api/source/temp/{task_id}")
        assert response2.status_code == 404


class TestExtractZipToTemp:
    """Tests for the _extract_zip_to_temp helper function."""

    def test_extract_zip_creates_temp_directory(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """_extract_zip_to_temp creates a directory under data/temp/zip-{uuid}/."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        zip_path = allowed_root / "logs.zip"
        _create_test_zip(zip_path, {"app.log": "test\n"})
        _patch_config(monkeypatch, allowed_root, data_dir)

        from diagnose_tool.api.routes_source import _extract_zip_to_temp

        extracted_path, task_id = _extract_zip_to_temp(zip_path)

        assert extracted_path.exists()
        assert extracted_path.name.startswith("zip-")
        assert task_id is not None
        assert len(task_id) == 8  # UUID hex first 8 chars

        # Verify contents were extracted into the temp directory
        assert (extracted_path / "app.log").exists()

    def test_extract_zip_preserves_structure(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """_extract_zip_to_temp preserves directory structure within ZIP."""
        allowed_root = tmp_path / "input"
        allowed_root.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        zip_path = allowed_root / "nested.zip"
        _create_test_zip(zip_path, {
            "logs/service-a/app.log": "service-a log",
            "logs/service-b/app.log": "service-b log",
        })
        _patch_config(monkeypatch, allowed_root, data_dir)

        from diagnose_tool.api.routes_source import _extract_zip_to_temp

        extracted_path, _ = _extract_zip_to_temp(zip_path)

        assert (extracted_path / "logs" / "service-a" / "app.log").exists()
        assert (extracted_path / "logs" / "service-b" / "app.log").exists()
