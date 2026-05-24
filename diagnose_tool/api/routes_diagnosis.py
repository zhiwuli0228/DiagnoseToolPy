"""POST /api/diagnosis — one-click AI preliminary diagnosis."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from diagnose_tool.analyzer.diagnosis import (
    DiagnosisOrchestrator,
    DiagnosisError,
    TaskNotFoundError,
    EvidenceNotFoundError,
)
from diagnose_tool.analyzer.evidence_cache import EvidenceCacheManager
from diagnose_tool.analyzer.evidence_compressor import (
    CompressionOptions,
    compress_log_entries,
    build_evidence_markdown,
    truncate_to_token_budget,
)
from diagnose_tool.core.llm_client import LLMClient, LLMClientError
from diagnose_tool.core.llm_config import AppLLMConfig, load_llm_config
from diagnose_tool.exporter import WorkspaceExporter, WorkspaceExportError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["diagnosis"])


# Load LLM config once at module level (startup)
_llm_config: AppLLMConfig | None = None


def _get_llm_config() -> AppLLMConfig:
    """Get cached LLM config, loading it once."""
    global _llm_config
    if _llm_config is None:
        _llm_config = load_llm_config()
    return _llm_config


class DiagnosisRequest(BaseModel):
    task_id: str = Field(min_length=1, description="Analysis task identifier")


class DiagnosisResponse(BaseModel):
    case_id: str
    diagnosis: str


# --- Degraded Response Models ---


class DegradedResponse(BaseModel):
    """Response when LLM is unavailable - provides workspace export option."""
    degraded: bool = True
    error_type: str = "llm_unavailable"
    message: str = "AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually."
    workspace_export_url: str = "/api/diagnosis/export-workspace"
    workspace_export_options: dict[str, Any] = Field(default_factory=dict)


# --- Export Workspace Models ---


class UserContextModel(BaseModel):
    """User-provided context with structured markers."""
    phenomenon: str = Field(default="")
    stack: str = Field(default="")
    params: str = Field(default="")


class ExportWorkspaceRequest(BaseModel):
    """Request to export diagnostic workspace to a user directory."""
    task_id: str | None = Field(default=None, description="Analysis task ID")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    cache_key: str | None = Field(default=None, description="Search/cluster cache key")
    workspace_dir: str = Field(min_length=1, description="User-selected workspace directory")
    user_context: UserContextModel | None = Field(default=None, description="User context to include")
    selections: list[SelectionItem] | None = Field(default=None, description="Selected items for diagnosis")


class ExportWorkspaceResponse(BaseModel):
    """Response after exporting workspace."""
    success: bool
    workspace_dir: str
    files_written: list[str] = Field(default_factory=list)
    detection_hint: str = "Save your diagnosis as result.md in the workspace directory. The system will detect it automatically."


class PreviewPromptRequest(BaseModel):
    """Request to preview diagnosis prompt without exporting."""
    task_id: str | None = Field(default=None, description="Analysis task ID")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    cache_key: str | None = Field(default=None, description="Search/cluster cache key")
    user_context: UserContextModel | None = Field(default=None, description="User context to include")
    selections: list[SelectionItem] | None = Field(default=None, description="Selected items for diagnosis")


class PreviewPromptResponse(BaseModel):
    """Response containing generated prompt content."""
    prompt: str


# --- Custom Diagnosis Models ---


class SelectionItem(BaseModel):
    """A single selection item from evidence basket."""
    type: str = Field(description="Selection type: group, group_all, log, or cluster")
    group_key: str | None = None
    id: str | None = None
    cluster_index: int | None = None


class CompressionOptionsModel(BaseModel):
    """Options for evidence compression."""
    include_stack: bool = Field(default=True)
    include_timeline: bool = Field(default=True)
    max_tokens: int = Field(default=2000, ge=100, le=10000)


class CustomDiagnosisRequest(BaseModel):
    """Request for custom diagnosis from search or cluster results."""
    cache_key: str = Field(min_length=1, description="Cache key from search or cluster")
    selections: list[SelectionItem] = Field(description="Selected items to diagnose")
    options: CompressionOptionsModel = Field(default_factory=CompressionOptionsModel)


class CustomDiagnosisResponse(BaseModel):
    """Response for custom diagnosis."""
    diagnosis: str


@router.post("/diagnosis", response_model=DiagnosisResponse)
def diagnose(request: DiagnosisRequest) -> DiagnosisResponse:
    """Run AI preliminary diagnosis for a completed analysis task.

    The diagnosis is assistive only and must be reviewed by a human engineer
    before being treated as confirmed root cause.
    """
    llm_config = _get_llm_config()

    if not llm_config.enabled:
        raise HTTPException(
            status_code=503,
            detail=(
                "AI diagnosis is not enabled. "
                "Set llm.enabled to true in config/app.yaml"
            ),
        )

    orchestrator = DiagnosisOrchestrator(llm_config, llm_config.data_dir)

    try:
        case_id, diagnosis = orchestrator.run(request.task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except EvidenceNotFoundError:
        raise HTTPException(status_code=404, detail="Evidence pack not found for task")
    except LLMClientError as exc:
        logger.warning("LLM API error during diagnosis: %s", exc)
        degraded = _degraded_response(
            error_msg=str(exc),
            task_id=request.task_id,
        )
        raise HTTPException(
            status_code=503,
            detail=degraded.model_dump(),
        )
    except DiagnosisError as exc:
        logger.error("Diagnosis error: %s", exc)
        raise HTTPException(status_code=500, detail="AI diagnosis failed")

    return DiagnosisResponse(case_id=case_id, diagnosis=diagnosis)


@router.post("/diagnosis/search", response_model=CustomDiagnosisResponse)
def diagnose_from_search(request: CustomDiagnosisRequest) -> CustomDiagnosisResponse:
    """Run AI diagnosis from search cache.

    Accepts cache_key from search results and user selections,
    compresses evidence, and returns LLM diagnosis.
    """
    llm_config = _get_llm_config()

    if not llm_config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI diagnosis is not enabled. Set llm.enabled to true in config/app.yaml",
        )

    # Load cache
    cache_mgr = EvidenceCacheManager(llm_config.data_dir)
    cache_dir = cache_mgr.get_cache(request.cache_key)
    if cache_dir is None:
        raise HTTPException(status_code=404, detail="Cache not found")

    # Load matched lines from cache
    all_entries = cache_mgr.load_matched_lines(request.cache_key)
    if not all_entries:
        raise HTTPException(status_code=404, detail="No cached entries found")

    # Convert entries to dict format for compression
    entries_dicts = [_entry_to_dict(e) for e in all_entries]

    # Resolve selections to specific entries
    selected_entries = _resolve_selections(
        entries_dicts, request.selections, request.cache_key, cache_mgr
    )

    if not selected_entries:
        raise HTTPException(status_code=400, detail="No entries selected for diagnosis")

    # Compress evidence
    compression_opts = CompressionOptions(
        include_stack=request.options.include_stack,
        include_timeline=request.options.include_timeline,
        max_tokens=request.options.max_tokens,
    )
    compressed = compress_log_entries(selected_entries, compression_opts)
    evidence_md = build_evidence_markdown(compressed, compression_opts)

    # Truncate to token budget
    evidence_md = truncate_to_token_budget(evidence_md, request.options.max_tokens)

    # Build prompt and call LLM
    try:
        diagnosis = _call_llm(llm_config, evidence_md)
    except LLMClientError as exc:
        logger.warning("LLM API error during search diagnosis: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=DegradedResponse(
                degraded=True,
                error_type="llm_unavailable",
                message="AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
                workspace_export_url="/api/diagnosis/export-workspace",
                workspace_export_options={
                    "cache_key": request.cache_key,
                    "selections": [s.model_dump() for s in request.selections],
                },
            ).model_dump(),
        )

    return CustomDiagnosisResponse(diagnosis=diagnosis)


@router.post("/diagnosis/cluster", response_model=CustomDiagnosisResponse)
def diagnose_from_cluster(request: CustomDiagnosisRequest) -> CustomDiagnosisResponse:
    """Run AI diagnosis from cluster cache.

    Accepts task_id as cache_key from cluster results and user selections,
    compresses evidence, and returns LLM diagnosis.
    """
    llm_config = _get_llm_config()

    if not llm_config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI diagnosis is not enabled. Set llm.enabled to true in config/app.yaml",
        )

    # For cluster, cache_key is the task_id
    cache_mgr = EvidenceCacheManager(llm_config.data_dir)
    cache_dir = cache_mgr.get_cache(request.cache_key)
    if cache_dir is None:
        raise HTTPException(status_code=404, detail="Cache not found")

    # Load matched lines from cache
    all_entries = cache_mgr.load_matched_lines(request.cache_key)
    if not all_entries:
        raise HTTPException(status_code=404, detail="No cached entries found")

    # Convert entries to dict format for compression
    entries_dicts = [_entry_to_dict(e) for e in all_entries]

    # Resolve selections - for cluster, cluster_index refers to position in result
    selected_entries = _resolve_cluster_selections(
        entries_dicts, request.selections
    )

    if not selected_entries:
        raise HTTPException(status_code=400, detail="No entries selected for diagnosis")

    # Compress evidence
    compression_opts = CompressionOptions(
        include_stack=request.options.include_stack,
        include_timeline=request.options.include_timeline,
        max_tokens=request.options.max_tokens,
    )
    compressed = compress_log_entries(selected_entries, compression_opts)
    evidence_md = build_evidence_markdown(compressed, compression_opts)

    # Truncate to token budget
    evidence_md = truncate_to_token_budget(evidence_md, request.options.max_tokens)

    # Build prompt and call LLM
    try:
        diagnosis = _call_llm(llm_config, evidence_md)
    except LLMClientError as exc:
        logger.warning("LLM API error during cluster diagnosis: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=DegradedResponse(
                degraded=True,
                error_type="llm_unavailable",
                message="AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
                workspace_export_url="/api/diagnosis/export-workspace",
                workspace_export_options={
                    "cache_key": request.cache_key,
                    "selections": [s.model_dump() for s in request.selections],
                },
            ).model_dump(),
        )

    return CustomDiagnosisResponse(diagnosis=diagnosis)


@router.post("/diagnosis/export-workspace", response_model=ExportWorkspaceResponse)
def export_workspace(request: ExportWorkspaceRequest) -> ExportWorkspaceResponse:
    """Export complete diagnostic workspace to user-specified directory.

    Creates directory structure with context, logs, cases, and diagnosis prompt.
    Allows user to complete diagnosis manually via OpenCode.
    """
    llm_config = _get_llm_config()

    # Validate that at least one source is provided
    if not request.task_id and not request.session_id and not request.cache_key:
        raise HTTPException(
            status_code=400,
            detail="At least one of task_id, session_id, or cache_key must be provided",
        )

    # Validate workspace_dir
    workspace_dir = Path(request.workspace_dir)
    if not workspace_dir.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Directory does not exist: {request.workspace_dir}",
        )

    # Prepare user context
    user_context = None
    if request.user_context:
        user_context = {
            "phenomenon": request.user_context.phenomenon or "",
            "stack": request.user_context.stack or "",
            "params": request.user_context.params or "",
        }

    # Prepare selections
    selections = None
    if request.selections:
        selections = [s.model_dump() for s in request.selections]

    exporter = WorkspaceExporter(llm_config)

    try:
        if request.task_id:
            files_written = exporter.export_from_task_id(
                task_id=request.task_id,
                workspace_dir=workspace_dir,
                user_context=user_context,
            )
        elif request.session_id:
            files_written = exporter.export_from_session(
                session_id=request.session_id,
                workspace_dir=workspace_dir,
                user_context=user_context,
            )
        elif request.cache_key and selections:
            files_written = exporter.export_from_cache(
                cache_key=request.cache_key,
                workspace_dir=workspace_dir,
                selections=selections,
                user_context=user_context,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="cache_key requires selections to be provided",
            )

        return ExportWorkspaceResponse(
            success=True,
            workspace_dir=str(workspace_dir),
            files_written=files_written,
        )

    except WorkspaceExportError as exc:
        logger.error("Workspace export failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error during workspace export: %s", exc)
        raise HTTPException(status_code=500, detail="Workspace export failed")


@router.post("/diagnosis/preview-prompt", response_model=PreviewPromptResponse)
def preview_prompt(request: PreviewPromptRequest) -> PreviewPromptResponse:
    """Preview diagnosis prompt without exporting to a directory.

    Generates the prompt content that would be used for workspace export.
    """
    llm_config = _get_llm_config()

    # Validate that at least one source is provided
    if not request.task_id and not request.session_id and not request.cache_key:
        raise HTTPException(
            status_code=400,
            detail="At least one of task_id, session_id, or cache_key must be provided",
        )

    # Prepare user context
    user_context = None
    if request.user_context:
        user_context = {
            "phenomenon": request.user_context.phenomenon or "",
            "stack": request.user_context.stack or "",
            "params": request.user_context.params or "",
        }

    # Prepare selections
    selections = None
    if request.selections:
        selections = [s.model_dump() for s in request.selections]

    exporter = WorkspaceExporter(llm_config)

    try:
        if request.cache_key and selections:
            # For cache-based preview (from search or cluster)
            prompt = exporter.generate_prompt_from_cache(
                cache_key=request.cache_key,
                selections=selections,
                user_context=user_context,
            )
        elif request.session_id:
            # For session-based preview (from diagnosis studio)
            prompt = exporter.generate_prompt_from_session(
                session_id=request.session_id,
                user_context=user_context,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="preview requires either cache_key+selections or session_id",
            )

        return PreviewPromptResponse(prompt=prompt)

    except WorkspaceExportError as exc:
        logger.error("Preview prompt failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error during preview: %s", exc)
        raise HTTPException(status_code=500, detail="Preview failed")


class CheckResultResponse(BaseModel):
    """Response for result.md check."""
    exists: bool
    content: str | None = None
    validation: dict | None = None


@router.get("/diagnosis/check-result")
def check_result(workspace_dir: str) -> CheckResultResponse:
    """Check if result.md exists in workspace directory.

    Validates content before returning.
    """
    workspace_path = Path(workspace_dir)
    result_path = workspace_path / "result.md"

    if not result_path.exists():
        return CheckResultResponse(exists=False)

    try:
        content = result_path.read_text(encoding="utf-8")

        # Validate content
        validation = {
            "is_empty": len(content.strip()) == 0,
            "length": len(content),
            "is_too_short": len(content) < 100,
            "is_prompt_template": _is_prompt_template(content),
        }

        # Return content only if valid
        if validation["is_empty"] or validation["is_too_short"] or validation["is_prompt_template"]:
            return CheckResultResponse(exists=True, content=None, validation=validation)

        return CheckResultResponse(exists=True, content=content, validation=validation)

    except OSError as exc:
        logger.error("Failed to read result.md: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to read result file")


def _is_prompt_template(content: str) -> bool:
    """Check if content appears to be the original prompt template."""
    prompt_markers = [
        "# Role",
        "You are an experienced",
        "{evidence_pack}",
        "{similar_cases}",
        "Diagnosis Instructions",
    ]
    content_lower = content.lower()
    match_count = sum(1 for marker in prompt_markers if marker.lower() in content_lower)
    return match_count >= 3


def _degraded_response(
    error_msg: str,
    task_id: str | None = None,
    session_id: str | None = None,
    cache_key: str | None = None,
    selections: list | None = None,
) -> DegradedResponse:
    """Build a degraded response for LLM unavailability."""
    options: dict[str, Any] = {}
    if task_id:
        options["task_id"] = task_id
    if session_id:
        options["session_id"] = session_id
    if cache_key:
        options["cache_key"] = cache_key
    if selections:
        options["selections"] = selections

    # Determine error type
    error_type = "llm_unavailable"
    if "500" in error_msg or "timeout" in error_msg.lower():
        error_type = "llm_error"

    return DegradedResponse(
        degraded=True,
        error_type=error_type,
        message="AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
        workspace_export_url="/api/diagnosis/export-workspace",
        workspace_export_options=options,
    )


def _entry_to_dict(entry: Any) -> dict:
    """Convert a CachedLogEntry to a dict for compression."""
    if isinstance(entry, dict):
        return entry
    return {
        "id": entry.id,
        "group_key": entry.group_key,
        "event": {
            "timestamp": entry.event.timestamp,
            "level": entry.event.level,
            "thread": entry.event.thread,
            "message": entry.event.message,
            "raw": entry.event.raw,
            "file_path": entry.event.file_path,
            "line_no": entry.event.line_no,
        },
        "context_before": [
            {
                "timestamp": e.timestamp,
                "level": e.level,
                "thread": e.thread,
                "message": e.message,
                "raw": e.raw,
                "file_path": e.file_path,
                "line_no": e.line_no,
            }
            for e in (entry.context_before or [])
        ],
        "context_after": [
            {
                "timestamp": e.timestamp,
                "level": e.level,
                "thread": e.thread,
                "message": e.message,
                "raw": e.raw,
                "file_path": e.file_path,
                "line_no": e.line_no,
            }
            for e in (entry.context_after or [])
        ],
    }


def _resolve_selections(
    entries_dicts: list[dict],
    selections: list[SelectionItem],
    cache_key: str,
    cache_mgr: EvidenceCacheManager,
) -> list[dict]:
    """Resolve selections to specific log entry dicts."""
    selected = []
    for sel in selections:
        if sel.type == "group":
            # Select all entries in the group
            group_key = sel.group_key
            if group_key:
                for entry in entries_dicts:
                    if entry.get("group_key") == group_key:
                        selected.append(entry)
        elif sel.type == "group_all":
            # Same as group - select all in the group
            group_key = sel.group_key
            if group_key:
                for entry in entries_dicts:
                    if entry.get("group_key") == group_key:
                        selected.append(entry)
        elif sel.type == "log":
            # Select single entry by ID
            entry_id = sel.id
            if entry_id:
                entry = cache_mgr.get_entry_by_id(cache_key, entry_id)
                if entry:
                    selected.append(_entry_to_dict(entry))
    return selected


def _resolve_cluster_selections(
    entries_dicts: list[dict],
    selections: list[SelectionItem],
) -> list[dict]:
    """Resolve selections for cluster results."""
    # Group entries by their position in the list (for cluster_index reference)
    # For cluster, we group by group_key and use cluster_index to select groups
    from collections import defaultdict

    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in entries_dicts:
        gk = entry.get("group_key", "unknown")
        groups[gk].append(entry)

    selected = []
    for sel in selections:
        if sel.type == "cluster":
            # cluster_index refers to group by position
            group_list = list(groups.keys())
            idx = sel.cluster_index
            if idx is not None and 0 <= idx < len(group_list):
                group_key = group_list[idx]
                selected.extend(groups[group_key])
        elif sel.type == "group":
            # For cluster, group_key selection
            group_key = sel.group_key
            if group_key and group_key in groups:
                selected.extend(groups[group_key])
        elif sel.type == "group_all":
            group_key = sel.group_key
            if group_key and group_key in groups:
                selected.extend(groups[group_key])
        elif sel.type == "log":
            entry_id = sel.id
            if entry_id:
                for entry in entries_dicts:
                    if entry.get("id") == entry_id:
                        selected.append(entry)
                        break

    return selected


def _call_llm(llm_config: AppLLMConfig, evidence_md: str) -> str:
    """Call LLM with evidence and return diagnosis."""
    template = (
        "# Role\n\n"
        "You are an experienced backend stability engineer.\n\n"
        "# Current Fault Evidence\n\n"
        "{evidence_pack}\n\n"
        "# Diagnosis Instructions\n\n"
        "Please analyze and provide a preliminary diagnosis.\n"
    )

    prompt = template.replace("{evidence_pack}", evidence_md)
    messages = [{"role": "user", "content": prompt}]

    llm_client = LLMClient(llm_config)
    return llm_client.chat(messages=messages)
