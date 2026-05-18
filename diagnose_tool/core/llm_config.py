"""LLM provider configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from diagnose_tool.core.config import ConfigError, DEFAULT_CONFIG_PATH


@dataclass(frozen=True)
class AppLLMConfig:
    """LLM provider settings loaded from YAML."""

    enabled: bool
    model: str
    base_url: str
    api_key: str
    timeout: int  # seconds
    data_dir: Path


def load_llm_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> AppLLMConfig:
    """Load LLM config from app.yaml.

    If the 'llm' section is entirely absent, returns AppLLMConfig with safe
    defaults (enabled=False).

    Raises ConfigError on invalid YAML structure.
    """
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML config: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read config file: {path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping")

    # Resolve data_dir from paths section for case output resolution
    base_dir = path.resolve().parent.parent
    paths = raw.get("paths", {})
    data_dir_raw = paths.get("data_dir", "data") if isinstance(paths, dict) else "data"
    data_dir = _resolve_path(data_dir_raw, base_dir)

    llm_section = raw.get("llm")
    if llm_section is None:
        # Section entirely absent — safe defaults
        return AppLLMConfig(
            enabled=False,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="",
            timeout=60,
            data_dir=data_dir,
        )

    if not isinstance(llm_section, dict):
        raise ConfigError("llm must be a mapping")

    enabled = bool(llm_section.get("enabled", False))
    model = str(llm_section.get("model", "gpt-4o-mini"))
    base_url = str(llm_section.get("base_url", "https://api.openai.com/v1"))
    api_key = str(llm_section.get("api_key", ""))

    timeout_raw = llm_section.get("timeout", 60)
    if isinstance(timeout_raw, bool) or not isinstance(timeout_raw, int):
        raise ConfigError("llm.timeout must be an integer")
    timeout = timeout_raw

    return AppLLMConfig(
        enabled=enabled,
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        data_dir=data_dir,
    )


def _resolve_path(value: str, base_dir: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("Configured paths must be non-empty strings")
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()