"""Test suggestion generation — pure Python, FastAPI-independent.

Given a completed diagnosis (`ai-diagnosis.md`) and the task's evidence
pack, calls the LLM with a focused prompt and returns a Markdown file
with reproduction / verification / negative test cases.

The diagnosis flow is unchanged: this module is a separate LLM call that
runs either as a manual endpoint or as a best-effort hook at the end
of ``DiagnosisOrchestrator.run()``. A failure here never affects the
diagnosis return value.
"""

from __future__ import annotations

import logging
from pathlib import Path

from diagnose_tool.analyzer.diagnosis import DiagnosisError, TaskNotFoundError
from diagnose_tool.core.llm_client import LLMClient
from diagnose_tool.core.llm_config import AppLLMConfig


logger = logging.getLogger(__name__)


TEMPLATE_FILENAME = "test-suggestion-template.md"


class DiagnosisNotFoundError(DiagnosisError):
    """Raised when ``data/cases/{task_id}/ai-diagnosis.md`` is missing."""


class TestSuggesterService:  # renamed from "TestSuggester" so pytest does not collect it
    """Generate executable test suggestions from a completed diagnosis."""

    __test__ = False  # tell pytest this is not a test class

    def __init__(self, llm_config: AppLLMConfig, data_dir: Path) -> None:
        self._llm = LLMClient(llm_config)
        self._data_dir = Path(data_dir)

    def run(self, task_id: str) -> str:
        """Return the LLM-generated test-suggestion markdown for ``task_id``."""

        task_output = self._data_dir / "output" / task_id
        if not task_output.exists():
            raise TaskNotFoundError(f"Task output directory not found: {task_output}")

        diagnosis_path = self._data_dir / "cases" / task_id / "ai-diagnosis.md"
        if not diagnosis_path.exists():
            raise DiagnosisNotFoundError(
                f"Diagnosis not found for task {task_id!r}; run diagnosis first. "
                f"Expected file: {diagnosis_path}"
            )

        diagnosis_text = diagnosis_path.read_text(encoding="utf-8")
        evidence_path = task_output / "evidence-pack.md"
        evidence_text = (
            evidence_path.read_text(encoding="utf-8") if evidence_path.exists() else ""
        )

        template = self._load_template()
        prompt = template.replace("{diagnosis}", diagnosis_text).replace(
            "{evidence_pack}", evidence_text
        )

        messages = [{"role": "user", "content": prompt}]
        return self._llm.chat(messages=messages)

    def run_and_save(self, task_id: str) -> tuple[str, Path]:
        """Run the suggester and write the result to ``test-suggestions.md``.

        Returns a ``(content, path)`` tuple. Existing files are overwritten.
        """

        content = self.run(task_id)
        output_path = self._data_dir / "output" / task_id / "test-suggestions.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return content, output_path

    def _load_template(self) -> str:
        """Load the prompt template from disk, falling back to the in-module default."""

        candidate = self._data_dir / "docs" / TEMPLATE_FILENAME
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
        return _FALLBACK_TEST_TEMPLATE


# Public alias used by callers (route, auto-hook, tests).
TestSuggester = TestSuggesterService


_FALLBACK_TEST_TEMPLATE = """\
You are a senior on-call engineer. Given the diagnosis and the evidence
pack for a fault, produce a small, executable set of test scenarios
that an on-call engineer can paste into a terminal or a test file to
verify or reproduce the failure.

The output MUST be valid Markdown with exactly three top-level sections
in this order: `## Reproduction`, `## Verification`, `## Negative /
Edge`. Each section MUST contain between one and four `### Test:`
entries. Do not produce any other section.

Each `### Test:` entry MUST follow this exact shape:

```
### Test: <short imperative name>
- **Type**: <one of: shell | python | junit | curl | go | other>
- **Goal**: <one sentence describing what the test proves>
- **Code**:
  <language-fenced code block, runnable as-is or with one obvious environment setup>
- **Expected**: <one sentence describing what success looks like>
```

Guidelines:

- Aim for 3-5 reproduction tests, 2-3 verification tests, and 1-2
  negative / edge tests. Total 6-10 tests.
- Use the smallest, most direct snippet that exercises the failure
  described in the diagnosis. Do not invent new dependencies.
- Prefer running against the same evidence the diagnosis cites (file
  paths, log lines, exception classes) so the test is reproducible
  without re-collecting data.
- When the diagnosis identifies a specific class, method, or
  configuration knob, the test SHOULD reference it by name.

Output ONLY the Markdown. No preamble, no closing remarks, no fenced
block around the whole output.

---

# Diagnosis

```
{diagnosis}
```

# Evidence Pack

```
{evidence_pack}
```
"""
