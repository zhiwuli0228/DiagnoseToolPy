"""Conversational diagnosis API — multi-turn AI diagnosis with user context."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from diagnose_tool.analyzer.case_quality_scorer import CaseQualityScorer, DraftManager
from diagnose_tool.analyzer.conversation_manager import (
    ConversationManager,
    ConversationState,
    UserContext,
)
from diagnose_tool.analyzer.question_generator import QuestionGenerator
from diagnose_tool.analyzer.session_store import SessionStore
from diagnose_tool.core.llm_client import LLMClientError
from diagnose_tool.core.llm_config import AppLLMConfig, load_llm_config

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


# --- Degraded Response Models ---


class DegradedResponse(BaseModel):
    """Response when LLM is unavailable - provides workspace export option."""
    degraded: bool = True
    error_type: str = "llm_unavailable"
    message: str = "AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually."
    workspace_export_url: str = "/api/diagnosis/export-workspace"
    workspace_export_options: dict = Field(default_factory=dict)


# --- Request/Response Models ---


class UserContextModel(BaseModel):
    """User-provided context with structured markers."""
    phenomenon: str = Field(default="", description="问题现象描述")
    stack: str = Field(default="", description="运行时堆栈信息")
    params: str = Field(default="", description="关键入参信息")


class ConversationStartRequest(BaseModel):
    """Start or continue a diagnosis conversation."""
    session_id: str | None = Field(default=None, description="Session ID (None to create new)")
    user_context: UserContextModel = Field(description="User provided context")
    evidence_refs: list[str] = Field(default_factory=list, description="Selected log evidence IDs")
    mode: str = Field(default="user-priority", description="Diagnosis mode: user-priority or log-priority")
    max_follow_up_rounds: int = Field(default=3, ge=1, le=10, description="Max follow-up question rounds")


class ConversationStartResponse(BaseModel):
    """Response after starting or continuing a conversation."""
    session_id: str
    is_new_session: bool
    turn_id: str
    state: str  # waiting_for_input, awaiting_user_reply, diagnosis_complete, skipped
    ai_question: str | None = None
    ai_diagnosis: str | None = None
    disclaimer: str | None = None


class ConversationContinueRequest(BaseModel):
    """Continue conversation with user's reply to follow-up question."""
    user_reply: str = Field(description="User's reply to the follow-up question")


class ConversationHistoryResponse(BaseModel):
    """Get conversation history and current state."""
    session_id: str
    status: str
    mode: str
    turns: list[dict]
    current_state: str


class SkipResponse(BaseModel):
    """Response when user skips follow-up questions."""
    session_id: str
    turn_id: str
    state: str
    ai_diagnosis: str
    disclaimer: str = "以下结论基于不完整信息，仅供参考。"


class EndConversationResponse(BaseModel):
    """Response after ending a conversation."""
    session_id: str
    quality_score: dict | None = None
    case_id: str | None = None
    is_draft: bool
    diagnosis: str


# --- Conversation Manager Setup ---


def _get_session_store(data_dir: Path) -> SessionStore:
    return SessionStore(data_dir / "sessions")


def _get_conversation_manager(llm_config: AppLLMConfig) -> ConversationManager:
    return ConversationManager(
        session_store=_get_session_store(llm_config.data_dir),
        data_dir=llm_config.data_dir,
        max_follow_up_rounds=3,
    )


def _get_question_generator(llm_config: AppLLMConfig) -> QuestionGenerator:
    return QuestionGenerator(
        llm_config=llm_config,
        data_dir=llm_config.data_dir,
    )


def _get_case_scorer(llm_config: AppLLMConfig) -> CaseQualityScorer:
    return CaseQualityScorer(
        cases_dir=llm_config.data_dir / "cases",
        drafts_dir=llm_config.data_dir / "cases" / "_drafts",
    )


# --- API Endpoints ---


@router.post("/diagnosis/conversation", response_model=ConversationStartResponse)
def start_conversation(
    request: ConversationStartRequest,
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
) -> ConversationStartResponse:
    """Create a new diagnosis conversation or continue an existing one.

    If session_id is provided, continues that session.
    Otherwise creates a new session.
    """
    llm_config = _get_llm_config()

    if not llm_config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI diagnosis is not enabled. Set llm.enabled to true in config/app.yaml",
        )

    manager = _get_conversation_manager(llm_config)
    qgen = _get_question_generator(llm_config)

    # Parse user context
    user_ctx = UserContext(
        phenomenon=request.user_context.phenomenon,
        stack=request.user_context.stack,
        params=request.user_context.params,
    )

    # Create or get session
    session_id = request.session_id or x_session_id
    metadata, turn, is_new = manager.create_or_continue(
        session_id=session_id,
        user_context=user_ctx,
        evidence_refs=request.evidence_refs,
        mode=request.mode,
    )

    # Evaluate sufficiency and generate response
    evidence = _build_evidence_context(request.evidence_refs, llm_config.data_dir)

    try:
        sufficiency = qgen.evaluate_sufficiency(
            user_context=user_ctx.to_dict(),
            evidence=evidence,
        )

        if sufficiency.sufficient:
            # Generate diagnosis directly
            similar_cases = _get_similar_cases(llm_config.data_dir)
            diag_result = qgen.generate_diagnosis(
                user_context=user_ctx.to_dict(),
                evidence=evidence,
                similar_cases=similar_cases,
            )

            turn.ai_diagnosis = diag_result.diagnosis
            turn.state = ConversationState.DIAGNOSIS_COMPLETE
            response_state = "diagnosis_complete"
            ai_diagnosis = diag_result.diagnosis
            ai_question = None
        else:
            # Generate follow-up question
            question_result = qgen.generate_question(
                user_context=user_ctx.to_dict(),
                missing=sufficiency.missing,
            )

            turn.ai_question = question_result.question
            turn.state = ConversationState.AWAITING_USER_REPLY
            response_state = "awaiting_user_reply"
            ai_question = question_result.question
            ai_diagnosis = None

    except LLMClientError as exc:
        logger.warning("LLM API error during conversation start: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=DegradedResponse(
                degraded=True,
                error_type="llm_unavailable",
                message="AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
                workspace_export_url="/api/diagnosis/export-workspace",
                workspace_export_options={
                    "session_id": metadata.session_id,
                    "user_context": request.user_context.model_dump(),
                    "evidence_refs": request.evidence_refs,
                },
            ).model_dump(),
        )

    # Save turn
    manager.save_turn(metadata.session_id, turn)

    return ConversationStartResponse(
        session_id=metadata.session_id,
        is_new_session=is_new,
        turn_id=turn.to_record().turn_id,
        state=response_state,
        ai_question=ai_question,
        ai_diagnosis=ai_diagnosis,
    )


@router.get("/diagnosis/conversation/{session_id}", response_model=ConversationHistoryResponse)
def get_conversation(session_id: str) -> ConversationHistoryResponse:
    """Get conversation state and history."""
    llm_config = _get_llm_config()
    store = _get_session_store(llm_config.data_dir)

    try:
        metadata = store.get_session(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    history = store.get_conversation_history(session_id)
    turns = [t.to_dict() for t in history]

    current_state = "unknown"
    if metadata.status == "completed":
        current_state = "diagnosis_complete"
    elif turns:
        last_turn = history[-1]
        current_state = last_turn.ai_diagnosis and "diagnosis_complete" or "awaiting_user_reply"

    return ConversationHistoryResponse(
        session_id=session_id,
        status=metadata.status,
        mode=metadata.mode,
        turns=turns,
        current_state=current_state,
    )


@router.post("/diagnosis/conversation/{session_id}/continue", response_model=ConversationStartResponse)
def continue_conversation(
    session_id: str,
    request: ConversationContinueRequest,
) -> ConversationStartResponse:
    """Continue conversation with user's reply to follow-up question."""
    llm_config = _get_llm_config()

    if not llm_config.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI diagnosis is not enabled.",
        )

    manager = _get_conversation_manager(llm_config)
    store = _get_session_store(llm_config.data_dir)
    qgen = _get_question_generator(llm_config)

    try:
        store.get_session(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    history = store.get_conversation_history(session_id)
    if not history:
        raise HTTPException(status_code=400, detail="No conversation to continue")

    last_turn = history[-1]
    turn_number = len(history) + 1

    # Create new turn with user's reply merged
    reply_ctx = UserContext.parse(request.user_reply)
    merged_ctx = UserContext(
        phenomenon=(
            (last_turn.user_context.get("phenomenon") or "")
            + ("\n" if reply_ctx.phenomenon else "")
            + reply_ctx.phenomenon
        ).strip(),
        stack=(
            (last_turn.user_context.get("stack") or "")
            + ("\n" if reply_ctx.stack else "")
            + reply_ctx.stack
        ).strip(),
        params=(
            (last_turn.user_context.get("params") or "")
            + ("\n" if reply_ctx.params else "")
            + reply_ctx.params
        ).strip(),
    )

    from diagnose_tool.analyzer.conversation_manager import ConversationTurn
    new_turn = ConversationTurn(
        turn_number=turn_number,
        user_context=merged_ctx,
        evidence_refs=last_turn.evidence_refs,
        mode=last_turn.mode,
    )

    # Evaluate again
    evidence = _build_evidence_context(new_turn.evidence_refs, llm_config.data_dir)

    try:
        sufficiency = qgen.evaluate_sufficiency(
            user_context=merged_ctx.to_dict(),
            evidence=evidence,
        )

        if sufficiency.sufficient:
            similar_cases = _get_similar_cases(llm_config.data_dir)
            diag_result = qgen.generate_diagnosis(
                user_context=merged_ctx.to_dict(),
                evidence=evidence,
                similar_cases=similar_cases,
            )
            new_turn.ai_diagnosis = diag_result.diagnosis
            new_turn.state = ConversationState.DIAGNOSIS_COMPLETE
            response_state = "diagnosis_complete"
            ai_question = None
            ai_diagnosis = diag_result.diagnosis
        else:
            question_result = qgen.generate_question(
                user_context=merged_ctx.to_dict(),
                missing=sufficiency.missing,
            )
            new_turn.ai_question = question_result.question
            new_turn.state = ConversationState.AWAITING_USER_REPLY
            response_state = "awaiting_user_reply"
            ai_question = question_result.question
            ai_diagnosis = None

    except LLMClientError as exc:
        logger.warning("LLM API error during conversation continue: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=DegradedResponse(
                degraded=True,
                error_type="llm_unavailable",
                message="AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
                workspace_export_url="/api/diagnosis/export-workspace",
                workspace_export_options={
                    "session_id": session_id,
                },
            ).model_dump(),
        )

    manager.save_turn(session_id, new_turn)

    return ConversationStartResponse(
        session_id=session_id,
        is_new_session=False,
        turn_id=new_turn.to_record().turn_id,
        state=response_state,
        ai_question=ai_question,
        ai_diagnosis=ai_diagnosis,
    )


@router.post("/diagnosis/conversation/{session_id}/skip", response_model=SkipResponse)
def skip_follow_up(session_id: str) -> SkipResponse:
    """Skip follow-up questions and force diagnosis with available info."""
    llm_config = _get_llm_config()

    if not llm_config.enabled:
        raise HTTPException(status_code=503, detail="AI diagnosis is not enabled.")

    store = _get_session_store(llm_config.data_dir)
    qgen = _get_question_generator(llm_config)
    manager = _get_conversation_manager(llm_config)

    try:
        store.get_session(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    history = store.get_conversation_history(session_id)
    if not history:
        raise HTTPException(status_code=400, detail="No conversation to skip")

    last_turn = history[-1]
    merged_ctx = UserContext(
        phenomenon=last_turn.user_context.get("phenomenon", ""),
        stack=last_turn.user_context.get("stack", ""),
        params=last_turn.user_context.get("params", ""),
    )

    evidence = _build_evidence_context(last_turn.evidence_refs, llm_config.data_dir)
    similar_cases = _get_similar_cases(llm_config.data_dir)

    try:
        diag_result = qgen.generate_diagnosis(
            user_context=merged_ctx.to_dict(),
            evidence=evidence,
            similar_cases=similar_cases,
            from_incomplete=True,
        )

        from diagnose_tool.analyzer.conversation_manager import ConversationTurn
        skip_turn = ConversationTurn(
            turn_number=len(history) + 1,
            user_context=merged_ctx,
            evidence_refs=last_turn.evidence_refs,
            mode=last_turn.mode,
            ai_diagnosis=f"以下结论基于不完整信息，仅供参考。\n\n{diag_result.diagnosis}",
            state=ConversationState.SKIPPED,
        )

        manager.save_turn(session_id, skip_turn)

        return SkipResponse(
            session_id=session_id,
            turn_id=skip_turn.to_record().turn_id,
            state="skipped",
            ai_diagnosis=diag_result.diagnosis,
        )

    except LLMClientError as exc:
        logger.warning("LLM API error during skip follow-up: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=DegradedResponse(
                degraded=True,
                error_type="llm_unavailable",
                message="AI diagnosis temporarily unavailable. You can export the workspace and diagnose manually.",
                workspace_export_url="/api/diagnosis/export-workspace",
                workspace_export_options={
                    "session_id": session_id,
                },
            ).model_dump(),
        )


@router.post("/diagnosis/conversation/{session_id}/end", response_model=EndConversationResponse)
def end_conversation(session_id: str) -> EndConversationResponse:
    """End conversation and trigger case quality scoring."""
    llm_config = _get_llm_config()

    store = _get_session_store(llm_config.data_dir)
    scorer = _get_case_scorer(llm_config)

    try:
        metadata = store.get_session(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    history = store.get_conversation_history(session_id)
    if not history:
        raise HTTPException(status_code=400, detail="No conversation to end")

    # Calculate quality score
    total_rounds = len(history)
    user_questions = sum(1 for t in history if t.ai_question)
    last_turn = history[-1]

    has_stack = bool(last_turn.user_context.get("stack"))
    has_phenomenon = bool(last_turn.user_context.get("phenomenon"))
    has_params = bool(last_turn.user_context.get("params"))

    quality = scorer.score_diagnosis(
        conversation_rounds=total_rounds,
        user_questions=user_questions,
        has_stack=has_stack,
        has_phenomenon=has_phenomenon,
        has_params=has_params,
        ai_confidence=0.5,
    )

    # End session
    metadata.status = "completed"
    store.update_session(metadata)

    diagnosis_content = last_turn.ai_diagnosis or "（无诊断结论）"
    conversation_data = [t.to_dict() for t in history]

    if scorer.should_promote(quality):
        # Auto-promote to case
        case_id = _promote_to_case(
            llm_config.data_dir / "cases",
            session_id,
            diagnosis_content,
            conversation_data,
        )
        is_draft = False
    else:
        # Create draft
        draft_mgr = DraftManager(llm_config.data_dir / "cases" / "_drafts")
        draft_path = draft_mgr.create_draft(
            session_id=session_id,
            quality_score=quality,
            diagnosis_content=diagnosis_content,
            conversation_history=conversation_data,
        )
        case_id = draft_path.name
        is_draft = True

    return EndConversationResponse(
        session_id=session_id,
        quality_score=quality.to_dict(),
        case_id=case_id,
        is_draft=is_draft,
        diagnosis=diagnosis_content,
    )


# --- Helpers ---


def _build_evidence_context(evidence_refs: list[str], data_dir: Path) -> str:
    """Build evidence context from refs. Simplified - integrate with evidence_cache."""
    if not evidence_refs:
        return "（无日志证据）"
    return f"（{len(evidence_refs)} 条日志证据）"


def _get_similar_cases(data_dir: Path) -> str:
    """Get similar cases context. Simplified - integrate with retrieval module."""
    return "（暂无历史案例参考）"


def _promote_to_case(
    cases_dir: Path,
    session_id: str,
    diagnosis_content: str,
    conversation_data: list[dict],
) -> str:
    """Promote conversation to a case."""
    import hashlib
    import json

    slug = hashlib.md5(session_id.encode()).hexdigest()[:8]
    case_id = slug
    case_dir = cases_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / "ai-diagnosis.md").write_text(
        f"# AI DIAGNOSIS\n\n{diagnosis_content}",
        encoding="utf-8",
    )

    (case_dir / "conversation.json").write_text(
        json.dumps(conversation_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    from datetime import datetime, timezone
    (case_dir / "metadata.yaml").write_text(
        f"case_id: {case_id}\n"
        f"source_session: {session_id}\n"
        f"created_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"auto_promoted: true\n",
        encoding="utf-8",
    )

    return case_id
