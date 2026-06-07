"""Unit tests for the TestSuggester service."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


def _load_suggester(tmp_path: Path):
    """Load test_suggester with a fake LLMClient and a tmp data_dir.

    The suggester module is loaded with importlib so we can patch
    ``LLMClient`` to a fake before the module imports it.
    """

    src_path = (
        Path(__file__).resolve().parent.parent
        / "diagnose_tool"
        / "analyzer"
        / "test_suggester.py"
    )
    spec = importlib.util.spec_from_file_location("_test_suggester_under_test", src_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # Patch LLMClient before module execution so the class reference resolves.
    fake_llm_module = MagicMock()
    sys.modules["diagnose_tool.core.llm_client"] = fake_llm_module
    spec.loader.exec_module(module)
    return module, fake_llm_module


def _seed_task(tmp_path: Path, task_id: str, *, with_diagnosis: bool = True, with_evidence: bool = True) -> None:
    task_dir = tmp_path / "output" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    if with_evidence:
        (task_dir / "evidence-pack.md").write_text("# evidence", encoding="utf-8")
    if with_diagnosis:
        case_dir = tmp_path / "cases" / task_id
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "ai-diagnosis.md").write_text("# diagnosis", encoding="utf-8")


def _make_suggester(tmp_path: Path, response_text: str = "# reproduction\n### Test: foo"):
    module, fake_llm_module = _load_suggester(tmp_path)
    fake_llm = MagicMock()
    fake_llm.chat.return_value = response_text
    suggester = module.TestSuggester(llm_config=MagicMock(), data_dir=tmp_path)
    suggester._llm = fake_llm  # type: ignore[attr-defined]
    return module, suggester, fake_llm


def test_run_returns_markdown(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    module, suggester, fake_llm = _make_suggester(tmp_path, response_text="## Reproduction\n### Test: x")

    result = suggester.run("t1")

    assert result == "## Reproduction\n### Test: x"
    assert fake_llm.chat.call_count == 1
    messages = fake_llm.chat.call_args.kwargs["messages"]
    assert messages[0]["role"] == "user"
    assert "# diagnosis" in messages[0]["content"]
    assert "# evidence" in messages[0]["content"]


def test_run_raises_when_diagnosis_missing(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1", with_diagnosis=False)
    module, suggester, _ = _make_suggester(tmp_path)

    with pytest.raises(module.DiagnosisNotFoundError):
        suggester.run("t1")


def test_run_raises_when_task_missing(tmp_path: Path) -> None:
    module, suggester, _ = _make_suggester(tmp_path)

    with pytest.raises(module.TaskNotFoundError):
        suggester.run("nonexistent")


def test_run_uses_evidence_when_present(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1", with_evidence=True)
    module, suggester, fake_llm = _make_suggester(tmp_path)

    suggester.run("t1")
    content = fake_llm.chat.call_args.kwargs["messages"][0]["content"]
    assert "# evidence" in content


def test_run_handles_missing_evidence_pack(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1", with_evidence=False)
    module, suggester, fake_llm = _make_suggester(tmp_path)

    result = suggester.run("t1")
    assert result  # non-empty
    content = fake_llm.chat.call_args.kwargs["messages"][0]["content"]
    # When evidence-pack.md is missing, the prompt still has the placeholder
    # substituted with an empty string, but the diagnosis block is still there.
    assert "# diagnosis" in content


def test_run_and_save_writes_file_and_overwrites(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    module, suggester, _ = _make_suggester(tmp_path, response_text="first")

    content, path = suggester.run_and_save("t1")
    assert content == "first"
    assert path == tmp_path / "output" / "t1" / "test-suggestions.md"
    assert path.read_text(encoding="utf-8") == "first"

    # Overwrite
    _, suggester2, _ = _make_suggester(tmp_path, response_text="second")
    content2, _ = suggester2.run_and_save("t1")
    assert content2 == "second"
    assert path.read_text(encoding="utf-8") == "second"


def test_load_template_uses_fallback_when_file_missing(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    module, suggester, _ = _make_suggester(tmp_path)

    template = suggester._load_template()  # type: ignore[attr-defined]
    # The fallback template names the same three sections (in backticks).
    assert "{diagnosis}" in template
    assert "{evidence_pack}" in template
    assert "Reproduction" in template
    assert "Verification" in template
    assert "Negative" in template


def test_load_template_reads_tracked_file(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    # Drop the template at the data_dir/docs location.
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "test-suggestion-template.md").write_text(
        "CUSTOM TEMPLATE\n{diagnosis}\n{evidence_pack}", encoding="utf-8"
    )
    module, suggester, _ = _make_suggester(tmp_path)

    template = suggester._load_template()  # type: ignore[attr-defined]
    assert template.startswith("CUSTOM TEMPLATE")
