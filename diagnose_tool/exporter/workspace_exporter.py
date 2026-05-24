"""Workspace exporter — creates diagnostic workspace for OpenCode consumption."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from diagnose_tool.analyzer.evidence_cache import EvidenceCacheManager
from diagnose_tool.analyzer.evidence_compressor import (
    CompressionOptions,
    compress_log_entries,
    build_evidence_markdown,
    truncate_to_token_budget,
)
from diagnose_tool.analyzer.diagnosis import (
    DiagnosisOrchestrator,
    TaskNotFoundError,
    EvidenceNotFoundError,
)
from diagnose_tool.core.llm_config import AppLLMConfig

logger = logging.getLogger(__name__)


class WorkspaceExportError(RuntimeError):
    """Raised when workspace export fails."""
    pass


class WorkspaceExporter:
    """Export complete diagnostic workspace to a user-specified directory."""

    def __init__(self, llm_config: AppLLMConfig) -> None:
        self._llm_config = llm_config
        self._data_dir = llm_config.data_dir
        self._cache_mgr = EvidenceCacheManager(self._data_dir)

    def export_from_task_id(
        self,
        task_id: str,
        workspace_dir: Path,
        user_context: dict[str, str] | None = None,
    ) -> list[str]:
        """Export workspace from a task ID and user context.

        Args:
            task_id: The analysis task identifier.
            workspace_dir: User-selected workspace directory.
            user_context: Optional user context (phenomenon, stack, params).

        Returns:
            List of file paths that were created.

        Raises:
            WorkspaceExportError: On validation or write failure.
        """
        # Validate workspace_dir
        self._validate_workspace_dir(workspace_dir)

        # Track created files for rollback
        created_files: list[Path] = []

        try:
            # Build workspace directory structure
            workspace_structure = self._build_workspace_dir(workspace_dir)

            # Read evidence pack
            task_output = self._data_dir / "output" / task_id
            if not task_output.exists():
                raise WorkspaceExportError(f"Task output directory not found: {task_output}")

            evidence_pack_path = task_output / "evidence-pack.md"
            if not evidence_pack_path.exists():
                raise WorkspaceExportError(f"Evidence pack not found: {evidence_pack_path}")

            evidence_pack = evidence_pack_path.read_text(encoding="utf-8")

            # Get similar cases
            similar_cases = self._get_similar_cases(task_output, max_cases=3)

            # Build and write context files
            ctx = user_context or {}
            self._write_context_files(workspace_structure.context_dir, ctx)

            # Write compressed evidence pack
            self._write_evidence_pack(workspace_structure.logs_dir, evidence_pack, task_output)

            # Write cases
            self._write_cases(workspace_structure.cases_dir, similar_cases)

            # Build prompt
            prompt_content = self._build_prompt(
                evidence_pack=evidence_pack,
                similar_cases=similar_cases,
                user_context=ctx,
            )
            self._write_file(workspace_structure.prompt_path, prompt_content, created_files)

            # Write README
            readme_content = self._build_readme(workspace_dir.name)
            self._write_file(workspace_structure.readme_path, readme_content, created_files)

            return [str(f) for f in created_files]

        except Exception as exc:
            # Rollback: delete created files
            self._rollback(created_files)
            if isinstance(exc, WorkspaceExportError):
                raise
            raise WorkspaceExportError(f"Workspace export failed: {exc}") from exc

    def export_from_cache(
        self,
        cache_key: str,
        workspace_dir: Path,
        selections: list[dict[str, Any]],
        user_context: dict[str, str] | None = None,
    ) -> list[str]:
        """Export workspace from search/cluster cache and user selections.

        Args:
            cache_key: Cache key from search or cluster results.
            workspace_dir: User-selected workspace directory.
            selections: Selected items to include.
            user_context: Optional user context.

        Returns:
            List of file paths that were created.

        Raises:
            WorkspaceExportError: On validation or write failure.
        """
        self._validate_workspace_dir(workspace_dir)
        created_files: list[Path] = []

        try:
            workspace_structure = self._build_workspace_dir(workspace_dir)

            # Load entries from cache
            all_entries = self._cache_mgr.load_matched_lines(cache_key)
            if not all_entries:
                raise WorkspaceExportError(f"No cached entries found for: {cache_key}")

            # Convert and resolve selections
            entries_dicts = [self._entry_to_dict(e) for e in all_entries]
            selected_entries = self._resolve_selections(entries_dicts, selections)

            if not selected_entries:
                raise WorkspaceExportError("No entries selected for diagnosis")

            # Compress evidence
            compression_opts = CompressionOptions(
                include_stack=True,
                include_timeline=True,
                max_tokens=2000,
            )
            compressed = compress_log_entries(selected_entries, compression_opts)
            evidence_md = build_evidence_markdown(compressed, compression_opts)
            evidence_md = truncate_to_token_budget(evidence_md, 2000)

            # Write context files
            ctx = user_context or {}
            self._write_context_files(workspace_structure.context_dir, ctx)

            # Write compressed evidence
            self._write_evidence_pack(workspace_structure.logs_dir, evidence_md, None)

            # Write cases (no similar cases from cache)
            self._write_empty_cases_dir(workspace_structure.cases_dir)

            # Build and write prompt
            prompt_content = self._build_prompt(
                evidence_pack=evidence_md,
                similar_cases=[],
                user_context=ctx,
            )
            self._write_file(workspace_structure.prompt_path, prompt_content, created_files)

            # Write README
            readme_content = self._build_readme(workspace_dir.name)
            self._write_file(workspace_structure.readme_path, readme_content, created_files)

            return [str(f) for f in created_files]

        except Exception as exc:
            self._rollback(created_files)
            if isinstance(exc, WorkspaceExportError):
                raise
            raise WorkspaceExportError(f"Workspace export failed: {exc}") from exc

    def generate_prompt_from_cache(
        self,
        cache_key: str,
        selections: list[dict[str, Any]],
        user_context: dict[str, str] | None = None,
    ) -> str:
        """Generate diagnosis prompt from cache without exporting.

        Args:
            cache_key: Cache key from search or cluster results.
            selections: Selected items to include.
            user_context: Optional user context.

        Returns:
            Generated prompt content as markdown string.

        Raises:
            WorkspaceExportError: If no entries found or selection is empty.
        """
        # Load entries from cache
        all_entries = self._cache_mgr.load_matched_lines(cache_key)
        if not all_entries:
            raise WorkspaceExportError(f"No cached entries found for: {cache_key}")

        # Convert and resolve selections
        entries_dicts = [self._entry_to_dict(e) for e in all_entries]
        selected_entries = self._resolve_selections(entries_dicts, selections)

        if not selected_entries:
            raise WorkspaceExportError("No entries selected for diagnosis")

        # Compress evidence
        compression_opts = CompressionOptions(
            include_stack=True,
            include_timeline=True,
            max_tokens=2000,
        )
        compressed = compress_log_entries(selected_entries, compression_opts)
        evidence_md = build_evidence_markdown(compressed, compression_opts)
        evidence_md = truncate_to_token_budget(evidence_md, 2000)

        # Build prompt (no similar cases from cache)
        ctx = user_context or {}
        prompt_content = self._build_prompt(
            evidence_pack=evidence_md,
            similar_cases=[],
            user_context=ctx,
        )

        return prompt_content

    def export_from_session(
        self,
        session_id: str,
        workspace_dir: Path,
        user_context: dict[str, str] | None = None,
    ) -> list[str]:
        """Export workspace from conversation session.

        Args:
            session_id: The conversation session identifier.
            workspace_dir: User-selected workspace directory.
            user_context: Optional user context to override session context.

        Returns:
            List of file paths that were created.

        Raises:
            WorkspaceExportError: On validation or write failure.
        """
        self._validate_workspace_dir(workspace_dir)
        created_files: list[Path] = []

        try:
            workspace_structure = self._build_workspace_dir(workspace_dir)

            # Load session
            from diagnose_tool.analyzer.session_store import SessionStore
            store = SessionStore(self._data_dir / "sessions")
            try:
                metadata = store.get_session(session_id)
            except Exception as exc:
                raise WorkspaceExportError(f"Session not found: {session_id}") from exc

            history = store.get_conversation_history(session_id)
            if not history:
                raise WorkspaceExportError(f"No conversation history for session: {session_id}")

            # Get latest turn context
            last_turn = history[-1]
            ctx = user_context or last_turn.user_context

            # Build evidence from session (simplified - just session context)
            evidence_md = self._build_session_evidence(session_id, history)

            # Write context files
            self._write_context_files(workspace_structure.context_dir, ctx)

            # Write evidence (no task output, just session context)
            self._write_evidence_pack(workspace_structure.logs_dir, evidence_md, None)

            # Write cases (no similar cases from session)
            self._write_empty_cases_dir(workspace_structure.cases_dir)

            # Build and write prompt
            prompt_content = self._build_prompt(
                evidence_pack=evidence_md,
                similar_cases=[],
                user_context=ctx,
            )
            self._write_file(workspace_structure.prompt_path, prompt_content, created_files)

            # Write README
            readme_content = self._build_readme(workspace_dir.name)
            self._write_file(workspace_structure.readme_path, readme_content, created_files)

            return [str(f) for f in created_files]

        except Exception as exc:
            self._rollback(created_files)
            if isinstance(exc, WorkspaceExportError):
                raise
            raise WorkspaceExportError(f"Workspace export failed: {exc}") from exc

    def generate_prompt_from_session(
        self,
        session_id: str,
        user_context: dict[str, str] | None = None,
    ) -> str:
        """Generate diagnosis prompt from conversation session without exporting.

        Args:
            session_id: The conversation session identifier.
            user_context: Optional user context to override session context.

        Returns:
            Generated prompt content as markdown string.

        Raises:
            WorkspaceExportError: If session or history not found.
        """
        from diagnose_tool.analyzer.session_store import SessionStore
        store = SessionStore(self._data_dir / "sessions")

        try:
            metadata = store.get_session(session_id)
        except Exception as exc:
            raise WorkspaceExportError(f"Session not found: {session_id}") from exc

        history = store.get_conversation_history(session_id)
        if not history:
            raise WorkspaceExportError(f"No conversation history for session: {session_id}")

        # Get latest turn context
        last_turn = history[-1]
        ctx = user_context or last_turn.user_context

        # Build evidence from session
        evidence_md = self._build_session_evidence(session_id, history)

        # Build prompt
        prompt_content = self._build_prompt(
            evidence_pack=evidence_md,
            similar_cases=[],
            user_context=ctx,
        )

        return prompt_content

    def _build_workspace_dir(self, workspace_dir: Path) -> _WorkspaceStructure:
        """Create workspace directory structure.

        Creates directories: context/, logs/, cases/
        Returns paths to key files.
        """
        workspace_dir = workspace_dir.resolve()

        # Create subdirectories
        context_dir = workspace_dir / "context"
        logs_dir = workspace_dir / "logs"
        cases_dir = workspace_dir / "cases"

        context_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        cases_dir.mkdir(parents=True, exist_ok=True)

        return _WorkspaceStructure(
            root=workspace_dir,
            context_dir=context_dir,
            logs_dir=logs_dir,
            cases_dir=cases_dir,
            readme_path=workspace_dir / "README.md",
            prompt_path=workspace_dir / "prompt.md",
            evidence_pack_path=logs_dir / "evidence-pack.md",
        )

    def _validate_workspace_dir(self, workspace_dir: Path) -> None:
        """Validate that workspace_dir is writable.

        Raises:
            WorkspaceExportError: If directory is not writable or doesn't exist.
        """
        if not workspace_dir.exists():
            raise WorkspaceExportError(
                f"Directory does not exist: {workspace_dir}. "
                "Please select an existing directory."
            )

        # Check if directory is writable
        if not workspace_dir.is_dir():
            raise WorkspaceExportError(f"Path is not a directory: {workspace_dir}")

        # Try to create a test file
        test_file = workspace_dir / ".write_test"
        try:
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
        except OSError as exc:
            raise WorkspaceExportError(
                f"Directory is not writable: {workspace_dir}. Error: {exc}"
            ) from exc

    def _write_context_files(
        self,
        context_dir: Path,
        user_context: dict[str, str],
    ) -> None:
        """Write context files (phenomenon.md, stack.md, params.md)."""
        phenomenon = user_context.get("phenomenon", "").strip()
        stack = user_context.get("stack", "").strip()
        params = user_context.get("params", "").strip()

        phenomenon_content = phenomenon if phenomenon else "（用户未提供问题现象）"
        stack_content = stack if stack else "（用户未提供堆栈信息）"
        params_content = params if params else "（用户未提供关键入参）"

        (context_dir / "phenomenon.md").write_text(phenomenon_content, encoding="utf-8")
        (context_dir / "stack.md").write_text(stack_content, encoding="utf-8")
        (context_dir / "params.md").write_text(params_content, encoding="utf-8")

    def _write_evidence_pack(
        self,
        logs_dir: Path,
        evidence_md: str,
        task_output: Path | None,
    ) -> None:
        """Write compressed evidence-pack.md to logs directory."""
        if task_output is not None:
            # For task-based export, we can include retrieval query if available
            retrieval_query_path = task_output / "retrieval-query.json"
            if retrieval_query_path.exists():
                retrieval_query = retrieval_query_path.read_text(encoding="utf-8")
                evidence_md = (
                    "## 检索查询\n\n"
                    f"```json\n{retrieval_query}\n```\n\n"
                    "---\n\n"
                    + evidence_md
                )

        (logs_dir / "evidence-pack.md").write_text(evidence_md, encoding="utf-8")

    def _write_cases(
        self,
        cases_dir: Path,
        similar_cases: list[tuple[str, float, dict]],
    ) -> None:
        """Write up to 3 similar case files to cases directory."""
        if not similar_cases:
            self._write_empty_cases_dir(cases_dir)
            return

        for i, (case_id, _score, _metadata) in enumerate(similar_cases[:3], 1):
            case_path = self._data_dir / "cases" / case_id / "case.md"
            if case_path.exists():
                content = case_path.read_text(encoding="utf-8")
                dest_path = cases_dir / f"case-{i:03d}.md"
                dest_path.write_text(content, encoding="utf-8")

    def _write_empty_cases_dir(self, cases_dir: Path) -> None:
        """Write a README indicating no similar cases available."""
        readme_content = (
            "# 相似案例\n\n"
            "未找到相似的历史案例。\n\n"
            "请基于当前证据和上下文进行独立诊断。\n"
        )
        (cases_dir / "README.md").write_text(readme_content, encoding="utf-8")

    def _build_prompt(
        self,
        evidence_pack: str,
        similar_cases: list[tuple[str, float, dict]],
        user_context: dict[str, str],
    ) -> str:
        """Build diagnosis prompt with all placeholders replaced.

        This method replicates the prompt building logic from DiagnosisOrchestrator
        to ensure consistency between direct diagnosis and workspace export.
        """
        # Build user context string
        user_context_parts = []
        if user_context.get("phenomenon"):
            user_context_parts.append(f"## 问题现象\n\n{user_context['phenomenon']}")
        if user_context.get("stack"):
            user_context_parts.append(f"## 堆栈信息\n\n```\n{user_context['stack']}\n```")
        if user_context.get("params"):
            user_context_parts.append(f"## 关键入参\n\n{user_context['params']}")

        user_context_md = "\n\n".join(user_context_parts) if user_context_parts else "（用户未提供额外上下文）"

        # Build similar cases context
        if similar_cases:
            case_parts = ["## Historical Case References\n"]
            for i, (case_id, score, metadata) in enumerate(similar_cases[:3], 1):
                case_path = self._data_dir / "cases" / case_id / "case.md"
                if case_path.exists():
                    case_content = case_path.read_text(encoding="utf-8")
                    # Extract summary from case content
                    summary = self._extract_case_summary(case_content)
                    case_parts.append(f"### Case {i} (score: {score:.2f})")
                    case_parts.append(f"**Case ID**: {case_id}")
                    case_parts.append(f"**Summary**: {summary}")
                    case_parts.append("")
                    case_parts.append(case_content[:500] + "..." if len(case_content) > 500 else case_content)
                    case_parts.append("")
            similar_cases_md = "\n".join(case_parts)
        else:
            similar_cases_md = (
                "## Historical Case References\n\n"
                "No similar cases found.\n\n"
                "*Note: Analyze the current issue independently.*\n"
            )

        # Build full prompt
        prompt_parts = [
            "# Role\n\n"
            "You are an experienced backend stability engineer.\n\n"
            "# User Provided Context\n\n"
            + user_context_md,
            "# Current Fault Evidence\n\n" + evidence_pack,
            "# Similar Historical Cases\n\n" + similar_cases_md,
            "# Diagnosis Instructions\n\n"
            "Please analyze the evidence and provide:\n"
            "1. Preliminary diagnosis (most likely root cause)\n"
            "2. Supporting evidence from the logs\n"
            "3. Recommended fix or further investigation steps\n\n"
            "# Constraints\n\n"
            "- Be specific and actionable\n"
            "- Distinguish between confirmed facts and hypotheses\n"
            "- If information is insufficient, state what additional data would help\n",
        ]

        return "\n\n".join(prompt_parts)

    def _build_readme(self, workspace_name: str) -> str:
        """Build README.md with diagnostic instructions."""
        return (
            f"# Diagnostic Workspace: {workspace_name}\n\n"
            "This workspace contains complete diagnostic context for manual analysis.\n\n"
            "## Directory Structure\n\n"
            "- `README.md` - This file\n"
            "- `prompt.md` - Diagnosis prompt with instructions\n"
            "- `context/` - User-provided context (phenomenon, stack, params)\n"
            "- `logs/` - Log evidence (compressed)\n"
            "- `cases/` - Similar historical cases\n\n"
            "## How to Use with OpenCode\n\n"
            "1. Open this directory in your IDE/editor\n"
            "2. Start OpenCode with this workspace context\n"
            "3. Read through the evidence and context files\n"
            "4. Use the diagnosis prompt in `prompt.md` as a guide\n"
            "5. Save your diagnosis as `result.md` in this directory\n\n"
            "## Saving Results\n\n"
            "When you've completed your diagnosis:\n"
            "1. Create a file named `result.md` in this directory\n"
            "2. Write your diagnosis findings in markdown format\n"
            "3. The diagnostic tool will detect the result file and offer to import it\n\n"
            "## Security Notice\n\n"
            "WARNING: This workspace may contain sensitive information from log files.\n"
            "Handle accordingly and do not share unless necessary.\n"
        )

    def _build_session_evidence(self, session_id: str, history: list) -> str:
        """Build evidence markdown from conversation session."""
        lines = [
            "# Conversation Session Evidence\n\n",
            f"**Session ID**: {session_id}\n",
            f"**Total Turns**: {len(history)}\n\n",
            "## Conversation Summary\n",
        ]

        for i, turn in enumerate(history, 1):
            lines.append(f"\n### Turn {i}\n")

            user_ctx = turn.user_context
            if user_ctx.get("phenomenon"):
                lines.append(f"**Phenomenon**: {user_ctx['phenomenon']}\n")
            if user_ctx.get("stack"):
                lines.append(f"**Stack**: {user_ctx['stack'][:200]}...\n" if len(user_ctx.get("stack", "")) > 200 else f"**Stack**: {user_ctx['stack']}\n")
            if user_ctx.get("params"):
                lines.append(f"**Params**: {user_ctx['params']}\n")

            if turn.ai_question:
                lines.append(f"**AI Question**: {turn.ai_question}\n")

            if turn.ai_diagnosis:
                lines.append(f"**AI Diagnosis**: {turn.ai_diagnosis}\n")

        return "\n".join(lines)

    def _get_similar_cases(
        self,
        task_output: Path,
        max_cases: int = 3,
    ) -> list[tuple[str, float, dict]]:
        """Get similar cases for a task.

        Returns:
            List of (case_id, score, metadata) tuples.
        """
        from diagnose_tool.retrieval.prompt_context import generate_prompt_context
        from diagnose_tool.retrieval.query_builder import build_retrieval_query, RetrievalQuery
        from diagnose_tool.retrieval.bm25_search import search_bm25
        from diagnose_tool.retrieval.keyword_search import search_by_keywords
        from diagnose_tool.retrieval.rule_matcher import match_by_rules

        retrieval_query_path = task_output / "retrieval-query.json"
        retrieval_query: RetrievalQuery | None = None
        if retrieval_query_path.exists():
            try:
                retrieval_query = build_retrieval_query(retrieval_query_path)
            except Exception:
                retrieval_query = None

        cases_dir = self._data_dir / "cases"
        if retrieval_query is None or not cases_dir.exists():
            return []

        results: list[tuple[str, float, dict]] = []

        # Keyword search
        keyword_results = search_by_keywords(retrieval_query, cases_dir)
        for case_id, score, metadata in keyword_results:
            results.append((case_id, score, metadata))

        # BM25 search
        try:
            bm25_results = search_bm25(retrieval_query, cases_dir)
            for case_id, score, metadata in bm25_results:
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
        rule_results = match_by_rules(retrieval_query, cases_dir)
        for case_id, score, metadata in rule_results:
            found = False
            for i, (cid, sc, meta) in enumerate(results):
                if cid == case_id:
                    results[i] = (cid, sc + score * 0.3, meta)
                    found = True
                    break
            if not found:
                results.append((case_id, score, metadata))

        # Sort by descending score, return top max_cases
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_cases]

    def _resolve_selections(
        self,
        entries_dicts: list[dict],
        selections: list[dict[str, Any]],
    ) -> list[dict]:
        """Resolve selections to specific log entry dicts."""
        from collections import defaultdict

        # Group entries by group_key
        groups: dict[str, list[dict]] = defaultdict(list)
        for entry in entries_dicts:
            gk = entry.get("group_key", "unknown")
            groups[gk].append(entry)

        selected = []
        for sel in selections:
            sel_type = sel.get("type", "")
            if sel_type == "group" or sel_type == "group_all":
                group_key = sel.get("group_key")
                if group_key and group_key in groups:
                    selected.extend(groups[group_key])
            elif sel_type == "log":
                entry_id = sel.get("id")
                if entry_id:
                    for entry in entries_dicts:
                        if entry.get("id") == entry_id:
                            selected.append(entry)
                            break
            elif sel_type == "cluster":
                cluster_index = sel.get("cluster_index")
                if cluster_index is not None:
                    group_list = list(groups.keys())
                    if 0 <= cluster_index < len(group_list):
                        group_key = group_list[cluster_index]
                        selected.extend(groups[group_key])

        return selected

    def _entry_to_dict(self, entry: Any) -> dict:
        """Convert a CachedLogEntry to a dict."""
        if isinstance(entry, dict):
            return entry
        return {
            "id": entry.id,
            "group_key": entry.group_key,
            "event": {
                "timestamp": entry.event.timestamp,
                "level": entry.event.level,
                "thread": entry.event.thread,
                "message": entry.event.message,
                "raw": entry.event.raw,
                "file_path": entry.event.file_path,
                "line_no": entry.event.line_no,
            },
            "context_before": [
                {
                    "timestamp": e.timestamp,
                    "level": e.level,
                    "thread": e.thread,
                    "message": e.message,
                    "raw": e.raw,
                    "file_path": e.file_path,
                    "line_no": e.line_no,
                }
                for e in (entry.context_before or [])
            ],
            "context_after": [
                {
                    "timestamp": e.timestamp,
                    "level": e.level,
                    "thread": e.thread,
                    "message": e.message,
                    "raw": e.raw,
                    "file_path": e.file_path,
                    "line_no": e.line_no,
                }
                for e in (entry.context_after or [])
            ],
        }

    def _extract_case_summary(self, case_content: str) -> str:
        """Extract summary from case content."""
        lines = case_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#") or line.startswith("##"):
                continue
            if line and len(line) > 20:
                return line[:100] + "..." if len(line) > 100 else line
        return "No summary available"

    def _write_file(
        self,
        path: Path,
        content: str,
        created_files: list[Path],
    ) -> None:
        """Write file and track for potential rollback."""
        path.write_text(content, encoding="utf-8")
        created_files.append(path)

    def _rollback(self, created_files: list[Path]) -> None:
        """Delete created files on failure."""
        for file_path in created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except OSError as exc:
                logger.warning("Failed to rollback file %s: %s", file_path, exc)


class _WorkspaceStructure:
    """Holds paths for workspace directory structure."""

    def __init__(
        self,
        root: Path,
        context_dir: Path,
        logs_dir: Path,
        cases_dir: Path,
        readme_path: Path,
        prompt_path: Path,
        evidence_pack_path: Path,
    ) -> None:
        self.root = root
        self.context_dir = context_dir
        self.logs_dir = logs_dir
        self.cases_dir = cases_dir
        self.readme_path = readme_path
        self.prompt_path = prompt_path
        self.evidence_pack_path = evidence_pack_path
