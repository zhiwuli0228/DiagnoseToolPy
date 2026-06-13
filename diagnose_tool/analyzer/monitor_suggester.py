"""Monitor suggestion generation — pure Python, FastAPI-independent.

Given a completed diagnosis (``ai-diagnosis.md``) and the task's evidence
pack, calls the LLM with a focused prompt and returns a Markdown file
with metrics / alerts / dashboard monitoring suggestions.

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


TEMPLATE_FILENAME = "monitor-suggestion-template.md"


class DiagnosisNotFoundError(DiagnosisError):
    """Raised when ``data/cases/{task_id}/ai-diagnosis.md`` is missing."""


class MonitorSuggesterService:
    """Generate monitoring suggestions from a completed diagnosis."""

    __test__ = False  # tell pytest this is not a test class

    def __init__(self, llm_config: AppLLMConfig, data_dir: Path) -> None:
        self._llm = LLMClient(llm_config)
        self._data_dir = Path(data_dir)

    def run(self, task_id: str) -> str:
        """Return the LLM-generated monitor-suggestion markdown for ``task_id``."""

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
        """Run the suggester and write the result to ``monitor-suggestions.md``.

        Returns a ``(content, path)`` tuple. Existing files are overwritten.
        """

        content = self.run(task_id)
        output_path = self._data_dir / "output" / task_id / "monitor-suggestions.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return content, output_path

    def _load_template(self) -> str:
        """Load the prompt template from disk, falling back to the in-module default."""

        candidate = self._data_dir / "docs" / TEMPLATE_FILENAME
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
        return _FALLBACK_MONITOR_TEMPLATE


# Public alias used by callers (route, auto-hook, tests).
MonitorSuggester = MonitorSuggesterService


_FALLBACK_MONITOR_TEMPLATE = """\
You are a senior SRE / observability engineer. Given the diagnosis and the
evidence pack for a fault, produce a small, actionable set of monitoring
suggestions that an operations engineer can implement to detect, alert on,
and observe similar failures in the future.

The output MUST be valid Markdown with exactly three top-level sections
in this order: `## Metrics`, `## Alerts`, `## Dashboard`. Each section
MUST contain between two and four `### Monitor:` entries. Do not produce
any other section.

Each `### Monitor:` entry MUST follow this exact shape:

```
### Monitor: <short descriptive name>
- **Type**: <one of: prometheus | jmx | micrometer | log-based | grafana-alert | prometheus-alertmanager | cloudwatch | custom>
- **Target**: <metric name, PromQL query, JMX MBean, log pattern, or dashboard panel>
- **Condition**: <threshold, duration, and evaluation window>
- **Action**: <what to do when triggered: page, slack, ticket, dashboard link>
```

Guidelines:

- Metrics section: 2-4 key metrics to watch continuously (CPU, memory, thread
  pools, queue depths, error rates, latency percentiles).
- Alerts section: 2-4 alerting rules with specific thresholds derived from the
  diagnosis. Reference the exact error patterns, exception classes, or resource
  limits mentioned in the diagnosis.
- Dashboard section: 2-4 dashboard panels for visual observability. Suggest
  panel types (time series, heatmap, stat, table) and what to correlate.
- When the diagnosis identifies a specific class, method, configuration knob,
  or resource limit, the monitoring suggestion SHOULD reference it by name.
- Prefer standard observability tools (Prometheus, Grafana, Micrometer, JMX)
  over proprietary ones unless the evidence clearly indicates a different stack.
- Total 6-12 monitor suggestions.

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
