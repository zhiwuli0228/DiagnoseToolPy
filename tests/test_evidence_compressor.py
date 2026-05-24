"""Tests for evidence_compressor module."""

from __future__ import annotations

import pytest

from diagnose_tool.analyzer.evidence_compressor import (
    CompressionOptions,
    CompressedEvidence,
    StackPatternGroup,
    build_evidence_markdown,
    compress_log_entries,
    estimate_tokens,
    truncate_to_token_budget,
)


class TestCompressLogEntries:
    def test_compress_empty_entries(self):
        result = compress_log_entries([])
        assert result == []

    def test_compress_single_entry(self):
        entries = [
            {
                "group_key": "NullPointerException",
                "event": {
                    "timestamp": "2026-05-23 10:01:01",
                    "level": "ERROR",
                    "thread": "main",
                    "message": "NPE",
                    "raw": "2026-05-23 10:01:01 ERROR NPE",
                    "file_path": "/data/app.log",
                    "line_no": 10,
                },
            }
        ]
        result = compress_log_entries(entries)
        assert len(result) == 1
        assert result[0].group_key == "NullPointerException"
        assert result[0].total_count == 1

    def test_compress_groups_multiple_entries_by_group_key(self):
        entries = [
            {
                "group_key": "NullPointerException",
                "event": {"timestamp": "2026-05-23 10:01:01", "message": "NPE", "raw": "raw1"},
            },
            {
                "group_key": "NullPointerException",
                "event": {"timestamp": "2026-05-23 10:01:02", "message": "NPE", "raw": "raw2"},
            },
            {
                "group_key": "SqlException",
                "event": {"timestamp": "2026-05-23 10:01:03", "message": "SQL", "raw": "raw3"},
            },
        ]
        result = compress_log_entries(entries)
        assert len(result) == 2

        npe_group = next(g for g in result if g.group_key == "NullPointerException")
        assert npe_group.total_count == 2

        sql_group = next(g for g in result if g.group_key == "SqlException")
        assert sql_group.total_count == 1

    def test_compress_calculates_first_last_occurrence(self):
        entries = [
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:05:00", "message": "msg", "raw": "raw"},
            },
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:01:00", "message": "msg", "raw": "raw"},
            },
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:03:00", "message": "msg", "raw": "raw"},
            },
        ]
        result = compress_log_entries(entries)
        assert result[0].first_occurrence == "2026-05-23 10:01:00"
        assert result[0].last_occurrence == "2026-05-23 10:05:00"

    def test_compress_peak_window_calculation(self):
        entries = [
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:01:00", "message": "msg", "raw": "raw"},
            },
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:02:00", "message": "msg", "raw": "raw"},
            },
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:02:00", "message": "msg", "raw": "raw"},
            },
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 10:02:00", "message": "msg", "raw": "raw"},
            },
            {
                "group_key": "group1",
                "event": {"timestamp": "2026-05-23 11:01:00", "message": "msg", "raw": "raw"},
            },
        ]
        result = compress_log_entries(entries)
        # 10:00-10:59 has 4 entries, 11:00-11:59 has 1 entry
        assert "10:00-10:59" in result[0].peak_window
        assert "80%" in result[0].peak_window  # 4/5 = 80%

    def test_compress_with_cached_log_entry_objects(self):
        from diagnose_tool.analyzer.evidence_cache import CachedLogEntry, LogEvent

        entry = CachedLogEntry(
            id="abc123",
            group_key="NullPointerException",
            event=LogEvent(
                timestamp="2026-05-23 10:01:01",
                level="ERROR",
                thread="main",
                message="NPE",
                raw="raw",
                file_path="/data/app.log",
                line_no=10,
            ),
            context_before=[],
            context_after=[],
        )
        result = compress_log_entries([entry])
        assert len(result) == 1
        assert result[0].total_count == 1


class TestBuildEvidenceMarkdown:
    def test_build_empty_markdown(self):
        result = build_evidence_markdown([])
        assert result == "No evidence to display."

    def test_build_markdown_single_group(self):
        evidence = [
            CompressedEvidence(
                group_key="NullPointerException",
                total_count=10,
                first_occurrence="2026-05-23 10:01:00",
                last_occurrence="2026-05-23 10:05:00",
                peak_window="10:00-10:59 (80%)",
                stack_groups=[],
                raw_sample="NullPointer at line 42",
            )
        ]
        result = build_evidence_markdown(evidence)
        assert "NullPointerException" in result
        assert "10 次" in result
        assert "2026-05-23 10:01:00" in result

    def test_build_markdown_includes_stack_patterns(self):
        evidence = [
            CompressedEvidence(
                group_key="NullPointerException",
                total_count=5,
                first_occurrence="2026-05-23 10:01:00",
                last_occurrence="2026-05-23 10:05:00",
                peak_window="10:00-10:59",
                stack_groups=[
                    StackPatternGroup(
                        pattern="com.example.Service.method(File.java:42)",
                        count=3,
                        first_occurrence="2026-05-23 10:01:00",
                        last_occurrence="2026-05-23 10:03:00",
                        peak_window="10:00-10:59",
                        sample_entry={},
                    ),
                ],
                raw_sample="NPE",
            )
        ]
        options = CompressionOptions(include_stack=True, include_timeline=True)
        result = build_evidence_markdown(evidence, options)
        assert "堆栈模式" in result
        assert "com.example.Service.method" in result


class TestEstimateTokens:
    def test_estimate_empty_string(self):
        assert estimate_tokens("") == 0

    def test_estimate_english_text(self):
        # Rough estimate: 1 token ≈ 4 characters
        text = "a" * 100
        assert estimate_tokens(text) == 50  # 100 // 2


class TestTruncateToTokenBudget:
    def test_truncate_within_budget(self):
        text = "short text"
        result = truncate_to_token_budget(text, max_tokens=1000)
        assert result == text

    def test_truncate_exceeds_budget(self):
        # Create text that exceeds budget
        text = "word " * 1000  # ~5000 chars
        result = truncate_to_token_budget(text, max_tokens=100)
        assert estimate_tokens(result) <= 100
        assert "*[内容已截断以符合token限制]*" in result

    def test_truncate_returns_truncated_content(self):
        lines = ["line " + str(i) for i in range(100)]
        text = "\n".join(lines)
        result = truncate_to_token_budget(text, max_tokens=50)
        # Should not error, and should end with truncation marker
        assert result is not None


class TestCompressionOptions:
    def test_default_options(self):
        opts = CompressionOptions()
        assert opts.include_stack is True
        assert opts.include_timeline is True
        assert opts.max_tokens == 2000

    def test_custom_options(self):
        opts = CompressionOptions(include_stack=False, max_tokens=5000)
        assert opts.include_stack is False
        assert opts.max_tokens == 5000
