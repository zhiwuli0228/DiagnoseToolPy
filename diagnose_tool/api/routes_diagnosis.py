"""POST /api/diagnosis — one-click AI preliminary diagnosis."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from diagnose_tool.analyzer.diagnosis import (
    DiagnosisOrchestrator,
    DiagnosisError,
    TaskNotFoundError,
    EvidenceNotFoundError,
)
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


class DiagnosisRequest(BaseModel):
    task_id: str = Field(min_length=1, description="Analysis task identifier")


class DiagnosisResponse(BaseModel):
    case_id: str
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
        # Safe error message only — no API key, full paths, or stack traces
        error_msg = str(exc)
        if "500" in error_msg or "timeout" in error_msg.lower():
            detail = "AI diagnosis failed: LLM API error"
        else:
            detail = "AI diagnosis failed"
        logger.warning("LLM API error during diagnosis: %s", exc)
        raise HTTPException(status_code=500, detail=detail)
    except DiagnosisError as exc:
        logger.error("Diagnosis error: %s", exc)
        raise HTTPException(status_code=500, detail="AI diagnosis failed")

    return DiagnosisResponse(case_id=case_id, diagnosis=diagnosis)