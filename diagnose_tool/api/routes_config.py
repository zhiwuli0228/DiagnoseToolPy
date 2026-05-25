"""Configuration API routes — read and hot-update app configuration."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from filelock import FileLock
from pydantic import BaseModel, Field
import yaml

from diagnose_tool.core.config import DEFAULT_CONFIG_PATH, load_config
from diagnose_tool.core.llm_config import load_llm_config
from diagnose_tool.core.security import PathValidationError


router = APIRouter(prefix="/api/config", tags=["config"])

CONFIG_PATH = Path(DEFAULT_CONFIG_PATH)
LOCK_PATH = Path(str(CONFIG_PATH) + ".lock")


class ConfigResponse(BaseModel):
    """Full application configuration for GET /api/config."""

    app: dict[str, str]
    server: dict[str, str | int]
    paths: dict[str, list[str] | str]
    llm: dict[str, bool | str | int]


class PathsPatchRequest(BaseModel):
    """Request body for PATCH /api/config/paths."""

    action: str = Field(pattern="^(add|remove)$")
    path: str = Field(min_length=1)


@router.get("", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    """Return the full application configuration.

    Merges AppConfig (app/server/paths) with AppLLMConfig (llm) into
    a single response so the frontend can fetch everything in one call.
    """
    try:
        app_config = load_config()
        llm_config = load_llm_config()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ConfigResponse(
        app={
            "name": app_config.name,
            "version": app_config.version,
        },
        server={
            "host": app_config.host,
            "port": app_config.port,
        },
        paths={
            "allowed_input_roots": [str(p) for p in app_config.allowed_input_roots],
            "data_dir": str(app_config.data_dir),
        },
        llm={
            "enabled": llm_config.enabled,
            "model": llm_config.model,
            "base_url": llm_config.base_url,
            "timeout": llm_config.timeout,
        },
    )


@router.patch("/paths")
def patch_paths(request: PathsPatchRequest) -> dict[str, str]:
    """Add or remove an allowed_input_roots entry.

    Uses file locking to serialize concurrent writes to config/app.yaml.
    """
    lock = FileLock(LOCK_PATH, timeout=10)
    with lock:
        # Read current YAML
        if not CONFIG_PATH.exists():
            raise HTTPException(status_code=500, detail="Config file not found")

        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise HTTPException(status_code=500, detail="Invalid config format")

        paths_section = raw.get("paths", {})
        if not isinstance(paths_section, dict):
            raise HTTPException(status_code=500, detail="Invalid paths format")

        roots = paths_section.get("allowed_input_roots", [])
        if not isinstance(roots, list):
            raise HTTPException(status_code=500, detail="Invalid allowed_input_roots format")

        normalized_path = str(Path(request.path).resolve())

        if request.action == "add":
            # Validate path exists and is a directory
            req_path = Path(request.path)
            if not req_path.exists():
                raise HTTPException(status_code=400, detail="Requested path does not exist")
            if not req_path.is_dir():
                raise HTTPException(status_code=400, detail="Requested path is not a directory")

            # Check for duplicate (compare resolved paths)
            existing_resolved = [str(Path(p).resolve()) for p in roots]
            if normalized_path in existing_resolved:
                raise HTTPException(status_code=400, detail="Path already in allowed_input_roots")

            roots.append(request.path)

        elif request.action == "remove":
            # Check path exists in list
            existing_resolved = {str(Path(p).resolve()): p for p in roots}
            if normalized_path not in existing_resolved:
                raise HTTPException(status_code=400, detail="Path not found in allowed_input_roots")

            # Must have at least one root left
            if len(roots) <= 1:
                raise HTTPException(status_code=400, detail="allowed_input_roots must have at least one entry")

            # Remove by original key to preserve order/comments
            original_key = existing_resolved[normalized_path]
            roots.remove(original_key)

        # Write back
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(raw, f, allow_unicode=True, sort_keys=False)

    return {"status": "ok", "action": request.action, "path": request.path}
