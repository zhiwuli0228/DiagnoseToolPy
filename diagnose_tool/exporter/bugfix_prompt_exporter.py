"""Bugfix prompt export for analysis task outputs."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class BugfixPromptExportError(RuntimeError):
    """Raised when bugfix prompt export fails."""


class BugfixPromptTaskNotFoundError(BugfixPromptExportError):
    """Raised when the requested task output cannot be located."""


@dataclass(frozen=True)
class BugfixPromptExportResult:
    """Result returned after generating a bugfix prompt."""

    task_id: str
    output_path: Path
    prompt: str


class BugfixPromptExporter:
    """Generate a deterministic implementation brief from task artifacts."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = Path(data_dir)

    def export_from_task_id(self, task_id: str) -> BugfixPromptExportResult:
        """Generate and persist `bugfix-prompt.md` for a task output."""
        task_output = self._resolve_task_output(task_id)
        task_data = self._read_task_yaml(task_output / "task.yaml")
        evidence_pack = self._read_required_text(task_output / "evidence-pack.md")
        case_draft = self._read_optional_text(task_output / "case-draft.md")
        retrieval_query = self._read_optional_json(task_output / "retrieval-query.json")

        prompt = self._build_prompt(
            task_id=task_id,
            task_data=task_data,
            evidence_pack=evidence_pack,
            case_draft=case_draft,
            retrieval_query=retrieval_query,
            source_artifacts=self._list_source_artifacts(task_output),
        )

        output_path = task_output / "bugfix-prompt.md"
        self._atomic_write_text(output_path, prompt)

        return BugfixPromptExportResult(
            task_id=task_id,
            output_path=output_path,
            prompt=prompt,
        )

    def _resolve_task_output(self, task_id: str) -> Path:
        task_output = self._data_dir / "output" / task_id
        if not task_output.exists() or not task_output.is_dir():
            raise BugfixPromptTaskNotFoundError(
                f"Task output directory not found: {task_output}"
            )
        return task_output

    def _read_task_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise BugfixPromptTaskNotFoundError(f"Required artifact not found: {path}")

        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BugfixPromptExportError(f"Unable to read task artifact: {path}") from exc

        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise BugfixPromptExportError(f"Invalid YAML in task artifact: {path}") from exc

        if not isinstance(data, dict):
            raise BugfixPromptExportError(f"Task YAML must be a mapping: {path}")
        return data

    def _read_required_text(self, path: Path) -> str:
        if not path.exists():
            raise BugfixPromptTaskNotFoundError(f"Required artifact not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BugfixPromptExportError(f"Unable to read task artifact: {path}") from exc

        if not content.strip():
            raise BugfixPromptExportError(f"Task artifact is empty: {path}")

        return content

    def _read_optional_text(self, path: Path) -> str | None:
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BugfixPromptExportError(f"Unable to read task artifact: {path}") from exc

    def _read_optional_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BugfixPromptExportError(f"Unable to read task artifact: {path}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BugfixPromptExportError(f"Invalid JSON in task artifact: {path}") from exc

        if not isinstance(data, dict):
            raise BugfixPromptExportError(f"Task JSON must be a mapping: {path}")
        return data

    def _list_source_artifacts(self, task_output: Path) -> list[str]:
        candidates = [
            "task.yaml",
            "evidence-pack.md",
            "case-draft.md",
            "retrieval-query.json",
        ]
        return [name for name in candidates if (task_output / name).exists()]

    def _build_prompt(
        self,
        task_id: str,
        task_data: dict[str, Any],
        evidence_pack: str,
        case_draft: str | None,
        retrieval_query: dict[str, Any] | None,
        source_artifacts: list[str],
    ) -> str:
        task_yaml = yaml.safe_dump(task_data, allow_unicode=True, sort_keys=False).strip()
        retrieval_query_json = (
            json.dumps(retrieval_query, ensure_ascii=False, indent=2, sort_keys=True).strip()
            if retrieval_query is not None
            else None
        )
        artifact_lines = (
            [f"- `{name}`" for name in source_artifacts]
            if source_artifacts
            else ["- (no source artifacts found)"]
        )

        summary_lines = [
            "# Bugfix Prompt",
            "",
            "## Task ID",
            "",
            task_id,
            "",
            "## Task Summary",
            "",
            _format_task_summary(task_data),
            "",
            "## Implementation Constraints",
            "",
            "- Keep the change minimal and scoped to the bugfix prompt export contract.",
            "- Preserve file-system source of truth and streaming-oriented behavior elsewhere in the project.",
            "- Do not introduce mandatory databases or widen unrelated refactors.",
            "- Keep outputs deterministic for the same task artifacts.",
            "",
            "## Source Artifacts",
            "",
            *artifact_lines,
            "",
            "## task.yaml",
            "",
            "```yaml",
            task_yaml,
            "```",
            "",
            "## Evidence Pack",
            "",
            _truncate_markdown(evidence_pack, 5000),
            "",
            "## Case Draft",
            "",
            case_draft.strip() if case_draft else "（case-draft.md 不存在）",
            "",
            "## Retrieval Query",
            "",
            "```json",
            retrieval_query_json if retrieval_query_json is not None else "null",
            "```",
            "",
            "## Suggested Verification",
            "",
            "1. Add or update regression tests for the API and exporter path.",
            "2. Verify `data/output/{task_id}/bugfix-prompt.md` is regenerated deterministically.",
            "3. Confirm the prompt can be copied into Claude Code or OpenCode without further editing.",
            "",
        ]

        return "\n".join(summary_lines).strip() + "\n"

    def _atomic_write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=str(path.parent),
                prefix=f".{path.name}.",
                suffix=".tmp",
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            temp_path.replace(path)
        except OSError as exc:
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    logger.warning("Failed to remove temporary bugfix prompt file: %s", temp_path)
            raise BugfixPromptExportError(f"Failed to write bugfix prompt: {path}") from exc


def _format_task_summary(task_data: dict[str, Any]) -> str:
    lines = [
        f"- Task ID: {task_data.get('task_id', '')}",
        f"- Source Type: {task_data.get('source_type', '')}",
        f"- Source Path: {task_data.get('source_path', '')}",
        f"- Mode: {task_data.get('mode', '')}",
        f"- Status: {task_data.get('status', '')}",
        f"- Created At: {task_data.get('created_at', '')}",
        f"- Started At: {task_data.get('started_at', '')}",
        f"- Finished At: {task_data.get('finished_at', '')}",
        f"- Total Files: {task_data.get('total_files', '')}",
        f"- Processed Files: {task_data.get('processed_files', '')}",
        f"- Total Bytes: {task_data.get('total_bytes', '')}",
        f"- Processed Bytes: {task_data.get('processed_bytes', '')}",
        f"- Error Count: {task_data.get('error_count', '')}",
        f"- Warn Count: {task_data.get('warn_count', '')}",
    ]

    outputs = task_data.get("outputs")
    if isinstance(outputs, dict) and outputs:
        lines.append("- Outputs:")
        for key, value in outputs.items():
            lines.append(f"  - {key}: {value}")

    return "\n".join(lines)


def _truncate_markdown(content: str, limit: int) -> str:
    stripped = content.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit].rstrip() + "\n\n[... truncated ...]"
