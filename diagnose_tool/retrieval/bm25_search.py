"""Optional BM25 full-text search using rank-bm25."""

from __future__ import annotations

import logging
from pathlib import Path

from diagnose_tool.retrieval.query_builder import RetrievalQuery

logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False
    BM25Okapi = None

ScoredCase = tuple[str, float, dict]

BM25_CORPUS_FILE = Path("data/indexes/bm25/corpus.jsonl")


def search_bm25(query: RetrievalQuery, cases_dir: Path) -> list[ScoredCase]:
    """Search cases using BM25 full-text search.

    Args:
        query: RetrievalQuery with keywords for full-text matching.
        cases_dir: Path to the cases directory.

    Returns:
        List of (case_id, score, metadata_dict) tuples sorted by descending score.
        Returns empty list if rank-bm25 is not installed.
    """
    if not _BM25_AVAILABLE:
        return []

    if not query.keywords:
        return []

    cases_dir = Path(cases_dir)
    if not cases_dir.exists():
        return []

    corpus, case_ids = _build_corpus(cases_dir)
    if not corpus:
        return []

    try:
        bm25 = BM25Okapi(corpus)
        tokenized_query = " ".join(query.keywords).lower().split()
        scores = bm25.get_scores(tokenized_query)

        results = [
            (case_ids[i], float(scores[i]), _load_case_metadata(cases_dir / case_ids[i]))
            for i in range(len(case_ids))
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    except Exception as e:
        logger.warning("BM25 search failed: %s", e)
        return []


def _load_case_metadata(case_path: Path) -> dict:
    """Load metadata.yaml for a case directory."""
    metadata_path = case_path / "metadata.yaml"
    if not metadata_path.exists():
        return {}
    try:
        import yaml
        with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _build_corpus(cases_dir: Path) -> tuple[list[list[str]], list[str]]:
    """Build BM25 corpus, preferring persisted JSONL if available."""
    # Try loading from persisted corpus file first
    corpus, case_ids = _load_corpus_from_jsonl(cases_dir / BM25_CORPUS_FILE.name)
    if corpus:
        return corpus, case_ids

    # Fall back to rebuilding from case directories
    return _rebuild_corpus_from_dirs(cases_dir)


def _load_corpus_from_jsonl(corpus_file: Path) -> tuple[list[list[str]], list[str]]:
    """Load BM25 corpus from a persisted JSONL file.

    Returns:
        Tuple of (tokenized_corpus, case_ids).
    """
    import json

    corpus: list[list[str]] = []
    case_ids: list[str] = []

    if not corpus_file.exists():
        return [], []

    with corpus_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                text_parts = entry.get("text_parts", [])
                combined = " ".join(text_parts).lower()
                tokens = [t for t in combined.split() if len(t) > 2]
                if tokens:
                    corpus.append(tokens)
                    case_ids.append(entry.get("case_id", ""))
            except Exception:
                continue

    return corpus, case_ids


def _rebuild_corpus_from_dirs(cases_dir: Path) -> tuple[list[list[str]], list[str]]:
    """Build BM25 corpus from case directories (fallback when no persisted corpus)."""
    corpus: list[list[str]] = []
    case_ids: list[str] = []

    for case_path in sorted(cases_dir.iterdir()):
        if not case_path.is_dir():
            continue

        case_md_path = case_path / "case.md"
        metadata_path = case_path / "metadata.yaml"

        if not case_md_path.exists():
            continue

        text_parts = []

        if metadata_path.exists():
            try:
                import yaml
                with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
                    metadata = yaml.safe_load(f) or {}
                text_parts.append(str(metadata.get("title", "")))
                text_parts.append(str(metadata.get("summary", "")))
                text_parts.append(" ".join(metadata.get("tags", [])))
                text_parts.append(" ".join(metadata.get("components", [])))
                text_parts.append(" ".join(metadata.get("fault_modes", [])))
            except Exception:
                pass

        try:
            with case_md_path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    text_parts.append(line.strip())
        except Exception:
            continue

        combined = " ".join(text_parts).lower()
        tokens = [t for t in combined.split() if len(t) > 2]
        if tokens:
            corpus.append(tokens)
            case_ids.append(case_path.name)

    return corpus, case_ids