# Monitor Suggestion Generation Design

## Purpose

Complete the last missing piece of V0.3 (AI Diagnosis Integration) by adding monitoring suggestion generation. This follows the exact same architecture as the existing test suggestion generation (`test_suggester.py`).

## Background

V0.3 roadmap includes: one-click AI diagnosis, save result, compare with human root cause, generate bugfix prompt, generate test suggestions, generate monitoring suggestions. All items are done except monitoring suggestions.

The test suggestion pattern is proven and well-structured:
- Standalone backend service (FastAPI-independent)
- Prompt template with `{diagnosis}` + `{evidence_pack}` placeholders
- Auto-hook in `DiagnosisOrchestrator.run()`
- POST endpoint for manual generation
- GET endpoint for reading persisted artifact
- Frontend panel with state-machine markdown parser + Ant Design cards

## Architecture

Mirror the test suggestion pattern component-for-component:

| Component | Test Suggestion (existing) | Monitor Suggestion (new) |
|---|---|---|
| Backend service | `diagnose_tool/analyzer/test_suggester.py` | `diagnose_tool/analyzer/monitor_suggester.py` |
| Template | `docs/05-domain/test-suggestion-template.md` | `docs/05-domain/monitor-suggestion-template.md` |
| Fallback template | `_FALLBACK_TEST_TEMPLATE` in module | `_FALLBACK_MONITOR_TEMPLATE` in module |
| Output file | `data/output/{task_id}/test-suggestions.md` | `data/output/{task_id}/monitor-suggestions.md` |
| Auto-hook flag | `_auto_generate_tests` | `_auto_generate_monitors` |
| POST endpoint | `POST /api/diagnosis/test-suggestions` | `POST /api/diagnosis/monitor-suggestions` |
| GET endpoint | `GET /api/source/task/{task_id}/test-suggestions` | `GET /api/source/task/{task_id}/monitor-suggestions` |
| Frontend panel | `TestSuggestionsPanel.tsx` | `MonitorSuggestionsPanel.tsx` |
| Tab label | "测试建议" | "监控建议" |

## LLM Output Structure

The template instructs the LLM to produce Markdown with exactly three top-level sections, each containing 2-4 `### Monitor:` entries:

```markdown
## Metrics
### Monitor: <short descriptive name>
- **Type**: <prometheus | jmx | micrometer | log-based | custom>
- **Target**: <metric name, query, or path>
- **Condition**: <threshold and duration>
- **Action**: <what to do when triggered>

## Alerts
### Monitor: <short descriptive name>
- **Type**: <prometheus-alertmanager | grafana-alert | cloudwatch | custom>
- **Target**: <alert rule or query>
- **Condition**: <threshold and evaluation window>
- **Action**: <notification channel and response>

## Dashboard
### Monitor: <short descriptive name>
- **Type**: <grafana | kibana | datadog | custom>
- **Target**: <panel type and data source>
- **Condition**: <visualization config>
- **Action**: <drill-down link or related alert>
```

Total: 6-12 monitor suggestions. The LLM should reference specific classes, methods, configs, and exception patterns from the diagnosis.

## Backend Service: `monitor_suggester.py`

Follow `test_suggester.py` exactly:

- Class: `MonitorSuggesterService` with `__test__ = False`
- Alias: `MonitorSuggester = MonitorSuggesterService`
- Constructor: `__init__(self, llm_config: AppLLMConfig, data_dir: Path)`
- `run(task_id) -> str`: validate task dir, read `ai-diagnosis.md`, read `evidence-pack.md`, load template, substitute placeholders, call LLM
- `run_and_save(task_id) -> tuple[str, Path]`: call `run()`, write to `data/output/{task_id}/monitor-suggestions.md`
- `_load_template()`: try disk first, fall back to `_FALLBACK_MONITOR_TEMPLATE`
- Error imports: `DiagnosisError`, `TaskNotFoundError` from `diagnosis.py`; define `DiagnosisNotFoundError` locally

## Auto-hook in Orchestrator

Append after the existing test hook in `DiagnosisOrchestrator.run()` (after line 146 of `diagnosis.py`):

```python
if getattr(self, "_auto_generate_monitors", True):
    try:
        from diagnose_tool.analyzer.monitor_suggester import MonitorSuggester
        MonitorSuggester(self._llm, self._data_dir).run_and_save(task_id)
    except Exception as exc:
        logger.warning(
            "monitor suggestion auto-generation failed for %s: %s",
            task_id,
            exc,
        )
```

Two hooks are independent. Either can fail without affecting the other or the diagnosis result.

## API Endpoints

### POST: Manual Generation

In `routes_diagnosis.py`:

- Model: `MonitorSuggestionsRequest(task_id: str)`
- Response: `MonitorSuggestionsResponse(content: str, path: str)`
- Route: `POST /api/diagnosis/monitor-suggestions`
- Error mapping: same as test suggestions (404 for missing diagnosis/task, 502 for LLM error, 500 for other)

### GET: Read Persisted Artifact

In `routes_source.py`:

- Route: `GET /api/source/task/{task_id}/monitor-suggestions`
- Response: `{ "content": string | null }`
- Delegates to `task_reader.read_monitor_suggestions(task_id)`

### task_reader Addition

Add `read_monitor_suggestions(task_id)` alongside `read_test_suggestions`, using `_read_text` helper with `_MONITOR_SUGGESTIONS_FILENAME = "monitor-suggestions.md"`.

## Frontend

### MonitorSuggestionsPanel.tsx

Follow `TestSuggestionsPanel.tsx` pattern:

- Fetch via `getTaskMonitorSuggestions(taskId)` from `taskApi.ts`
- Parse with `parseMonitorSuggestions(content)` state machine:
  - Split on `## ` headings for sections (Metrics, Alerts, Dashboard)
  - Split on `### Monitor:` for individual entries
  - Extract: name, type, target, condition, action
- Render: Ant Design `Card` per section, inner `Card` per monitor entry
  - Title with monitor name + `Tag` for type
  - Target, Condition, Action as labeled text
  - "Copy" button for the target query/metric

### Frontend API Layer

- `diagnosisApi.ts`: add `generateMonitorSuggestions(taskId)` -> `POST /api/diagnosis/monitor-suggestions`
- `taskApi.ts`: add `getTaskMonitorSuggestions(taskId)` -> `GET /api/source/task/{taskId}/monitor-suggestions`

### TaskDetailPage Integration

- Add 6th tab "监控建议" (key: `monitorSuggestions`)
- Add `monitorSuggestionsKey` state for refresh control
- Add "Generate monitor suggestions" button in Actions tab
- Tab renders `<MonitorSuggestionsPanel taskId={taskId} refreshKey={monitorSuggestionsKey} />`

## Data Flow

```
User clicks "Generate monitor suggestions" in Actions tab
  → POST /api/diagnosis/monitor-suggestions { task_id }
  → MonitorSuggester.run_and_save(task_id)
  → reads ai-diagnosis.md + evidence-pack.md
  → calls LLM with monitor template
  → writes data/output/{task_id}/monitor-suggestions.md
  → returns { content, path }
  → frontend increments refreshKey
  → MonitorSuggestionsPanel re-fetches via GET endpoint
  → parses markdown, renders cards
```

Auto-hook path (same flow, triggered at end of diagnosis):
```
DiagnosisOrchestrator.run() completes ai-diagnosis.md write
  → test hook runs (existing)
  → monitor hook runs (new)
  → both fire-and-forget, failures logged as warning
```

## Testing

- Unit tests for `MonitorSuggesterService`: mock LLM, verify template loading, verify file write
- Unit tests for duplicate error handling (missing task, missing diagnosis)
- API tests for POST endpoint: happy path, missing diagnosis (404), LLM failure (502)
- API tests for GET endpoint: returns content when file exists, returns null when missing
- Frontend: parser unit tests for `parseMonitorSuggestions` with sample markdown
