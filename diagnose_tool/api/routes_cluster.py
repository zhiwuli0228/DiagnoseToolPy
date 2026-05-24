"""Cluster analysis API routes."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from diagnose_tool.analyzer.cluster_analyzer import (
    ClusterAnalyzer,
    read_cluster_result,
    read_progress,
)
from diagnose_tool.core.config import load_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["cluster"])

_config = None


def _get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config


class ClusterRequest(BaseModel):
    source_path: str


class ClusterResponse(BaseModel):
    task_id: str


class ClusterStatusResponse(BaseModel):
    status: str
    progress: int
    current_step: str
    clusters: list | None = None


def _run_cluster_task(task_id: str, source_path: str, data_dir: Path) -> None:
    """Background task that runs the clustering analysis."""
    try:
        analyzer = ClusterAnalyzer(data_dir)
        analyzer.run(task_id, source_path)
    except Exception as exc:
        logger.error("Cluster task %s failed: %s", task_id, exc)


@router.post("/cluster", response_model=ClusterResponse)
def create_cluster_task(request: ClusterRequest, background_tasks: BackgroundTasks) -> ClusterResponse:
    """Create a new cluster analysis task.

    The task runs asynchronously in the background. Poll GET /api/cluster/{task_id}
    for progress and results.
    """
    config = _get_config()

    # Validate source path
    source = Path(request.source_path)
    if not source.exists():
        raise HTTPException(status_code=400, detail=f"Source path does not exist: {request.source_path}")

    analyzer = ClusterAnalyzer(config.data_dir)
    task_id, task_output = analyzer.create_task(request.source_path)

    # Write initial progress before returning
    progress_path = task_output / "progress.json"
    progress_path.write_text(
        json.dumps({
            "status": "scanning",
            "progress": 0,
            "current_step": "准备扫描...",
            "updated_at": datetime.now().isoformat(),
        }, ensure_ascii=False),
        encoding="utf-8"
    )

    # Schedule background task
    background_tasks.add_task(_run_cluster_task, task_id, str(source), config.data_dir)

    return ClusterResponse(task_id=task_id)


@router.get("/cluster/{task_id}/matched-lines/{cluster_index}")
def get_cluster_matched_lines(task_id: str, cluster_index: int) -> dict:
    """Get matched lines for a specific cluster group.

    Returns matched log lines from the cache for the cluster at the given index.
    """
    from diagnose_tool.analyzer.evidence_cache import EvidenceCacheManager

    config = _get_config()
    task_output = config.data_dir / "output" / task_id

    if not task_output.exists():
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    # Read cluster result to get group keys
    result = read_cluster_result(task_output)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Cluster result not found")

    if cluster_index < 0 or cluster_index >= len(result.clusters):
        raise HTTPException(status_code=400, detail=f"Invalid cluster index: {cluster_index}")

    # Get the group key for this cluster index (exception_class is the grouping key)
    group_key = result.clusters[cluster_index].exception_class

    # Load matched lines from cache
    cache_mgr = EvidenceCacheManager(config.data_dir)
    entries = cache_mgr.load_matched_lines(task_id)

    # Filter and deduplicate entries by group key and ID
    # Use dict to preserve order while deduplicating by ID
    seen_ids: set[str] = set()
    matched_lines: list[dict] = []
    for e in entries:
        if e.group_key != group_key:
            continue
        if e.id in seen_ids:
            continue
        seen_ids.add(e.id)
        matched_lines.append({
            "id": e.id,
            "group_key": e.group_key,
            "event": {
                "timestamp": e.event.timestamp,
                "level": e.event.level,
                "thread": e.event.thread,
                "message": e.event.message,
                "raw": e.event.raw,
                "file_path": e.event.file_path,
                "line_no": e.event.line_no,
            },
            "context_before": [
                {
                    "timestamp": c.timestamp,
                    "level": c.level,
                    "thread": c.thread,
                    "message": c.message,
                    "raw": c.raw,
                    "file_path": c.file_path,
                    "line_no": c.line_no,
                }
                for c in e.context_before
            ],
            "context_after": [
                {
                    "timestamp": c.timestamp,
                    "level": c.level,
                    "thread": c.thread,
                    "message": c.message,
                    "raw": c.raw,
                    "file_path": c.file_path,
                    "line_no": c.line_no,
                }
                for c in e.context_after
            ],
        })

    return {
        "cluster_index": cluster_index,
        "group_key": group_key,
        "matched_lines": matched_lines,
        "total": len(matched_lines),
    }


@router.get("/cluster/{task_id}", response_model=ClusterStatusResponse)
def get_cluster_status(task_id: str) -> ClusterStatusResponse:
    """Get cluster analysis progress or results.

    Returns current status, progress percentage, and current step.
    When status is "done", includes full cluster results.
    """
    config = _get_config()
    task_output = config.data_dir / "output" / task_id

    if not task_output.exists():
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    progress = read_progress(task_output)
    if progress is None:
        raise HTTPException(status_code=404, detail=f"Task progress not found: {task_id}")

    if progress.status == "done":
        result = read_cluster_result(task_output)
        clusters = None
        if result is not None:
            clusters = [
                {
                    "exception_class": c.exception_class,
                    "count": c.count,
                    "sample_messages": c.sample_messages,
                    "time_distribution": c.time_distribution,
                    "matched_cases": [
                        {
                            "case_id": mc.case_id,
                            "score": mc.score,
                            "summary": mc.summary,
                            "root_cause": mc.root_cause,
                            "solution": mc.solution,
                        }
                        for mc in c.matched_cases
                    ],
                }
                for c in result.clusters
            ]
        return ClusterStatusResponse(
            status=progress.status,
            progress=progress.progress,
            current_step=progress.current_step,
            clusters=clusters,
        )
    else:
        return ClusterStatusResponse(
            status=progress.status,
            progress=progress.progress,
            current_step=progress.current_step,
            clusters=None,
        )