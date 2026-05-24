"""Case quality scoring and draft management — pure Python, FastAPI-independent."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


# --- Data Models --------------------------------------------------------


@dataclass
class QualityScore:
    """Quality score breakdown for a diagnosis."""
    total: float
    conversation_rounds: float
    user_questions: float
    completeness: float
    ai_confidence: float
    breakdown: dict = field(default_factory=dict)
    recommendation: str = "unknown"  # auto_promote, draft, unknown

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "conversation_rounds": self.conversation_rounds,
            "user_questions": self.user_questions,
            "completeness": self.completeness,
            "ai_confidence": self.ai_confidence,
            "breakdown": self.breakdown,
            "recommendation": self.recommendation,
        }


# --- Quality Scorer -----------------------------------------------------


class CaseQualityScorer:
    """Scores diagnosis quality and manages draft cases."""

    # Scoring weights
    ROUNDS_WEIGHT = 0.3
    QUESTIONS_WEIGHT = 0.2
    COMPLETENESS_WEIGHT = 0.3
    CONFIDENCE_WEIGHT = 0.2

    # Thresholds
    PROMOTE_THRESHOLD = 8.0

    # Rounds scoring
    ROUNDS_SCORE_1 = 2.0
    ROUNDS_SCORE_2 = 6.0
    ROUNDS_SCORE_3_PLUS = 10.0

    def __init__(self, cases_dir: Path, drafts_dir: Path) -> None:
        self._cases_dir = Path(cases_dir)
        self._drafts_dir = Path(drafts_dir)

    def score_diagnosis(
        self,
        conversation_rounds: int,
        user_questions: int,
        has_stack: bool,
        has_phenomenon: bool,
        has_params: bool,
        ai_confidence: float = 0.5,
    ) -> QualityScore:
        """Calculate quality score for a diagnosis.

        Args:
            conversation_rounds: Number of conversation turns.
            user_questions: Number of user-initiated questions.
            has_stack: Whether stack trace was provided.
            has_phenomenon: Whether phenomenon description was provided.
            has_params: Whether parameters were provided.
            ai_confidence: AI confidence score (0.0-1.0).

        Returns:
            QualityScore with breakdown and recommendation.
        """
        rounds_score = self._score_rounds(conversation_rounds)
        questions_score = self._score_questions(user_questions)
        completeness_score = self._score_completeness(
            has_stack, has_phenomenon, has_params
        )
        confidence_score = ai_confidence * 10

        total = (
            rounds_score * self.ROUNDS_WEIGHT
            + questions_score * self.QUESTIONS_WEIGHT
            + completeness_score * self.COMPLETENESS_WEIGHT
            + confidence_score * self.CONFIDENCE_WEIGHT
        )

        recommendation = (
            "auto_promote"
            if total >= self.PROMOTE_THRESHOLD
            else "draft"
        )

        return QualityScore(
            total=round(total, 2),
            conversation_rounds=rounds_score,
            user_questions=questions_score,
            completeness=completeness_score,
            ai_confidence=confidence_score,
            breakdown={
                "conversation_rounds": {
                    "score": rounds_score,
                    "raw": conversation_rounds,
                },
                "user_questions": {
                    "score": questions_score,
                    "raw": user_questions,
                },
                "completeness": {
                    "score": completeness_score,
                    "has_stack": has_stack,
                    "has_phenomenon": has_phenomenon,
                    "has_params": has_params,
                },
                "ai_confidence": {
                    "score": confidence_score,
                    "raw": ai_confidence,
                },
            },
            recommendation=recommendation,
        )

    def should_promote(self, score: QualityScore) -> bool:
        """Check if score warrants auto-promotion."""
        return score.recommendation == "auto_promote"

    def _score_rounds(self, rounds: int) -> float:
        if rounds <= 0:
            return 0.0
        elif rounds == 1:
            return self.ROUNDS_SCORE_1
        elif rounds == 2:
            return self.ROUNDS_SCORE_2
        else:
            return self.ROUNDS_SCORE_3_PLUS

    def _score_questions(self, questions: int) -> float:
        return min((questions / 5) * 10, 10.0)

    def _score_completeness(
        self,
        has_stack: bool,
        has_phenomenon: bool,
        has_params: bool,
    ) -> float:
        score = 0.0
        if has_stack:
            score += 4.0
        if has_phenomenon:
            score += 3.0
        if has_params:
            score += 3.0
        return score


class DraftManager:
    """Manages draft cases in the drafts directory."""

    def __init__(self, drafts_dir: Path) -> None:
        self._drafts_dir = Path(drafts_dir)
        self._drafts_dir.mkdir(parents=True, exist_ok=True)

    def create_draft(
        self,
        session_id: str,
        quality_score: QualityScore,
        diagnosis_content: str,
        conversation_history: list[dict],
    ) -> Path:
        """Create a draft case from a low-quality diagnosis.

        Args:
            session_id: Original session identifier.
            quality_score: Quality evaluation result.
            diagnosis_content: The diagnosis text.
            conversation_history: List of conversation turn dicts.

        Returns:
            Path to created draft directory.
        """
        import uuid
        draft_id = str(uuid.uuid4())[:8]
        draft_dir = self._drafts_dir / f"draft_{draft_id}"
        draft_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "draft_id": draft_id,
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": quality_score.to_dict(),
            "status": "pending_review",
        }

        (draft_dir / "metadata.yaml").write_text(
            yaml.safe_dump(metadata, allow_unicode=True),
            encoding="utf-8",
        )

        (draft_dir / "ai-diagnosis.md").write_text(
            f"# DRAFT AI DIAGNOSIS — PENDING REVIEW\n\n"
            f"> Quality Score: {quality_score.total}/10\n"
            f"> Recommendation: {quality_score.recommendation}\n\n"
            f"{diagnosis_content}",
            encoding="utf-8",
        )

        import json
        (draft_dir / "conversation.json").write_text(
            json.dumps(conversation_history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info("Created draft case: %s", draft_dir.name)
        return draft_dir

    def promote_draft(self, draft_dir: Path, cases_dir: Path) -> Path:
        """Promote a draft case to正式 case directory.

        Args:
            draft_dir: Draft case directory.
            cases_dir: Target cases directory.

        Returns:
            Path to promoted case directory.
        """
        if not draft_dir.exists():
            raise FileNotFoundError(f"Draft not found: {draft_dir}")

        metadata = yaml.safe_load(
            (draft_dir / "metadata.yaml").read_text(encoding="utf-8")
        )

        import hashlib
        slug = hashlib.md5(
            metadata["session_id"].encode()
        ).hexdigest()[:8]

        case_id = f"{slug}"
        case_dir = cases_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(draft_dir / "ai-diagnosis.md", case_dir / "ai-diagnosis.md")
        shutil.copy2(draft_dir / "conversation.json", case_dir / "conversation.json")

        case_metadata = {
            "case_id": case_id,
            "source_session": metadata["session_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "promoted_from_draft": True,
            "original_draft_id": metadata["draft_id"],
            "quality_score": metadata["quality_score"],
        }
        (case_dir / "metadata.yaml").write_text(
            yaml.safe_dump(case_metadata, allow_unicode=True),
            encoding="utf-8",
        )

        shutil.rmtree(draft_dir)
        logger.info("Promoted draft to case: %s", case_id)
        return case_dir

    def cleanup_old_drafts(self, max_age_days: int = 30) -> int:
        """Remove drafts older than max_age_days.

        Args:
            max_age_days: Maximum age in days before deletion.

        Returns:
            Number of drafts removed.
        """
        if not self._drafts_dir.exists():
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        removed = 0

        for draft_path in self._drafts_dir.iterdir():
            if not draft_path.is_dir():
                continue

            try:
                metadata_path = draft_path / "metadata.yaml"
                if not metadata_path.exists():
                    continue

                metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
                created = datetime.fromisoformat(metadata["created_at"])

                if created < cutoff:
                    shutil.rmtree(draft_path)
                    removed += 1
                    logger.info("Removed expired draft: %s", draft_path.name)
            except Exception as exc:
                logger.warning("Failed to check draft %s: %s", draft_path, exc)

        return removed
