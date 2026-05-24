"""Tests for stack_parser module."""

from __future__ import annotations

import pytest

from diagnose_tool.analyzer.stack_parser import (
    ParsedStack,
    StackFrame,
    StackParser,
    StackParserOptions,
    parse_stack,
)


class TestStackFrame:
    def test_to_short_string_with_line(self):
        frame = StackFrame(
            class_name="com.demo.OrderService",
            method="processOrder",
            file_name="OrderService.java",
            line_number=42,
        )
        assert frame.to_short_string() == "com.demo.OrderService.processOrder(OrderService.java:42)"

    def test_to_short_string_without_line(self):
        frame = StackFrame(
            class_name="com.demo.OrderService",
            method="processOrder",
            file_name="OrderService.java",
            line_number=None,
        )
        assert frame.to_short_string() == "com.demo.OrderService.processOrder(OrderService.java)"

    def test_to_string_normal(self):
        frame = StackFrame(
            class_name="com.demo.OrderService",
            method="processOrder",
            file_name="OrderService.java",
            line_number=42,
        )
        assert frame.to_string() == "at com.demo.OrderService.processOrder(OrderService.java:42)"

    def test_to_string_native(self):
        frame = StackFrame(
            class_name="com.demo.OrderService",
            method="nativeMethod",
            file_name=None,
            line_number=None,
            is_native=True,
        )
        # Native frames show null for file_name since it's None
        assert "nativeMethod" in frame.to_string()
        assert "(native)" in frame.to_string()


class TestParsedStack:
    def test_to_display_string(self):
        frames = [
            StackFrame("com.demo.A", "methodA", "A.java", 10),
            StackFrame("com.demo.B", "methodB", "B.java", 20),
        ]
        stack = ParsedStack(
            total_lines=2,
            display_lines=2,
            exception_type=None,
            entry_point=None,
            frames=frames,
        )
        result = stack.to_display_string()
        assert "com.demo.A.methodA(A.java:10)" in result
        assert "com.demo.B.methodB(B.java:20)" in result

    def test_to_display_string_truncated(self):
        frames = [
            StackFrame("com.demo.A", "methodA", "A.java", 10),
        ]
        stack = ParsedStack(
            total_lines=100,
            display_lines=1,
            exception_type=None,
            entry_point=None,
            frames=frames,
            truncated=True,
            truncated_count=99,
        )
        result = stack.to_display_string()
        assert "99 行已省略" in result


class TestStackParserOptions:
    def test_default_options(self):
        opts = StackParserOptions()
        assert opts.max_lines == 50
        assert opts.merge_repeated is True
        assert opts.merge_package is True
        assert opts.show_suggestion is True
        assert opts.suggestion_threshold == 30


class TestStackParser:
    @pytest.fixture
    def parser(self):
        return StackParser()

    def test_parse_simple_hotspot_format(self, parser):
        raw = """java.lang.NullPointerException
    at com.demo.OrderService.processOrder(OrderService.java:42)
    at com.demo.Controller.orderController(OrderController.java:20)"""
        result = parser.parse(raw)
        assert result.total_lines == 3
        assert result.exception_type is None  # No "Caused by:" pattern
        # Both frames are in same package, so package merging keeps only one
        assert len(result.frames) == 1
        assert result.frames[0].class_name == "com.demo.OrderService"
        assert result.frames[0].method == "processOrder"
        assert result.frames[0].file_name == "OrderService.java"
        assert result.frames[0].line_number == 42

    def test_parse_with_caused_by(self, parser):
        raw = """java.lang.Exception
Caused by: java.lang.NullPointerException
    at com.demo.Service.method(Service.java:100)"""
        result = parser.parse(raw)
        assert result.exception_type == "java.lang.NullPointerException"

    def test_parse_native_method(self, parser):
        raw = """java.lang.Exception
    at com.demo.NativeMethod.execute(Native Method)
    at com.framework.Service.main(Service.java:50)"""
        result = parser.parse(raw)
        # Only the second frame is parsed (different packages avoid merging)
        native_frames = [f for f in result.frames if f.is_native]
        assert len(native_frames) >= 1
        assert native_frames[0].file_name is None

    def test_parse_unknown_source(self, parser):
        raw = """java.lang.Exception
    at com.demo.Unknown.method(Unknown Source)
    at com.framework.Service.main(Service.java:50)"""
        result = parser.parse(raw)
        unknown_frames = [f for f in result.frames if f.is_native]
        assert len(unknown_frames) >= 1

    def test_parse_entry_point_detection(self, parser):
        # Use different packages to avoid merging, and put DispatcherServlet first
        raw = """java.lang.Exception
    at org.springframework.web.servlet.DispatcherServlet.doGet(DispatcherServlet.java:100)
    at com.demo.Controller.handle(Controller.java:30)"""
        result = parser.parse(raw)
        # Entry point should be DispatcherServlet since it's a known entry point class
        assert result.entry_point is not None
        assert "DispatcherServlet" in result.entry_point

    def test_parse_empty_input(self, parser):
        result = parser.parse("")
        assert result.total_lines == 0
        assert result.frames == []
        assert result.exception_type is None

    def test_merge_repeated_frames(self, parser):
        raw = """java.lang.Exception
    at com.demo.A.method(A.java:10)
    at com.demo.A.method(A.java:10)
    at com.demo.A.method(A.java:10)
    at com.demo.B.method(B.java:20)"""
        result = parser.parse(raw)
        # Repeated frames should be merged, but count is tracked
        assert len(result.frames) <= 4
        assert len(result.repeat_groups) >= 1

    def test_merge_package_frames(self, parser):
        raw = """java.lang.Exception
    at com.demo.internal.Cache.get(Cache.java:10)
    at com.demo.internal.Cache.put(Cache.java:20)
    at com.demo.internal.Cache.remove(Cache.java:30)
    at com.demo.Controller.handle(Controller.java:40)"""
        result = parser.parse(raw)
        # Same-package frames should be merged
        assert len(result.package_groups) >= 1

    def test_truncation(self):
        parser = StackParser(StackParserOptions(max_lines=5, merge_package=False))
        lines = []
        for i in range(20):
            lines.append(f"    at com.demo.Class{i}.method(File.java:{i})")
        raw = "java.lang.Exception\n" + "\n".join(lines)
        result = parser.parse(raw)
        assert result.truncated is True
        assert result.display_lines <= 5

    def test_truncation_keeps_head_and_tail(self):
        parser = StackParser(StackParserOptions(max_lines=5, merge_package=False))
        lines = []
        for i in range(20):
            lines.append(f"    at com.demo.Class{i}.method(File.java:{i})")
        raw = "java.lang.Exception\n" + "\n".join(lines)
        result = parser.parse(raw)
        # Should keep first 2 and last 3 (since max_lines=5, keep_head=2, keep_tail=3)
        frame_strings = [f.to_short_string() for f in result.frames]
        assert "Class0.method" in frame_strings[0]
        assert "Class19.method" in frame_strings[-1]

    def test_no_truncation_under_limit(self):
        parser = StackParser(StackParserOptions(max_lines=50))
        lines = [f"    at com.demo.Class{i}.method(File.java:{i})" for i in range(30)]
        raw = "java.lang.Exception\n" + "\n".join(lines)
        result = parser.parse(raw)
        assert result.truncated is False
        assert result.truncated_count == 0

    def test_merge_repeated_disabled(self):
        parser = StackParser(StackParserOptions(merge_repeated=False))
        raw = """java.lang.Exception
    at com.demo.A.method(A.java:10)
    at com.demo.A.method(A.java:10)
    at com.demo.A.method(A.java:10)
    at com.demo.B.method(B.java:20)"""
        result = parser.parse(raw)
        # Should not merge when disabled
        assert len(result.repeat_groups) == 0

    def test_merge_package_disabled(self):
        parser = StackParser(StackParserOptions(merge_package=False))
        raw = """java.lang.Exception
    at com.demo.internal.Cache.get(Cache.java:10)
    at com.demo.internal.Cache.put(Cache.java:20)
    at com.demo.Controller.handle(Controller.java:30)"""
        result = parser.parse(raw)
        assert len(result.package_groups) == 0

    def test_anonymous_class_format(self):
        parser = StackParser()
        raw = """java.lang.Exception
    at com.demo.Controller$$Lambda$12345/0x00000000.resolve(Unknown Source)
    at com.demo.Controller.handle(Controller.java:30)"""
        result = parser.parse(raw)
        assert len(result.frames) >= 1

    def test_classload_format(self):
        parser = StackParser()
        raw = """java.lang.Exception
    at com.demo.Classload.checkValid(Classload.java:100+10)
    at com.demo.Controller.handle(Controller.java:30)"""
        result = parser.parse(raw)
        # Should parse the classload format with offset
        assert len(result.frames) >= 1

    def test_needs_suggestion_under_threshold(self):
        parser = StackParser(StackParserOptions(suggestion_threshold=30))
        lines = [f"    at com.demo.Class{i}.method(File.java:{i})" for i in range(20)]
        raw = "java.lang.Exception\n" + "\n".join(lines)
        assert parser.needs_suggestion(raw) is False

    def test_needs_suggestion_over_threshold(self):
        parser = StackParser(StackParserOptions(suggestion_threshold=30))
        lines = [f"    at com.demo.Class{i}.method(File.java:{i})" for i in range(40)]
        raw = "java.lang.Exception\n" + "\n".join(lines)
        assert parser.needs_suggestion(raw) is True


class TestParseStackConvenienceFunction:
    def test_parse_stack_default_options(self):
        raw = """java.lang.NullPointerException
    at com.demo.Service.method(Service.java:50)"""
        result = parse_stack(raw)
        assert result.total_lines == 2
        assert len(result.frames) == 1
        assert result.frames[0].method == "method"

    def test_parse_stack_custom_max_lines(self):
        lines = [f"    at com.demo.Class{i}.method(File.java:{i})" for i in range(100)]
        raw = "java.lang.Exception\n" + "\n".join(lines)
        result = parse_stack(raw, max_lines=10, merge_package=False)
        assert result.display_lines == 10
        assert result.truncated is True

    def test_parse_stack_disable_merging(self):
        raw = """java.lang.Exception
    at com.demo.A.method(A.java:10)
    at com.demo.A.method(A.java:10)
    at com.demo.internal.Cache.get(Cache.java:10)
    at com.demo.internal.Cache.put(Cache.java:20)"""
        result = parse_stack(raw, merge_repeated=False, merge_package=False)
        assert len(result.repeat_groups) == 0
        assert len(result.package_groups) == 0
