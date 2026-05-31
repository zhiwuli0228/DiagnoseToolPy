"""Tests for retrieval module."""

from __future__ import annotations

import json
import yaml
from pathlib import Path

import pytest

from diagnose_tool.retrieval import (
    build_retrieval_query,
    generate_prompt_context,
    match_by_rules,
    search_bm25,
    search_by_keywords,
)
from diagnose_tool.retrieval.query_builder import RetrievalQuery


class TestBuildRetrievalQuery:
    def test_build_query_from_file(self, tmp_path: Path):
        query_file = tmp_path / "retrieval-query.json"
        query_file.write_text(
            json.dumps({
                "task_id": "task-123",
                "summary": "Test summary",
                "components": ["order-core", "payment"],
                "fault_modes": ["timeout"],
                "exception_classes": [],
                "keywords": ["connection", "timeout"],
                "stack_symbols": [],
                "log_templates": [],
            }),
            encoding="utf-8",
        )

        query = build_retrieval_query(query_file)

        assert query.task_id == "task-123"
        assert query.summary == "Test summary"
        assert query.components == ["order-core", "payment"]
        assert query.fault_modes == ["timeout"]
        assert query.keywords == ["connection", "timeout"]

    def test_build_query_from_directory(self, tmp_path: Path):
        output_dir = tmp_path / "task_output"
        output_dir.mkdir()
        (output_dir / "retrieval-query.json").write_text(
            json.dumps({
                "task_id": "task-456",
                "summary": "Dir summary",
                "components": ["auth-service"],
                "fault_modes": ["auth_failure"],
                "exception_classes": ["UnauthorizedError"],
                "keywords": ["token", "expired"],
                "stack_symbols": [],
                "log_templates": [],
            }),
            encoding="utf-8",
        )

        query = build_retrieval_query(output_dir)

        assert query.task_id == "task-456"
        assert query.exception_classes == ["UnauthorizedError"]

    def test_build_query_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            build_retrieval_query(tmp_path / "nonexistent.json")

    def test_build_query_malformed_json(self, tmp_path: Path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json", encoding="utf-8")

        with pytest.raises(ValueError):
            build_retrieval_query(bad_file)


class TestKeywordSearch:
    def test_keyword_search_returns_scores(self, tmp_path: Path):
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()

        case1_dir = cases_dir / "CASE-001_test-case"
        case1_dir.mkdir()
        metadata1 = {
            "case_id": "CASE-001",
            "title": "Test Case",
            "slug": "test-case",
            "source_type": "auto",
            "status": "archived",
            "confidence": "confirmed",
            "tags": ["timeout", "network"],
            "components": ["order-service"],
            "fault_modes": ["timeout"],
            "exception_classes": [],
            "key_phrases": [],
        }
        with (case1_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(metadata1, f)
        (case1_dir / "case.md").write_text(
            "# Test Case\nConnection timeout occurred.\n", encoding="utf-8"
        )

        index_file = cases_dir / "index.yaml"
        with index_file.open("w", encoding="utf-8") as f:
            yaml.dump([{"case_id": "CASE-001", "title": "Test Case", "slug": "test-case"}], f)

        query = RetrievalQuery(
            keywords=["timeout", "connection"],
            components=["order-service"],
            fault_modes=["timeout"],
        )

        results = search_by_keywords(query, cases_dir)

        assert len(results) == 1
        assert results[0][0] == "CASE-001_test-case"
        assert results[0][1] > 0

    def test_keyword_search_empty_on_no_match(self, tmp_path: Path):
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()

        case1_dir = cases_dir / "CASE-001_no-match"
        case1_dir.mkdir()
        metadata1 = {
            "case_id": "CASE-001",
            "title": "No Match Case",
            "slug": "no-match",
            "source_type": "auto",
            "status": "archived",
            "confidence": "confirmed",
            "tags": ["database"],
            "components": ["db-service"],
            "fault_modes": [],
            "exception_classes": [],
            "key_phrases": [],
        }
        with (case1_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(metadata1, f)
        (case1_dir / "case.md").write_text("# No Match\n", encoding="utf-8")

        query = RetrievalQuery(
            keywords=["completely", "different", "keywords"],
            components=["other-service"],
            fault_modes=["other-fault"],
        )

        results = search_by_keywords(query, cases_dir)

        assert results == []


class TestRuleMatcher:
    def test_rule_matcher_returns_scores(self, tmp_path: Path):
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()

        case1_dir = cases_dir / "CASE-001_rule-test"
        case1_dir.mkdir()
        metadata1 = {
            "case_id": "CASE-001",
            "title": "Rule Test",
            "slug": "rule-test",
            "source_type": "auto",
            "status": "archived",
            "confidence": "confirmed",
            "tags": ["critical", "payment"],
            "components": ["payment-gateway"],
            "fault_modes": ["transaction_failed"],
            "exception_classes": ["PaymentException"],
            "key_phrases": ["card declined"],
        }
        with (case1_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(metadata1, f)
        (case1_dir / "case.md").write_text("# Rule Test\n", encoding="utf-8")

        query = RetrievalQuery(
            fault_modes=["transaction_failed"],
            exception_classes=["PaymentException"],
            components=["payment-gateway"],
        )

        results = match_by_rules(query, cases_dir)

        assert len(results) == 1
        assert results[0][0] == "CASE-001_rule-test"
        assert results[0][1] > 0

    def test_rule_matcher_empty_on_no_match(self, tmp_path: Path):
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()

        case1_dir = cases_dir / "CASE-001_nomatch"
        case1_dir.mkdir()
        metadata1 = {
            "case_id": "CASE-001",
            "title": "No Match",
            "slug": "nomatch",
            "source_type": "auto",
            "status": "archived",
            "confidence": "confirmed",
            "tags": [],
            "components": [],
            "fault_modes": ["unknown"],
            "exception_classes": [],
            "key_phrases": [],
        }
        with (case1_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(metadata1, f)
        (case1_dir / "case.md").write_text("# No Match\n", encoding="utf-8")

        query = RetrievalQuery(
            fault_modes=["completely_different_fault"],
        )

        results = match_by_rules(query, cases_dir)

        assert results == []


class TestBM25Search:
    def test_bm25_returns_scores(self, tmp_path: Path):
        import importlib.util
        if importlib.util.find_spec("rank_bm25") is None:
            pytest.skip("rank-bm25 not installed")

        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()

        case1_dir = cases_dir / "CASE-001_bm25"
        case1_dir.mkdir()
        metadata1 = {
            "case_id": "CASE-001",
            "title": "BM25 Test",
            "slug": "bm25",
            "source_type": "auto",
            "status": "archived",
            "confidence": "confirmed",
            "tags": [],
            "components": [],
            "fault_modes": [],
            "exception_classes": [],
            "key_phrases": [],
        }
        with (case1_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(metadata1, f)
        (case1_dir / "case.md").write_text(
            "# BM25 Test\nConnection pool exhausted, database timeout.\n", encoding="utf-8"
        )

        query = RetrievalQuery(keywords=["connection", "pool", "exhausted"])

        results = search_bm25(query, cases_dir)

        assert len(results) >= 1
        assert results[0][0] == "CASE-001_bm25"
        assert results[0][1] != 0  # BM25 can return negative scores; any non-zero score means a match

    def test_bm25_empty_when_not_available(self, tmp_path: Path):
        import diagnose_tool.retrieval.bm25_search as bm25_module

        original_available = bm25_module._BM25_AVAILABLE

        try:
            bm25_module._BM25_AVAILABLE = False

            query = RetrievalQuery(keywords=["test"])
            results = search_bm25(query, tmp_path)

            assert results == []
        finally:
            bm25_module._BM25_AVAILABLE = original_available


class TestPromptContext:
    def test_prompt_context_has_markers(self, tmp_path: Path):
        query = RetrievalQuery(
            task_id="task-789",
            summary="Current issue analysis",
        )

        cases = [
            ("CASE-001_test", 5.0, {
                "title": "Historical Timeout",
                "summary": "Previous timeout issue",
                "fault_modes": ["timeout"],
                "components": ["order-service"],
                "tags": ["critical"],
            }),
        ]

        context = generate_prompt_context(query, cases, max_cases=3)

        assert "References Only" in context or "references only" in context.lower()
        assert "CASE-001_test" in context
        assert "Historical Timeout" in context

    def test_prompt_context_bounded(self, tmp_path: Path):
        query = RetrievalQuery(task_id="task-bound")

        cases = [
            (f"CASE-{i:03d}_case", float(i), {
                "title": f"Case {i}",
                "summary": f"Summary {i}",
                "fault_modes": [],
                "components": [],
                "tags": [],
            })
            for i in range(10)
        ]

        context = generate_prompt_context(query, cases, max_cases=3)

        assert "Case 1" in context or "CASE-001_case" in context
        assert context.count("### Case:") == 3

    def test_prompt_context_empty(self, tmp_path: Path):
        query = RetrievalQuery(task_id="task-empty")

        context = generate_prompt_context(query, [], max_cases=3)

        assert "No similar" in context or "no similar" in context.lower()
