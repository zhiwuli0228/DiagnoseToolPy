"""Tests for cluster_analyzer module."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from diagnose_tool.analyzer.cluster_analyzer import (
    _atomic_write_text,
    CaseTextExtractor,
    ClusterAnalyzer,
    ClusterGroup,
    MatchedCase,
    PHASE_AGGREGATE,
    PHASE_DONE,
    PHASE_MATCH,
    PHASE_SCAN,
    PROGRESS_LABELS,
    read_cluster_result,
    read_progress,
)
from diagnose_tool.analyzer.log_aggregator import AggregatedGroup


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


class TestClusterAnalyzerPerformanceGuards:
    def test_run_does_not_rebuild_full_error_list_for_cache(self, tmp_path: Path, monkeypatch) -> None:
        analyzer = ClusterAnalyzer(tmp_path)
        task_id, _ = analyzer.create_task("/logs")

        aggregated_groups = [
            AggregatedGroup(
                key="NullPointerException",
                count=50000,
                sample_message="ERROR NullPointerException",
                sample_timestamp="2026-06-06T10:00:00",
                sample_thread="worker-1",
                sample_level="ERROR",
                file_path="/logs/app.log",
                matched_lines=[
                    {
                        "timestamp": "2026-06-06T10:00:00",
                        "level": "ERROR",
                        "thread": "worker-1",
                        "message": "NullPointerException happened",
                        "raw": "2026-06-06 10:00:00 ERROR NullPointerException happened",
                        "file_path": "/logs/app.log",
                        "line_no": 100,
                    }
                ],
            )
        ]
        matched_clusters = [
            ClusterGroup(
                exception_class="NullPointerException",
                count=50000,
                sample_messages=["NullPointerException happened"],
                time_distribution={"peak_hour": "10:00-10:59", "range": "10:00 - 10:00"},
                matched_cases=[],
            )
        ]

        monkeypatch.setattr(analyzer, "_prepare_file_list", lambda source_path: ([], None))
        monkeypatch.setattr(
            analyzer,
            "_scan_and_aggregate_streaming",
            lambda task_output, files, total_files, zip_source_path=None, total_bytes=0: aggregated_groups,
        )
        monkeypatch.setattr(analyzer, "_match_historical_cases", lambda groups: matched_clusters)
        monkeypatch.setattr(
            analyzer,
            "_scan_and_extract_errors_from_files",
            lambda files, zip_source_path=None: (_ for _ in ()).throw(
                AssertionError("full error list rebuild should not be called")
            ),
        )

        result = analyzer.run(task_id, "/logs")

        assert result.total_errors == 50000
        cache_path = tmp_path / "output" / task_id / "matched-lines.jsonl"
        assert cache_path.exists()


class TestByteProgress:
    def test_progress_includes_total_bytes_and_current_file(self, tmp_path: Path, monkeypatch) -> None:
        """During a scan, progress.json includes processed_bytes, total_bytes, current_file."""
        from diagnose_tool.analyzer.scanner import ScannedFile

        analyzer = ClusterAnalyzer(tmp_path)
        task_id, _ = analyzer.create_task("/logs")

        files = [
            ScannedFile(path="/logs/a.log", name="a.log", size=2048, type="log"),
            ScannedFile(path="/logs/b.log", name="b.log", size=4096, type="log"),
        ]
        captured: list[dict] = []

        def fake_scan(task_output, files, total_files, zip_source_path=None, total_bytes=0):
            progress_path = task_output / "progress.json"
            captured.append(json.loads(progress_path.read_text(encoding="utf-8")))
            return []

        monkeypatch.setattr(analyzer, "_prepare_file_list", lambda source_path: (files, None))
        monkeypatch.setattr(analyzer, "_scan_and_aggregate_streaming", fake_scan)
        monkeypatch.setattr(analyzer, "_match_historical_cases", lambda groups: [])

        analyzer.run(task_id, "/logs")

        assert captured, "expected at least one progress write during scan"
        snapshot = captured[0]
        assert "total_bytes" in snapshot
        assert snapshot["total_bytes"] == 6144
        assert "processed_bytes" in snapshot
        assert "current_file" in snapshot

    def test_progress_advances_within_very_large_file(self, tmp_path: Path, monkeypatch) -> None:
        """Progress advances before a single very large file finishes."""
        from diagnose_tool.analyzer.scanner import ScannedFile

        analyzer = ClusterAnalyzer(tmp_path)
        task_id, task_output = analyzer.create_task("/logs")

        large_file = ScannedFile(path="/logs/big.log", name="big.log", size=200 * 1024 * 1024, type="log")
        files = [large_file]

        progress_writes: list[dict] = []

        def fake_scan(task_output, files, total_files, zip_source_path=None, total_bytes=0):
            progress_path = task_output / "progress.json"
            # Capture the initial write
            progress_writes.append(json.loads(progress_path.read_text(encoding="utf-8")))
            # Simulate a scan-stage write with current_file set
            (task_output / "progress.json").write_text(
                json.dumps({
                    "status": "scanning",
                    "progress": 30,
                    "current_file": "big.log",
                    "processed_bytes": 64 * 1024 * 1024,
                    "total_bytes": total_bytes,
                })
            )
            progress_writes.append(json.loads(progress_path.read_text(encoding="utf-8")))
            return []

        monkeypatch.setattr(analyzer, "_prepare_file_list", lambda source_path: (files, None))
        monkeypatch.setattr(analyzer, "_scan_and_aggregate_streaming", fake_scan)
        monkeypatch.setattr(analyzer, "_match_historical_cases", lambda groups: [])

        analyzer.run(task_id, "/logs")

        assert progress_writes, "expected at least one progress write"
        first = progress_writes[0]
        assert first["total_bytes"] == 200 * 1024 * 1024
        # A second progress write within the large file should advertise the
        # current file so users can see progress before the file completes.
        later = progress_writes[-1]
        assert later["current_file"] == "big.log"
        assert later["processed_bytes"] == 64 * 1024 * 1024

    def test_terminal_failure_state_is_persisted(self, tmp_path: Path, monkeypatch) -> None:
        """If the background scan raises, progress.json records terminal failed state."""
        analyzer = ClusterAnalyzer(tmp_path)
        task_id, task_output = analyzer.create_task("/logs")

        def boom(*args, **kwargs):
            raise RuntimeError("simulated scan failure")

        monkeypatch.setattr(analyzer, "_prepare_file_list", boom)

        with pytest.raises(RuntimeError):
            analyzer.run(task_id, "/logs")

        progress = json.loads((task_output / "progress.json").read_text(encoding="utf-8"))
        assert progress["status"] == "failed"
        assert "error" in progress
        assert "simulated scan failure" in progress["error"]


class TestAtomicProgressWrite:
    def test_atomic_write_text_leaves_no_temp_files(self, tmp_path: Path) -> None:
        target = tmp_path / "progress.json"
        _atomic_write_text(target, '{"a": 1}')
        assert target.exists()
        assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}
        # No leftover temp files in the same directory
        leftover = [p for p in tmp_path.iterdir() if p.name != "progress.json"]
        assert leftover == []

    def test_atomic_write_text_overwrites_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "progress.json"
        target.write_text('{"old": true}', encoding="utf-8")
        _atomic_write_text(target, '{"new": true}')
        assert json.loads(target.read_text(encoding="utf-8")) == {"new": True}

    def test_update_progress_is_safe_under_concurrent_reads(self, tmp_path: Path) -> None:
        """A reader polling the file must never see a half-written/empty value.

        Reproduces the race that the press test caught: the analyzer writes
        progress.json frequently while a benchmark worker polls the same
        file. Before the atomic-write fix, a reader could see `''` or
        partial bytes and `read_progress` would return None → 404.
        """
        from diagnose_tool.analyzer.cluster_analyzer import (
            ClusterAnalyzer,
            read_progress,
        )

        analyzer = ClusterAnalyzer(tmp_path)
        _, task_output = analyzer.create_task("/logs")
        # Seed the file with a valid initial write so the reader never sees
        # a "no file yet" condition (which is a legitimate return, not a
        # race). After this the test only fails if a half-written file
        # leaks through.
        analyzer._update_progress(
            task_output,
            "scanning",
            0,
            processed_files=0,
            total_files=100,
            processed_bytes=0,
            total_bytes=100_000_000,
            current_file="seed",
        )
        assert read_progress(task_output) is not None

        stop = threading.Event()
        bad_reads: list[str] = []
        read_count = 0

        def writer() -> None:
            i = 0
            while not stop.is_set():
                analyzer._update_progress(
                    task_output,
                    "scanning",
                    i % 101,
                    processed_files=i,
                    total_files=100,
                    processed_bytes=i * 1_000_000,
                    total_bytes=100_000_000,
                    current_file=f"file-{i}.log",
                    message=f"tick {i}",
                )
                i += 1

        def reader() -> None:
            nonlocal read_count
            import time
            while not stop.is_set():
                progress = read_progress(task_output)
                read_count += 1
                if progress is None:
                    bad_reads.append("None")
                else:
                    if not isinstance(progress.status, str) or not progress.status:
                        bad_reads.append(f"empty status: {progress.status!r}")
                    if not isinstance(progress.progress, int) or not (
                        0 <= progress.progress <= 100
                    ):
                        bad_reads.append(
                            f"bad progress: {progress.progress!r}"
                        )
                time.sleep(0.001)

        w = threading.Thread(target=writer, daemon=True)
        r = threading.Thread(target=reader, daemon=True)
        w.start()
        r.start()
        # Let the race run long enough that many writes and reads happen.
        import time
        time.sleep(0.4)
        stop.set()
        w.join(timeout=2)
        r.join(timeout=2)

        assert read_count > 20, f"reader did not poll enough: {read_count}"
        assert not bad_reads, (
            f"reader observed partial/empty progress.json: {bad_reads[:5]}"
        )

    def test_update_progress_keeps_under_load(self, tmp_path: Path) -> None:
        """Many sequential updates leave exactly the expected final state."""
        from diagnose_tool.analyzer.cluster_analyzer import ClusterAnalyzer

        analyzer = ClusterAnalyzer(tmp_path)
        _, task_output = analyzer.create_task("/logs")
        for i in range(200):
            analyzer._update_progress(
                task_output,
                "scanning",
                i % 101,
                processed_bytes=i * 1024,
                total_bytes=10_000_000,
                current_file=f"file-{i}.log",
            )
        # Final state must be the last write
        data = json.loads((task_output / "progress.json").read_text(encoding="utf-8"))
        assert data["processed_bytes"] == 199 * 1024
        assert data["current_file"] == "file-199.log"
