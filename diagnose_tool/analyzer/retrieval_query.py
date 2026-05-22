"""Retrieval query generation."""

from __future__ import annotations

import json
import re

from diagnose_tool.analyzer.classifier import ClassificationResult
from diagnose_tool.analyzer.header_parser import ParsedLogRecord
from diagnose_tool.analyzer.output_context import OutputContext

# Pattern to match stack trace lines like "at com.demo.Class.method(File.java:123)"
STACK_LINE_RE = re.compile(r"\bat\s+([\w.]+\.[\w<>]+)\([\w]+\.java:\d+\)")
# Pattern to match "Caused by: com.example.SomeException"
CAUSED_BY_RE = re.compile(r"Caused by:\s*([\w.]+\.(?:Exception|Error|RuntimeException))")
# Pattern to match exception class names in log messages (e.g. "JedisConnectionException")
EXCEPTION_CLASS_RE = re.compile(r"\b([A-Z]\w*(?:Exception|Error|RuntimeException))\b")


def generate_retrieval_query(
    output_context: OutputContext,
    classifications: list[ClassificationResult],
    records: list[ParsedLogRecord],
) -> None:
    output_context.ensure_directories()

    query = _build_retrieval_query(output_context, classifications, records)

    (output_context.output_dir() / "retrieval-query.json").write_text(
        json.dumps(query, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _build_retrieval_query(
    output_context: OutputContext,
    classifications: list[ClassificationResult],
    records: list[ParsedLogRecord],
) -> dict:
    components: set[str] = set()
    fault_modes: set[str] = set()
    exception_classes: set[str] = set()
    keywords: set[str] = set()
    stack_symbols: set[str] = set()
    log_templates: set[str] = set()

    for c in classifications:
        if c.category != "unknown":
            fault_modes.add(c.category)
            if c.rule:
                for kw in c.rule.keywords:
                    keywords.add(kw)

    for record in records:
        if record.module:
            components.add(record.module)
        if record.logger:
            components.add(record.logger)
        if record.message:
            msg = record.message.strip()
            if 5 < len(msg) < 100:
                log_templates.add(msg[:100])

        # Extract exception classes and stack symbols from raw log lines
        raw = record.raw
        if record.level in ("ERROR", "WARN", "WARNING"):
            for match in CAUSED_BY_RE.finditer(raw):
                exception_classes.add(match.group(1))
            for match in EXCEPTION_CLASS_RE.finditer(raw):
                exception_classes.add(match.group(1))
            for match in STACK_LINE_RE.finditer(raw):
                stack_symbols.add(match.group(1))

    summary_parts = []
    if fault_modes:
        summary_parts.append(f"{', '.join(sorted(fault_modes))}类型的故障")
    if components:
        summary_parts.append(f"涉及组件: {', '.join(sorted(components)[:3])}")

    summary = "; ".join(summary_parts) if summary_parts else "日志分析完成"

    return {
        "task_id": output_context.task_id,
        "summary": summary,
        "components": sorted(components)[:10],
        "fault_modes": sorted(fault_modes),
        "exception_classes": sorted(exception_classes)[:10],
        "keywords": sorted(keywords)[:20],
        "stack_symbols": sorted(stack_symbols)[:20],
        "log_templates": sorted(log_templates)[:10],
    }
