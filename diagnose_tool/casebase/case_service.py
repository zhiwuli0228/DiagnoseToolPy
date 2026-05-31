"""Case service for orchestrating case operations."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

import yaml

from diagnose_tool.casebase.case_indexer import (
    CASES_DIR,
    add_case_to_index,
    append_case_to_bm25_corpus,
    get_index,
)
from diagnose_tool.casebase.case_loader import load_case
from diagnose_tool.casebase.case_models import (
    CaseConfidence,
    CaseSourceType,
    CaseStatus,
    FaultCase,
    FaultCaseMetadata,
)
from diagnose_tool.casebase.case_writer import archive_case_from_task

logger = logging.getLogger(__name__)


def create_case_from_analysis(
    task_output_path: Path,
    case_metadata: FaultCaseMetadata,
    cases_dir: Path | None = None,
) -> Path:
    case_dir = archive_case_from_task(task_output_path, case_metadata, cases_dir=cases_dir)
    add_case_to_index(case_metadata, cases_dir=cases_dir)
    if case_metadata.status == CaseStatus.ARCHIVED:
        append_case_to_bm25_corpus(case_dir)
    return case_dir


def _generate_case_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"CASE-{timestamp}"


def _generate_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def create_manual_case(
    title: str,
    content: str = "",
    status: CaseStatus = CaseStatus.DRAFT,
    confidence: CaseConfidence = CaseConfidence.UNCONFIRMED,
    slug: str | None = None,
    tags: list[str] | None = None,
    components: list[str] | None = None,
    fault_modes: list[str] | None = None,
    exception_classes: list[str] | None = None,
    key_phrases: list[str] | None = None,
    cases_dir: Path | None = None,
) -> FaultCase:
    if cases_dir is None:
        cases_dir = CASES_DIR

    if slug is None:
        slug = _generate_slug(title)

    case_id = _generate_case_id()
    case_dir_name = f"{case_id}_{slug}"
    case_dir = cases_dir / case_dir_name

    if case_dir.exists():
        suffix = uuid.uuid4().hex[:6]
        case_id = f"{case_id}-{suffix}"
        case_dir_name = f"{case_id}_{slug}"
        case_dir = cases_dir / case_dir_name

    cases_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)

    metadata = FaultCaseMetadata(
        case_id=case_id,
        title=title,
        slug=slug,
        source_type=CaseSourceType.MANUAL,
        status=status,
        confidence=confidence,
        tags=tags or [],
        components=components or [],
        fault_modes=fault_modes or [],
        exception_classes=exception_classes or [],
        key_phrases=key_phrases or [],
    )

    metadata_path = case_dir / "metadata.yaml"
    with metadata_path.open("w", encoding="utf-8") as f:
        yaml.dump(metadata.to_dict(), f, allow_unicode=True, sort_keys=False)

    case_md_path = case_dir / "case.md"
    case_md_path.write_text(content or f"# {title}\n\n", encoding="utf-8")

    if status == CaseStatus.ARCHIVED:
        add_case_to_index(metadata, cases_dir=cases_dir)
        append_case_to_bm25_corpus(case_dir)

    return FaultCase(
        metadata=metadata,
        case_path=str(case_dir),
        evidence_path=str(case_dir),
        case_md_content=content,
    )


def get_all_cases(
    cases_dir: Path | None = None,
) -> list[FaultCase]:
    if cases_dir is None:
        cases_dir = CASES_DIR

    entries = get_index(cases_dir=cases_dir)
    cases: list[FaultCase] = []

    for entry in entries:
        case_dir = cases_dir / f"{entry.case_id}_{entry.slug}"
        if case_dir.exists():
            try:
                fault_case = load_case(case_dir)
                cases.append(fault_case)
            except Exception as exc:
                logger.warning("Skipped case %s while listing: %s", case_dir, exc)
                continue

    return cases


def get_case(
    case_id: str,
    cases_dir: Path | None = None,
) -> FaultCase:
    if cases_dir is None:
        cases_dir = CASES_DIR

    entries = get_index(cases_dir=cases_dir)

    for entry in entries:
        if entry.case_id == case_id:
            case_dir = cases_dir / f"{entry.case_id}_{entry.slug}"
            if case_dir.exists():
                return load_case(case_dir)

    raise FileNotFoundError(f"Case not found: {case_id}")
