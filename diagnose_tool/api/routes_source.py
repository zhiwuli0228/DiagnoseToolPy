"""Source directory API routes."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
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
    )

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

    return result


def _validate_source_path(path: str):
    config = load_config()
    try:
        return validate_server_directory(path, config.allowed_input_roots)
    except PathValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc