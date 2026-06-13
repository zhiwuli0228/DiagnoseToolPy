# Monitor Suggestion Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add monitoring suggestion generation to complete V0.3, mirroring the existing test suggestion pattern.

**Architecture:** New `MonitorSuggesterService` in `diagnose_tool/analyzer/monitor_suggester.py` reads `ai-diagnosis.md` + `evidence-pack.md`, calls LLM with a monitoring-focused prompt template, writes `monitor-suggestions.md`. Auto-hook in orchestrator, POST+GET API endpoints, frontend panel with 6th tab.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, React 18, TypeScript, Ant Design 5

---

## File Map

| Action | File | Purpose |
|--------|------|---------|
| Create | `diagnose_tool/analyzer/monitor_suggester.py` | Backend service |
| Create | `docs/05-domain/monitor-suggestion-template.md` | Prompt template |
| Create | `tests/test_monitor_suggester.py` | Backend unit tests |
| Modify | `diagnose_tool/analyzer/diagnosis.py:146-148` | Add auto-hook |
| Modify | `diagnose_tool/analyzer/task_reader.py:30,152-155` | Add reader function |
| Modify | `diagnose_tool/api/routes_diagnosis.py:18-21,680` | Add POST endpoint |
| Modify | `diagnose_tool/api/routes_source.py:310-323` | Add GET endpoint |
| Create | `frontend/src/components/MonitorSuggestionsPanel.tsx` | Frontend panel |
| Modify | `frontend/src/api/diagnosisApi.ts:162-178` | Add generation API |
| Modify | `frontend/src/api/taskApi.ts:51-56` | Add read API |
| Modify | `frontend/src/pages/TaskDetailPage.tsx` | Add tab + button |

---

### Task 1: Backend Service — `monitor_suggester.py`

**Files:**
- Create: `diagnose_tool/analyzer/monitor_suggester.py`
- Create: `tests/test_monitor_suggester.py`

- [ ] **Step 1: Write unit tests for MonitorSuggesterService**

```python
# tests/test_monitor_suggester.py
"""Unit tests for the MonitorSuggester service."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _load_suggester(tmp_path: Path):
    """Load monitor_suggester with a fake LLMClient and a tmp data_dir."""
    src_path = (
        Path(__file__).resolve().parent.parent
        / "diagnose_tool"
        / "analyzer"
        / "monitor_suggester.py"
    )
    spec = importlib.util.spec_from_file_location("_monitor_suggester_under_test", src_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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


def _make_suggester(tmp_path: Path, response_text: str = "## Metrics\n### Monitor: heap usage"):
    module, fake_llm_module = _load_suggester(tmp_path)
    fake_llm = MagicMock()
    fake_llm.chat.return_value = response_text
    suggester = module.MonitorSuggester(llm_config=MagicMock(), data_dir=tmp_path)
    suggester._llm = fake_llm
    return module, suggester, fake_llm


def test_run_returns_markdown(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    module, suggester, fake_llm = _make_suggester(tmp_path, response_text="## Metrics\n### Monitor: x")

    result = suggester.run("t1")

    assert result == "## Metrics\n### Monitor: x"
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
    assert result
    content = fake_llm.chat.call_args.kwargs["messages"][0]["content"]
    assert "# diagnosis" in content


def test_run_and_save_writes_file_and_overwrites(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    module, suggester, _ = _make_suggester(tmp_path, response_text="first")

    content, path = suggester.run_and_save("t1")
    assert content == "first"
    assert path == tmp_path / "output" / "t1" / "monitor-suggestions.md"
    assert path.read_text(encoding="utf-8") == "first"

    _, suggester2, _ = _make_suggester(tmp_path, response_text="second")
    content2, _ = suggester2.run_and_save("t1")
    assert content2 == "second"
    assert path.read_text(encoding="utf-8") == "second"


def test_load_template_uses_fallback_when_file_missing(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    module, suggester, _ = _make_suggester(tmp_path)

    template = suggester._load_template()
    assert "{diagnosis}" in template
    assert "{evidence_pack}" in template
    assert "Metrics" in template
    assert "Alerts" in template
    assert "Dashboard" in template


def test_load_template_reads_tracked_file(tmp_path: Path) -> None:
    _seed_task(tmp_path, "t1")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "monitor-suggestion-template.md").write_text(
        "CUSTOM TEMPLATE\n{diagnosis}\n{evidence_pack}", encoding="utf-8"
    )
    module, suggester, _ = _make_suggester(tmp_path)

    template = suggester._load_template()
    assert template.startswith("CUSTOM TEMPLATE")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run pytest tests/test_monitor_suggester.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'diagnose_tool.analyzer.monitor_suggester'`

- [ ] **Step 3: Create the prompt template**

```markdown
# docs/05-domain/monitor-suggestion-template.md
# Monitor Suggestion Prompt Template

This template is consumed by `diagnose_tool/analyzer/monitor_suggester.py`.
The two placeholders below are filled in at call time:

- `{diagnosis}` — the full text of `data/cases/{task_id}/ai-diagnosis.md`
- `{evidence_pack}` — the full text of `data/output/{task_id}/evidence-pack.md`

---

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
```

- [ ] **Step 4: Create the backend service**

```python
# diagnose_tool/analyzer/monitor_suggester.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run pytest tests/test_monitor_suggester.py -v`
Expected: All 8 tests PASS

- [ ] **Step 6: Run full test suite to check for regressions**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run pytest`
Expected: All existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add diagnose_tool/analyzer/monitor_suggester.py docs/05-domain/monitor-suggestion-template.md tests/test_monitor_suggester.py
git commit -m "feat(analyzer): add monitor suggestion generation service and template"
```

---

### Task 2: Auto-hook + Task Reader

**Files:**
- Modify: `diagnose_tool/analyzer/diagnosis.py:146-148`
- Modify: `diagnose_tool/analyzer/task_reader.py:30,152-155`

- [ ] **Step 1: Add auto-hook in DiagnosisOrchestrator.run()**

In `diagnose_tool/analyzer/diagnosis.py`, after the existing test-suggestion auto-hook (after line 146), add:

```python
        if getattr(self, "_auto_generate_monitors", True):
            try:
                from diagnose_tool.analyzer.monitor_suggester import MonitorSuggester
                MonitorSuggester(self._llm, self._data_dir).run_and_save(task_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "monitor suggestion auto-generation failed for %s: %s",
                    task_id,
                    exc,
                )
```

- [ ] **Step 2: Add `read_monitor_suggestions` to task_reader.py**

In `diagnose_tool/analyzer/task_reader.py`, add the filename constant after line 30:

```python
_MONITOR_SUGGESTIONS_FILENAME = "monitor-suggestions.md"
```

Add the reader function after `read_test_suggestions` (after line 155):

```python
def read_monitor_suggestions(task_id: str) -> str | None:
    """Return the text of ``monitor-suggestions.md`` or ``None`` if missing."""

    return _read_text(task_id, _MONITOR_SUGGESTIONS_FILENAME)
```

- [ ] **Step 3: Run tests to verify no regressions**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run pytest tests/test_monitor_suggester.py tests/test_test_suggester.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add diagnose_tool/analyzer/diagnosis.py diagnose_tool/analyzer/task_reader.py
git commit -m "feat(analyzer): add monitor suggestion auto-hook and task reader"
```

---

### Task 3: API Endpoints — POST + GET

**Files:**
- Modify: `diagnose_tool/api/routes_diagnosis.py:18-21,680`
- Modify: `diagnose_tool/api/routes_source.py:310-323`

- [ ] **Step 1: Add POST endpoint in routes_diagnosis.py**

Add import after line 21:

```python
from diagnose_tool.analyzer.monitor_suggester import (
    MonitorSuggester,
    DiagnosisNotFoundError as MonitorDiagnosisNotFoundError,
)
```

Add the endpoint after the test-suggestions endpoint (after line 680):

```python
# ---------------------------------------------------------------------------
# Monitor suggestion generation
#
# Generates monitoring suggestions (metrics / alerts / dashboard) from a
# completed diagnosis. Writes the result to
# data/output/{task_id}/monitor-suggestions.md.
# ---------------------------------------------------------------------------


class MonitorSuggestionsRequest(BaseModel):
    task_id: str = Field(min_length=1)


class MonitorSuggestionsResponse(BaseModel):
    content: str
    path: str


@router.post("/diagnosis/monitor-suggestions", response_model=MonitorSuggestionsResponse)
def generate_monitor_suggestions(request: MonitorSuggestionsRequest) -> MonitorSuggestionsResponse:
    """Generate monitoring suggestions for ``request.task_id``.

    Reads the existing ``ai-diagnosis.md`` and ``evidence-pack.md`` from
    disk, calls the LLM, and writes the result to
    ``data/output/{task_id}/monitor-suggestions.md``. A failure is a 4xx
    (missing diagnosis / task) or 5xx (LLM error).
    """

    llm_config = _get_llm_config()
    if not llm_config.enabled:
        raise HTTPException(
            status_code=503,
            detail="LLM is not enabled. Set llm.enabled to true in config/app.yaml",
        )

    suggester = MonitorSuggester(llm_config, llm_config.data_dir)
    try:
        content, output_path = suggester.run_and_save(request.task_id)
    except MonitorDiagnosisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LLMClientError as exc:
        logger.warning("LLM API error during monitor suggestion generation: %s", exc)
        raise HTTPException(status_code=502, detail="LLM call failed") from exc
    except DiagnosisError as exc:
        logger.error("Monitor suggestion generation error: %s", exc)
        raise HTTPException(status_code=500, detail="Monitor suggestion generation failed") from exc

    return MonitorSuggestionsResponse(content=content, path=str(output_path))
```

- [ ] **Step 2: Add GET endpoint in routes_source.py**

Add the endpoint after the test-suggestions GET endpoint (after line 323):

```python
@router.get("/task/{task_id}/monitor-suggestions")
def get_task_monitor_suggestions(task_id: str) -> dict[str, object]:
    """Return the text of ``monitor-suggestions.md`` for ``task_id`` or ``null``.

    The file is produced by the ``MonitorSuggester`` (either the auto-hook
    at the end of ``DiagnosisOrchestrator.run()`` or the manual
    ``POST /api/diagnosis/monitor-suggestions`` endpoint).
    """

    try:
        content = task_reader.read_monitor_suggestions(task_id)
    except task_reader.InvalidTaskIdError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"content": content}
```

- [ ] **Step 3: Run backend tests**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run pytest tests/test_monitor_suggester.py tests/test_diagnosis_api.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add diagnose_tool/api/routes_diagnosis.py diagnose_tool/api/routes_source.py
git commit -m "feat(api): add monitor suggestion POST and GET endpoints"
```

---

### Task 4: Frontend API Layer

**Files:**
- Modify: `frontend/src/api/diagnosisApi.ts`
- Modify: `frontend/src/api/taskApi.ts`

- [ ] **Step 1: Add `generateMonitorSuggestions` to diagnosisApi.ts**

Append after the `generateTestSuggestions` function (after line 178):

```typescript
export interface MonitorSuggestionsResponse {
  content: string;
  path: string;
}

export async function generateMonitorSuggestions(taskId: string): Promise<MonitorSuggestionsResponse> {
  const response = await fetch('/api/diagnosis/monitor-suggestions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}
```

- [ ] **Step 2: Add `getTaskMonitorSuggestions` to taskApi.ts**

Append after the `getTaskTestSuggestions` function (after line 56):

```typescript
export async function getTaskMonitorSuggestions(taskId: string): Promise<string | null> {
  const response = await api.get<TaskTextPayload>(
    `/source/task/${encodeURIComponent(taskId)}/monitor-suggestions`,
  );
  return response.data.content;
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy/frontend && npm run build`
Expected: Build succeeds with no type errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/diagnosisApi.ts frontend/src/api/taskApi.ts
git commit -m "feat(frontend/api): add monitor suggestion generation and read functions"
```

---

### Task 5: Frontend Panel — `MonitorSuggestionsPanel.tsx`

**Files:**
- Create: `frontend/src/components/MonitorSuggestionsPanel.tsx`

- [ ] **Step 1: Create the MonitorSuggestionsPanel component**

```tsx
// frontend/src/components/MonitorSuggestionsPanel.tsx
import { useEffect, useState } from 'react';
import { Card, Alert, Spin, Tag, Space, Button, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { getTaskMonitorSuggestions } from '../api/taskApi';

interface MonitorSuggestionsPanelProps {
  taskId: string;
  refreshKey?: number;
}

interface ParsedMonitor {
  name: string;
  type: string | null;
  target: string | null;
  condition: string | null;
  action: string | null;
}

function parseMonitorSuggestions(content: string): { section: string; monitors: ParsedMonitor[] }[] {
  if (!content.trim()) return [];
  const lines = content.split('\n');
  const sections: { section: string; monitors: ParsedMonitor[] }[] = [];
  let currentSection = '';
  let currentMonitor: ParsedMonitor | null = null;

  const flush = () => {
    if (currentMonitor) {
      sections[sections.length - 1].monitors.push(currentMonitor);
    }
    currentMonitor = null;
  };

  for (const line of lines) {
    const sectionMatch = line.match(/^##\s+(.+)$/);
    if (sectionMatch) {
      flush();
      currentSection = sectionMatch[1].trim();
      sections.push({ section: currentSection, monitors: [] });
      continue;
    }
    const monitorMatch = line.match(/^###\s+Monitor:\s*(.+)$/);
    if (monitorMatch) {
      flush();
      currentMonitor = { name: monitorMatch[1].trim(), type: null, target: null, condition: null, action: null };
      continue;
    }
    if (!currentMonitor) continue;

    const typeMatch = line.match(/^-\s*\*\*Type\*\*:\s*(.+)$/);
    if (typeMatch) { currentMonitor.type = typeMatch[1].trim(); continue; }
    const targetMatch = line.match(/^-\s*\*\*Target\*\*:\s*(.+)$/);
    if (targetMatch) { currentMonitor.target = targetMatch[1].trim(); continue; }
    const conditionMatch = line.match(/^-\s*\*\*Condition\*\*:\s*(.+)$/);
    if (conditionMatch) { currentMonitor.condition = conditionMatch[1].trim(); continue; }
    const actionMatch = line.match(/^-\s*\*\*Action\*\*:\s*(.+)$/);
    if (actionMatch) { currentMonitor.action = actionMatch[1].trim(); continue; }
  }
  flush();
  return sections;
}

function copyToClipboard(text: string) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  return Promise.reject(new Error('Clipboard API unavailable'));
}

function MonitorSuggestionsPanel({ taskId, refreshKey = 0 }: MonitorSuggestionsPanelProps) {
  const { t } = useTranslation();
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTaskMonitorSuggestions(taskId)
      .then(data => {
        if (!cancelled) setContent(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const axiosError = err as { message?: string };
        setError(axiosError.message || t('taskDetail.monitorSuggestions.loadError', 'Failed to load monitor suggestions'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [taskId, refreshKey]);

  if (loading) {
    return <Spin />;
  }
  if (error) {
    return <Alert type="error" message={error} />;
  }
  if (!content) {
    return (
      <Alert
        type="info"
        showIcon
        message={t('taskDetail.monitorSuggestions.notProduced', 'No monitor suggestions yet. Use the Generate button in Actions to produce them.')}
      />
    );
  }

  const sections = parseMonitorSuggestions(content);
  if (sections.length === 0 || sections.every(s => s.monitors.length === 0)) {
    return (
      <Alert
        type="warning"
        showIcon
        message={t('taskDetail.monitorSuggestions.empty', 'The monitor-suggestions file is empty or could not be parsed.')}
      />
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {sections.map(section => (
        <Card key={section.section} size="small" title={section.section}>
          {section.monitors.length === 0 ? (
            <span style={{ color: '#999' }}>{t('taskDetail.monitorSuggestions.emptySection', 'No monitors in this section.')}</span>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {section.monitors.map((monitor, idx) => (
                <Card
                  key={`${section.section}-${idx}`}
                  size="small"
                  type="inner"
                  title={
                    <Space>
                      <span>{monitor.name}</span>
                      {monitor.type && <Tag color="blue">{monitor.type}</Tag>}
                    </Space>
                  }
                  extra={
                    monitor.target && (
                      <Button
                        size="small"
                        onClick={() => {
                          copyToClipboard(monitor.target!).then(
                            () => message.success(t('taskDetail.monitorSuggestions.copied', 'Copied')),
                            () => message.error(t('taskDetail.monitorSuggestions.copyFailed', 'Copy failed')),
                          );
                        }}
                        data-testid="copy-monitor-target"
                      >
                        {t('taskDetail.monitorSuggestions.copy', 'Copy')}
                      </Button>
                    )
                  }
                >
                  {monitor.target && (
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>{t('taskDetail.monitorSuggestions.target', 'Target')}:</strong>{' '}
                      <code>{monitor.target}</code>
                    </p>
                  )}
                  {monitor.condition && (
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>{t('taskDetail.monitorSuggestions.condition', 'Condition')}:</strong> {monitor.condition}
                    </p>
                  )}
                  {monitor.action && (
                    <p style={{ margin: '8px 0 0 0', color: '#555' }}>
                      <strong>{t('taskDetail.monitorSuggestions.action', 'Action')}:</strong> {monitor.action}
                    </p>
                  )}
                </Card>
              ))}
            </Space>
          )}
        </Card>
      ))}
    </Space>
  );
}

export default MonitorSuggestionsPanel;
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/MonitorSuggestionsPanel.tsx
git commit -m "feat(frontend): add MonitorSuggestionsPanel component"
```

---

### Task 6: TaskDetailPage Integration — 6th Tab + Actions Button

**Files:**
- Modify: `frontend/src/pages/TaskDetailPage.tsx`

- [ ] **Step 1: Add imports**

Add to the imports section (after the `TestSuggestionsPanel` import):

```typescript
import { generateMonitorSuggestions } from '../api/diagnosisApi';
import MonitorSuggestionsPanel from '../components/MonitorSuggestionsPanel';
```

Add `generateMonitorSuggestions` to the existing `diagnosisApi` import if it exists already, or add a new import line.

- [ ] **Step 2: Add state variables**

After the existing `testSuggestionsKey` state (line 59), add:

```typescript
const [generatingMonitors, setGeneratingMonitors] = useState(false);
const [monitorSuggestionsKey, setMonitorSuggestionsKey] = useState(0);
```

- [ ] **Step 3: Add generate handler**

After the existing `generateSuggestions` handler (after line 73), add:

```typescript
const generateMonitors = async () => {
    setGeneratingMonitors(true);
    try {
      await generateMonitorSuggestions(taskId);
      message.success(t('taskDetail.actions.generateMonitors.success', 'Monitor suggestions generated'));
      setMonitorSuggestionsKey(k => k + 1);
    } catch (err: unknown) {
      const errObj = err as { message?: string };
      message.error(errObj.message || t('taskDetail.actions.generateMonitors.failed', 'Failed to generate monitor suggestions'));
    } finally {
      setGeneratingMonitors(false);
    }
  };
```

- [ ] **Step 4: Add the 6th tab**

In the tabs array, insert a new tab before the `actions` tab:

```typescript
{
    key: 'monitorSuggestions',
    label: t('taskDetail.tabs.monitorSuggestions', 'Monitor Suggestions'),
    children: (
        <MonitorSuggestionsPanel
            taskId={taskId}
            refreshKey={monitorSuggestionsKey}
        />
    ),
},
```

- [ ] **Step 5: Add generate button in Actions tab**

In the Actions tab's content, after the "Generate test suggestions" button, add:

```typescript
<Button
    onClick={generateMonitors}
    loading={generatingMonitors}
    data-testid="action-generate-monitors"
>
    {t('taskDetail.actions.generateMonitors.label', 'Generate monitor suggestions')}
</Button>
```

- [ ] **Step 6: Verify TypeScript compiles**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 7: Run frontend tests**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy/frontend && npm test`
Expected: All tests pass

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/TaskDetailPage.tsx
git commit -m "feat(frontend): add monitor suggestions tab and generate button to TaskDetailPage"
```

---

### Task 7: Final Verification

- [ ] **Step 1: Run full backend test suite**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run pytest`
Expected: All tests pass, no regressions

- [ ] **Step 2: Run frontend build + tests**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy/frontend && npm run build && npm test`
Expected: Build succeeds, all tests pass

- [ ] **Step 3: Run lint**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run ruff check .`
Expected: No errors

- [ ] **Step 4: Start dev server and verify in browser**

Run: `cd E:/009workspace/claudecode/DiagnoseToolPy && uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload`
Then: `cd E:/009workspace/claudecode/DiagnoseToolPy/frontend && npm run dev`

Verify:
1. Navigate to a completed task's detail page
2. Confirm 6 tabs are visible (Overview, Evidence & Threads, Key Logs & Case Draft, Test Suggestions, Monitor Suggestions, Actions)
3. Click "Monitor Suggestions" tab — should show "No monitor suggestions yet" info alert
4. Go to Actions tab, click "Generate monitor suggestions" — should call the API (will fail without LLM config, but the button and flow should work)
5. Check browser console for no errors

- [ ] **Step 5: Final commit with all changes**

```bash
git status
# Verify only expected files are modified
```
