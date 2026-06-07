"""Tests for thread evidence resolver integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from diagnose_tool.analyzer.thread_artifact import (
    format_thread_entries_markdown,
    resolve_thread_refs,
    write_thread_artifacts,
)
from diagnose_tool.analyzer.thread_stack_parser import (
    ParseStatus,
    ThreadDumpResult,
    ThreadFrame,
)
from diagnose_tool.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_output_ctx(tmp_path: Path, task_id: str = "test-task-001"):
    """Create an OutputContext that writes to tmp_path."""
    output_dir = tmp_path / task_id

    class _PatchedCtx:
        def __init__(self):
            self.task_id = task_id

        def output_dir(self):
            return output_dir

        def artifacts_dir(self):
            return output_dir / "artifacts"

        def ensure_directories(self):
            self.output_dir().mkdir(parents=True, exist_ok=True)
            self.artifacts_dir().mkdir(parents=True, exist_ok=True)

    return _PatchedCtx()


def _sample_results():
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
            lock_hints=[],
            raw_text='"worker-1" #2 prio=5\n   java.lang.Thread.State: BLOCKED',
            parse_status=ParseStatus.FULL,
        ),
    ]


class TestResolveThreadRefs:
    def test_resolve_valid_refs(self, tmp_path):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, _sample_results())

        entries = json.loads((tmp_path / "test-task-001" / "artifacts" / "thread-stack-results.jsonl").read_text().splitlines()[0].strip())
        ref = entries["thread_ref"] if isinstance(entries, dict) else None

        # Read all entries to get refs
        lines = (tmp_path / "test-task-001" / "artifacts" / "thread-stack-results.jsonl").read_text().strip().splitlines()
        refs = [json.loads(l)["thread_ref"] for l in lines]

        resolved, missing = resolve_thread_refs(tmp_path / "test-task-001", refs)
        assert len(resolved) == 2
        assert len(missing) == 0

    def test_resolve_missing_ref(self, tmp_path):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, _sample_results())

        resolved, missing = resolve_thread_refs(
            tmp_path / "test-task-001",
            ["thread:test-task-001:99:deadbeef"],
        )
        assert len(resolved) == 0
        assert len(missing) == 1

    def test_resolve_mixed(self, tmp_path):
        ctx = _make_output_ctx(tmp_path)
        write_thread_artifacts(ctx, _sample_results())

        lines = (tmp_path / "test-task-001" / "artifacts" / "thread-stack-results.jsonl").read_text().strip().splitlines()
        valid_ref = json.loads(lines[0])["thread_ref"]

        resolved, missing = resolve_thread_refs(
            tmp_path / "test-task-001",
            [valid_ref, "thread:test-task-001:99:deadbeef"],
        )
        assert len(resolved) == 1
        assert len(missing) == 1

    def test_no_artifact(self, tmp_path):
        resolved, missing = resolve_thread_refs(
            tmp_path / "nonexistent",
            ["thread:x:0:abc"],
        )
        assert len(resolved) == 0
        assert len(missing) == 1


class TestFormatThreadEntriesMarkdown:
    def test_format_single_entry(self):
        entries = [{
            "thread_name": "main",
            "thread_state": "RUNNABLE",
            "parse_status": "FULL",
            "raw_text": "thread dump content",
        }]
        md = format_thread_entries_markdown(entries)
        assert "Thread: main" in md
        assert "RUNNABLE" in md
        assert "thread dump content" in md

    def test_format_multiple_entries(self):
        entries = [
            {"thread_name": "main", "thread_state": "RUNNABLE", "parse_status": "FULL", "raw_text": "content1"},
            {"thread_name": "worker", "thread_state": "BLOCKED", "parse_status": "FULL", "raw_text": "content2"},
        ]
        md = format_thread_entries_markdown(entries)
        assert "Thread: main" in md
        assert "Thread: worker" in md

    def test_format_empty(self):
        md = format_thread_entries_markdown([])
        assert md == ""

    def test_format_unnamed_thread(self):
        entries = [{"thread_name": None, "thread_state": "RUNNABLE", "parse_status": "RAW", "raw_text": "raw"}]
        md = format_thread_entries_markdown(entries)
        assert "(unnamed)" in md
