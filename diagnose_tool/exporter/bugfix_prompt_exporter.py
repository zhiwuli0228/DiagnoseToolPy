"""Bugfix prompt exporter for analysis task outputs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import yaml

from diagnose_tool.core.llm_config import AppLLMConfig

logger = logging.getLogger(__name__)


class BugfixPromptExportError(RuntimeError):
    """Raised when bugfix prompt export fails."""


class BugfixPromptTaskNotFoundError(BugfixPromptExportError):
    """Raised when the requested analysis task output does not exist."""


class BugfixPromptArtifactError(BugfixPromptExportError):
    """Raised when a required task artifact is missing or unreadable."""


class BugfixPromptWriteError(BugfixPromptExportError):
    """Raised when the bugfix prompt file cannot be written safely."""


@dataclass(frozen=True)
class BugfixPromptExportResult:
    """Result of a bugfix prompt export."""

    task_id: str
    output_path: Path
    prompt: str
    source_files: tuple[Path, ...]


class BugfixPromptExporter:
    """Build bugfix prompt markdown from an existing analysis task output."""

    def __init__(self, llm_config: AppLLMConfig) -> None:
        self._llm_config = llm_config
        self._data_dir = llm_config.data_dir

    def export_from_task_id(self, task_id: str) -> BugfixPromptExportResult:
        """Generate and persist bugfix-prompt.md for the requested task."""
        task_output = self._data_dir / "output" / task_id
        if not task_output.exists():
            raise BugfixPromptTaskNotFoundError(f"Task output directory not found: {task_output}")
        if not task_output.is_dir():
            raise BugfixPromptTaskNotFoundError(f"Task output path is not a directory: {task_output}")

        task_meta = self._read_task_metadata(task_output)
        evidence_pack = self._read_required_text(task_output / "evidence-pack.md", "evidence-pack.md")
        case_draft = self._read_optional_text(task_output / "case-draft.md")
        case_metadata = self._read_optional_yaml(task_output / "case-metadata-draft.yaml")
        retrieval_query = self._read_optional_json(task_output / "retrieval-query.json")
        progress = self._read_optional_json(task_output / "progress.json")
        summary_html = self._read_optional_text(task_output / "summary.html")
        key_logs = self._read_optional_text(task_output / "key-logs.txt")

        prompt = self._build_prompt(
            task_output=task_output,
            task_meta=task_meta,
            evidence_pack=evidence_pack,
            case_draft=case_draft,
            case_metadata=case_metadata,
            retrieval_query=retrieval_query,
            progress=progress,
            summary_html=summary_html,
            key_logs=key_logs,
        )

        output_path = task_output / "bugfix-prompt.md"
        self._write_atomic(output_path, prompt)

        return BugfixPromptExportResult(
            task_id=task_id,
            output_path=output_path,
            prompt=prompt,
            source_files=(
                task_output / "task.yaml",
                task_output / "evidence-pack.md",
                *(task_output / name for name in [
                    "case-draft.md",
                    "case-metadata-draft.yaml",
                    "retrieval-query.json",
                    "progress.json",
                    "summary.html",
                    "key-logs.txt",
                ]),
            ),
        )

    def _read_task_metadata(self, task_output: Path) -> dict[str, Any]:
        path = task_output / "task.yaml"
        if not path.exists():
            raise BugfixPromptArtifactError(f"Required task artifact not found: {path}")

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise BugfixPromptArtifactError(f"Failed to read task metadata: {path}") from exc

        if not isinstance(data, dict):
            raise BugfixPromptArtifactError(f"Invalid task metadata format: {path}")
        return data

    def _read_required_text(self, path: Path, label: str) -> str:
        if not path.exists():
            raise BugfixPromptArtifactError(f"Required task artifact not found: {path}")
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            raise BugfixPromptArtifactError(f"Failed to read {label}: {path}") from exc
        if not content.strip():
            raise BugfixPromptArtifactError(f"Required task artifact is empty: {path}")
        return content

    def _read_optional_text(self, path: Path) -> str | None:
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            raise BugfixPromptArtifactError(f"Failed to read optional artifact: {path}") from exc
        return content

    def _read_optional_yaml(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise BugfixPromptArtifactError(f"Failed to read YAML artifact: {path}") from exc
        if data is None:
            return None
        if not isinstance(data, dict):
            raise BugfixPromptArtifactError(f"Invalid YAML artifact format: {path}")
        return data

    def _read_optional_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise BugfixPromptArtifactError(f"Failed to read JSON artifact: {path}") from exc
        if not isinstance(data, dict):
            raise BugfixPromptArtifactError(f"Invalid JSON artifact format: {path}")
        return data

    def _build_prompt(
        self,
        task_output: Path,
        task_meta: dict[str, Any],
        evidence_pack: str,
        case_draft: str | None,
        case_metadata: dict[str, Any] | None,
        retrieval_query: dict[str, Any] | None,
        progress: dict[str, Any] | None,
        summary_html: str | None,
        key_logs: str | None,
    ) -> str:
        title = self._derive_title(task_meta, case_draft, case_metadata)
        problem_summary = self._build_problem_summary(task_meta, case_draft, case_metadata, retrieval_query, progress)
        evidence_summary = self._build_evidence_summary(evidence_pack, key_logs, summary_html)
        diagnosis_state = self._build_diagnosis_state(case_metadata, case_draft, retrieval_query)
        guardrails = self._build_guardrails()
        fix_plan = self._build_fix_plan(task_meta, retrieval_query)
        regression_tests = self._build_regression_tests(retrieval_query, case_metadata)
        human_questions = self._build_human_questions()

        metadata_lines = self._format_task_metadata(task_meta, task_output, progress)
        source_artifacts = self._format_source_artifacts(task_output)

        sections = [
            f"# {title}",
            "",
            "## Task Metadata",
            "",
            *metadata_lines,
            "",
            "## Problem Summary",
            "",
            problem_summary,
            "",
            "## Evidence Summary",
            "",
            evidence_summary,
            "",
            "## Diagnosis State / Hypothesis",
            "",
            diagnosis_state,
            "",
            "## Implementation Guardrails",
            "",
            *guardrails,
            "",
            "## Suggested Fix Plan",
            "",
            *fix_plan,
            "",
            "## Regression Tests",
            "",
            *regression_tests,
            "",
            "## Human Confirmation Questions",
            "",
            *human_questions,
            "",
            "## Source Artifacts",
            "",
            *source_artifacts,
            "",
            "## Important Notes",
            "",
            "- This prompt is derived from existing analysis task outputs only.",
            "- Historical references are references only and must not be treated as confirmed facts for the current issue.",
            "- AI diagnosis remains preliminary unless a human-confirmed root cause is explicitly recorded.",
        ]

        return "\n".join(sections).strip() + "\n"

    def _derive_title(
        self,
        task_meta: dict[str, Any],
        case_draft: str | None,
        case_metadata: dict[str, Any] | None,
    ) -> str:
        if case_metadata and isinstance(case_metadata.get("title"), str) and case_metadata["title"].strip():
            return f"Bugfix Prompt for {case_metadata['title'].strip()}"
        if case_draft:
            first_heading = self._extract_first_heading(case_draft)
            if first_heading:
                return f"Bugfix Prompt for {first_heading}"
        task_id = str(task_meta.get("task_id", "unknown-task"))
        return f"Bugfix Prompt for {task_id}"

    def _format_task_metadata(
        self,
        task_meta: dict[str, Any],
        task_output: Path,
        progress: dict[str, Any] | None,
    ) -> list[str]:
        outputs = task_meta.get("outputs") if isinstance(task_meta.get("outputs"), dict) else {}
        lines = [
            f"- Task ID: `{task_meta.get('task_id', task_output.name)}`",
            f"- Source Type: `{task_meta.get('source_type', 'UNKNOWN')}`",
            f"- Source Path: `{task_meta.get('source_path', '')}`",
            f"- Mode: `{task_meta.get('mode', 'UNKNOWN')}`",
            f"- Status: `{task_meta.get('status', 'UNKNOWN')}`",
            f"- Created At: `{task_meta.get('created_at', '')}`",
            f"- Started At: `{task_meta.get('started_at', '')}`",
            f"- Finished At: `{task_meta.get('finished_at', '')}`",
            f"- Total Files: `{task_meta.get('total_files', 0)}`",
            f"- Processed Files: `{task_meta.get('processed_files', 0)}`",
            f"- Total Bytes: `{task_meta.get('total_bytes', 0)}`",
            f"- Processed Bytes: `{task_meta.get('processed_bytes', 0)}`",
            f"- Error Count: `{task_meta.get('error_count', 0)}`",
            f"- Warn Count: `{task_meta.get('warn_count', 0)}`",
        ]

        if outputs:
            outputs_text = ", ".join(f"{k}={v}" for k, v in outputs.items() if v)
            if outputs_text:
                lines.append(f"- Outputs: `{outputs_text}`")
        if progress:
            progress_text = ", ".join(
                f"{k}={progress.get(k)}"
                for k in ("status", "processed_files", "total_files", "processed_bytes", "total_bytes", "message")
                if progress.get(k) is not None
            )
            if progress_text:
                lines.append(f"- Current Progress: `{progress_text}`")
        return lines

    def _build_problem_summary(
        self,
        task_meta: dict[str, Any],
        case_draft: str | None,
        case_metadata: dict[str, Any] | None,
        retrieval_query: dict[str, Any] | None,
        progress: dict[str, Any] | None,
    ) -> str:
        summary_parts: list[str] = []

        title = self._extract_first_heading(case_draft or "")
        if title:
            summary_parts.append(f"当前任务已形成草稿标题：{title}。")
        else:
            summary_parts.append(f"当前任务 `{task_meta.get('task_id', '')}` 已完成分析输出，但尚未沉淀明确的手工结论标题。")

        errors = task_meta.get("error_count")
        warns = task_meta.get("warn_count")
        files = task_meta.get("total_files")
        if errors is not None or warns is not None or files is not None:
            summary_parts.append(
                f"任务输出统计显示 {files or 0} 个文件、{errors or 0} 个 ERROR、{warns or 0} 个 WARN，说明该问题具备可复现的日志证据。"
            )

        if retrieval_query:
            components = retrieval_query.get("components") or []
            fault_modes = retrieval_query.get("fault_modes") or []
            exception_classes = retrieval_query.get("exception_classes") or []
            keywords = retrieval_query.get("keywords") or []
            summary_bits = []
            if fault_modes:
                summary_bits.append(f"fault modes={', '.join(str(v) for v in fault_modes[:4])}")
            if components:
                summary_bits.append(f"components={', '.join(str(v) for v in components[:4])}")
            if exception_classes:
                summary_bits.append(f"exceptions={', '.join(str(v) for v in exception_classes[:4])}")
            if keywords:
                summary_bits.append(f"keywords={', '.join(str(v) for v in keywords[:6])}")
            if summary_bits:
                summary_parts.append("检索向量与规则信号包括：" + "；".join(summary_bits) + "。")

        if case_metadata:
            confidence = str(case_metadata.get("confidence", "")).strip()
            status = str(case_metadata.get("status", "")).strip()
            if confidence or status:
                summary_parts.append(
                    f"当前案例草稿状态为 `{status or 'unknown'}`，置信度标记为 `{confidence or 'unknown'}`；在人工确认前仍应视为假设。"
                )

        if progress and progress.get("message"):
            summary_parts.append(f"最近一次处理进度消息：{progress['message']}")

        return "\n\n".join(f"- {part}" for part in summary_parts)

    def _build_evidence_summary(
        self,
        evidence_pack: str,
        key_logs: str | None,
        summary_html: str | None,
    ) -> str:
        excerpt_parts = ["已生成的证据包是主要输入来源；不要重新读取完整原始日志。"]
        evidence_excerpt = self._excerpt_text(evidence_pack, max_lines=24, max_chars=2200)
        excerpt_parts.append("证据包摘录：")
        excerpt_parts.append("")
        excerpt_parts.append("```markdown")
        excerpt_parts.append(evidence_excerpt)
        excerpt_parts.append("```")

        if key_logs:
            excerpt_parts.append("")
            excerpt_parts.append("关键日志摘录（仅供核对，非完整日志）：")
            excerpt_parts.append("")
            excerpt_parts.append("```text")
            excerpt_parts.append(self._excerpt_text(key_logs, max_lines=12, max_chars=900))
            excerpt_parts.append("```")

        if summary_html:
            excerpt_parts.append("")
            excerpt_parts.append("HTML 报告存在并可作为人审补充，不在此处展开全文。")

        return "\n".join(excerpt_parts)

    def _build_diagnosis_state(
        self,
        case_metadata: dict[str, Any] | None,
        case_draft: str | None,
        retrieval_query: dict[str, Any] | None,
    ) -> str:
        state_lines = [
            "本 prompt 以现有分析任务输出为基础，面向后续实现端生成修复方案。",
            "除非单独有人审根因已记录，否则默认将 AI 诊断视为 preliminary。",
        ]

        if case_metadata:
            confidence = str(case_metadata.get("confidence", "")).strip()
            status = str(case_metadata.get("status", "")).strip()
            if status or confidence:
                state_lines.append(f"案例草稿显示 status=`{status or 'unknown'}`、confidence=`{confidence or 'unknown'}`。")

        if case_draft:
            summary = self._extract_markdown_summary(case_draft)
            if summary:
                state_lines.append(f"案例草稿摘要：{summary}")

        if retrieval_query:
            components = retrieval_query.get("components") or []
            if components:
                state_lines.append(f"建议优先关注组件：{', '.join(str(c) for c in components[:5])}。")

        state_lines.append("历史案例与检索结果仅供参考，不能直接替代当前问题的确认根因。")
        return "\n".join(f"- {line}" for line in state_lines)

    def _build_guardrails(self) -> list[str]:
        return [
            "- Treat any AI diagnosis as preliminary unless a human-confirmed root cause is explicitly recorded.",
            "- Do not invent new facts from raw logs or from unavailable artifacts.",
            "- Do not expand the fix into unrelated refactors, storage redesign, or governance changes.",
            "- Keep implementation bounded to the diagnosed issue and its direct regression surface.",
            "- Do not load full raw log files into memory while preparing this prompt.",
            "- Historical case references are references only and must not be treated as confirmed facts.",
        ]

    def _build_fix_plan(
        self,
        task_meta: dict[str, Any],
        retrieval_query: dict[str, Any] | None,
    ) -> list[str]:
        steps = [
            "1. Reproduce the issue from the evidence bundle and confirm the minimal failing path.",
            "2. Identify the smallest code path that explains the observed failure without widening scope.",
            "3. Implement the fix with the least behavioral change necessary to resolve the defect.",
            "4. Add or update regression tests that fail before the fix and pass after the fix.",
            "5. Re-run the relevant checks and verify no unrelated behavior regressed.",
        ]

        if retrieval_query:
            components = retrieval_query.get("components") or []
            exception_classes = retrieval_query.get("exception_classes") or []
            keywords = retrieval_query.get("keywords") or []
            if components:
                steps.append(f"6. Inspect component boundaries for: {', '.join(str(c) for c in components[:4])}.")
            if exception_classes:
                steps.append(f"7. Validate exception handling for: {', '.join(str(e) for e in exception_classes[:4])}.")
            if keywords:
                steps.append(f"8. Check the key log phrases: {', '.join(str(k) for k in keywords[:6])}.")

        return [f"- {step}" if not step.startswith("- ") else step for step in steps]

    def _build_regression_tests(
        self,
        retrieval_query: dict[str, Any] | None,
        case_metadata: dict[str, Any] | None,
    ) -> list[str]:
        tests = [
            "- Add a regression test that reproduces the failure with the smallest stable fixture possible.",
            "- Verify the bugfix prompt remains deterministic when regenerated from unchanged task artifacts.",
            "- Cover the missing-artifact path so the exporter fails safely without writing partial output.",
        ]

        if retrieval_query:
            components = retrieval_query.get("components") or []
            exception_classes = retrieval_query.get("exception_classes") or []
            fault_modes = retrieval_query.get("fault_modes") or []
            if components:
                tests.append(f"- Assert the prompt mentions the affected components: {', '.join(str(c) for c in components[:4])}.")
            if exception_classes:
                tests.append(f"- Assert the prompt surfaces exception classes: {', '.join(str(e) for e in exception_classes[:4])}.")
            if fault_modes:
                tests.append(f"- Assert the prompt preserves the dominant fault modes: {', '.join(str(v) for v in fault_modes[:4])}.")

        if case_metadata and case_metadata.get("confidence"):
            tests.append("- Ensure the diagnosis-state wording reflects whether the current evidence is still preliminary or human-confirmed.")

        return tests

    def _build_human_questions(self) -> list[str]:
        return [
            "- What exact user-visible symptom should the implementation preserve as the acceptance criterion?",
            "- Which code paths are out of scope for the first fix and should be explicitly avoided?",
            "- Are there any regression scenarios that must be added before the change can be considered complete?",
            "- Can the generated prompt be handed directly to Claude Code or OpenCode without additional manual rewriting?",
        ]

    def _format_source_artifacts(self, task_output: Path) -> list[str]:
        artifacts = [
            "- `task.yaml`",
            "- `evidence-pack.md`",
            "- `case-draft.md` (if present)",
            "- `case-metadata-draft.yaml` (if present)",
            "- `retrieval-query.json` (if present)",
            "- `progress.json` (if present)",
            "- `summary.html` (if present)",
            "- `key-logs.txt` (if present)",
        ]
        artifacts.append(f"- Generated output: `{task_output / 'bugfix-prompt.md'}`")
        return artifacts

    def _extract_first_heading(self, content: str) -> str | None:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    return heading
        return None

    def _extract_markdown_summary(self, content: str) -> str:
        lines = self._meaningful_lines(content)
        if not lines:
            return ""
        return self._join_excerpt(lines, max_chars=180)

    def _excerpt_text(self, content: str, max_lines: int, max_chars: int) -> str:
        lines = self._meaningful_lines(content)[:max_lines]
        if not lines:
            return "(empty)"
        return self._join_excerpt(lines, max_chars=max_chars)

    def _meaningful_lines(self, content: str) -> list[str]:
        lines: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("```"):
                continue
            if line in {"(待填写)", "(待填写) 请描述观察到的故障现象", "(待填写) 请分析可能的根本原因", "(待填写) 请评估影响范围"}:
                continue
            lines.append(line)
        return lines

    def _join_excerpt(self, lines: list[str], max_chars: int) -> str:
        excerpt = " ".join(lines)
        if len(excerpt) > max_chars:
            excerpt = excerpt[:max_chars].rstrip() + "..."
        return excerpt

    def _write_atomic(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=path.parent,
                prefix=f".{path.stem}.",
                suffix=".tmp",
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = Path(tmp_file.name)
            tmp_path.replace(path)
        except Exception as exc:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    logger.warning("Failed to cleanup temp bugfix prompt file: %s", tmp_path)
            if isinstance(exc, BugfixPromptExportError):
                raise
            raise BugfixPromptWriteError(f"Failed to write bugfix prompt: {path}") from exc
