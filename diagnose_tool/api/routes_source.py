"""Source directory API routes."""

from __future__ import annotations

import shutil
import uuid
import zipfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from diagnose_tool.analyzer.log_search import search_log_content
from diagnose_tool.analyzer.scanner import scan_directory
from diagnose_tool.core.config import load_config


# Track extracted ZIP directories: task_id -> extracted_path
_extracted_dirs: dict[str, Path] = {}


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
    is_zip = request.path.lower().endswith(".zip")
    if is_zip:
        # For ZIP files, validate the file exists and is within allowed roots
        path = _validate_source_file(request.path)
        if not zipfile.is_zipfile(path):
            raise HTTPException(status_code=400, detail="Not a valid ZIP file")
    else:
        path = _validate_source_path(request.path)
    return {"allowed": True, "path": str(path), "name": path.name, "is_zip": is_zip}


@router.post("/scan")
def scan_source_directory(request: SourcePathRequest) -> dict[str, object]:
    is_zip = request.path.lower().endswith(".zip")

    if is_zip:
        # For ZIP files, validate file exists and is valid
        path = _validate_source_file(request.path)
        if not zipfile.is_zipfile(path):
            raise HTTPException(status_code=400, detail="Not a valid ZIP file")
        extracted_path, task_id = _extract_zip_to_temp(path)
        result = scan_directory(extracted_path).to_dict()
        result["extracted_path"] = str(extracted_path)
        result["zip_task_id"] = task_id
        return result

    # Regular directory scan
    path = _validate_source_path(request.path)
    result = scan_directory(path).to_dict()
    return result


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
    """Validate a source directory path for local use.

    Checks:
    1. Path exists
    2. Is a directory (not file)
    """
    requested = Path(path).resolve()

    if not requested.exists():
        raise HTTPException(status_code=400, detail="Requested path does not exist")

    if not requested.is_dir():
        raise HTTPException(status_code=400, detail="Requested path is not a directory")

    return requested


def _validate_source_file(path: str):
    """Validate a source file path for local use.

    Checks:
    1. Path exists
    2. Is a file (not directory)
    """
    requested = Path(path).resolve()

    if not requested.exists():
        raise HTTPException(status_code=400, detail="Requested path does not exist")

    if not requested.is_file():
        raise HTTPException(status_code=400, detail="Requested path is not a file")

    return requested


def _extract_zip_to_temp(zip_path: Path) -> tuple[Path, str]:
    """Extract a ZIP file to a temporary directory.

    Args:
        zip_path: Path to the ZIP file.

    Returns:
        Tuple of (extracted_path, task_id).
    """
    config = load_config()
    task_id = uuid.uuid4().hex[:8]
    temp_base = config.data_dir / "temp"
    temp_base.mkdir(parents=True, exist_ok=True)
    extracted_path = temp_base / f"zip-{task_id}"
    extracted_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extracted_path)

    _extracted_dirs[task_id] = extracted_path
    return extracted_path, task_id


@router.delete("/temp/{task_id}")
def cleanup_temp_dir(task_id: str) -> dict[str, str]:
    """Delete a previously extracted temporary directory."""
    if task_id not in _extracted_dirs:
        raise HTTPException(status_code=404, detail="Temp directory not found")
    extracted_path = _extracted_dirs.pop(task_id)
    if extracted_path.exists():
        shutil.rmtree(extracted_path)
    return {"status": "cleaned", "task_id": task_id}