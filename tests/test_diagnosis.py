"""Tests for diagnose_tool/analyzer/diagnosis.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from diagnose_tool.analyzer.diagnosis import (
    DiagnosisOrchestrator,
    TaskNotFoundError,
    EvidenceNotFoundError,
)
from diagnose_tool.core.llm_client import LLMClientError
from diagnose_tool.core.llm_config import AppLLMConfig


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


class TestDiagnosisOrchestrator:
    """Tests for DiagnosisOrchestrator.run()."""

    def test_task_not_found_error_raised_when_output_dir_missing(
        self, default_config: AppLLMConfig, tmp_path: Path
    ) -> None:
        """TaskNotFoundError raised when data/output/{task_id} does not exist."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)

        orchestrator = DiagnosisOrchestrator(default_config, data_dir)

        with pytest.raises(TaskNotFoundError):
            orchestrator.run("nonexistent-task")

    def test_evidence_not_found_error_raised_when_evidence_pack_missing(
        self, default_config: AppLLMConfig, tmp_path: Path
    ) -> None:
        """EvidenceNotFoundError raised when evidence-pack.md missing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        task_output = data_dir / "output" / "task-001"
        task_output.mkdir(parents=True)

        orchestrator = DiagnosisOrchestrator(default_config, data_dir)

        with pytest.raises(EvidenceNotFoundError):
            orchestrator.run("task-001")

    def test_successful_diagnosis_returns_case_id_and_text(
        self, default_config: AppLLMConfig, tmp_path: Path, monkeypatch
    ) -> None:
        """Successful flow: returns (case_id, diagnosis_text), writes ai-diagnosis.md."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        task_output = data_dir / "output" / "task-001"
        task_output.mkdir(parents=True)

        # Create evidence-pack.md
        (task_output / "evidence-pack.md").write_text(
            "# Evidence Pack\n\nSome logs here.", encoding="utf-8"
        )

        # Create retrieval-query.json (optional, but we'll include it)
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

        # Mock LLM client to return a diagnosis
        def mock_chat(messages, **kwargs):
            return "## Diagnosis\n\nThis appears to be a database connection issue."

        # We need to patch the LLM client inside DiagnosisOrchestrator
        # The orchestrator imports LLMClient at module level, so we patch it there
        import diagnose_tool.analyzer.diagnosis as diag_module

        class MockLLMClient:
            def __init__(self, config):
                pass

            def chat(self, messages, **kwargs):
                return mock_chat(messages)

        # Patch the LLMClient class in the diagnosis module
        monkeypatch.setattr(diag_module, "LLMClient", MockLLMClient)

        orchestrator = DiagnosisOrchestrator(default_config, data_dir)
        case_id, diagnosis_text = orchestrator.run("task-001")

        assert case_id == "task-001"
        assert "database connection issue" in diagnosis_text

        # Verify ai-diagnosis.md was written with preliminary header
        ai_diag_path = data_dir / "cases" / "task-001" / "ai-diagnosis.md"
        assert ai_diag_path.exists()
        content = ai_diag_path.read_text(encoding="utf-8")
        assert "PRELIMINARY AI DIAGNOSIS" in content
        assert "NOT CONFIRMED ROOT CAUSE" in content

    def test_retrieval_query_missing_uses_empty_context(
        self, default_config: AppLLMConfig, tmp_path: Path, monkeypatch
    ) -> None:
        """retrieval-query.json absent → graceful degradation with empty retrieval context."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        task_output = data_dir / "output" / "task-002"
        task_output.mkdir(parents=True)

        # Create evidence-pack.md only (no retrieval-query.json)
        (task_output / "evidence-pack.md").write_text(
            "# Evidence Pack\n\nLogs.", encoding="utf-8"
        )

        def mock_chat(messages, **kwargs):
            # Verify the prompt has "No retrieval query available" context
            content = messages[0]["content"]
            if "No retrieval query available" not in content:
                raise AssertionError(
                    "Expected empty retrieval context when retrieval-query.json is absent"
                )
            return "Diagnosis OK"

        import diagnose_tool.analyzer.diagnosis as diag_module

        class MockLLMClient:
            def __init__(self, config):
                pass

            def chat(self, messages, **kwargs):
                return mock_chat(messages)

        monkeypatch.setattr(diag_module, "LLMClient", MockLLMClient)

        orchestrator = DiagnosisOrchestrator(default_config, data_dir)
        case_id, diagnosis_text = orchestrator.run("task-002")
        assert case_id == "task-002"
        assert diagnosis_text == "Diagnosis OK"

    def test_llm_client_error_propagates(
        self, default_config: AppLLMConfig, tmp_path: Path, monkeypatch
    ) -> None:
        """LLM API error → LLMClientError propagates as DiagnosisError."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        task_output = data_dir / "output" / "task-003"
        task_output.mkdir(parents=True)
        (task_output / "evidence-pack.md").write_text("# Evidence", encoding="utf-8")

        import diagnose_tool.analyzer.diagnosis as diag_module

        class MockLLMClientThatFails:
            def __init__(self, config):
                pass

            def chat(self, messages, **kwargs):
                raise LLMClientError("LLM API returned 500")

        monkeypatch.setattr(diag_module, "LLMClient", MockLLMClientThatFails)

        orchestrator = DiagnosisOrchestrator(default_config, data_dir)
        with pytest.raises(LLMClientError, match="LLM API returned 500"):
            orchestrator.run("task-003")

    def test_ai_diagnosis_md_has_correct_format(
        self, default_config: AppLLMConfig, tmp_path: Path, monkeypatch
    ) -> None:
        """ai-diagnosis.md written with correct preliminary header and disclaimer."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        task_output = data_dir / "output" / "task-004"
        task_output.mkdir(parents=True)
        (task_output / "evidence-pack.md").write_text("# Evidence", encoding="utf-8")

        import diagnose_tool.analyzer.diagnosis as diag_module

        class MockLLMClient:
            def __init__(self, config):
                pass

            def chat(self, messages, **kwargs):
                return "Confirmed: database timeout."

        monkeypatch.setattr(diag_module, "LLMClient", MockLLMClient)

        orchestrator = DiagnosisOrchestrator(default_config, data_dir)
        orchestrator.run("task-004")

        ai_diag_path = data_dir / "cases" / "task-004" / "ai-diagnosis.md"
        content = ai_diag_path.read_text(encoding="utf-8")

        assert "PRELIMINARY AI DIAGNOSIS — NOT CONFIRMED ROOT CAUSE" in content
        assert "**NOT** the confirmed root cause" in content
        assert "Generated At" in content
        assert "Task ID" in content
        assert "task-004" in content
        assert "Source Evidence" in content
        assert "database timeout" in content