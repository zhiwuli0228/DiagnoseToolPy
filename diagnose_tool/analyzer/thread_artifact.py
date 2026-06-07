"""Thread evidence artifact writer and resolver.

Writes parsed thread dump results as rebuildable task artifacts and
provides stable ``thread_ref`` identifiers for downstream resolution.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from diagnose_tool.analyzer.output_context import OutputContext
from diagnose_tool.analyzer.thread_stack_parser import ThreadDumpResult

ARTIFACT_FILENAME = "thread-stack-results.jsonl"
SUMMARY_FILENAME = "thread-stack-summary.md"


def _make_thread_ref(task_id: str, index: int, thread_name: str | None) -> str:
    """Generate a stable, opaque thread reference.

    The ref encodes the task scope and a short name-derived suffix so that
    the same logical thread always gets the same ref, even if the JSONL
    line order shifts slightly between runs.

    Format: ``thread:<task_id>:<index>:<name_hash8>``
    """
    name_part = thread_name or ""
    name_hash = hashlib.sha256(name_part.encode("utf-8")).hexdigest()[:8]
    return f"thread:{task_id}:{index}:{name_hash}"


def _result_to_entry(
    task_id: str, index: int, result: ThreadDumpResult
) -> dict:
    """Convert a single ``ThreadDumpResult`` to a JSONL-ready dict."""
    thread_ref = _make_thread_ref(task_id, index, result.thread_name)
    frames_summary: list[str] = []
    for f in result.frames[:5]:
        if f.class_name and f.method:
            frames_summary.append(f"{f.class_name}.{f.method}")

    return {
        "thread_ref": thread_ref,
        "thread_name": result.thread_name,
        "thread_state": result.thread_state,
        "parse_status": result.parse_status.value,
        "frame_count": len(result.frames),
        "lock_count": len(result.lock_hints),
        "frames_summary": frames_summary,
        "raw_text": result.raw_text,
    }


def write_thread_artifacts(
    output_context: OutputContext,
    results: list[ThreadDumpResult],
) -> Path:
    """Write thread evidence artifacts to the task output directory.

    Writes:
    - ``artifacts/thread-stack-results.jsonl`` (machine-readable)
    - ``thread-stack-summary.md`` (human-readable)

    Returns the path to the JSONL artifact.
    """
    output_context.ensure_directories()
    task_id = output_context.task_id

    # Write JSONL artifact
    jsonl_path = output_context.artifacts_dir() / ARTIFACT_FILENAME
    with jsonl_path.open("w", encoding="utf-8") as f:
        for idx, result in enumerate(results):
            entry = _result_to_entry(task_id, idx, result)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Write summary markdown
    summary_path = output_context.output_dir() / SUMMARY_FILENAME
    _write_summary(summary_path, task_id, results)

    return jsonl_path


def _write_summary(
    path: Path, task_id: str, results: list[ThreadDumpResult]
) -> None:
    """Write a human-readable thread summary markdown."""
    status_counts: dict[str, int] = {}
    for r in results:
        s = r.parse_status.value
        status_counts[s] = status_counts.get(s, 0) + 1

    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Thread Stack Summary — {task_id}\n\n")
        f.write(f"**Total threads:** {len(results)}\n\n")

        parts = []
        for status in ("FULL", "PARTIAL", "RAW"):
            count = status_counts.get(status, 0)
            if count:
                parts.append(f"{status} {count}")
        if parts:
            f.write(f"**Status:** {' / '.join(parts)}\n\n")

        f.write("| # | Thread Name | State | Parse Status | Frames |\n")
        f.write("|---|---|---|---|---|\n")
        for idx, r in enumerate(results):
            name = r.thread_name or "(unnamed)"
            state = r.thread_state or "-"
            status = r.parse_status.value
            frames = len(r.frames)
            f.write(f"| {idx + 1} | {name} | {state} | {status} | {frames} |\n")


def load_thread_artifact(output_dir: Path) -> list[dict]:
    """Load thread entries from the JSONL artifact.

    Returns a list of dicts, one per thread entry.
    Returns an empty list if the artifact does not exist.
    """
    jsonl_path = output_dir / "artifacts" / ARTIFACT_FILENAME
    if not jsonl_path.exists():
        return []

    entries: list[dict] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def resolve_thread_ref(output_dir: Path, thread_ref: str) -> dict | None:
    """Resolve a single ``thread_ref`` against the task artifact.

    Returns the matching entry dict, or ``None`` if not found.
    """
    entries = load_thread_artifact(output_dir)
    for entry in entries:
        if entry.get("thread_ref") == thread_ref:
            return entry
    return None


def resolve_thread_refs(output_dir: Path, thread_refs: list[str]) -> tuple[list[dict], list[str]]:
    """Resolve multiple ``thread_ref`` values against the task artifact.

    Returns:
        A tuple of (resolved_entries, missing_refs).
    """
    entries = load_thread_artifact(output_dir)
    by_ref = {e.get("thread_ref"): e for e in entries}
    resolved = []
    missing = []
    for ref in thread_refs:
        entry = by_ref.get(ref)
        if entry:
            resolved.append(entry)
        else:
            missing.append(ref)
    return resolved, missing


def format_thread_entries_markdown(entries: list[dict]) -> str:
    """Format resolved thread entries as markdown for prompt inclusion.

    Each entry includes thread name, state, parse status, and raw text.
    """
    if not entries:
        return ""

    parts = ["## Thread Stack Evidence\n"]
    for entry in entries:
        name = entry.get("thread_name") or "(unnamed)"
        state = entry.get("thread_state") or "-"
        status = entry.get("parse_status", "RAW")
        parts.append(f"### Thread: {name}")
        parts.append(f"- **State:** {state}")
        parts.append(f"- **Parse Status:** {status}")
        parts.append("")
        parts.append("```")
        parts.append(entry.get("raw_text", ""))
        parts.append("```")
        parts.append("")

    return "\n".join(parts)
