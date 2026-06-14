"""Tests for evidence pack generation."""

from __future__ import annotations

import json
from pathlib import Path


from diagnose_tool.analyzer.classifier import ClassificationResult, ClassificationRule, UNKNOWN_RESULT
from diagnose_tool.analyzer.evidence import (
    MAX_SAMPLES_PER_CATEGORY,
    generate_evidence_pack,
    generate_key_logs,
    generate_raw_samples,
    _build_classification_stats,
    _get_top_exceptions,
)
from diagnose_tool.analyzer.header_parser import ParsedLogRecord, ParseStatus
from diagnose_tool.analyzer.output_context import OutputContext
from diagnose_tool.analyzer.thread_stack_parser import (
    ThreadDumpResult,
    ThreadFrame,
    LockHint,
    ParseStatus as ThreadParseStatus,
)


class TestEvidencePack:
    def test_evidence_pack_contains_required_sections(self, tmp_path: Path):
        ctx = OutputContext(
            task_id="test-task",
            source_path="/data/logs",
            created_at="2026-05-17 10:00:00",
            total_files=5,
            total_bytes=1024,
            error_count=3,
            warn_count=10,
        )
        records = [
            ParsedLogRecord(
                timestamp="2026-05-17 10:01:01",
                level="ERROR",
                module="test",
                thread="t1",
                logger="Logger",
                message="error1",
                raw="2026-05-17 10:01:01 ERROR test",
                file_path="/data/logs/app.log",
                line_no=1,
                parse_status=ParseStatus.FULL,
            )
        ]
        rule = ClassificationRule(
            category="null-pointer",
            display_name="NullPointer",
            severity="ERROR",
            keywords=["NullPointer"],
        )
        classifications = [
            ClassificationResult(
                category="null-pointer",
                display_name="NullPointer",
                severity="ERROR",
                matched_keyword="NullPointer",
                rule=rule,
            )
        ]
        generate_evidence_pack(ctx, records, classifications, 3, 10, [])

        content = (ctx.output_dir() / "evidence-pack.md").read_text(encoding="utf-8")
        assert "## 1. 基本信息" in content
        assert "## 2. 异常分类统计" in content
        assert "## 3. 异常时间线" in content
        assert "## 4. 关键日志特征" in content
        assert "## 5. Top 关键异常样例" in content

    def test_evidence_pack_stats_table_has_rows(self, tmp_path: Path):
        ctx = OutputContext(
            task_id="test-task",
            source_path="/data/logs",
            created_at="2026-05-17 10:00:00",
            error_count=3,
            warn_count=10,
        )
        rule = ClassificationRule(
            category="null-pointer",
            display_name="NullPointer",
            severity="ERROR",
            keywords=["NullPointer"],
        )
        classifications = [
            ClassificationResult(
                category="null-pointer",
                display_name="NullPointer",
                severity="ERROR",
                matched_keyword="NullPointer",
                rule=rule,
            )
        ]
        generate_evidence_pack(ctx, [], classifications, 3, 10, [])
        content = (ctx.output_dir() / "evidence-pack.md").read_text(encoding="utf-8")
        assert "null-pointer" in content


class TestKeyLogs:
    def test_key_logs_contains_labeled_excerpts(self, tmp_path: Path):
        ctx = OutputContext(
            task_id="test-task",
            source_path="/data/logs",
            created_at="2026-05-17 10:00:00",
        )
        records = [
            ParsedLogRecord(
                timestamp="2026-05-17 10:01:01",
                level="ERROR",
                module="test",
                thread="t1",
                logger="Logger",
                message="error1",
                raw="ERROR null pointer occurred",
                file_path="/data/logs/app.log",
                line_no=1,
                parse_status=ParseStatus.FULL,
            )
        ]
        rule = ClassificationRule(
            category="null-pointer",
            display_name="NullPointer",
            severity="ERROR",
            keywords=["NullPointer"],
        )
        classifications = [
            ClassificationResult(
                category="null-pointer",
                display_name="NullPointer",
                severity="ERROR",
                matched_keyword="NullPointer",
                rule=rule,
            )
        ]
        generate_key_logs(ctx, records, classifications)
        content = (ctx.output_dir() / "key-logs.txt").read_text(encoding="utf-8")
        assert "[null-pointer]" in content
        assert "ERROR null pointer occurred" in content

    def test_key_logs_bounded_to_max(self, tmp_path: Path):
        ctx = OutputContext(
            task_id="test-task",
            source_path="/data/logs",
            created_at="2026-05-17 10:00:00",
        )
        records = [
            ParsedLogRecord(
                timestamp="2026-05-17 10:01:01",
                level="ERROR",
                module="test",
                thread="t1",
                logger="Logger",
                message=f"error{i}",
                raw=f"ERROR error{i}",
                file_path="/data/logs/app.log",
                line_no=i,
                parse_status=ParseStatus.FULL,
            )
            for i in range(30)
        ]
        rule = ClassificationRule(
            category="error",
            display_name="Error",
            severity="ERROR",
            keywords=["ERROR"],
        )
        classifications = [
            ClassificationResult(
                category="error",
                display_name="Error",
                severity="ERROR",
                matched_keyword="ERROR",
                rule=rule,
            )
            for _ in range(30)
        ]
        generate_key_logs(ctx, records, classifications)
        content = (ctx.output_dir() / "key-logs.txt").read_text(encoding="utf-8")
        lines = [line for line in content.split("\n") if line and not line.startswith("(")]
        assert len(lines) <= MAX_SAMPLES_PER_CATEGORY


class TestRawSamples:
    def test_raw_samples_valid_jsonl(self, tmp_path: Path):
        ctx = OutputContext(
            task_id="test-task",
            source_path="/data/logs",
            created_at="2026-05-17 10:00:00",
        )
        records = [
            ParsedLogRecord(
                timestamp="2026-05-17 10:01:01",
                level="ERROR",
                module="test",
                thread="t1",
                logger="Logger",
                message="error1",
                raw="ERROR NullPointerException occurred",
                file_path="/data/logs/app.log",
                line_no=1,
                parse_status=ParseStatus.FULL,
            )
        ]
        rule = ClassificationRule(
            category="null-pointer",
            display_name="NullPointer",
            severity="ERROR",
            keywords=["NullPointer"],
        )
        classifications = [
            ClassificationResult(
                category="null-pointer",
                display_name="NullPointer",
                severity="ERROR",
                matched_keyword="NullPointer",
                rule=rule,
            )
        ]
        generate_raw_samples(ctx, records, classifications)
        path = ctx.artifacts_dir() / "raw-samples.jsonl"
        assert path.exists()
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["category"] == "null-pointer"
        assert "raw" in obj


class TestBuildClassificationStats:
    def test_counts_by_category(self):
        rule = ClassificationRule(
            category="null-pointer",
            display_name="NullPointer",
            severity="ERROR",
            keywords=["NPE"],
        )
        classifications = [
            ClassificationResult(
                category="null-pointer",
                display_name="NullPointer",
                severity="ERROR",
                matched_keyword="NPE",
                rule=rule,
            )
            for _ in range(3)
        ]
        stats = _build_classification_stats(classifications)
        assert stats["null-pointer"] == 3

    def test_ignores_unknown(self):
        classifications = [UNKNOWN_RESULT for _ in range(5)]
        stats = _build_classification_stats(classifications)
        assert stats == {}


class TestGetTopExceptions:
    def test_returns_top_n(self):
        rule1 = ClassificationRule(category="a", display_name="A", severity="ERROR", keywords=["a"])
        rule2 = ClassificationRule(category="b", display_name="B", severity="ERROR", keywords=["b"])
        classifications = [
            ClassificationResult(category="a", display_name="A", severity="ERROR", matched_keyword="a", rule=rule1),
            ClassificationResult(category="a", display_name="A", severity="ERROR", matched_keyword="a", rule=rule1),
            ClassificationResult(category="b", display_name="B", severity="ERROR", matched_keyword="b", rule=rule2),
        ]
        top = _get_top_exceptions(classifications, top_n=2)
        assert len(top) == 2
        assert top[0][0] == "a"
        assert top[0][2] == 2


def _make_output_context(task_id: str = "test-task") -> OutputContext:
    """Create a minimal OutputContext for testing."""
    return OutputContext(
        task_id=task_id,
        source_path="/data/logs",
        created_at="2026-05-17 10:00:00",
        total_files=5,
        total_bytes=1024,
        error_count=3,
        warn_count=10,
    )


class TestThreadDumpSection:
    def test_evidence_pack_includes_thread_dump_section(self, tmp_path: Path) -> None:
        """Evidence pack should include thread dump analysis section when results provided."""
        ctx = _make_output_context()
        records: list[ParsedLogRecord] = []
        classifications: list[ClassificationResult] = []
        timeline: list[dict] = []

        thread_results = [
            ThreadDumpResult(
                thread_name="worker-1",
                thread_state="BLOCKED",
                frames=[
                    ThreadFrame(raw_text="\tat com.Lock.acquire(Lock.java:20)", class_name="com.Lock", method="acquire"),
                    ThreadFrame(raw_text="\tat com.Worker.run(Worker.java:10)", class_name="com.Worker", method="run"),
                ],
                lock_hints=[
                    LockHint(raw_text="    - waiting to lock <0x0007> (a java.lang.Object)", hint_type="waiting_to_lock", lock_address="0x0007", lock_class="java.lang.Object"),
                ],
                parse_status=ThreadParseStatus.FULL,
            ),
            ThreadDumpResult(
                thread_name="worker-2",
                thread_state="RUNNABLE",
                frames=[
                    ThreadFrame(raw_text="\tat com.Main.main(Main.java:5)", class_name="com.Main", method="main"),
                ],
                lock_hints=[],
                parse_status=ThreadParseStatus.FULL,
            ),
        ]

        generate_evidence_pack(ctx, records, classifications, 0, 0, timeline, thread_results=thread_results)

        content = (ctx.output_dir() / "evidence-pack.md").read_text(encoding="utf-8")
        assert "线程 Dump 分析" in content
        assert "线程总数" in content
        assert "BLOCKED" in content
        assert "worker-1" in content

    def test_evidence_pack_no_thread_section_when_no_results(self, tmp_path: Path) -> None:
        """Evidence pack should not include thread section when no results provided."""
        ctx = _make_output_context()
        generate_evidence_pack(ctx, [], [], 0, 0, [])

        content = (ctx.output_dir() / "evidence-pack.md").read_text(encoding="utf-8")
        assert "线程 Dump 分析" not in content
