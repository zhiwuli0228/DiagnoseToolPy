"""Tests for thread artifact writer and resolver."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from diagnose_tool.analyzer.output_context import OutputContext
from diagnose_tool.analyzer.thread_artifact import (
    load_thread_artifact,
    resolve_thread_ref,
    write_thread_artifacts,
)
from diagnose_tool.analyzer.thread_stack_parser import (
    ParseStatus,
    ThreadDumpResult,
    ThreadFrame,
    LockHint,
    parse_thread_dump_all,
)


@pytest.fixture
def tmp_output_context(tmp_path: Path):
    """Create a minimal OutputContext rooted in a temp directory."""
    # Patch the output dir to use tmp_path
    ctx = OutputContext(
        task_id="test-task-001",
        source_path="/tmp/source",
        created_at="2026-06-07 10:00:00",
    )
    # Override output_dir by monkey-patching
    orig_output_dir = ctx.output_dir
    ctx.__dict__["_output_dir_override"] = tmp_path / "test-task-001"
    # We'll use the real OutputContext but redirect via monkeypatch
    return ctx, tmp_path


@pytest.fixture
def sample_results() -> list[ThreadDumpResult]:
    """Two parsed thread results for testing."""
    return [
        ThreadDumpResult(
            thread_name="main",
            thread_state="RUNNABLE",
            frames=[
                ThreadFrame(raw_text="\tat com.Main.run(Main.java:10)",
                            class_name="com.Main", method="run",
                            file_name="Main.java", line_number=10),
            ],
            lock_hints=[],
            raw_text='"main" #1 prio=5\n   java.lang.Thread.State: RUNNABLE\n\tat com.Main.run(Main.java:10)',
            parse_status=ParseStatus.FULL,
        ),
        ThreadDumpResult(
            thread_name="worker-1",
            thread_state="BLOCKED",
            frames=[],
            lock_hints=[LockHint(raw_text="- waiting to lock <0x123> (a java.lang.Object)",
                                 hint_type="waiting_to_lock", lock_address="0x123",
                                 lock_class="java.lang.Object")],
            raw_text='"worker-1" #2 prio=5\n   java.lang.Thread.State: BLOCKED\n\tat com.Worker.doWork(Worker.java:20)',
            parse_status=ParseStatus.FULL,
        ),
    ]


def _make_output_ctx(tmp_path: Path, task_id: str = "test-task-001") -> OutputContext:
    """Create an OutputContext that writes to tmp_path."""
    ctx = OutputContext(
        task_id=task_id,
        source_path="/tmp/source",
        created_at="2026-06-07 10:00:00",
    )
    # We need to redirect output_dir to tmp_path. Since OutputContext is
    # frozen, we'll monkey-patch the methods.
    output_dir = tmp_path / task_id

    class _PatchedCtx(OutputContext):
        def output_dir(self) -> Path:
            return output_dir

        def artifacts_dir(self) -> Path:
            return output_dir / "artifacts"

        def ensure_directories(self) -> None:
            self.output_dir().mkdir(parents=True, exist_ok=True)
            self.artifacts_dir().mkdir(parents=True, exist_ok=True)

    return _PatchedCtx(
        task_id=task_id,
        source_path="/tmp/source",
        created_at="2026-06-07 10:00:00",
    )


class TestWriteThreadArtifacts:
    def test_writes_jsonl_and_summary(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        jsonl_path = write_thread_artifacts(ctx, sample_results)

        assert jsonl_path.exists()
        assert (tmp_path / "test-task-001" / "thread-stack-summary.md").exists()

    def test_jsonl_has_correct_count(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, sample_results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        assert len(entries) == 2

    def test_jsonl_entry_has_required_fields(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, sample_results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        entry = entries[0]
        assert "thread_ref" in entry
        assert "thread_name" in entry
        assert "thread_state" in entry
        assert "parse_status" in entry
        assert "frame_count" in entry
        assert "lock_count" in entry
        assert "frames_summary" in entry
        assert "raw_text" in entry

    def test_thread_ref_is_stable(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, sample_results)

        entries1 = load_thread_artifact(tmp_path / "test-task-001")

        # Write again with same data
        write_thread_artifacts(ctx, sample_results)
        entries2 = load_thread_artifact(tmp_path / "test-task-001")

        assert entries1[0]["thread_ref"] == entries2[0]["thread_ref"]
        assert entries1[1]["thread_ref"] == entries2[1]["thread_ref"]

    def test_thread_ref_encodes_task_id(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, sample_results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        for entry in entries:
            assert entry["thread_ref"].startswith("thread:test-task-001:")

    def test_different_tasks_get_different_refs(self, tmp_path, sample_results):
        ctx1 = _make_output_ctx(tmp_path, "task-a")
        ctx2 = _make_output_ctx(tmp_path, "task-b")
        write_thread_artifacts(ctx1, sample_results)
        write_thread_artifacts(ctx2, sample_results)

        entries_a = load_thread_artifact(tmp_path / "task-a")
        entries_b = load_thread_artifact(tmp_path / "task-b")

        assert entries_a[0]["thread_ref"] != entries_b[0]["thread_ref"]

    def test_empty_results(self, tmp_path):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, [])

        entries = load_thread_artifact(tmp_path / "test-task-001")
        assert entries == []

    def test_parse_status_preserved(self, tmp_path):
        results = [
            ThreadDumpResult(
                thread_name="full-thread", thread_state="RUNNABLE",
                frames=[ThreadFrame(raw_text="\tat com.Main.run(Main.java:10)",
                                    class_name="com.Main", method="run")],
                parse_status=ParseStatus.FULL,
            ),
            ThreadDumpResult(
                thread_name="partial-thread", thread_state="RUNNABLE",
                frames=[], parse_status=ParseStatus.PARTIAL,
            ),
            ThreadDumpResult(
                thread_name=None, thread_state=None,
                frames=[], parse_status=ParseStatus.RAW,
            ),
        ]
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        assert entries[0]["parse_status"] == "FULL"
        assert entries[1]["parse_status"] == "PARTIAL"
        assert entries[2]["parse_status"] == "RAW"

    def test_frames_summary_limited_to_5(self, tmp_path):
        frames = [
            ThreadFrame(raw_text=f"\tat com.Foo.bar{i}(Foo.java:{i})",
                        class_name="com.Foo", method=f"bar{i}")
            for i in range(10)
        ]
        results = [
            ThreadDumpResult(
                thread_name="many-frames", thread_state="RUNNABLE",
                frames=frames, parse_status=ParseStatus.FULL,
            )
        ]
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        assert len(entries[0]["frames_summary"]) == 5


class TestResolveThreadRef:
    def test_resolve_valid_ref(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, sample_results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        ref = entries[0]["thread_ref"]

        resolved = resolve_thread_ref(tmp_path / "test-task-001", ref)
        assert resolved is not None
        assert resolved["thread_name"] == "main"

    def test_resolve_missing_ref_returns_none(self, tmp_path, sample_results):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, sample_results)

        resolved = resolve_thread_ref(tmp_path / "test-task-001", "thread:fake:99:deadbeef")
        assert resolved is None

    def test_resolve_no_artifact_returns_none(self, tmp_path):
        resolved = resolve_thread_ref(tmp_path / "nonexistent", "thread:x:0:abc")
        assert resolved is None


class TestLoadThreadArtifact:
    def test_missing_artifact_returns_empty(self, tmp_path):
        entries = load_thread_artifact(tmp_path / "nonexistent")
        assert entries == []

    def test_roundtrip_from_real_parser(self, tmp_path):
        """Write and read back using actual parser output."""
        dump = '''\
"main" #1 prio=5 os_prio=0 tid=0x00007f8b8c00a800 nid=0x1234 runnable [0x00007f8b8bffe000]
   java.lang.Thread.State: RUNNABLE
\tat com.demo.Main.run(Main.java:42)

"worker" #2 daemon prio=5 os_prio=0 tid=0x00007f8b8c00b000 nid=0x5678 waiting on condition [0x00007f8b8cffe000]
   java.lang.Thread.State: WAITING (parking)
\tat sun.misc.Unsafe.park(Native Method)
'''
        results = parse_thread_dump_all(dump)
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, results)

        entries = load_thread_artifact(tmp_path / "test-task-001")
        assert len(entries) == 2
        assert entries[0]["thread_name"] == "main"
        assert entries[1]["thread_name"] == "worker"
        assert entries[0]["thread_ref"].startswith("thread:test-task-001:")
