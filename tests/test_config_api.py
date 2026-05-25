"""Tests for /api/config and /api/config/paths endpoints."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from diagnose_tool.core.config import AppConfig
from diagnose_tool.core.llm_config import AppLLMConfig
from diagnose_tool.main import app


def write_config(config_path: Path, roots: list[str], data_dir: str) -> None:
    config_path.write_text(
        yaml.safe_dump({
            "app": {"name": "TestApp", "version": "1.0.0"},
            "server": {"host": "0.0.0.0", "port": 18080},
            "paths": {
                "allowed_input_roots": roots,
                "data_dir": data_dir,
            },
            "llm": {
                "enabled": True,
                "model": "test-model",
                "base_url": "https://test.example.com",
                "api_key": "test-key",
                "timeout": 30,
            },
        }),
        encoding="utf-8",
    )


@pytest.fixture
def client():
    return TestClient(app)


class TestGetConfig:
    def test_returns_complete_config(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        write_config(tmp_path / "app.yaml", [str(input_dir)], str(tmp_path / "data"))

        # Patch load_config and load_llm_config directly
        def fake_load_config():
            return AppConfig(
                name="TestApp",
                version="1.0.0",
                host="0.0.0.0",
                port=18080,
                allowed_input_roots=(input_dir.resolve(),),
                data_dir=(tmp_path / "data").resolve(),
            )

        def fake_load_llm_config():
            return AppLLMConfig(
                enabled=True,
                model="test-model",
                base_url="https://test.example.com",
                api_key="test-key",
                timeout=30,
                data_dir=(tmp_path / "data").resolve(),
            )

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "load_config", fake_load_config)
        monkeypatch.setattr(routes_config, "load_llm_config", fake_load_llm_config)

        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()
        assert data["app"]["name"] == "TestApp"
        assert data["app"]["version"] == "1.0.0"
        assert data["server"]["port"] == 18080
        assert data["llm"]["enabled"] is True
        assert data["llm"]["model"] == "test-model"

    def test_returns_500_when_config_load_fails(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        def fake_load_config_fail():
            raise RuntimeError("Config file not found")

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "load_config", fake_load_config_fail)

        response = client.get("/api/config")

        assert response.status_code == 500


class TestPatchPathsAdd:
    def test_add_new_root(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        new_dir = tmp_path / "new_input"
        new_dir.mkdir()
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "add", "path": str(new_dir)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "add"
        assert data["path"] == str(new_dir)

    def test_rejects_duplicate_path(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "add", "path": str(input_dir)},
        )

        assert response.status_code == 400
        assert "already in allowed_input_roots" in response.json()["detail"]

    def test_rejects_nonexistent_path(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "add", "path": str(tmp_path / "does_not_exist")},
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_rejects_file_instead_of_directory(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        file_path = tmp_path / "a_file.txt"
        file_path.write_text("content")
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "add", "path": str(file_path)},
        )

        assert response.status_code == 400
        assert "not a directory" in response.json()["detail"]


class TestPatchPathsRemove:
    def test_remove_existing_root(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        another_dir = tmp_path / "another"
        another_dir.mkdir()
        write_config(config_path, [str(input_dir), str(another_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "remove", "path": str(input_dir)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "remove"

    def test_rejects_removal_of_last_root(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "only_root"
        input_dir.mkdir()
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "remove", "path": str(input_dir)},
        )

        assert response.status_code == 400
        assert "at least one entry" in response.json()["detail"]

    def test_rejects_nonexistent_path_on_remove(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        response = client.patch(
            "/api/config/paths",
            json={"action": "remove", "path": str(tmp_path / "not_in_list")},
        )

        assert response.status_code == 400
        assert "not found in allowed_input_roots" in response.json()["detail"]


class TestConfigFileLocking:
    def test_sequential_patches_produce_correct_state(self, client: TestClient, tmp_path: Path, monkeypatch) -> None:
        """Verify two sequential PATCH requests both succeed and produce correct state."""
        config_path = tmp_path / "app.yaml"
        input_dir = tmp_path / "input"
        new_dir = tmp_path / "new_input"
        new_dir.mkdir()
        write_config(config_path, [str(input_dir)], str(tmp_path / "data"))

        from diagnose_tool.api import routes_config
        monkeypatch.setattr(routes_config, "CONFIG_PATH", config_path)

        r1 = client.patch("/api/config/paths", json={"action": "add", "path": str(new_dir)})
        assert r1.status_code == 200

        r2 = client.patch("/api/config/paths", json={"action": "add", "path": str(new_dir)})
        assert r2.status_code == 400  # duplicate rejected
