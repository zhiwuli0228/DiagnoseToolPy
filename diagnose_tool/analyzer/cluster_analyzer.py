"""Cluster analysis: anomaly clustering with historical case matching."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import tempfile
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

from diagnose_tool.analyzer.evidence_cache import (
    EvidenceCacheManager,
    generate_entry_id,
    LogEvent,
    CachedLogEntry,
)
from diagnose_tool.analyzer.log_aggregator import (
    aggregate_log_lines,
    AggregationOptions,
    AggregatedGroup,
)
from diagnose_tool.retrieval.keyword_search import search_by_keywords
from diagnose_tool.retrieval.query_builder import RetrievalQuery
from diagnose_tool.retrieval.rule_matcher import match_by_rules

logger = logging.getLogger(__name__)

# Progress phases
PHASE_SCAN = "scanning"
PHASE_AGGREGATE = "aggregating"
PHASE_MATCH = "matching"
PHASE_DONE = "done"

PROGRESS_LABELS = {
    PHASE_SCAN: "扫描日志中...",
    PHASE_AGGREGATE: "异常聚类中...",
    PHASE_MATCH: "历史案例匹配中...",
    PHASE_DONE: "分析完成",
}

MAX_SAMPLE_MESSAGES = 10
MAX_LINES_PER_CLUSTER = 100000

# Section extraction patterns
_ROOT_CAUSE_PATTERNS = [
    re.compile(r"##\s*Root Cause", re.IGNORECASE),
    re.compile(r"##\s*根因", re.IGNORECASE),
    re.compile(r"##\s*原因", re.IGNORECASE),
]
_SOLUTION_PATTERNS = [
    re.compile(r"##\s*Solution", re.IGNORECASE),
    re.compile(r"##\s*解决方案", re.IGNORECASE),
    re.compile(r"##\s*修复", re.IGNORECASE),
]


@dataclass
class MatchedCase:
    case_id: str
    score: float
    summary: str
    root_cause: str | None = None
    solution: str | None = None


@dataclass
class ClusterGroup:
    exception_class: str
    count: int
    sample_messages: list[str] = field(default_factory=list)
    time_distribution: dict = field(default_factory=dict)
    matched_cases: list[MatchedCase] = field(default_factory=list)


@dataclass
class ClusterResult:
    task_id: str
    clusters: list[ClusterGroup] = field(default_factory=list)
    total_errors: int = 0


@dataclass
class TaskProgress:
    status: str
    progress: int
    current_step: str


# Patterns for message normalization (copied from log_aggregator)
_TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?')
_NUMERIC_RE = re.compile(r'\b\d+\b')
_STRING_RE = re.compile(r'"[^"]*"')
_HEX_RE = re.compile(r'0x[0-9a-fA-F]+')


def _normalize_message(message: str) -> str:
    """Normalize a log message for consistent display.

    Replaces dynamic values (numbers, strings, hex) with placeholders
    so similar events with different values share the same template.
    """
    text = message
    text = _TIMESTAMP_RE.sub('<TS>', text)
    text = _STRING_RE.sub('<S>', text)
    text = _HEX_RE.sub('<HEX>', text)
    text = _NUMERIC_RE.sub('<N>', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class CaseTextExtractor:
    """Extract structured fields from case.md files."""

    def extract(self, case_md_path: Path) -> dict:
        """Extract root_cause, solution, and summary from case.md.

        Args:
            case_md_path: Path to case.md file.

        Returns:
            Dict with root_cause, solution, and summary fields.
        """
        if not case_md_path.exists():
            return {"summary": "", "root_cause": None, "solution": None}

        try:
            content = case_md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return {"summary": "", "root_cause": None, "solution": None}

        root_cause = self._extract_section(content, _ROOT_CAUSE_PATTERNS)
        solution = self._extract_section(content, _SOLUTION_PATTERNS)
        summary = self._extract_summary(content)

        return {
            "summary": summary,
            "root_cause": root_cause,
            "solution": solution,
        }

    def _extract_section(self, content: str, patterns: list[re.Pattern]) -> str | None:
        """Extract content under a heading matching one of the patterns."""
        for pattern in patterns:
            match = pattern.search(content)
            if match:
                start = match.end()
                # Find next ## heading or end of file
                next_heading = re.search(r"\n##\s", content[start:])
                if next_heading:
                    end = start + next_heading.start()
                else:
                    end = len(content)
                section = content[start:end].strip()
                if section:
                    return section
        return None

    def _extract_summary(self, content: str) -> str:
        """Extract summary - first paragraph or first line after title."""
        # Skip title lines (starting with #)
        lines = content.split("\n")
        paragraph_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped:
                paragraph_lines.append(stripped)
                if len(paragraph_lines) >= 3:
                    break
            else:
                if paragraph_lines:
                    break

        if paragraph_lines:
            return " ".join(paragraph_lines[:3])
        return ""


class ClusterAnalyzer:
    """Async clustering + historical case matching orchestrator."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = Path(data_dir)
        self._cases_dir = self._data_dir / "cases"
        self._extractor = CaseTextExtractor()

    def create_task(self, source_path: str) -> tuple[str, Path]:
        """Create a new cluster task directory.

        Args:
            source_path: Path to log source (directory or file).

        Returns:
            Tuple of (task_id, task_output_dir).
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"cluster-{timestamp}-{uuid.uuid4().hex[:6]}"
        task_output = self._data_dir / "output" / task_id
        task_output.mkdir(parents=True, exist_ok=True)
        return task_id, task_output

    def run(self, task_id: str, source_path: str) -> ClusterResult:
        """Run the full clustering pipeline.

        Args:
            task_id: The task identifier.
            source_path: Path to log source.

        Returns:
            ClusterResult with all clusters and matched cases.
        """
        task_output = self._data_dir / "output" / task_id

        # Phase 1: Scan and extract ERROR/WARN lines with streaming aggregation
        self._update_progress(task_output, PHASE_SCAN, 20)
        files, zip_source_path = self._prepare_file_list(source_path)
        total_files = len(files)
        aggregated_groups = self._scan_and_aggregate_streaming(
            task_output, files, total_files, zip_source_path=zip_source_path
        )

        if not aggregated_groups:
            result = ClusterResult(task_id=task_id, clusters=[], total_errors=0)
            self._write_result(task_output, result)
            self._update_progress(task_output, PHASE_DONE, 100)
            return result

        # Phase 2: Match historical cases
        self._update_progress(task_output, PHASE_MATCH, 80)
        clusters = self._match_historical_cases(aggregated_groups)

        # Phase 3: Write result
        self._update_progress(task_output, PHASE_DONE, 100)
        result = ClusterResult(
            task_id=task_id,
            clusters=clusters,
            total_errors=sum(g.count for g in clusters),
        )
        self._write_result(task_output, result)

        # Phase 4: Write matched-lines.jsonl for diagnosis cache
        # Use streaming when zip_source_path is available (no extractall)
        error_lines = self._scan_and_extract_errors_from_files(files, zip_source_path)
        self._write_matched_lines_cache(task_output, aggregated_groups, error_lines)

        return result

    def _update_progress(self, task_output: Path, status: str, progress: int) -> None:
        """Write progress.json at each phase transition."""
        progress_path = task_output / "progress.json"
        data = {
            "status": status,
            "progress": progress,
            "current_step": PROGRESS_LABELS.get(status, status),
            "updated_at": datetime.now().isoformat(),
        }
        progress_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def _prepare_file_list(self, source_path: str) -> tuple[list, Path | None]:
        """Prepare the list of files to scan.

        Args:
            source_path: Path to log directory, file, or ZIP archive.

        Returns:
            Tuple of (list of ScannedFile objects, zip_source_path or None).
            The second element is the ZIP file path itself when source is a ZIP
            (for streaming reads), or None for regular directories/files.
        """
        from diagnose_tool.analyzer.scanner import scan_directory

        source = Path(source_path)
        zip_source_path: Path | None = None

        # Handle ZIP archives - return ZIP path for streaming (no extractall)
        if source.is_file() and source.suffix.lower() == ".zip":
            zip_source_path = source
            from diagnose_tool.analyzer.scanner import ScannedFile
            files = [
                ScannedFile(
                    path=str(source.resolve()),
                    name=source.name,
                    size=source.stat().st_size,
                    type="zip",
                )
            ]
            return files, zip_source_path

        # Collect all files to scan
        if source.is_dir():
            scan_result = scan_directory(source)
            return list(scan_result.files), zip_source_path
        else:
            from diagnose_tool.analyzer.scanner import ScannedFile
            return [
                ScannedFile(
                    path=str(source.resolve()),
                    name=source.name,
                    size=source.stat().st_size,
                    type=source.suffix.removeprefix("."),
                )
            ], zip_source_path

    def _scan_and_extract_errors_gen(
        self, source_path: str
    ) -> Iterator[dict]:
        """Scan log source and yield ERROR/WARN lines as a generator.

        Memory-efficient: yields error lines one at a time instead of
        collecting all into a list.

        Args:
            source_path: Path to log directory, file, or ZIP archive.

        Yields:
            Log line dicts with timestamp, level, message, thread, raw.
        """
        files, _extracted_dir = self._prepare_file_list(source_path)
        error_level_pattern = re.compile(r"\b(ERROR|WARN|WARNING|SEVERE|FATAL)\b", re.IGNORECASE)
        timestamp_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
        )

        for file_info in files:
            file_path = Path(file_info.path)
            try:
                for log_line in self._read_log_lines(file_path):
                    if error_level_pattern.search(log_line.raw):
                        parsed = self._parse_log_line(log_line, timestamp_pattern)
                        yield parsed
            except Exception as e:
                logger.warning("Failed to read %s: %s", file_path, e)

    def _scan_and_extract_errors(
        self, source_path: str
    ) -> list[dict]:
        """Scan log source and extract ERROR/WARN lines.

        Args:
            source_path: Path to log directory, file, or ZIP archive.

        Returns:
            List of log line dicts with timestamp, level, message, thread, raw.
        """
        return list(self._scan_and_extract_errors_gen(source_path))

    def _scan_and_extract_errors_from_files(
        self, files: list, zip_source_path: Path | None = None
    ) -> list[dict]:
        """Extract ERROR/WARN lines from an already-prepared file list.

        When zip_source_path is provided, uses streaming to avoid disk I/O.

        Args:
            files: List of ScannedFile objects from _prepare_file_list.
            zip_source_path: ZIP file path for streaming read, or None for file-based.

        Returns:
            List of log line dicts with timestamp, level, message, thread, raw.
        """
        error_level_pattern = re.compile(r"\b(ERROR|WARN|WARNING|SEVERE|FATAL)\b", re.IGNORECASE)
        timestamp_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
        )
        results = []

        if zip_source_path is not None:
            # Streaming path: read directly from ZIP without extractall
            from diagnose_tool.analyzer.reader import read_log_lines_from_zip_streaming
            for log_line in read_log_lines_from_zip_streaming(zip_source_path):
                if error_level_pattern.search(log_line.raw):
                    parsed = self._parse_log_line(log_line, timestamp_pattern)
                    results.append(parsed)
            return results

        # File-based path: iterate over extracted files
        for file_info in files:
            file_path = Path(file_info.path)
            try:
                for log_line in self._read_log_lines(file_path):
                    if error_level_pattern.search(log_line.raw):
                        parsed = self._parse_log_line(log_line, timestamp_pattern)
                        results.append(parsed)
            except Exception as e:
                logger.warning("Failed to read %s: %s", file_path, e)

    def _scan_and_aggregate_streaming(
        self,
        task_output: Path,
        files: list,
        total_files: int,
        zip_source_path: Path | None = None,
    ) -> list:
        """Scan files and aggregate clusters in a streaming fashion.

        Memory-efficient: accumulates groups incrementally without storing
        all error lines in memory.

        Args:
            task_output: Task output directory for progress updates.
            files: List of files to scan.
            total_files: Total number of files for progress calculation.

        Returns:
            List of AggregatedGroup sorted by count descending.
        """
        from diagnose_tool.analyzer.log_aggregator import aggregate_log_lines_streaming, AggregationOptions

        error_level_pattern = re.compile(r"\b(ERROR|WARN|WARNING|SEVERE|FATAL)\b", re.IGNORECASE)
        timestamp_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
        )

        opts = AggregationOptions(
            group_by_exception=True,
            include_thread=False,
            include_time=True,
            message_only=False,
        )

        # Accumulators: key -> group data (memory-efficient)
        group_counts: dict[str, int] = defaultdict(int)
        group_first_line: dict[str, dict] = {}
        group_samples: dict[str, list[dict]] = defaultdict(list)

        processed_files = 0
        # 如果传入了 zip_source_path，直接流式读取 ZIP，跳过 files 列表
        if zip_source_path is not None:
            from diagnose_tool.analyzer.reader import read_log_lines_from_zip_streaming
            for log_line in read_log_lines_from_zip_streaming(zip_source_path):
                if error_level_pattern.search(log_line.raw):
                    parsed = self._parse_log_line(log_line, timestamp_pattern)
                    key = self._build_group_key(parsed, opts)
                    group_counts[key] += 1
                    if key not in group_first_line:
                        group_first_line[key] = parsed
                    if len(group_samples[key]) < MAX_SAMPLE_MESSAGES:
                        group_samples[key].append(parsed)
            processed_files = total_files
        else:
            # 现有的 for file_info in files: 循环
            for file_info in files:
                file_path = Path(file_info.path)
                try:
                    for log_line in self._read_log_lines(file_path):
                        if error_level_pattern.search(log_line.raw):
                            parsed = self._parse_log_line(log_line, timestamp_pattern)
                            key = self._build_group_key(parsed, opts)

                            group_counts[key] += 1
                            if key not in group_first_line:
                                group_first_line[key] = parsed
                            if len(group_samples[key]) < MAX_SAMPLE_MESSAGES:
                                group_samples[key].append(parsed)
                except Exception as e:
                    logger.warning("Failed to read %s: %s", file_path, e)

                processed_files += 1
                # Update progress every 10 files or at the end
                if processed_files % 10 == 0 or processed_files == total_files:
                    progress = 20 + int(30 * processed_files / total_files)
                    self._update_progress(task_output, PHASE_SCAN, progress)

        # Build AggregatedGroup list from accumulators
        results: list = []
        for key in group_counts:
            first = group_first_line[key]
            results.append(AggregatedGroup(
                key=key,
                count=group_counts[key],
                sample_message=self._build_sample_message(first, opts),
                sample_timestamp=first.get("timestamp") or "",
                sample_thread=first.get("thread") or "",
                sample_level=first.get("level") or "",
                file_path=first.get("file_path") or "",
                matched_lines=group_samples[key],
            ))

        results.sort(key=lambda g: g.count, reverse=True)
        return results

    def _build_group_key(self, line: dict, options: AggregationOptions) -> str:
        """Build a group key from a log line dict (duplicates log_aggregator logic)."""
        raw = line.get("raw", "") or ""
        exc = self._extract_exception_class(raw)
        if exc and options.group_by_exception:
            key = exc
        else:
            key = _normalize_message(line.get("message") or "")
        if options.include_time and line.get("timestamp"):
            ts = line["timestamp"]
            if "T" in ts:
                key = f"{key} [{ts[11:16]}]"
            elif " " in ts:
                key = f"{key} [{ts[11:16]}]"
        return key

    def _build_sample_message(self, line: dict, options: AggregationOptions) -> str:
        """Build a human-readable sample message line."""
        parts = []
        if options.include_time and line.get("timestamp"):
            parts.append(line["timestamp"][11:16])
        if not options.message_only and line.get("level"):
            parts.append(line["level"])
        msg = line.get("message") or line.get("raw") or ""
        parts.append(msg)
        return " ".join(parts)

    def _read_log_lines(self, path: Path):
        """Read log lines from a single file or .gz archive."""
        from diagnose_tool.analyzer.reader import read_log_lines_in_archive

        return read_log_lines_in_archive(path)

    def _extract_zip_archive(self, zip_path: Path) -> Path:
        """Extract a ZIP archive to a temporary directory.

        Args:
            zip_path: Path to the ZIP file.

        Returns:
            Path to the extracted directory. Caller is responsible for cleanup
            if they want to remove it.
        """
        import zipfile

        extract_dir = self._data_dir / "temp" / f"zip-{uuid.uuid4().hex[:8]}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
            logger.info("Extracted ZIP %s to %s", zip_path, extract_dir)
            return extract_dir
        except zipfile.BadZipFile:
            logger.warning("Invalid ZIP file: %s", zip_path)
            raise

    def _parse_log_line(
        self, log_line, timestamp_pattern: re.Pattern
    ) -> dict:
        """Parse a log line into structured fields."""
        raw = log_line.raw

        ts_match = timestamp_pattern.search(raw)
        timestamp = ts_match.group(1) if ts_match else ""

        level_match = re.search(r"\b(ERROR|WARN|WARNING|SEVERE|FATAL)\b", raw, re.IGNORECASE)
        level = level_match.group(1).upper() if level_match else ""

        # Extract thread from bracket patterns like [worker-1] or [service@host]
        thread_match = re.search(r"\[([^\]]+)\]", raw)
        thread = thread_match.group(1) if thread_match else ""

        # Extract message (everything after level, remove thread bracket)
        if level_match:
            msg_start = level_match.end()
            message = raw[msg_start:].strip()
            # Remove the thread bracket that appears right after level
            message = re.sub(r"^\[\S+\]\s*", "", message)
            # Clean up leading punctuation/spaces
            message = message.lstrip(":- ").lstrip()
        else:
            message = raw

        return {
            "timestamp": timestamp,
            "level": level,
            "thread": thread,
            "message": message,
            "raw": raw,
            "file_path": log_line.file_path,
        }

    def _aggregate_clusters(self, error_lines: list[dict]) -> list[AggregatedGroup]:
        """Aggregate error lines into clusters.

        Args:
            error_lines: List of parsed log line dicts.

        Returns:
            List of AggregatedGroup sorted by count descending.
        """
        if not error_lines:
            return []

        opts = AggregationOptions(
            group_by_exception=True,
            include_thread=False,
            include_time=True,
            message_only=False,
        )
        return aggregate_log_lines(error_lines, opts, max_sample_lines=MAX_SAMPLE_MESSAGES)

    def _match_historical_cases(
        self, aggregated_groups: list[AggregatedGroup]
    ) -> list[ClusterGroup]:
        """Match each cluster group against historical cases using dual-track matching.

        Args:
            aggregated_groups: List of AggregatedGroup from log_aggregator.

        Returns:
            List of ClusterGroup with matched historical cases.
        """
        if not self._cases_dir.exists():
            return [
                ClusterGroup(
                    exception_class=g.key,
                    count=g.count,
                    sample_messages=[g.sample_message],
                    time_distribution=self._compute_time_distribution(g),
                    matched_cases=[],
                )
                for g in aggregated_groups
            ]

        clusters: list[ClusterGroup] = []
        for group in aggregated_groups:
            exception_class = self._extract_exception_class(group.key)
            query = RetrievalQuery(
                exception_classes=[exception_class] if exception_class else [],
                keywords=self._extract_keywords_from_message(group.sample_message),
            )

            matched = self._dual_track_match(query, group)

            # Extract normalized sample messages (replace dynamic values)
            sample_msgs = []
            for m in group.matched_lines[:MAX_SAMPLE_MESSAGES]:
                raw_msg = m.get("message") or m.get("raw") or ""
                normalized = _normalize_message(raw_msg)
                sample_msgs.append(normalized)

            clusters.append(
                ClusterGroup(
                    exception_class=group.key,
                    count=group.count,
                    sample_messages=sample_msgs,
                    time_distribution=self._compute_time_distribution(group),
                    matched_cases=matched,
                )
            )

        return clusters

    def _dual_track_match(
        self, query: RetrievalQuery, group: AggregatedGroup
    ) -> list[MatchedCase]:
        """Dual-track matching: metadata + case body text."""
        all_matches: dict[str, float] = {}
        metadata_fields: dict[str, dict] = {}

        # Track 1: metadata field matching
        keyword_results = search_by_keywords(query, self._cases_dir)
        rule_results = match_by_rules(query, self._cases_dir)

        for case_id, score, metadata in keyword_results:
            all_matches[case_id] = all_matches.get(case_id, 0) + score * 0.6
            metadata_fields[case_id] = metadata

        for case_id, score, metadata in rule_results:
            all_matches[case_id] = all_matches.get(case_id, 0) + score * 0.6
            if case_id not in metadata_fields:
                metadata_fields[case_id] = metadata

        # Track 2: case body text matching
        body_scores = self._match_by_case_body(query, group)
        for case_id, score in body_scores.items():
            all_matches[case_id] = all_matches.get(case_id, 0) + score * 0.4

        # Sort and return top matches
        sorted_matches = sorted(all_matches.items(), key=lambda x: x[1], reverse=True)
        matched_cases: list[MatchedCase] = []

        for case_id, combined_score in sorted_matches[:3]:
            if combined_score < 0.3:
                break

            case_dir = self._cases_dir / case_id
            case_md_path = case_dir / "case.md"
            extracted = self._extractor.extract(case_md_path)
            metadata = metadata_fields.get(case_id, {})

            matched_cases.append(
                MatchedCase(
                    case_id=case_id,
                    score=round(combined_score, 2),
                    summary=extracted.get("summary", "") or metadata.get("summary", ""),
                    root_cause=extracted.get("root_cause"),
                    solution=extracted.get("solution"),
                )
            )

        return matched_cases

    def _match_by_case_body(
        self, query: RetrievalQuery, group: AggregatedGroup
    ) -> dict[str, float]:
        """Match query against case.md body text."""
        scores: dict[str, float] = {}

        if not query.exception_classes and not query.keywords:
            return scores

        search_terms = set()
        for exc in query.exception_classes:
            search_terms.add(exc.lower())
        for kw in query.keywords:
            search_terms.add(kw.lower())

        if not self._cases_dir.exists():
            return scores

        for case_dir in self._cases_dir.iterdir():
            if not case_dir.is_dir():
                continue
            case_md_path = case_dir / "case.md"
            if not case_md_path.exists():
                continue

            extracted = self._extractor.extract(case_md_path)
            case_text = " ".join(
                filter(None, [
                    extracted.get("summary", ""),
                    extracted.get("root_cause", "") or "",
                    extracted.get("solution", "") or "",
                ])
            ).lower()

            if not case_text:
                continue

            matches = sum(1 for term in search_terms if term in case_text)
            if matches > 0:
                scores[case_dir.name] = matches / len(search_terms)

        return scores

    def _extract_exception_class(self, key: str) -> str | None:
        """Extract exception class name from group key."""
        from diagnose_tool.analyzer.log_aggregator import _extract_exception_class
        return _extract_exception_class(key)

    def _extract_keywords_from_message(self, message: str) -> list[str]:
        """Extract potential keywords from a log message."""
        # Extract capitalized words that might be class/component names
        words = re.findall(r"\b[A-Z][a-zA-Z0-9]+\b", message)
        # Filter out common non-meaningful words
        filtered = [w for w in words if len(w) > 3 and w not in ("INFO", "DEBUG", "TRACE", "ERROR", "WARN", "SEVERE")]
        return filtered[:5]

    def _compute_time_distribution(self, group: AggregatedGroup) -> dict:
        """Compute time distribution for a cluster group."""
        timestamps: list[str] = []
        for line_dict in group.matched_lines:
            ts = line_dict.get("timestamp", "")
            if ts:
                timestamps.append(ts)

        if not timestamps:
            return {"peak_hour": "N/A", "range": "N/A"}

        hours: dict[str, int] = defaultdict(int)
        for ts in timestamps:
            if "T" in ts:
                hour = ts[11:13]
            elif " " in ts:
                hour = ts[11:13]
            else:
                continue
            hours[f"{hour}:00-{hour}:59"] += 1

        if not hours:
            return {"peak_hour": "N/A", "range": "N/A"}

        peak_hour = max(hours.items(), key=lambda x: x[1])[0]

        try:
            sorted_ts = sorted(timestamps)
            first = sorted_ts[0]
            last = sorted_ts[-1]
            if "T" in first:
                range_str = f"{first[11:16]} - {last[11:16]}"
            elif " " in first:
                range_str = f"{first[11:16]} - {last[11:16]}"
            else:
                range_str = "N/A"
        except Exception:
            range_str = "N/A"

        return {"peak_hour": peak_hour, "range": range_str}

    def _write_result(self, task_output: Path, result: ClusterResult) -> None:
        """Write cluster-result.json to task output directory."""
        result_path = task_output / "cluster-result.json"
        data = {
            "task_id": result.task_id,
            "total_errors": result.total_errors,
            "clusters": [
                {
                    "exception_class": c.exception_class,
                    "count": c.count,
                    "sample_messages": c.sample_messages,
                    "time_distribution": c.time_distribution,
                    "matched_cases": [
                        {
                            "case_id": mc.case_id,
                            "score": mc.score,
                            "summary": mc.summary,
                            "root_cause": mc.root_cause,
                            "solution": mc.solution,
                        }
                        for mc in c.matched_cases
                    ],
                }
                for c in result.clusters
            ],
        }
        result_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_matched_lines_cache(
        self,
        task_output: Path,
        aggregated_groups: list[AggregatedGroup],
        error_lines: list[dict],
    ) -> None:
        """Write matched-lines.jsonl for cluster diagnosis cache.

        Args:
            task_output: The task output directory path.
            aggregated_groups: List of AggregatedGroup from log aggregator.
            error_lines: Full list of error log lines for context.
        """
        matched_lines_path = task_output / "matched-lines.jsonl"
        if not aggregated_groups:
            return

        # Build event index from error_lines for context lookup
        event_index = self._build_event_index(error_lines)

        # Write each group's matched lines to cache, deduplicating by entry ID
        # to avoid hash collisions from repeated log entries with same file/line/timestamp
        seen_ids: set[str] = set()
        with matched_lines_path.open("w", encoding="utf-8") as f:
            for group in aggregated_groups:
                group_key = group.key
                for line_dict in group.matched_lines:
                    ts = line_dict.get("timestamp") or ""
                    fp = line_dict.get("file_path") or ""
                    ln = line_dict.get("line_no") or 0
                    entry_id = generate_entry_id(fp, ln, ts)
                    # Skip duplicate entries with same ID
                    if entry_id in seen_ids:
                        continue
                    seen_ids.add(entry_id)
                    entry = self._build_cache_entry(line_dict, group_key, event_index, error_lines)
                    f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def _build_event_index(self, error_lines: list[dict]) -> dict[str, int]:
        """Build an index of error lines by ID for context lookup."""
        index = {}
        for i, line in enumerate(error_lines):
            ts = line.get("timestamp") or ""
            fp = line.get("file_path") or ""
            ln = line.get("line_no") or 0
            entry_id = generate_entry_id(fp, ln, ts)
            index[entry_id] = i
        return index

    def _build_cache_entry(
        self,
        line_dict: dict,
        group_key: str,
        event_index: dict[str, int],
        error_lines: list[dict],
    ) -> CachedLogEntry:
        """Build a cache entry with context events."""
        ts = line_dict.get("timestamp") or ""
        fp = line_dict.get("file_path") or ""
        ln = line_dict.get("line_no") or 0
        entry_id = generate_entry_id(fp, ln, ts)

        event = LogEvent(
            timestamp=ts,
            level=line_dict.get("level") or "",
            thread=line_dict.get("thread") or "",
            message=line_dict.get("message") or "",
            raw=line_dict.get("raw") or "",
            file_path=fp,
            line_no=ln,
        )

        # Get context from error_lines using index
        context_before = self._get_context_events(event_index, entry_id, error_lines, direction=-1)
        context_after = self._get_context_events(event_index, entry_id, error_lines, direction=1)

        return CachedLogEntry(
            id=entry_id,
            group_key=group_key,
            event=event,
            context_before=context_before,
            context_after=context_after,
        )

    def _get_context_events(
        self,
        event_index: dict[str, int],
        current_id: str,
        error_lines: list[dict],
        direction: int,
    ) -> list[LogEvent]:
        """Get context events in a direction from error_lines."""
        if current_id not in event_index:
            return []
        current_pos = event_index[current_id]
        result = []
        pos = current_pos + direction
        for _ in range(5):  # CONTEXT_EVENTS = 5
            if 0 <= pos < len(error_lines):
                line = error_lines[pos]
                ts = line.get("timestamp") or ""
                fp = line.get("file_path") or ""
                ln = line.get("line_no") or 0
                result.append(LogEvent(
                    timestamp=ts,
                    level=line.get("level") or "",
                    thread=line.get("thread") or "",
                    message=line.get("message") or "",
                    raw=line.get("raw") or "",
                    file_path=fp,
                    line_no=ln,
                ))
                pos += direction
            else:
                break
        return result


def read_progress(task_output: Path) -> TaskProgress | None:
    """Read progress.json from task output directory."""
    progress_path = task_output / "progress.json"
    if not progress_path.exists():
        return None
    try:
        data = json.loads(progress_path.read_text(encoding="utf-8"))
        return TaskProgress(
            status=data.get("status", "unknown"),
            progress=data.get("progress", 0),
            current_step=data.get("current_step", ""),
        )
    except (OSError, json.JSONDecodeError):
        return None


def read_cluster_result(task_output: Path) -> ClusterResult | None:
    """Read cluster-result.json from task output directory."""
    result_path = task_output / "cluster-result.json"
    if not result_path.exists():
        return None
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
        clusters = []
        for c in data.get("clusters", []):
            matched_cases = [
                MatchedCase(
                    case_id=mc["case_id"],
                    score=mc["score"],
                    summary=mc["summary"],
                    root_cause=mc.get("root_cause"),
                    solution=mc.get("solution"),
                )
                for mc in c.get("matched_cases", [])
            ]
            clusters.append(
                ClusterGroup(
                    exception_class=c["exception_class"],
                    count=c["count"],
                    sample_messages=c.get("sample_messages", []),
                    time_distribution=c.get("time_distribution", {}),
                    matched_cases=matched_cases,
                )
            )
        return ClusterResult(
            task_id=data["task_id"],
            clusters=clusters,
            total_errors=data.get("total_errors", 0),
        )
    except (OSError, json.JSONDecodeError, KeyError):
        return None