"""Tests for case_quality_scorer module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import yaml

from diagnose_tool.analyzer.case_quality_scorer import (
    CaseQualityScorer,
    DraftManager,
    QualityScore,
)


class TestQualityScore:
    def test_quality_score_to_dict(self):
        score = QualityScore(
            total=7.5,
            conversation_rounds=8.0,
            user_questions=6.0,
            completeness=8.0,
            ai_confidence=7.0,
            breakdown={"key": "value"},
            recommendation="draft",
        )
        result = score.to_dict()
        assert result["total"] == 7.5
        assert result["conversation_rounds"] == 8.0
        assert result["user_questions"] == 6.0
        assert result["completeness"] == 8.0
        assert result["ai_confidence"] == 7.0
        assert result["breakdown"] == {"key": "value"}
        assert result["recommendation"] == "draft"


class TestCaseQualityScorer:
    @pytest.fixture
    def scorer(self, tmp_path):
        cases_dir = tmp_path / "cases"
        drafts_dir = tmp_path / "drafts"
        return CaseQualityScorer(cases_dir, drafts_dir)

    def test_score_diagnosis_full_info(self, scorer):
        result = scorer.score_diagnosis(
            conversation_rounds=3,
            user_questions=5,
            has_stack=True,
            has_phenomenon=True,
            has_params=True,
            ai_confidence=0.8,
        )
        assert result.total >= 8.0
        assert result.recommendation == "auto_promote"

    def test_score_diagnosis_minimal_info(self, scorer):
        result = scorer.score_diagnosis(
            conversation_rounds=0,
            user_questions=0,
            has_stack=False,
            has_phenomenon=False,
            has_params=False,
            ai_confidence=0.2,
        )
        assert result.total < 5.0
        assert result.recommendation == "draft"

    def test_score_rounds_scoring(self, scorer):
        # 0 rounds = 0
        assert scorer._score_rounds(0) == 0.0
        # 1 round = 2.0
        assert scorer._score_rounds(1) == 2.0
        # 2 rounds = 6.0
        assert scorer._score_rounds(2) == 6.0
        # 3+ rounds = 10.0
        assert scorer._score_rounds(3) == 10.0
        assert scorer._score_rounds(10) == 10.0

    def test_score_questions_scaling(self, scorer):
        # 0 questions = 0
        assert scorer._score_questions(0) == 0.0
        # 5 questions = 10 (full score)
        assert scorer._score_questions(5) == 10.0
        # 10 questions = 10 (capped)
        assert scorer._score_questions(10) == 10.0
        # 2.5 questions = 5
        assert scorer._score_questions(2) == 4.0

    def test_score_completeness(self, scorer):
        # Nothing = 0
        assert scorer._score_completeness(False, False, False) == 0.0
        # Just stack = 4
        assert scorer._score_completeness(True, False, False) == 4.0
        # Just phenomenon = 3
        assert scorer._score_completeness(False, True, False) == 3.0
        # Just params = 3
        assert scorer._score_completeness(False, False, True) == 3.0
        # All three = 10
        assert scorer._score_completeness(True, True, True) == 10.0
        # Stack + phenomenon = 7
        assert scorer._score_completeness(True, True, False) == 7.0

    def test_should_promote(self, scorer):
        auto_score = QualityScore(
            total=8.5,
            conversation_rounds=10.0,
            user_questions=10.0,
            completeness=10.0,
            ai_confidence=8.0,
            recommendation="auto_promote",
        )
        draft_score = QualityScore(
            total=7.5,
            conversation_rounds=8.0,
            user_questions=6.0,
            completeness=8.0,
            ai_confidence=7.0,
            recommendation="draft",
        )
        assert scorer.should_promote(auto_score) is True
        assert scorer.should_promote(draft_score) is False

    def test_score_breakdown_contains_details(self, scorer):
        result = scorer.score_diagnosis(
            conversation_rounds=2,
            user_questions=3,
            has_stack=True,
            has_phenomenon=True,
            has_params=False,
            ai_confidence=0.6,
        )
        assert "conversation_rounds" in result.breakdown
        assert result.breakdown["conversation_rounds"]["raw"] == 2
        assert "completeness" in result.breakdown
        assert result.breakdown["completeness"]["has_stack"] is True
        assert result.breakdown["completeness"]["has_phenomenon"] is True
        assert result.breakdown["completeness"]["has_params"] is False

    def test_promote_threshold_boundary(self, scorer):
        # Score just at threshold
        result_at_threshold = scorer.score_diagnosis(
            conversation_rounds=3,
            user_questions=10,
            has_stack=True,
            has_phenomenon=True,
            has_params=True,
            ai_confidence=1.0,
        )
        assert result_at_threshold.recommendation == "auto_promote"


class TestDraftManager:
    @pytest.fixture
    def drafts_dir(self, tmp_path):
        return tmp_path / "drafts"

    @pytest.fixture
    def cases_dir(self, tmp_path):
        return tmp_path / "cases"

    @pytest.fixture
    def manager(self, drafts_dir):
        return DraftManager(drafts_dir)

    def test_create_draft(self, manager, drafts_dir):
        score = QualityScore(
            total=6.5,
            conversation_rounds=5.0,
            user_questions=4.0,
            completeness=7.0,
            ai_confidence=6.5,
            recommendation="draft",
        )
        history = [
            {"turn": 1, "user": "hello", "ai": "how can I help?"},
        ]

        draft_path = manager.create_draft(
            session_id="test-session-123",
            quality_score=score,
            diagnosis_content="Possible memory leak in cache",
            conversation_history=history,
        )

        assert draft_path.exists()
        assert (draft_path / "metadata.yaml").exists()
        assert (draft_path / "ai-diagnosis.md").exists()
        assert (draft_path / "conversation.json").exists()

        # Verify metadata
        metadata = yaml.safe_load(
            (draft_path / "metadata.yaml").read_text(encoding="utf-8")
        )
        assert metadata["session_id"] == "test-session-123"
        assert metadata["quality_score"]["total"] == 6.5
        assert metadata["status"] == "pending_review"

    def test_create_draft_content(self, manager):
        score = QualityScore(
            total=5.0,
            conversation_rounds=2.0,
            user_questions=2.0,
            completeness=5.0,
            ai_confidence=5.0,
            recommendation="draft",
        )

        draft_path = manager.create_draft(
            session_id="session-abc",
            quality_score=score,
            diagnosis_content="Connection pool may be exhausted",
            conversation_history=[],
        )

        content = (draft_path / "ai-diagnosis.md").read_text(encoding="utf-8")
        assert "DRAFT AI DIAGNOSIS" in content
        assert "Quality Score: 5.0/10" in content
        assert "Connection pool may be exhausted" in content

    def test_cleanup_old_drafts(self, manager, drafts_dir):
        # Create an old draft manually
        old_draft = drafts_dir / "draft_old123"
        old_draft.mkdir()
        old_date = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
        metadata = {"draft_id": "old123", "created_at": old_date}
        (old_draft / "metadata.yaml").write_text(
            yaml.safe_dump(metadata), encoding="utf-8"
        )

        # Create a recent draft
        recent_draft = drafts_dir / "draft_recent456"
        recent_draft.mkdir()
        recent_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        metadata = {"draft_id": "recent456", "created_at": recent_date}
        (recent_draft / "metadata.yaml").write_text(
            yaml.safe_dump(metadata), encoding="utf-8"
        )

        removed = manager.cleanup_old_drafts(max_age_days=30)
        assert removed == 1
        assert not old_draft.exists()
        assert recent_draft.exists()

    def test_cleanup_old_drafts_none_exist(self, manager):
        removed = manager.cleanup_old_drafts(max_age_days=30)
        assert removed == 0

    def test_promote_draft(self, manager, drafts_dir, cases_dir):
        # Create a draft first
        score = QualityScore(
            total=6.5,
            conversation_rounds=5.0,
            user_questions=4.0,
            completeness=7.0,
            ai_confidence=6.5,
            recommendation="draft",
        )
        draft_path = manager.create_draft(
            session_id="promote-session",
            quality_score=score,
            diagnosis_content="Test diagnosis",
            conversation_history=[],
        )

        # Promote it
        case_path = manager.promote_draft(draft_path, cases_dir)

        assert case_path.exists()
        assert (case_path / "ai-diagnosis.md").exists()
        assert (case_path / "metadata.yaml").exists()

        # Verify metadata
        case_metadata = yaml.safe_load(
            (case_path / "metadata.yaml").read_text(encoding="utf-8")
        )
        assert case_metadata["source_session"] == "promote-session"
        assert case_metadata["promoted_from_draft"] is True

        # Draft should be removed
        assert not draft_path.exists()

    def test_promote_draft_not_found(self, manager, cases_dir):
        nonexistent = manager._drafts_dir / "nonexistent"
        with pytest.raises(FileNotFoundError, match="Draft not found"):
            manager.promote_draft(nonexistent, cases_dir)
