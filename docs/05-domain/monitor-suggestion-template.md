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
