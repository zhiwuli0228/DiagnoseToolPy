"""Cleanup jobs for sessions and drafts."""

from __future__ import annotations

import logging
from pathlib import Path

from diagnose_tool.analyzer.case_quality_scorer import DraftManager
from diagnose_tool.analyzer.session_store import SessionStore

logger = logging.getLogger(__name__)


def run_cleanup(
    data_dir: Path,
    session_max_age_days: int = 7,
    draft_max_age_days: int = 30,
) -> dict[str, int]:
    """Run cleanup for expired sessions and drafts.

    Args:
        data_dir: The data directory containing sessions/ and cases/.
        session_max_age_days: Remove sessions inactive longer than this.
        draft_max_age_days: Remove drafts older than this.

    Returns:
        Dict with 'sessions_removed' and 'drafts_removed' counts.
    """
    sessions_removed = 0
    drafts_removed = 0

    # Cleanup sessions
    sessions_dir = data_dir / "sessions"
    if sessions_dir.exists():
        try:
            store = SessionStore(sessions_dir)
            sessions_removed = store.cleanup_inactive(max_age_days=session_max_age_days)
            logger.info("Cleaned up %d expired sessions", sessions_removed)
        except Exception as exc:
            logger.error("Failed to cleanup sessions: %s", exc)

    # Cleanup drafts
    drafts_dir = data_dir / "cases" / "_drafts"
    if drafts_dir.exists():
        try:
            draft_manager = DraftManager(drafts_dir)
            # Reset drafts_dir to the correct path (DraftManager creates it)
            draft_manager._drafts_dir = drafts_dir
            drafts_removed = draft_manager.cleanup_old_drafts(max_age_days=draft_max_age_days)
            logger.info("Cleaned up %d expired drafts", drafts_removed)
        except Exception as exc:
            logger.error("Failed to cleanup drafts: %s", exc)

    return {
        "sessions_removed": sessions_removed,
        "drafts_removed": drafts_removed,
    }
