"""Tests for diagnose_tool/exporter/workspace_exporter.py."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from diagnose_tool.core.llm_config import AppLLMConfig
from diagnose_tool.exporter.workspace_exporter import (
    WorkspaceExporter,
    WorkspaceExportError,
)


@pytest.fixture
def default_config(tmp_path: Path) -> AppLLMConfig:
    """Default LLM config for testing."""
    return AppLLMConfig(
        enabled=True,
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        timeout=60,
        data_dir=tmp_path,
    )


@pytest.fixture
def workspace_dir(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    return tmp_path / "workspace"


@pytest.fixture
def task_with_evidence(tmp_path: Path) -> tuple[Path, Path]:
    """Create a task with evidence-pack.md."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    task_output = data_dir / "output" / "task-001"
    task_output.mkdir(parents=True)

    # Create evidence-pack.md
    (task_output / "evidence-pack.md").write_text(
        "# Evidence Pack\n\n2026-05-23 10:01:01 ERROR [order-core] OrderService - order failed",
        encoding="utf-8"
    )

    # Create retrieval-query.json
    retrieval_query_data = {
        "task_id": "task-001",
        "summary": "Test task",
        "keywords": ["error", "exception"],
        "components": [],
        "fault_modes": [],
        "exception_classes": [],
        "stack_symbols": [],
        "log_templates": [],
    }
    (task_output / "retrieval-query.json").write_text(
        json.dumps(retrieval_query_data), encoding="utf-8"
    )

    return data_dir, task_output


class TestWorkspaceExporter:
    """Tests for WorkspaceExporter."""

    def test_validate_workspace_dir_rejects_nonexistent_dir(
        self, default_config: AppLLMConfig, tmp_path: Path
    ) -> None:
        """WorkspaceExportError raised when directory does not exist."""
        exporter = WorkspaceExporter(default_config)

        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(WorkspaceExportError) as exc_info:
            exporter._validate_workspace_dir(nonexistent_dir)

        assert "does not exist" in str(exc_info.value)

    def test_validate_workspace_dir_rejects_unwritable_dir(
        self, default_config: AppLLMConfig, tmp_path: Path
    ) -> None:
        """WorkspaceExportError raised when directory is not writable."""
        exporter = WorkspaceExporter(default_config)

        # Create a file instead of directory
        test_file = tmp_path / "testfile"
        test_file.write_text("test", encoding="utf-8")

        with pytest.raises(WorkspaceExportError) as exc_info:
            exporter._validate_workspace_dir(test_file)

        assert "not a directory" in str(exc_info.value)

    def test_build_workspace_dir_creates_subdirectories(
        self, default_config: AppLLMConfig, workspace_dir: Path
    ) -> None:
        """_build_workspace_dir creates context/, logs/, cases/ subdirectories."""
        exporter = WorkspaceExporter(default_config)

        workspace_dir.mkdir(parents=True)
        structure = exporter._build_workspace_dir(workspace_dir)

        assert structure.context_dir.exists()
        assert structure.logs_dir.exists()
        assert structure.cases_dir.exists()
        assert structure.readme_path == workspace_dir / "README.md"
        assert structure.prompt_path == workspace_dir / "prompt.md"
        assert structure.evidence_pack_path == workspace_dir / "logs" / "evidence-pack.md"

    def test_export_from_task_id_creates_all_files(
        self, default_config: AppLLMConfig, task_with_evidence: tuple[Path, Path], workspace_dir: Path
    ) -> None:
        """export_from_task_id creates all required files in workspace."""
        data_dir, task_output = task_with_evidence
        default_config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=data_dir,
        )

        exporter = WorkspaceExporter(default_config)
        workspace_dir.mkdir(parents=True)

        files_written = exporter.export_from_task_id(
            task_id="task-001",
            workspace_dir=workspace_dir,
            user_context={"phenomenon": "Order failed", "stack": "Error at OrderService", "params": "order_id=123"},
        )

        # Verify files exist
        assert (workspace_dir / "README.md").exists()
        assert (workspace_dir / "prompt.md").exists()
        assert (workspace_dir / "context" / "phenomenon.md").exists()
        assert (workspace_dir / "context" / "stack.md").exists()
        assert (workspace_dir / "context" / "params.md").exists()
        assert (workspace_dir / "logs" / "evidence-pack.md").exists()
        assert (workspace_dir / "cases").exists()

        # Verify content
        assert "Order failed" in (workspace_dir / "context" / "phenomenon.md").read_text(encoding="utf-8")
        assert "OrderService" in (workspace_dir / "context" / "stack.md").read_text(encoding="utf-8")

    def test_export_from_task_id_rollback_on_failure(
        self, default_config: AppLLMConfig, task_with_evidence: tuple[Path, Path], tmp_path: Path
    ) -> None:
        """Rollback deletes created files when export fails."""
        data_dir, task_output = task_with_evidence
        default_config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=data_dir,
        )

        exporter = WorkspaceExporter(default_config)

        # Create workspace dir but make it read-only after structure is built
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir(parents=True)

        # Try to export with invalid task_id to trigger failure
        with pytest.raises(WorkspaceExportError):
            exporter.export_from_task_id(
                task_id="nonexistent-task",
                workspace_dir=workspace_dir,
            )

    def test_write_context_files_with_empty_context(
        self, default_config: AppLLMConfig, tmp_path: Path
    ) -> None:
        """Empty user context results in placeholder text."""
        exporter = WorkspaceExporter(default_config)
        context_dir = tmp_path / "context"
        context_dir.mkdir(parents=True)

        exporter._write_context_files(context_dir, {})

        phenomenon_content = (context_dir / "phenomenon.md").read_text(encoding="utf-8")
        stack_content = (context_dir / "stack.md").read_text(encoding="utf-8")
        params_content = (context_dir / "params.md").read_text(encoding="utf-8")

        assert "用户未提供" in phenomenon_content
        assert "用户未提供" in stack_content
        assert "用户未提供" in params_content
        assert "问题现象" in phenomenon_content

    def test_write_context_files_with_populated_context(
        self, default_config: AppLLMConfig, tmp_path: Path
    ) -> None:
        """Populated user context is written correctly."""
        exporter = WorkspaceExporter(default_config)
        context_dir = tmp_path / "context"
        context_dir.mkdir(parents=True)

        exporter._write_context_files(context_dir, {
            "phenomenon": "Service down",
            "stack": "NullPointerException",
            "params": "server=prod-1",
        })

        assert "Service down" in (context_dir / "phenomenon.md").read_text(encoding="utf-8")
        assert "NullPointerException" in (context_dir / "stack.md").read_text(encoding="utf-8")
        assert "server=prod-1" in (context_dir / "params.md").read_text(encoding="utf-8")

    def test_build_prompt_contains_role_definition(
        self, default_config: AppLLMConfig
    ) -> None:
        """Prompt contains role definition."""
        exporter = WorkspaceExporter(default_config)

        prompt = exporter._build_prompt(
            evidence_pack="# Evidence\n\nTest evidence",
            similar_cases=[],
            user_context={},
        )

        assert "Role" in prompt
        assert "backend stability engineer" in prompt.lower()

    def test_build_prompt_contains_evidence(
        self, default_config: AppLLMConfig
    ) -> None:
        """Prompt contains evidence pack."""
        exporter = WorkspaceExporter(default_config)

        prompt = exporter._build_prompt(
            evidence_pack="# Evidence\n\nTest evidence",
            similar_cases=[],
            user_context={},
        )

        assert "Test evidence" in prompt
        assert "Current Fault Evidence" in prompt

    def test_build_prompt_contains_constraints(
        self, default_config: AppLLMConfig
    ) -> None:
        """Prompt contains constraints section."""
        exporter = WorkspaceExporter(default_config)

        prompt = exporter._build_prompt(
            evidence_pack="# Evidence\n\nTest evidence",
            similar_cases=[],
            user_context={},
        )

        assert "Constraints" in prompt or "constraints" in prompt.lower()

    def test_build_readme_contains_directory_structure(
        self, default_config: AppLLMConfig
    ) -> None:
        """README contains directory structure explanation."""
        exporter = WorkspaceExporter(default_config)

        readme = exporter._build_readme("test-workspace")

        assert "Directory Structure" in readme
        assert "context/" in readme
        assert "logs/" in readme
        assert "cases/" in readme
        assert "prompt.md" in readme

    def test_build_readme_contains_result_instructions(
        self, default_config: AppLLMConfig
    ) -> None:
        """README contains instructions for saving result.md."""
        exporter = WorkspaceExporter(default_config)

        readme = exporter._build_readme("test-workspace")

        assert "result.md" in readme
        assert "Save your diagnosis" in readme or "保存" in readme


class TestWorkspaceStructure:
    """Tests for workspace directory structure."""

    def test_workspace_has_correct_directory_structure(
        self, default_config: AppLLMConfig, task_with_evidence: tuple[Path, Path], workspace_dir: Path
    ) -> None:
        """Workspace directory structure matches spec."""
        data_dir, _ = task_with_evidence
        default_config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=data_dir,
        )

        exporter = WorkspaceExporter(default_config)
        workspace_dir.mkdir(parents=True)

        exporter.export_from_task_id(
            task_id="task-001",
            workspace_dir=workspace_dir,
        )

        # Verify structure matches spec
        assert workspace_dir.exists()
        assert (workspace_dir / "README.md").exists()
        assert (workspace_dir / "prompt.md").exists()
        assert (workspace_dir / "context").is_dir()
        assert (workspace_dir / "context" / "phenomenon.md").exists()
        assert (workspace_dir / "context" / "stack.md").exists()
        assert (workspace_dir / "context" / "params.md").exists()
        assert (workspace_dir / "logs").is_dir()
        assert (workspace_dir / "logs" / "evidence-pack.md").exists()
        assert (workspace_dir / "cases").is_dir()
