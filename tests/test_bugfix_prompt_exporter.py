"""Tests for diagnose_tool/exporter/bugfix_prompt_exporter.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from diagnose_tool.exporter.bugfix_prompt_exporter import (
    BugfixPromptExportError,
    BugfixPromptExporter,
    BugfixPromptTaskNotFoundError,
)


@pytest.fixture
def task_output_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    output_dir = data_dir / "output" / "task-001"
    output_dir.mkdir(parents=True)

    (output_dir / "task.yaml").write_text(
        "\n".join(
            [
                "task_id: task-001",
                "source_type: SERVER_DIRECTORY",
                "source_path: /data/logs/app",
                "mode: STANDARD",
                "status: SUCCESS",
                "created_at: '2026-05-31 10:00:00'",
                "started_at: '2026-05-31 10:00:01'",
                "finished_at: '2026-05-31 10:05:00'",
                "total_files: 3",
                "processed_files: 3",
                "total_bytes: 1024",
                "processed_bytes: 1024",
                "error_count: 1",
                "warn_count: 2",
                "outputs:",
                "  summary: summary.html",
                "  evidence_pack: evidence-pack.md",
                "  case_draft: case-draft.md",
                "  retrieval_query: retrieval-query.json",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "evidence-pack.md").write_text(
        "# Evidence Pack\n\n- ERROR connection failed\n- WARN retry timeout",
        encoding="utf-8",
    )
    (output_dir / "case-draft.md").write_text(
        "# Draft Case\n\n## Root Cause\nConnection pool exhaustion.",
        encoding="utf-8",
    )
    (output_dir / "retrieval-query.json").write_text(
        json.dumps(
            {
                "task_id": "task-001",
                "summary": "Connection pool exhaustion",
                "components": ["OrderService"],
                "fault_modes": ["resource_exhaustion"],
                "exception_classes": ["TimeoutException"],
                "keywords": ["connection", "timeout"],
                "stack_symbols": ["com.demo.OrderService.placeOrder"],
                "log_templates": ["Connection failed"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return data_dir


def test_exporter_generates_prompt_and_overwrites_atomically(task_output_dir: Path) -> None:
    exporter = BugfixPromptExporter(task_output_dir)

    first = exporter.export_from_task_id("task-001")
    output_path = task_output_dir / "output" / "task-001" / "bugfix-prompt.md"

    assert first.output_path == output_path
    assert output_path.exists()

    prompt = output_path.read_text(encoding="utf-8")
    assert prompt == first.prompt
    assert "# Bugfix Prompt" in prompt
    assert "task-001" in prompt
    assert "Connection pool exhaustion" in prompt
    assert "evidence-pack.md" in prompt
    assert "retrieval-query.json" in prompt

    output_path.write_text("stale content", encoding="utf-8")
    second = exporter.export_from_task_id("task-001")
    assert second.prompt == first.prompt
    assert output_path.read_text(encoding="utf-8") == first.prompt


def test_exporter_requires_task_directory(task_output_dir: Path) -> None:
    exporter = BugfixPromptExporter(task_output_dir)

    with pytest.raises(BugfixPromptTaskNotFoundError):
        exporter.export_from_task_id("missing-task")


def test_exporter_requires_evidence_pack(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_dir = data_dir / "output" / "task-001"
    output_dir.mkdir(parents=True)
    (output_dir / "task.yaml").write_text("task_id: task-001\n", encoding="utf-8")

    exporter = BugfixPromptExporter(data_dir)

    with pytest.raises(BugfixPromptTaskNotFoundError):
        exporter.export_from_task_id("task-001")


def test_exporter_rejects_invalid_task_yaml(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_dir = data_dir / "output" / "task-001"
    output_dir.mkdir(parents=True)
    (output_dir / "task.yaml").write_text("- not-a-mapping", encoding="utf-8")
    (output_dir / "evidence-pack.md").write_text("evidence", encoding="utf-8")

    exporter = BugfixPromptExporter(data_dir)

    with pytest.raises(BugfixPromptExportError):
        exporter.export_from_task_id("task-001")
