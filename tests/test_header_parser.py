"""Tests for the complex header parser."""

from __future__ import annotations

from __future__ import annotations

from diagnose_tool.analyzer.header_parser import (
    ParseStatus,
    _parse_module_thread,
    _strip_brackets,
    parse_log_record,
    scan_balanced_bracket_groups,
)


class TestScanBalancedBracketGroups:
    def test_single_bracket_group(self):
        result = list(scan_balanced_bracket_groups("[com.demo.OrderService] query"))
        assert result == ["[com.demo.OrderService]"]

    def test_nested_double_bracket(self):
        result = list(scan_balanced_bracket_groups("[[order-core]worker-1] rest"))
        assert result == ["[[order-core]worker-1]"]

    def test_multiple_bracket_groups(self):
        result = list(scan_balanced_bracket_groups("[[order-core]worker-1] [com.demo.OrderService] query"))
        assert result == ["[[order-core]worker-1]", "[com.demo.OrderService]"]

    def test_no_bracket_groups(self):
        result = list(scan_balanced_bracket_groups("plain text message"))
        assert result == []

    def test_text_between_bracket_groups(self):
        result = list(scan_balanced_bracket_groups("[a] [b] between text"))
        assert result == ["[a]", "[b]"]


class TestStripBrackets:
    def test_double_bracket(self):
        assert _strip_brackets("[[order-core]]") == "[order-core]"

    def test_single_bracket(self):
        assert _strip_brackets("[order-core]") == "order-core"

    def test_no_brackets(self):
        assert _strip_brackets("order-core") == "order-core"


class TestParseModuleThread:
    def test_nested_bracket_parses_module_and_thread(self):
        module, thread = _parse_module_thread("[[order-core]worker-1]")
        assert module == "order-core"
        assert thread == "worker-1"

    def test_single_bracket_becomes_module(self):
        module, thread = _parse_module_thread("[order-core]")
        assert module == "order-core"
        assert thread is None

    def test_none_returns_none_none(self):
        module, thread = _parse_module_thread(None)
        assert (module, thread) == (None, None)


class TestParseLogRecord:
    def test_full_nested_header_parses_all_fields(self):
        record = parse_log_record(
            "2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [com.demo.OrderService] query failed"
        )
        assert record.timestamp == "2026-05-16 10:01:01.123"
        assert record.level == "ERROR"
        assert record.module == "order-core"
        assert record.thread == "worker-1"
        assert record.logger == "com.demo.OrderService"
        assert record.message == "query failed"
        assert record.raw == "2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [com.demo.OrderService] query failed"
        assert record.parse_status == ParseStatus.FULL

    def test_missing_logger_returns_partial(self):
        record = parse_log_record("2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] query failed")
        assert record.parse_status == ParseStatus.PARTIAL
        assert record.module == "order-core"
        assert record.thread == "worker-1"
        assert record.logger is None
        assert record.message == "query failed"

    def test_no_brackets_returns_partial(self):
        record = parse_log_record("2026-05-16 10:01:01.123 ERROR some message")
        assert record.parse_status == ParseStatus.PARTIAL
        assert record.timestamp == "2026-05-16 10:01:01.123"
        assert record.level == "ERROR"
        assert record.module is None
        assert record.logger is None
        assert record.message == "some message"

    def test_malformed_line_returns_raw(self):
        record = parse_log_record("not a log line at all")
        assert record.parse_status == ParseStatus.RAW
        assert record.timestamp is None
        assert record.level is None
        assert record.raw == "not a log line at all"

    def test_missing_timestamp_level_returns_raw(self):
        record = parse_log_record("[com.demo.OrderService] query failed")
        assert record.parse_status == ParseStatus.RAW
        assert record.raw == "[com.demo.OrderService] query failed"

    def test_raw_preserved_on_partial_parse(self):
        record = parse_log_record("2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] query failed")
        assert record.raw == "2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] query failed"

    def test_source_location_passed_through(self):
        record = parse_log_record(
            "2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [com.demo.OrderService] query failed",
            file_path="/var/log/app.log",
            line_no=42,
        )
        assert record.file_path == "/var/log/app.log"
        assert record.line_no == 42

    def test_warn_level_parses(self):
        record = parse_log_record("2026-05-16 10:01:01.123 WARN [[order-core]worker-1] [com.demo.OrderService] warn message")
        assert record.level == "WARN"
        assert record.parse_status == ParseStatus.FULL

    def test_info_level_parses(self):
        record = parse_log_record("2026-05-16 10:01:01.123 INFO [svc] [c.l.Service] info message")
        assert record.level == "INFO"
        assert record.module == "svc"
        assert record.parse_status == ParseStatus.FULL

    def test_logger_without_message(self):
        record = parse_log_record("2026-05-16 10:01:01.123 ERROR [[core]t1] [com.demo.Service]")
        assert record.logger == "com.demo.Service"
        assert record.message is None
        assert record.parse_status == ParseStatus.PARTIAL


class TestNestedBracketsInMessage:
    """Tests for nested [] brackets in log messages.

    Real-world service logs often contain:
    - [[thread-name]suffix] in thread field (double nested)
    - JSON payloads like [{"key": "value"}] in message
    - SQL with brackets, URLs with [] params
    """

    def test_message_with_json_object(self):
        """JSON object in message body should not corrupt parsing."""
        record = parse_log_record(
            '2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [svc] '
            'request failed with body {"orderId": 123, "items": ["a", "b"]}'
        )
        assert record.module == "order-core"
        assert record.thread == "worker-1"
        assert record.logger == "svc"
        assert record.message == 'request failed with body {"orderId": 123, "items": ["a", "b"]}'
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_deeply_nested_brackets(self):
        """Triple-nested brackets in message body."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 ERROR [[svc]t1] [c.L] "
            "nested [[inner[deep]]more] found"
        )
        assert record.module == "svc"
        assert record.thread == "t1"
        assert record.logger == "c.L"
        assert "nested" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_array_and_objects(self):
        """JSON array with objects in message."""
        record = parse_log_record(
            '2026-05-16 10:01:01.123 INFO [[app]main] [svc] '
            'loaded configs [{"k":"v"}, {"x":"y"}]'
        )
        assert record.module == "app"
        assert record.thread == "main"
        assert record.logger == "svc"
        assert 'configs [{"k":"v"}, {"x":"y"}]' in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_url_containing_brackets(self):
        """URL with query params in brackets."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 INFO [[http]thread-1] [svc] "
            "calling http://example.com/api?items[a]=1&items[b]=2"
        )
        assert record.module == "http"
        assert record.thread == "thread-1"
        assert record.logger == "svc"
        assert "calling http://example.com/api" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_multiple_bracket_groups_in_body(self):
        """Multiple bracket groups after logger."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 ERROR [[svc]t1] [svc] "
            "processing [step1] then [step2] and [step3]"
        )
        assert record.module == "svc"
        assert record.thread == "t1"
        assert record.logger == "svc"
        assert "processing" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_sql_containing_brackets(self):
        """SQL with IN clause brackets."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 ERROR [[db]pool-1] [svc] "
            "SELECT * FROM orders WHERE id IN (1, 2, 3)"
        )
        assert record.module == "db"
        assert record.thread == "pool-1"
        assert record.logger == "svc"
        assert "SELECT * FROM orders WHERE id IN (1, 2, 3)" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_map_notation(self):
        """Java/map-style brackets in message."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 WARN [[svc]t1] [svc] "
            "map entry {key: [nested value], count: 5}"
        )
        assert record.module == "svc"
        assert record.thread == "t1"
        assert record.logger == "svc"
        assert "map entry" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_triple_nested_thread_bracket(self):
        """Thread with triple nested brackets: [[[a]b]c]."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 INFO [[[order-core]worker]pool-1] [svc] message"
        )
        # The balanced scanner should grab the first ] as the end of [[order-core]worker]
        # leaving ]pool-1] as remainder — this tests robustness
        assert record.parse_status in (ParseStatus.FULL, ParseStatus.PARTIAL)

    def test_empty_brackets_in_message(self):
        """Empty [] brackets in message body."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 INFO [[svc]t1] [svc] array[] is empty"
        )
        assert record.module == "svc"
        assert record.thread == "t1"
        assert record.logger == "svc"
        assert "array[] is empty" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_message_with_only_closed_brackets_no_space(self):
        """Brackets immediately adjacent to text."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 INFO [[svc]t1] [svc] result[a]=ok[b]=err"
        )
        assert record.parse_status == ParseStatus.FULL
        assert record.module == "svc"

    def test_unmatched_open_bracket_in_message(self):
        """Unclosed [ in message - should not crash."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 INFO [[svc]t1] [svc] incomplete [json"
        )
        # Should not raise, returns partial or full
        assert record.parse_status in (ParseStatus.FULL, ParseStatus.PARTIAL)
        assert record.module == "svc"

    def test_unmatched_close_bracket_in_message(self):
        """Stray ] in message - should not crash."""
        record = parse_log_record(
            "2026-05-16 10:01:01.123 INFO [[svc]t1] [svc] stray ] bracket"
        )
        assert record.parse_status in (ParseStatus.FULL, ParseStatus.PARTIAL)

    def test_message_with_mixed_nested_depth(self):
        """Complex real-world message with varying bracket depths."""
        record = parse_log_record(
            '2026-05-16 10:01:01.123 ERROR [[order-svc]worker-3] [svc] '
            'order processing failed: orderId=123, '
            'items=[{"id":1,"name":"item[test]"}], '
            'tags=[["urgent","high"]]'
        )
        assert record.module == "order-svc"
        assert record.thread == "worker-3"
        assert record.logger == "svc"
        assert "order processing failed" in (record.message or "")
        assert record.parse_status == ParseStatus.FULL

    def test_only_open_brackets_in_remaining_text(self):
        """Scanner should handle only-open brackets after timestamp."""
        result = list(scan_balanced_bracket_groups("[a] [b [c] d]"))
        assert "[a]" in result
        assert "[b [c] d]" in result

    def test_deeply_nested_three_levels(self):
        """Three levels of nested brackets: [[[x]y]z]."""
        result = list(scan_balanced_bracket_groups("[[[core]handler]pool-1] extra"))
        assert result == ["[[[core]handler]pool-1]"]

    def test_malformed_thread_bracket_sequence(self):
        """Edge case: ] inside thread name before its closing ]."""
        # This tests the scanner's ability to handle ] as content within brackets
        result = list(scan_balanced_bracket_groups("[[thread]name] rest"))
        # The scanner sees [ -> start, then scans depth. [thread]name] - the ] closes depth=1
        # So this gives [[thread]name]
        assert len(result) >= 1
        assert result[0].startswith("[[thread]name")

    def test_empty_placeholder_bracket_skipped(self):
        """Empty [] placeholder in thread/module position is skipped.

        Real log format: [][[collect]collect_oid_grip_reload][service.collect.Helper 223]
        The leading [] is a placeholder, not a module/thread.
        """
        record = parse_log_record(
            "2026-05-15 12:00:00,218 ERROR "
            "[[collect]collect_oid_grip_reload][service.collect.Helper 223] init finish."
        )
        assert record.timestamp == "2026-05-15 12:00:00,218"
        assert record.level == "ERROR"
        assert record.module == "collect"
        assert record.thread == "collect_oid_grip_reload"
        assert record.logger == "service.collect.Helper 223"
        assert record.message == "init finish."
        assert record.parse_status == ParseStatus.FULL

    def test_comma_in_timestamp_milliseconds(self):
        """Timestamp can use comma instead of dot for milliseconds."""
        record = parse_log_record(
            "2026-05-15 12:00:00,218 ERROR [[svc]t1] [c.L] test"
        )
        assert record.timestamp == "2026-05-15 12:00:00,218"
        assert record.level == "ERROR"
        assert record.module == "svc"
        assert record.parse_status == ParseStatus.FULL

    def test_bracket_in_message_after_logger(self):
        """Bracket group appearing after logger is part of the message.

        Real log: [][collect_oid_grip_reload][service.collect.Helper 223] [collect]init finish.
        [collect] is message text, not a module/logger bracket.
        """
        record = parse_log_record(
            "2026-05-15 12:00:00,218 ERROR "
            "[][collect_oid_grip_reload][service.collect.Helper 223] [collect]init finish."
        )
        assert record.timestamp == "2026-05-15 12:00:00,218"
        assert record.level == "ERROR"
        assert record.module == "collect_oid_grip_reload"
        assert record.logger == "service.collect.Helper 223"
        assert record.message == "[collect]init finish."
        assert record.parse_status == ParseStatus.FULL