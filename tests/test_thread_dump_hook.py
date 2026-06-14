# tests/test_thread_dump_hook.py
"""Tests for thread dump hook — state machine scanning and integration."""

from __future__ import annotations

from pathlib import Path

from diagnose_tool.analyzer.thread_dump_hook import scan_and_parse_thread_dumps
from diagnose_tool.analyzer.thread_stack_parser import ParseStatus


SAMPLE_THREAD_HEADER = '"worker-1" #42 daemon prio=5 os_prio=0 tid=0x00007f8b4c128000 nid=0x1a2b waiting on condition [0x00007f8b3c0fe000]\n'
SAMPLE_THREAD_STATE = '   java.lang.Thread.State: WAITING (parking)\n'
SAMPLE_FRAME = '\tat sun.misc.Unsafe.park(Native Method)\n'
SAMPLE_LOCK_HINT = '    - parking to wait for <0x000000008ab12340> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)\n'

SAMPLE_LOG_LINE = '2026-06-14 10:01:01.123 ERROR [main] com.demo.OrderService - query failed\n'


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestStateDetection:
    """Test that the state machine correctly identifies thread dump blocks."""

    def test_pure_log_file_returns_empty(self, tmp_path: Path) -> None:
        """A file with only log lines should produce no thread results."""
        log_file = tmp_path / "app.log"
        _write_file(log_file, SAMPLE_LOG_LINE * 5)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(log_file)],
            output_dir=tmp_path / "output",
            task_id="test-001",
        )
        assert results == []

    def test_pure_dump_file(self, tmp_path: Path) -> None:
        """A file with only thread dump blocks should be parsed."""
        dump_file = tmp_path / "jstack.log"
        content = SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME * 3
        _write_file(dump_file, content)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(dump_file)],
            output_dir=tmp_path / "output",
            task_id="test-002",
        )
        assert len(results) >= 1
        assert any(r.thread_name == "worker-1" for r in results)
        # Verify parsing quality
        worker = [r for r in results if r.thread_name == "worker-1"][0]
        assert worker.thread_state == "WAITING"
        assert len(worker.frames) > 0
        assert worker.parse_status in (ParseStatus.FULL, ParseStatus.PARTIAL)

    def test_mixed_file_log_then_dump(self, tmp_path: Path) -> None:
        """A file with log lines followed by a thread dump should detect the dump."""
        mixed_file = tmp_path / "mixed.log"
        content = SAMPLE_LOG_LINE * 3 + "\n" + SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME * 2
        _write_file(mixed_file, content)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(mixed_file)],
            output_dir=tmp_path / "output",
            task_id="test-003",
        )
        assert len(results) >= 1

    def test_mixed_file_dump_then_log(self, tmp_path: Path) -> None:
        """A file with a thread dump followed by log lines should detect the dump."""
        mixed_file = tmp_path / "mixed.log"
        content = SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME + "\n" + SAMPLE_LOG_LINE * 3
        _write_file(mixed_file, content)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(mixed_file)],
            output_dir=tmp_path / "output",
            task_id="test-004",
        )
        assert len(results) >= 1

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """An empty file should produce no results."""
        empty_file = tmp_path / "empty.log"
        _write_file(empty_file, "")

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(empty_file)],
            output_dir=tmp_path / "output",
            task_id="test-005",
        )
        assert results == []

    def test_multiple_threads_in_one_file(self, tmp_path: Path) -> None:
        """Multiple thread blocks in one file should all be detected."""
        dump_file = tmp_path / "jstack.log"
        thread1 = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)\n'
        thread2 = '"worker-2" #2 daemon prio=5\n   java.lang.Thread.State: BLOCKED\n\tat com.Lock.acquire(Lock.java:20)\n'
        _write_file(dump_file, thread1 + thread2)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(dump_file)],
            output_dir=tmp_path / "output",
            task_id="test-006",
        )
        assert len(results) == 2
        # Verify parsing quality for each thread
        w1 = [r for r in results if r.thread_name == "worker-1"][0]
        assert w1.thread_state == "RUNNABLE"
        assert len(w1.frames) > 0
        assert w1.parse_status in (ParseStatus.FULL, ParseStatus.PARTIAL)
        w2 = [r for r in results if r.thread_name == "worker-2"][0]
        assert w2.thread_state == "BLOCKED"
        assert len(w2.frames) > 0
        assert w2.parse_status in (ParseStatus.FULL, ParseStatus.PARTIAL)


def _make_scanned_file(path: Path):
    """Create a minimal ScannedFile-like object."""
    from dataclasses import dataclass

    @dataclass
    class FakeScannedFile:
        path: str
        name: str
        size: int
        type: str

    return FakeScannedFile(
        path=str(path),
        name=path.name,
        size=path.stat().st_size,
        type="log",
    )


class TestMultiFile:
    """Test scanning across multiple files."""

    def test_partial_files_contain_dumps(self, tmp_path: Path) -> None:
        """Only files with thread dumps should contribute results."""
        log_file = tmp_path / "app.log"
        dump_file = tmp_path / "jstack.log"
        _write_file(log_file, SAMPLE_LOG_LINE * 3)
        _write_file(dump_file, SAMPLE_THREAD_HEADER + SAMPLE_THREAD_STATE + SAMPLE_FRAME)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(log_file), _make_scanned_file(dump_file)],
            output_dir=tmp_path / "output",
            task_id="test-multi-001",
        )
        assert len(results) >= 1

    def test_multiple_dump_files(self, tmp_path: Path) -> None:
        """Thread dumps from multiple files should all be collected."""
        dump1 = tmp_path / "jstack1.log"
        dump2 = tmp_path / "jstack2.log"
        thread1 = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)\n'
        thread2 = '"worker-2" #2 daemon prio=5\n   java.lang.Thread.State: BLOCKED\n\tat com.Lock.acquire(Lock.java:20)\n'
        _write_file(dump1, thread1)
        _write_file(dump2, thread2)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(dump1), _make_scanned_file(dump2)],
            output_dir=tmp_path / "output",
            task_id="test-multi-002",
        )
        assert len(results) == 2


class TestErrorTolerance:
    """Test that errors in individual files don't abort the pipeline."""

    def test_nonexistent_file_skipped(self, tmp_path: Path) -> None:
        """A file that doesn't exist should be skipped without raising."""
        from dataclasses import dataclass

        @dataclass
        class FakeScannedFile:
            path: str
            name: str
            size: int
            type: str

        missing = tmp_path / "missing.log"
        fake = FakeScannedFile(
            path=str(missing),
            name=missing.name,
            size=0,
            type="log",
        )
        results = scan_and_parse_thread_dumps(
            files=[fake],
            output_dir=tmp_path / "output",
            task_id="test-err-001",
        )
        assert results == []

    def test_corrupted_dump_block_skipped(self, tmp_path: Path) -> None:
        """A file with garbage between valid thread headers should still parse what it can."""
        bad_file = tmp_path / "bad.log"
        valid_thread = '"worker-1" #1 daemon prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)\n'
        garbage = "this is not a valid thread dump block at all\n" * 10
        _write_file(bad_file, valid_thread + garbage)

        results = scan_and_parse_thread_dumps(
            files=[_make_scanned_file(bad_file)],
            output_dir=tmp_path / "output",
            task_id="test-err-002",
        )
        # Should still get at least the valid thread
        assert len(results) >= 1
