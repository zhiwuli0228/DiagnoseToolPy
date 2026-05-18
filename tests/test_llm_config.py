"""Tests for diagnose_tool/core/llm_config.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from diagnose_tool.core.config import ConfigError
from diagnose_tool.core.llm_config import load_llm_config


class TestLoadLLMConfig:
    """Test load_llm_config() from app.yaml."""

    def test_full_valid_config(self, tmp_path: Path) -> None:
        """Full valid config loads all fields correctly."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n"
            "llm:\n  enabled: true\n"
            "  model: gpt-4o\n"
            "  base_url: https://api.example.com/v1\n"
            "  api_key: secret-key-123\n"
            "  timeout: 30\n",
            encoding="utf-8",
        )

        cfg = load_llm_config(config_file)

        assert cfg.enabled is True
        assert cfg.model == "gpt-4o"
        assert cfg.base_url == "https://api.example.com/v1"
        assert cfg.api_key == "secret-key-123"
        assert cfg.timeout == 30
        assert isinstance(cfg.data_dir, Path)

    def test_llm_section_absent_returns_enabled_false(self, tmp_path: Path) -> None:
        """Missing llm section → enabled=False, safe defaults."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n",
            encoding="utf-8",
        )

        cfg = load_llm_config(config_file)

        assert cfg.enabled is False
        assert cfg.model == "gpt-4o-mini"
        assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.api_key == ""
        assert cfg.timeout == 60
        assert isinstance(cfg.data_dir, Path)

    def test_llm_enabled_absent_treated_as_false(self, tmp_path: Path) -> None:
        """llm.enabled absent in YAML → treated as false."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n"
            "llm:\n  model: gpt-4o-mini\n",
            encoding="utf-8",
        )

        cfg = load_llm_config(config_file)

        assert cfg.enabled is False

    def test_invalid_yaml_raises_config_error(self, tmp_path: Path) -> None:
        """Invalid YAML structure → raises ConfigError."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        with pytest.raises(ConfigError):
            load_llm_config(config_file)

    def test_defaults_applied_when_optional_fields_absent(self, tmp_path: Path) -> None:
        """Optional fields absent → defaults are applied."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n"
            "llm:\n  enabled: true\n",
            encoding="utf-8",
        )

        cfg = load_llm_config(config_file)

        assert cfg.model == "gpt-4o-mini"
        assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.api_key == ""
        assert cfg.timeout == 60

    def test_timeout_invalid_type_raises_config_error(self, tmp_path: Path) -> None:
        """llm.timeout must be integer → raises ConfigError on bool or string."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n"
            "llm:\n  enabled: true\n"
            "  timeout: yes\n",
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="timeout"):
            load_llm_config(config_file)

    def test_timeout_bool_raises_config_error(self, tmp_path: Path) -> None:
        """llm.timeout as boolean → raises ConfigError."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n"
            "llm:\n  enabled: true\n"
            "  timeout: true\n",
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="timeout"):
            load_llm_config(config_file)

    def test_config_file_not_found_raises(self) -> None:
        """Missing config file → raises ConfigError."""
        with pytest.raises(ConfigError, match="not found"):
            load_llm_config("nonexistent.yaml")

    def test_llm_section_not_mapping_raises(self, tmp_path: Path) -> None:
        """llm section present but not a mapping → ConfigError."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: data\n"
            "llm: just-a-string\n",
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="llm must be a mapping"):
            load_llm_config(config_file)

    def test_data_dir_resolved_relative_to_base(self, tmp_path: Path) -> None:
        """data_dir relative path resolved relative to config file's parent."""
        config_file = tmp_path / "config" / "app.yaml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(
            "app:\n  name: Test\n  version: 1.0\n"
            "server:\n  host: localhost\n  port: 8000\n"
            "paths:\n  data_dir: mydata\n"
            "llm:\n  enabled: false\n",
            encoding="utf-8",
        )

        cfg = load_llm_config(config_file)

        # Resolved relative to config file's parent parent (base_dir)
        assert cfg.data_dir == (tmp_path / "mydata").resolve()