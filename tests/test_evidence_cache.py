"""Tests for evidence_cache module."""

from __future__ import annotations

import pytest
from pathlib import Path

from diagnose_tool.analyzer.evidence_cache import (
    CONTEXT_EVENTS,
    CachedLogEntry,
    EvidenceCacheManager,
    LogEvent,
    generate_entry_id,
)


class TestGenerateEntryId:
    def test_same_inputs_produce_same_id(self):
        id1 = generate_entry_id("/path/to/file.log", 42, "2026-05-23 10:01:01")
        id2 = generate_entry_id("/path/to/file.log", 42, "2026-05-23 10:01:01")
        assert id1 == id2

    def test_different_file_produces_different_id(self):
        id1 = generate_entry_id("/path/to/file1.log", 42, "2026-05-23 10:01:01")
        id2 = generate_entry_id("/path/to/file2.log", 42, "2026-05-23 10:01:01")
        assert id1 != id2

    def test_different_line_produces_different_id(self):
        id1 = generate_entry_id("/path/to/file.log", 42, "2026-05-23 10:01:01")
        id2 = generate_entry_id("/path/to/file.log", 43, "2026-05-23 10:01:01")
        assert id1 != id2

    def test_different_timestamp_produces_different_id(self):
        id1 = generate_entry_id("/path/to/file.log", 42, "2026-05-23 10:01:01")
        id2 = generate_entry_id("/path/to/file.log", 42, "2026-05-23 10:01:02")
        assert id1 != id2

    def test_id_length_is_16(self):
        id1 = generate_entry_id("/path/to/file.log", 42, "2026-05-23 10:01:01")
        assert len(id1) == 16


class TestEvidenceCacheManager:
    def test_create_search_cache_returns_cache_key(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Connection failed",
                "raw": "2026-05-23 10:01:01 ERROR main Connection failed",
                "file_path": "/data/app.log",
                "line_no": 10,
            }
        ]
        group_keys = {0: "NullPointerException"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)

        assert cache_key.startswith("search-")
        assert (tmp_path / "output" / cache_key / "matched-lines.jsonl").exists()

    def test_create_search_cache_writes_meta(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error",
                "raw": "raw text",
                "file_path": "/data/app.log",
                "line_no": 10,
            }
        ]

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, {0: "group1"})
        meta_path = tmp_path / "output" / cache_key / "meta.json"

        assert meta_path.exists()
        import json
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["cache_key"] == cache_key
        assert meta["source_path"] == "/data"
        assert meta["type"] == "search"

    def test_load_matched_lines_returns_entries(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 1",
                "raw": "raw 1",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
            {
                "timestamp": "2026-05-23 10:01:02",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 2",
                "raw": "raw 2",
                "file_path": "/data/app.log",
                "line_no": 20,
            },
        ]
        group_keys = {0: "NullPointerException", 1: "NullPointerException"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)
        entries = cache_mgr.load_matched_lines(cache_key)

        assert len(entries) == 2
        assert all(isinstance(e, CachedLogEntry) for e in entries)
        assert entries[0].event.message == "Error 1"
        assert entries[1].event.message == "Error 2"

    def test_load_matched_lines_includes_context(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "INFO",
                "thread": "main",
                "message": "Line 1",
                "raw": "raw 1",
                "file_path": "/data/app.log",
                "line_no": 1,
            },
            {
                "timestamp": "2026-05-23 10:01:02",
                "level": "ERROR",
                "thread": "main",
                "message": "Error line",
                "raw": "raw 2",
                "file_path": "/data/app.log",
                "line_no": 2,
            },
            {
                "timestamp": "2026-05-23 10:01:03",
                "level": "INFO",
                "thread": "main",
                "message": "Line 3",
                "raw": "raw 3",
                "file_path": "/data/app.log",
                "line_no": 3,
            },
        ]
        group_keys = {0: "group", 1: "group", 2: "group"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)
        entries = cache_mgr.load_matched_lines(cache_key)

        # The middle entry should have context before and after
        middle_entry = entries[1]
        assert len(middle_entry.context_before) == 1  # CONTEXT_EVENTS = 5, but only 1 available
        assert len(middle_entry.context_after) == 1

    def test_load_matched_lines_nonexistent_returns_empty(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        entries = cache_mgr.load_matched_lines("nonexistent-cache")
        assert entries == []

    def test_get_entries_by_group(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 1",
                "raw": "raw 1",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
            {
                "timestamp": "2026-05-23 10:01:02",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 2",
                "raw": "raw 2",
                "file_path": "/data/app.log",
                "line_no": 20,
            },
        ]
        group_keys = {0: "NullPointerException", 1: "SqlException"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)
        entries = cache_mgr.get_entries_by_group(cache_key, "NullPointerException")

        assert len(entries) == 1
        assert entries[0].group_key == "NullPointerException"

    def test_get_entry_by_id(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 1",
                "raw": "raw 1",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        group_keys = {0: "group1"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)
        entries = cache_mgr.load_matched_lines(cache_key)
        entry_id = entries[0].id

        found = cache_mgr.get_entry_by_id(cache_key, entry_id)
        assert found is not None
        assert found.id == entry_id

    def test_get_entry_by_id_not_found(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 1",
                "raw": "raw 1",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]
        group_keys = {0: "group1"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)

        found = cache_mgr.get_entry_by_id(cache_key, "nonexistent-id")
        assert found is None

    def test_get_entries_by_ids(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 1",
                "raw": "raw 1",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
            {
                "timestamp": "2026-05-23 10:01:02",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 2",
                "raw": "raw 2",
                "file_path": "/data/app.log",
                "line_no": 20,
            },
            {
                "timestamp": "2026-05-23 10:01:03",
                "level": "ERROR",
                "thread": "main",
                "message": "Error 3",
                "raw": "raw 3",
                "file_path": "/data/app.log",
                "line_no": 30,
            },
        ]
        group_keys = {0: "group1", 1: "group1", 2: "group1"}

        cache_key = cache_mgr.create_search_cache("/data", matched_lines, group_keys)
        entries = cache_mgr.load_matched_lines(cache_key)

        # Get first and third entries by ID
        target_ids = [entries[0].id, entries[2].id]
        found = cache_mgr.get_entries_by_ids(cache_key, target_ids)

        assert len(found) == 2
        found_ids = {e.id for e in found}
        assert target_ids[0] in found_ids
        assert target_ids[1] in found_ids

    def test_list_caches(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error",
                "raw": "raw",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]

        # Create two caches
        key1 = cache_mgr.create_search_cache("/data1", matched_lines, {0: "g1"})
        key2 = cache_mgr.create_search_cache("/data2", matched_lines, {0: "g2"})

        caches = cache_mgr.list_caches()
        assert key1 in caches
        assert key2 in caches

    def test_list_caches_filtered_by_type(self, tmp_path: Path):
        cache_mgr = EvidenceCacheManager(tmp_path)
        matched_lines = [
            {
                "timestamp": "2026-05-23 10:01:01",
                "level": "ERROR",
                "thread": "main",
                "message": "Error",
                "raw": "raw",
                "file_path": "/data/app.log",
                "line_no": 10,
            },
        ]

        key = cache_mgr.create_search_cache("/data", matched_lines, {0: "g1"})

        all_caches = cache_mgr.list_caches()
        search_caches = cache_mgr.list_caches(cache_type="search")

        assert key in all_caches
        assert key in search_caches
