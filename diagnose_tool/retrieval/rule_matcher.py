"""Rule-based case matching using metadata fields."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from diagnose_tool.retrieval.query_builder import RetrievalQuery

logger = logging.getLogger(__name__)

ScoredCase = tuple[str, float, dict]


def match_by_rules(query: RetrievalQuery, cases_dir: Path) -> list[ScoredCase]:
    """Match cases by rule-based field overlap.

    Args:
        query: RetrievalQuery with tags, components, fault_modes, etc.
        cases_dir: Path to the cases directory.

    Returns:
        List of (case_id, score, metadata_dict) tuples sorted by descending score.
    """
    if not any([query.components, query.fault_modes, query.exception_classes]):
        return []

    cases_dir = Path(cases_dir)
    if not cases_dir.exists():
        return []

    results: list[ScoredCase] = []

    for case_path in cases_dir.iterdir():
        if not case_path.is_dir():
            continue

        metadata_path = case_path / "metadata.yaml"
        if not metadata_path.exists():
            continue

        try:
            with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
                metadata = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning("Failed to read metadata %s: %s", metadata_path, e)
            continue

        score = _compute_rule_score(query, metadata)
        if score > 0:
            case_id = case_path.name
            results.append((case_id, score, metadata))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _compute_rule_score(query: RetrievalQuery, metadata: dict) -> float:
    """Compute rule-based score using metadata field overlap."""
    score = 0.0

    query_components = set(c.lower() for c in query.components)
    query_fault_modes = set(f.lower() for f in query.fault_modes)
    query_exception_classes = set(e.lower() for e in query.exception_classes)
    query_key_phrases = set(kp.lower() for kp in getattr(query, "key_phrases", []))
    query_tags = set(t.lower() for t in getattr(query, "tags", []))

    metadata_components = set(c.lower() for c in metadata.get("components", []))
    metadata_fault_modes = set(f.lower() for f in metadata.get("fault_modes", []))
    metadata_exception_classes = set(e.lower() for e in metadata.get("exception_classes", []))
    metadata_key_phrases = set(kp.lower() for kp in metadata.get("key_phrases", []))
    metadata_tags = set(t.lower() for t in metadata.get("tags", []))

    if query_fault_modes & metadata_fault_modes:
        score += len(query_fault_modes & metadata_fault_modes) * 3.0

    if query_exception_classes & metadata_exception_classes:
        score += len(query_exception_classes & metadata_exception_classes) * 3.0

    if query_components & metadata_components:
        score += len(query_components & metadata_components) * 2.0

    if query_key_phrases & metadata_key_phrases:
        score += len(query_key_phrases & metadata_key_phrases) * 2.0

    if query_tags & metadata_tags:
        score += len(query_tags & metadata_tags) * 1.0

    return score
