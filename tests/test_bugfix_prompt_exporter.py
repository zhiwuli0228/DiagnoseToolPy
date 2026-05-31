"""Tests for diagnose_tool/exporter/bugfix_prompt_exporter.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from diagnose_tool.core.llm_config import AppLLMConfig
from diagnose_tool.exporter.bugfix_prompt_exporter import (
    BugfixPromptArtifactError,
    BugfixPromptExporter,
    BugfixPromptTaskNotFoundError,
)


@pytest.fixture
def llm_config(tmp_path: Path) -> AppLLMConfig:
    return AppLLMConfig(
        enabled=True,
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        timeout=60,
        data_dir=tmp_path,
    )


def _write_task_output(data_dir: Path, task_id: str, *, evidence_text: str, title: str = "NullPointerException 导致任务失败") -> Path:
    task_output = data_dir / "output" / task_id
    task_output.mkdir(parents=True)

    task_meta = {
        "task_id": task_id,
        "source_type": "SERVER_DIRECTORY",
        "source_path": "/data/input/logs",
        "mode": "STANDARD",
        "status": "SUCCESS",
        "created_at": "2026-05-31 10:00:00",
        "started_at": "2026-05-31 10:00:01",
        "finished_at": "2026-05-31 10:03:00",
        "total_files": 3,
        "processed_files": 3,
        "total_bytes": 1024,
        "processed_bytes": 1024,
        "error_count": 4,
        "warn_count": 1,
        "outputs": {
            "summary": "summary.html",
            "evidence_pack": "evidence-pack.md",
            "key_logs": "key-logs.txt",
            "case_draft": "case-draft.md",
        },
    }
    (task_output / "task.yaml").write_text(
        yaml.safe_dump(task_meta, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (task_output / "evidence-pack.md").write_text(evidence_text, encoding="utf-8")
    (task_output / "case-draft.md").write_text(
        f"# {title}\n\n## 故障描述\n\n服务在处理请求时抛出空指针异常。\n\n## 可能根因\n\n依赖对象未初始化。\n",
        encoding="utf-8",
    )
    (task_output / "case-metadata-draft.yaml").write_text(
        yaml.safe_dump(
            {
                "case_id": "CASE-TASK-001",
                "title": title,
                "slug": "null-pointer-task-failure",
                "source_type": "auto",
                "status": "draft",
                "confidence": "unconfirmed",
                "tags": ["bugfix"],
                "components": ["diagnose_tool.api"],
                "fault_modes": ["null_pointer"],
                "exception_classes": ["NullPointerException"],
                "key_phrases": ["依赖对象未初始化"],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (task_output / "retrieval-query.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "summary": "null_pointer 故障类型的故障; 涉及组件: diagnose_tool.api",
                "components": ["diagnose_tool.api"],
                "fault_modes": ["null_pointer"],
                "exception_classes": ["NullPointerException"],
                "keywords": ["依赖对象未初始化", "空指针"],
                "stack_symbols": ["com.demo.Service.handle"],
                "log_templates": ["NullPointerException at service layer"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (task_output / "progress.json").write_text(
        json.dumps(
            {
                "status": "SUCCESS",
                "processed_files": 3,
                "total_files": 3,
                "processed_bytes": 1024,
                "total_bytes": 1024,
                "message": "analysis complete",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (task_output / "summary.html").write_text("<html><body><h1>Summary</h1></body></html>", encoding="utf-8")
    (task_output / "key-logs.txt").write_text("[error] NullPointerException\n", encoding="utf-8")
    return task_output


def test_export_from_task_id_creates_bugfix_prompt(llm_config: AppLLMConfig) -> None:
    data_dir = llm_config.data_dir
    task_output = _write_task_output(
        data_dir,
        "task-001",
        evidence_text="# Evidence Pack\n\n## 1. 基本信息\n- 任务ID：task-001\n- 文件数量：3\n- ERROR数量：4\n",
    )

    exporter = BugfixPromptExporter(llm_config)
    result = exporter.export_from_task_id("task-001")

    assert result.output_path == task_output / "bugfix-prompt.md"
    assert result.output_path.exists()
    content = result.output_path.read_text(encoding="utf-8")
    assert "Bugfix Prompt for NullPointerException 导致任务失败" in content
    assert "## Task Metadata" in content
    assert "## Evidence Summary" in content
    assert "NullPointerException" in content
    assert "AI diagnosis remains preliminary" in content
    assert "bugfix-prompt.md" in content
    assert result.prompt == content


def test_export_from_task_id_overwrites_existing_prompt(llm_config: AppLLMConfig) -> None:
    data_dir = llm_config.data_dir
    task_output = _write_task_output(
        data_dir,
        "task-002",
        evidence_text="# Evidence Pack\n\nFirst evidence snippet.\n",
    )

    exporter = BugfixPromptExporter(llm_config)
    first = exporter.export_from_task_id("task-002")
    (task_output / "evidence-pack.md").write_text(
        "# Evidence Pack\n\nUpdated evidence snippet.\n",
        encoding="utf-8",
    )

    second = exporter.export_from_task_id("task-002")

    assert first.output_path == second.output_path
    assert "First evidence snippet." in first.prompt
    assert "Updated evidence snippet." in second.prompt
    assert second.output_path.read_text(encoding="utf-8") == second.prompt


def test_export_from_task_id_missing_required_artifact_raises(llm_config: AppLLMConfig) -> None:
    data_dir = llm_config.data_dir
    task_output = data_dir / "output" / "task-003"
    task_output.mkdir(parents=True)
    (task_output / "task.yaml").write_text(
        yaml.safe_dump({"task_id": "task-003"}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    exporter = BugfixPromptExporter(llm_config)

    with pytest.raises(BugfixPromptArtifactError):
        exporter.export_from_task_id("task-003")

    assert not (task_output / "bugfix-prompt.md").exists()


def test_export_from_task_id_missing_task_raises(llm_config: AppLLMConfig) -> None:
    exporter = BugfixPromptExporter(llm_config)

    with pytest.raises(BugfixPromptTaskNotFoundError):
        exporter.export_from_task_id("missing-task")
