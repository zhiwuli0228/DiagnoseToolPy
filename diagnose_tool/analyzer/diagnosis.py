"""AI diagnosis orchestrator — pure Python, FastAPI-independent."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from diagnose_tool.core.llm_client import LLMClient
from diagnose_tool.core.llm_config import AppLLMConfig
from diagnose_tool.retrieval.bm25_search import search_bm25
from diagnose_tool.retrieval.keyword_search import search_by_keywords
from diagnose_tool.retrieval.prompt_context import generate_prompt_context
from diagnose_tool.retrieval.query_builder import RetrievalQuery, build_retrieval_query
from diagnose_tool.retrieval.rule_matcher import match_by_rules

logger = logging.getLogger(__name__)

# --- Exceptions ---------------------------------------------------------


class DiagnosisError(RuntimeError):
    """Base exception for diagnosis errors."""
    pass


class TaskNotFoundError(DiagnosisError):
    """Raised when task output directory not found."""
    pass


class EvidenceNotFoundError(DiagnosisError):
    """Raised when evidence-pack.md not found."""
    pass


# --- Orchestrator --------------------------------------------------------


class DiagnosisOrchestrator:
    """Orchestrates the full AI diagnosis flow from task evidence to LLM response."""

    def __init__(self, llm_config: AppLLMConfig, data_dir: Path) -> None:
        self._llm = LLMClient(llm_config)
        self._data_dir = Path(data_dir)

    def run(self, task_id: str) -> tuple[str, str]:
        """Run AI diagnosis for a task.

        Args:
            task_id: The identifier of the analysis task.

        Returns:
            A tuple of (case_id, diagnosis_text).

        Raises:
            TaskNotFoundError: When ``data/output/{task_id}`` does not exist.
            EvidenceNotFoundError: When ``evidence-pack.md`` not found.
            LLMClientError: When the LLM API call fails.
        """
        task_output = self._data_dir / "output" / task_id

        if not task_output.exists():
            raise TaskNotFoundError(f"Task output directory not found: {task_output}")

        evidence_pack_path = task_output / "evidence-pack.md"
        if not evidence_pack_path.exists():
            raise EvidenceNotFoundError(
                f"Evidence pack not found: {evidence_pack_path}"
            )

        # Read evidence pack
        evidence_pack = _read_file(evidence_pack_path)

        # Read retrieval query if present
        retrieval_query_path = task_output / "retrieval-query.json"
        retrieval_query: RetrievalQuery | None = None
        if retrieval_query_path.exists():
            try:
                retrieval_query = build_retrieval_query(retrieval_query_path)
            except Exception:
                retrieval_query = None

        # Build retrieval context — similar cases
        cases_dir = self._data_dir / "cases"
        similar_cases = self._query_similar_cases(retrieval_query, cases_dir)

        if retrieval_query is not None:
            prompt_context = generate_prompt_context(
                retrieval_query,
                similar_cases,
                max_cases=3,
            )
        else:
            prompt_context = (
                "## Historical Case References\n\n"
                "No retrieval query available.\n\n"
                "*Note: Analyze the current issue independently.*\n"
            )

        # Read and fill prompt template
        prompt_template_path = _find_prompt_template(self._data_dir)
        if prompt_template_path is not None:
            template = _read_file(prompt_template_path)
        else:
            template = _fallback_template()

        full_prompt = template.replace("{evidence_pack}", evidence_pack).replace(
            "{similar_cases}", prompt_context
        )

        # Call LLM
        messages = [{"role": "user", "content": full_prompt}]
        diagnosis_text = self._llm.chat(messages=messages)

        # Determine case_id and ensure case directory exists
        case_id = task_id
        case_dir = cases_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Write ai-diagnosis.md
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diagnosis_md = _build_diagnosis_md(
            timestamp=timestamp,
            task_id=task_id,
            source_evidence_paths=_format_source_paths(task_output),
            diagnosis_content=diagnosis_text,
        )

        ai_diagnosis_path = case_dir / "ai-diagnosis.md"
        ai_diagnosis_path.write_text(diagnosis_md, encoding="utf-8")

        return case_id, diagnosis_text

    def run_with_context(
        self,
        task_id: str,
        user_context: dict[str, str],
        mode: Literal["user-priority", "log-priority"] = "user-priority",
    ) -> tuple[str, str]:
        """Run AI diagnosis with user-provided context.

        Args:
            task_id: The identifier of the analysis task.
            user_context: Dict with keys: phenomenon, stack, params.
            mode: Priority mode - "user-priority" or "log-priority".

        Returns:
            A tuple of (case_id, diagnosis_text).

        Raises:
            TaskNotFoundError: When ``data/output/{task_id}`` does not exist.
            EvidenceNotFoundError: When ``evidence-pack.md`` not found.
            LLMClientError: When the LLM API call fails.
        """
        task_output = self._data_dir / "output" / task_id

        if not task_output.exists():
            raise TaskNotFoundError(f"Task output directory not found: {task_output}")

        evidence_pack_path = task_output / "evidence-pack.md"
        if not evidence_pack_path.exists():
            raise EvidenceNotFoundError(
                f"Evidence pack not found: {evidence_pack_path}"
            )

        # Read evidence pack
        evidence_pack = _read_file(evidence_pack_path)

        # Read retrieval query if present
        retrieval_query_path = task_output / "retrieval-query.json"
        retrieval_query: RetrievalQuery | None = None
        if retrieval_query_path.exists():
            try:
                retrieval_query = build_retrieval_query(retrieval_query_path)
            except Exception:
                retrieval_query = None

        # Build retrieval context — similar cases
        cases_dir = self._data_dir / "cases"
        similar_cases = self._query_similar_cases(retrieval_query, cases_dir)

        if retrieval_query is not None:
            prompt_context = generate_prompt_context(
                retrieval_query,
                similar_cases,
                max_cases=3,
            )
        else:
            prompt_context = (
                "## Historical Case References\n\n"
                "No retrieval query available.\n\n"
                "*Note: Analyze the current issue independently.*\n"
            )

        # Build user context string
        user_context_md = _build_user_context_md(user_context)

        # Build prompt based on priority mode
        if mode == "user-priority":
            prompt_parts = [
                "# User Provided Context\n\n" + user_context_md,
                "# Log Evidence\n\n" + evidence_pack,
                "# Similar Historical Cases\n\n" + prompt_context,
            ]
        else:  # log-priority
            prompt_parts = [
                "# Log Evidence\n\n" + evidence_pack,
                "# User Provided Context\n\n" + user_context_md,
                "# Similar Historical Cases\n\n" + prompt_context,
            ]

        full_prompt = "\n\n".join(prompt_parts)

        # Call LLM
        messages = [{"role": "user", "content": full_prompt}]
        diagnosis_text = self._llm.chat(messages=messages)

        # Determine case_id and ensure case directory exists
        case_id = task_id
        case_dir = cases_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Write ai-diagnosis.md
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diagnosis_md = _build_diagnosis_md(
            timestamp=timestamp,
            task_id=task_id,
            source_evidence_paths=_format_source_paths(task_output),
            diagnosis_content=diagnosis_text,
        )

        ai_diagnosis_path = case_dir / "ai-diagnosis.md"
        ai_diagnosis_path.write_text(diagnosis_md, encoding="utf-8")

        return case_id, diagnosis_text

    def _query_similar_cases(
        self,
        query: RetrievalQuery | None,
        cases_dir: Path,
    ) -> list[tuple[str, float, dict]]:
        """Query retrieval module for similar cases.

        Returns:
            List of (case_id, score, metadata_dict) tuples.
        """
        if query is None or not cases_dir.exists():
            return []

        results: list[tuple[str, float, dict]] = []

        # Keyword search
        keyword_results = search_by_keywords(query, cases_dir)
        for case_id, score, metadata in keyword_results:
            results.append((case_id, score, metadata))

        # BM25 search (optional, skip if not available)
        try:
            bm25_results = search_bm25(query, cases_dir)
            for case_id, score, metadata in bm25_results:
                # Merge with existing or add
                found = False
                for i, (cid, sc, meta) in enumerate(results):
                    if cid == case_id:
                        results[i] = (cid, sc + score * 0.5, meta)
                        found = True
                        break
                if not found:
                    results.append((case_id, score, metadata))
        except Exception:
            pass

        # Rule matching
        rule_results = match_by_rules(query, cases_dir)
        for case_id, score, metadata in rule_results:
            found = False
            for i, (cid, sc, meta) in enumerate(results):
                if cid == case_id:
                    results[i] = (cid, sc + score * 0.3, meta)
                    found = True
                    break
            if not found:
                results.append((case_id, score, metadata))

        # Sort by descending score, return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:10]


def _read_file(path: Path) -> str:
    """Read file content safely with UTF-8 and error replacement."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise DiagnosisError(f"Failed to read file {path}: {exc}") from exc


def _find_prompt_template(data_dir: Path) -> Path | None:
    """Find the prompt template relative to the project root.

    Assumes the project root is two levels above data_dir
    (e.g. data_dir = .../DiagnoseToolPy/data → root = .../DiagnoseToolPy).
    """
    project_root = data_dir.parent
    template_path = project_root / "docs" / "05-domain" / "prompt-template.md"
    return template_path if template_path.exists() else None


def _fallback_template() -> str:
    """Return a minimal fallback prompt template."""
    return (
        "# Role\n\n"
        "You are an experienced backend stability engineer.\n\n"
        "# Current Fault Evidence\n\n"
        "{evidence_pack}\n\n"
        "# Similar Historical Cases\n\n"
        "{similar_cases}\n\n"
        "# Diagnosis Instructions\n\n"
        "Please analyze and provide a preliminary diagnosis.\n"
    )


def _build_diagnosis_md(
    timestamp: str,
    task_id: str,
    source_evidence_paths: str,
    diagnosis_content: str,
) -> str:
    """Build the ai-diagnosis.md content."""
    lines = [
        "# PRELIMINARY AI DIAGNOSIS — NOT CONFIRMED ROOT CAUSE",
        "",
        "> **Disclaimer**: This diagnosis was generated by an AI model and represents a\n"
        "> preliminary hypothesis. It is **NOT** the confirmed root cause.\n"
        "> A human engineer must review, validate, and confirm before treating this as fact.",
        "",
        "## Generated At",
        "",
        timestamp,
        "",
        "## Task ID",
        "",
        task_id,
        "",
        "## Source Evidence",
        "",
        source_evidence_paths,
        "",
        "---",
        "",
        diagnosis_content,
    ]
    return "\n".join(lines)


def _format_source_paths(task_output: Path) -> str:
    """Format source evidence paths as a markdown list."""
    evidence_pack = f"- Evidence pack: `output/{task_output.name}/evidence-pack.md`"
    retrieval_query = f"- Retrieval query: `output/{task_output.name}/retrieval-query.json`"
    return f"{evidence_pack}\n{retrieval_query}"


def _build_user_context_md(user_context: dict[str, str]) -> str:
    """Build user context as markdown.

    Args:
        user_context: Dict with keys: phenomenon, stack, params.

    Returns:
        Formatted markdown string.
    """
    parts = []

    if user_context.get("phenomenon"):
        parts.append(f"## 问题现象\n\n{user_context['phenomenon']}")

    if user_context.get("stack"):
        parts.append(f"## 堆栈信息\n\n```\n{user_context['stack']}\n```")

    if user_context.get("params"):
        parts.append(f"## 关键入参\n\n{user_context['params']}")

    if not parts:
        return "（用户未提供额外上下文）"

    return "\n\n".join(parts)