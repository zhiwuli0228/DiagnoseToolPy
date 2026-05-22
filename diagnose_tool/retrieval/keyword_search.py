"""Keyword-based case search without embeddings."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from diagnose_tool.retrieval.query_builder import RetrievalQuery

logger = logging.getLogger(__name__)

ScoredCase = tuple[str, float, dict]


def search_by_keywords(query: RetrievalQuery, cases_dir: Path) -> list[ScoredCase]:
    """Search cases by keyword overlap.

    Args:
        query: RetrievalQuery with keywords and other fields to match.
        cases_dir: Path to the cases directory.

    Returns:
        List of (case_id, score, metadata_dict) tuples sorted by descending score.
    """
    if not query.keywords and not query.components and not query.fault_modes:
        return []

    cases_dir = Path(cases_dir)
    if not cases_dir.exists():
        return []

    results: list[ScoredCase] = []

    for case_path in cases_dir.iterdir():
        if not case_path.is_dir():
            continue

        metadata_path = case_path / "metadata.yaml"
        case_md_path = case_path / "case.md"

        if not metadata_path.exists():
            continue

        try:
            with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
                metadata = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning("Failed to read metadata %s: %s", metadata_path, e)
            continue

        score = _compute_keyword_score(query, metadata, case_md_path)
        if score > 0:
            case_id = case_path.name
            results.append((case_id, score, metadata))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _compute_keyword_score(query: RetrievalQuery, metadata: dict, case_md_path: Path) -> float:
    """Compute keyword overlap score between query and case."""
    score = 0.0

    query_keywords = set(query.keywords)
    query_components = set(query.components)
    query_fault_modes = set(query.fault_modes)

    metadata_tags = set(metadata.get("tags", []))
    metadata_components = set(metadata.get("components", []))
    metadata_fault_modes = set(metadata.get("fault_modes", []))

    if query_keywords & metadata_tags:
        score += len(query_keywords & metadata_tags) * 2.0

    if query_components & metadata_components:
        score += len(query_components & metadata_components) * 1.5

    if query_fault_modes & metadata_fault_modes:
        score += len(query_fault_modes & metadata_fault_modes) * 2.0

    case_text_lower = _read_case_text(case_md_path)
    if case_text_lower:
        query_text_lower = set(
            kw.lower() for kw in query.keywords + query.components + query.fault_modes
        )
        matched = sum(1 for kw in query_text_lower if kw in case_text_lower)
        score += matched * 0.5

    return score


def _read_case_text(case_md_path: Path) -> str:
    """Stream read case.md content."""
    if not case_md_path.exists():
        return ""

    try:
        with case_md_path.open("r", encoding="utf-8", errors="replace") as f:
            return f.read().lower()
    except Exception:
        return ""
