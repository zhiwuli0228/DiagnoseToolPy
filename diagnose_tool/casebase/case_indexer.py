"""Case indexer for maintaining case index."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from diagnose_tool.casebase.case_models import CaseIndexEntry, FaultCaseMetadata


logger = logging.getLogger(__name__)

CASES_DIR = Path("data/cases")
INDEX_FILE = CASES_DIR / "index.yaml"
BM25_CORPUS_FILE = Path("data/indexes/bm25/corpus.jsonl")


class CaseIndexError(Exception):
    pass


def rebuild_index(cases_dir: Path | None = None) -> list[CaseIndexEntry]:
    if cases_dir is None:
        cases_dir = CASES_DIR

    if not cases_dir.exists():
        return []

    entries: list[CaseIndexEntry] = []

    for case_subdir in cases_dir.iterdir():
        if not case_subdir.is_dir():
            continue

        if case_subdir.name == "index.yaml":
            continue

        metadata_path = case_subdir / "metadata.yaml"
        if not metadata_path.exists():
            logger.warning("Skipping case directory without metadata: %s", case_subdir.name)
            continue

        try:
            with metadata_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            metadata = FaultCaseMetadata.from_dict(data)
            entry = CaseIndexEntry.from_metadata(metadata)
            entries.append(entry)
        except Exception as e:
            logger.warning("Skipping malformed metadata in %s: %s", case_subdir.name, e)
            continue

    entries.sort(key=lambda e: e.created_at, reverse=True)
    return entries


def add_case_to_index(
    metadata: FaultCaseMetadata,
    cases_dir: Path | None = None,
    index_file: Path | None = None,
) -> None:
    if cases_dir is None:
        cases_dir = CASES_DIR

    cases_dir.mkdir(parents=True, exist_ok=True)

    entry = CaseIndexEntry.from_metadata(metadata)
    entries = get_index(cases_dir=cases_dir, index_file=index_file)

    existing = [i for i, e in enumerate(entries) if e.case_id == entry.case_id]
    if existing:
        entries[existing[0]] = entry
    else:
        entries.insert(0, entry)

    effective_index_file = index_file if index_file is not None else cases_dir / "index.yaml"
    write_index(entries, effective_index_file)


def get_index(
    cases_dir: Path | None = None,
    index_file: Path | None = None,
) -> list[CaseIndexEntry]:
    if cases_dir is None:
        cases_dir = CASES_DIR
    if index_file is None:
        index_file = cases_dir / "index.yaml"

    if not index_file.exists():
        return []

    with index_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return []

    return [CaseIndexEntry.from_dict(entry) for entry in data]


def rebuild_bm25_corpus(cases_dir: Path | None = None) -> list[dict]:
    """Rebuild the BM25 corpus from all case directories.

    Returns:
        List of corpus entries as dicts (one per case).
    """
    if cases_dir is None:
        cases_dir = CASES_DIR

    if not cases_dir.exists():
        return []

    corpus: list[dict] = []

    for case_subdir in cases_dir.iterdir():
        if not case_subdir.is_dir():
            continue

        case_id = case_subdir.name
        case_md_path = case_subdir / "case.md"
        metadata_path = case_subdir / "metadata.yaml"

        text_parts: list[str] = []

        if metadata_path.exists():
            try:
                with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
                    data = yaml.safe_load(f) or {}
                text_parts.append(str(data.get("title", "")))
                text_parts.append(str(data.get("summary", "")))
                text_parts.extend(data.get("tags", []))
                text_parts.extend(data.get("components", []))
                text_parts.extend(data.get("fault_modes", []))
            except Exception as e:
                logger.warning("Failed to read metadata for corpus: %s", e)

        if case_md_path.exists():
            try:
                with case_md_path.open("r", encoding="utf-8", errors="replace") as f:
                    text_parts.append(f.read())
            except Exception:
                pass

        if text_parts:
            corpus.append({"case_id": case_id, "text_parts": text_parts})

    return corpus


def rebuild_bm25_corpus_and_save(cases_dir: Path | None = None) -> None:
    """Rebuild the BM25 corpus and persist to corpus.jsonl."""
    if cases_dir is None:
        cases_dir = CASES_DIR

    import json

    corpus = rebuild_bm25_corpus(cases_dir)
    BM25_CORPUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with BM25_CORPUS_FILE.open("w", encoding="utf-8") as f:
        for entry in corpus:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_case_to_bm25_corpus(case_dir: Path, corpus_file: Path | None = None) -> None:
    """Append a single case's text to the BM25 corpus JSONL file.

    Removes any prior entry for the same case_id before appending.
    """
    import json

    if corpus_file is None:
        corpus_file = BM25_CORPUS_FILE

    case_id = case_dir.name
    metadata_path = case_dir / "metadata.yaml"
    case_md_path = case_dir / "case.md"

    text_parts: list[str] = []

    if metadata_path.exists():
        try:
            with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
                data = yaml.safe_load(f) or {}
            text_parts.append(str(data.get("title", "")))
            text_parts.append(str(data.get("summary", "")))
            text_parts.extend(data.get("tags", []))
            text_parts.extend(data.get("components", []))
            text_parts.extend(data.get("fault_modes", []))
        except Exception as e:
            logger.warning("Failed to read metadata for BM25 corpus append: %s", e)

    if case_md_path.exists():
        try:
            with case_md_path.open("r", encoding="utf-8", errors="replace") as f:
                text_parts.append(f.read())
        except Exception:
            pass

    new_entry = json.dumps({"case_id": case_id, "text_parts": text_parts}, ensure_ascii=False)

    corpus_file.parent.mkdir(parents=True, exist_ok=True)

    existing_lines: list[str] = []
    if corpus_file.exists():
        with corpus_file.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("case_id") != case_id:
                        existing_lines.append(line)
                except Exception:
                    continue

    with corpus_file.open("w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(line + "\n")
        f.write(new_entry + "\n")


def write_index(entries: list[CaseIndexEntry], index_file: Path) -> None:
    index_file.parent.mkdir(parents=True, exist_ok=True)
    data = [entry.to_dict() for entry in entries]
    with index_file.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
