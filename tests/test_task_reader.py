"""Unit tests for the task_reader service."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_task_reader(tmp_path: Path):
    """Load task_reader with the output root pointed at a tmp path.

    The service module reads ``data/output`` directly, so we use
    importlib to load a one-off copy that exposes the same functions
    but resolves paths under ``tmp_path``.
    """

    src_path = Path(__file__).resolve().parent.parent / "diagnose_tool" / "analyzer" / "task_reader.py"
    spec = importlib.util.spec_from_file_location("_task_reader_under_test", src_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module._OUTPUT_ROOT = tmp_path
    return module


def test_validate_task_id_accepts_safe_inputs(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    assert mod._validate_task_id("abc-123") == "abc-123"
    assert mod._validate_task_id("ABC_xyz-09") == "ABC_xyz-09"
    assert mod._validate_task_id("a") == "a"


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "..",
        "../etc/passwd",
        "abc/def",
        "abc\\def",
        "abc def",
        "abc;rm",
        "abc.def",
        "abc/def/../etc",
        "任务",
    ],
)
def test_validate_task_id_rejects_unsafe_inputs(tmp_path: Path, bad_id: str) -> None:
    mod = _load_task_reader(tmp_path)
    with pytest.raises(mod.InvalidTaskIdError):
        mod._validate_task_id(bad_id)


def test_list_tasks_returns_empty_when_root_missing(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    assert mod.list_tasks() == []


def test_list_tasks_skips_dirs_without_progress(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    (tmp_path / "no-progress").mkdir()
    (tmp_path / "no-progress" / "evidence-pack.md").write_text("x", encoding="utf-8")
    (tmp_path / "with-progress").mkdir()
    (tmp_path / "with-progress" / "progress.json").write_text(
        json.dumps({"status": "done", "progress": 100, "updated_at": "2026-06-01T10:00:00Z"}),
        encoding="utf-8",
    )
    (tmp_path / "bench-full").mkdir()
    summaries = mod.list_tasks()
    ids = [s.task_id for s in summaries]
    assert ids == ["with-progress"]


def test_list_tasks_sorted_by_updated_at_desc(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    for name, ts in [
        ("a", "2026-06-01T10:00:00Z"),
        ("b", "2026-06-02T10:00:00Z"),
        ("c", "2026-06-01T05:00:00Z"),
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / "progress.json").write_text(
            json.dumps({"status": "done", "updated_at": ts}), encoding="utf-8"
        )
    summaries = mod.list_tasks()
    assert [s.task_id for s in summaries] == ["b", "a", "c"]


def test_read_progress_returns_dict(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    d = tmp_path / "t1"
    d.mkdir()
    payload = {"status": "done", "progress": 100, "current_step": "分析完成"}
    (d / "progress.json").write_text(json.dumps(payload), encoding="utf-8")
    assert mod.read_progress("t1") == payload


def test_read_progress_missing_returns_none(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    (tmp_path / "empty").mkdir()
    assert mod.read_progress("empty") is None


def test_read_progress_invalid_json_returns_none(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    d = tmp_path / "broken"
    d.mkdir()
    (d / "progress.json").write_text("{not json", encoding="utf-8")
    assert mod.read_progress("broken") is None


def test_read_evidence_pack_returns_text(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    d = tmp_path / "t1"
    d.mkdir()
    (d / "evidence-pack.md").write_text("# evidence", encoding="utf-8")
    assert mod.read_evidence_pack("t1") == "# evidence"


def test_read_evidence_pack_missing_returns_none(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    d = tmp_path / "t1"
    d.mkdir()
    assert mod.read_evidence_pack("t1") is None


def test_read_key_logs_returns_text(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    d = tmp_path / "t1"
    d.mkdir()
    (d / "key-logs.txt").write_text("[error] foo\n[warn] bar\n", encoding="utf-8")
    assert mod.read_key_logs("t1") == "[error] foo\n[warn] bar\n"


def test_read_case_draft_returns_text(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    d = tmp_path / "t1"
    d.mkdir()
    (d / "case-draft.md").write_text("## case", encoding="utf-8")
    assert mod.read_case_draft("t1") == "## case"


def test_readers_reject_invalid_task_id(tmp_path: Path) -> None:
    mod = _load_task_reader(tmp_path)
    with pytest.raises(mod.InvalidTaskIdError):
        mod.read_progress("..")
    with pytest.raises(mod.InvalidTaskIdError):
        mod.read_evidence_pack("..")
    with pytest.raises(mod.InvalidTaskIdError):
        mod.read_key_logs("..")
    with pytest.raises(mod.InvalidTaskIdError):
        mod.read_case_draft("..")
