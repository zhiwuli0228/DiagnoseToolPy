"""Tests for cluster_analyzer module."""

from __future__ import annotations

import pytest
from pathlib import Path

from diagnose_tool.analyzer.cluster_analyzer import (
    CaseTextExtractor,
    ClusterAnalyzer,
    ClusterGroup,
    ClusterResult,
    MatchedCase,
    PHASE_AGGREGATE,
    PHASE_DONE,
    PHASE_MATCH,
    PHASE_SCAN,
    PROGRESS_LABELS,
    read_cluster_result,
    read_progress,
)


class TestCaseTextExtractor:
    def test_extract_root_cause_section(self, tmp_path: Path):
        case_md = tmp_path / "case.md"
        case_md.write_text(
            "# Case\n\n"
            "## Root Cause\n\n"
            "Connection pool exhausted due to high traffic.\n\n"
            "## Solution\n\n"
            "Increase maxTotal in JedisPool config.\n",
            encoding="utf-8",
        )
        extractor = CaseTextExtractor()
        result = extractor.extract(case_md)
        assert result["root_cause"] == "Connection pool exhausted due to high traffic."
        assert result["solution"] == "Increase maxTotal in JedisPool config."
        assert result["summary"] != ""

    def test_extract_chinese_root_cause_section(self, tmp_path: Path):
        case_md = tmp_path / "case.md"
        case_md.write_text(
            "# Case\n\n"
            "## 根因\n\n"
            "数据库连接耗尽。\n\n"
            "## 解决方案\n\n"
            "调大连接池。\n",
            encoding="utf-8",
        )
        extractor = CaseTextExtractor()
        result = extractor.extract(case_md)
        assert result["root_cause"] == "数据库连接耗尽。"
        assert result["solution"] == "调大连接池。"

    def test_extract_summary_from_first_paragraph(self, tmp_path: Path):
        case_md = tmp_path / "case.md"
        case_md.write_text(
            "# Case Title\n\n"
            "This is the first paragraph summary of the case.\n\n"
            "More details here.\n",
            encoding="utf-8",
        )
        extractor = CaseTextExtractor()
        result = extractor.extract(case_md)
        assert "This is the first paragraph summary" in result["summary"]

    def test_missing_section_returns_none(self, tmp_path: Path):
        case_md = tmp_path / "case.md"
        case_md.write_text(
            "# Case\n\nNo root cause or solution sections here.\n",
            encoding="utf-8",
        )
        extractor = CaseTextExtractor()
        result = extractor.extract(case_md)
        assert result["root_cause"] is None
        assert result["solution"] is None

    def test_nonexistent_file_returns_empty(self, tmp_path: Path):
        extractor = CaseTextExtractor()
        result = extractor.extract(tmp_path / "nonexistent.md")
        assert result == {"summary": "", "root_cause": None, "solution": None}


class TestProgressLabels:
    def test_phase_labels_exist(self):
        assert PHASE_SCAN in PROGRESS_LABELS
        assert PHASE_AGGREGATE in PROGRESS_LABELS
        assert PHASE_MATCH in PROGRESS_LABELS
        assert PHASE_DONE in PROGRESS_LABELS
        assert PROGRESS_LABELS[PHASE_SCAN] == "扫描日志中..."
        assert PROGRESS_LABELS[PHASE_AGGREGATE] == "异常聚类中..."
        assert PROGRESS_LABELS[PHASE_MATCH] == "历史案例匹配中..."
        assert PROGRESS_LABELS[PHASE_DONE] == "分析完成"


class TestReadProgress:
    def test_read_progress_returns_correct_data(self, tmp_path: Path):
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            '{"status": "aggregating", "progress": 50, "current_step": "异常聚类中..."}',
            encoding="utf-8",
        )
        result = read_progress(tmp_path)
        assert result is not None
        assert result.status == "aggregating"
        assert result.progress == 50
        assert result.current_step == "异常聚类中..."

    def test_read_progress_returns_none_for_missing_file(self, tmp_path: Path):
        result = read_progress(tmp_path)
        assert result is None

    def test_read_progress_returns_none_for_malformed_json(self, tmp_path: Path):
        progress_file = tmp_path / "progress.json"
        progress_file.write_text("not json", encoding="utf-8")
        result = read_progress(tmp_path)
        assert result is None


class TestReadClusterResult:
    def test_read_cluster_result_returns_correct_data(self, tmp_path: Path):
        result_file = tmp_path / "cluster-result.json"
        result_file.write_text(
            '{"task_id": "cluster-001", "total_errors": 100, "clusters": []}',
            encoding="utf-8",
        )
        result = read_cluster_result(tmp_path)
        assert result is not None
        assert result.task_id == "cluster-001"
        assert result.total_errors == 100
        assert result.clusters == []

    def test_read_cluster_result_with_clusters(self, tmp_path: Path):
        result_file = tmp_path / "cluster-result.json"
        result_file.write_text(
            '{"task_id": "cluster-001", "total_errors": 50, "clusters": ['
            '{"exception_class": "NullPointerException", "count": 25, '
            '"sample_messages": ["NPE at line 10"], '
            '"time_distribution": {"peak_hour": "14:00-14:59", "range": "13:00-15:00"}, '
            '"matched_cases": []}'
            "]}",
            encoding="utf-8",
        )
        result = read_cluster_result(tmp_path)
        assert result is not None
        assert len(result.clusters) == 1
        assert result.clusters[0].exception_class == "NullPointerException"
        assert result.clusters[0].count == 25

    def test_read_cluster_result_returns_none_for_missing_file(self, tmp_path: Path):
        result = read_cluster_result(tmp_path)
        assert result is None


class TestClusterAnalyzerCreateTask:
    def test_create_task_returns_task_id_and_dir(self, tmp_path: Path):
        analyzer = ClusterAnalyzer(tmp_path)
        task_id, task_output = analyzer.create_task("/some/path")
        assert task_id.startswith("cluster-")
        assert task_output == tmp_path / "output" / task_id
        assert task_output.exists()


class TestClusterGroupDataclass:
    def test_cluster_group_fields(self):
        group = ClusterGroup(
            exception_class="NullPointerException",
            count=10,
            sample_messages=["NPE at line 1", "NPE at line 2"],
            time_distribution={"peak_hour": "14:00-14:59", "range": "13:00-15:00"},
            matched_cases=[
                MatchedCase(
                    case_id="case-001",
                    score=0.85,
                    summary="Connection pool issue",
                    root_cause="pool exhausted",
                    solution="increase pool size",
                )
            ],
        )
        assert group.exception_class == "NullPointerException"
        assert group.count == 10
        assert len(group.sample_messages) == 2
        assert group.time_distribution["peak_hour"] == "14:00-14:59"
        assert len(group.matched_cases) == 1
        assert group.matched_cases[0].case_id == "case-001"
        assert group.matched_cases[0].score == 0.85


class TestMatchedCaseDataclass:
    def test_matched_case_fields(self):
        mc = MatchedCase(
            case_id="case-042",
            score=0.72,
            summary="SQL timeout",
            root_cause="slow query",
            solution="add index",
        )
        assert mc.case_id == "case-042"
        assert mc.score == 0.72
        assert mc.summary == "SQL timeout"
        assert mc.root_cause == "slow query"
        assert mc.solution == "add index"

    def test_matched_case_null_optional_fields(self):
        mc = MatchedCase(case_id="case-001", score=0.5, summary="Test")
        assert mc.root_cause is None
        assert mc.solution is None