"""Source directory API routes."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from diagnose_tool.analyzer.log_search import search_log_content
from diagnose_tool.analyzer.scanner import scan_directory
from diagnose_tool.core.config import load_config
from diagnose_tool.core.security import PathValidationError, validate_server_directory


router = APIRouter(prefix="/api/source", tags=["source"])


class SourcePathRequest(BaseModel):
    path: str = Field(min_length=1)


class LogSearchRequest(BaseModel):
    path: str = Field(min_length=1)
    time_start: str | None = None
    time_end: str | None = None
    thread: str | None = None
    keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    max_lines: int = Field(default=1000, le=10000)
    aggregate: bool = False
    include_thread: bool = False
    include_time: bool = False
    message_only: bool = False
    include_stack: bool = True


@router.post("/check")
def check_source_directory(request: SourcePathRequest) -> dict[str, object]:
    path = _validate_source_path(request.path)
    return {"allowed": True, "path": str(path), "name": path.name}


@router.post("/scan")
def scan_source_directory(request: SourcePathRequest) -> dict[str, object]:
    path = _validate_source_path(request.path)
    return scan_directory(path).to_dict()


@router.post("/search")
def search_logs(request: LogSearchRequest) -> dict:
    _validate_source_path(request.path)
    result = search_log_content(
        path=request.path,
        time_start=request.time_start,
        time_end=request.time_end,
        thread=request.thread,
        keywords=request.keywords,
        exclude_keywords=request.exclude_keywords,
        max_lines=request.max_lines,
        include_stack=request.include_stack,
    )

    # Build group_keys mapping from aggregated results if available
    group_keys: dict[int, str] = {}
    if request.aggregate and result["results"]:
        from diagnose_tool.analyzer.log_aggregator import (
            aggregate_log_lines,
            AggregationOptions,
        )
        opts = AggregationOptions(
            group_by_exception=True,
            include_thread=request.include_thread,
            include_time=request.include_time,
            message_only=request.message_only,
        )
        aggregated = aggregate_log_lines(result["results"], opts)
        result["aggregated"] = [asdict(g) for g in aggregated]

        # Build group_keys: map result index to group key
        # matched_lines contains the same dict objects as result["results"], so we can
        # use identity check (is) instead of value comparison to avoid path format issues
        results_list = result["results"]
        results_index = {id(res): idx for idx, res in enumerate(results_list)}
        for g in aggregated:
            for line_dict in g.matched_lines:
                idx = results_index.get(id(line_dict))
                if idx is not None:
                    group_keys[idx] = g.key

    # Store matched lines in cache for later diagnosis
    if result["results"]:
        from diagnose_tool.analyzer.evidence_cache import EvidenceCacheManager
        from diagnose_tool.core.config import load_config

        config = load_config()
        cache_mgr = EvidenceCacheManager(config.data_dir)
        cache_key = cache_mgr.create_search_cache(
            request.path,
            result["results"],
            group_keys,
        )
        result["cache_key"] = cache_key

    return result


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)) -> dict:
    """Upload files to the server's upload directory.

    Files are saved under data/input/uploads/{timestamp}/ preserving relative paths.
    """
    config = load_config()
    upload_base = Path("data/input/uploads")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    upload_dir = upload_base / timestamp
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for file in files:
        if not file.filename:
            continue
        file_path = upload_dir / file.filename
        # Preserve directory structure from webkitRelativePath if present
        if hasattr(file, 'webkitRelativePath') and file.webkitRelativePath:
            rel = Path(file.webkitRelativePath)
            if rel.parent and rel.parent.name:
                file_path = upload_dir / file.webkitRelativePath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        with file_path.open("wb") as f:
            f.write(content)
        saved_count += 1

    # Register upload dir in allowed_input_roots dynamically if not already present
    # Use the absolute path for validation
    abs_upload_dir = upload_dir.resolve()
    return {
        "path": str(abs_upload_dir),
        "file_count": saved_count,
        "relative_path": f"data/input/uploads/{timestamp}",
    }


def _validate_source_path(path: str):
    config = load_config()
    try:
        return validate_server_directory(path, config.allowed_input_roots)
    except PathValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc