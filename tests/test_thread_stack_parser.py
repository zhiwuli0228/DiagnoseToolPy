"""Tests for thread_stack_parser module."""

from __future__ import annotations

from diagnose_tool.analyzer.thread_stack_parser import (
    LockHint,
    ParseStatus,
    ThreadDumpResult,
    ThreadFrame,
    parse_thread_dump,
    parse_thread_dump_all,
)


# --- Fixtures -----------------------------------------------------------

STANDARD_DUMP = '''\
"http-nio-8080-exec-1" #42 daemon prio=5 os_prio=0 tid=0x00007f8b8c00a800 nid=0x1234 waiting on condition [0x00007f8b8bffe000]
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x000000076ab089b0> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
        at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
        at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1067)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1127)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
        at java.lang.Thread.run(Thread.java:748)

   Locked ownable synchronizers:
        - None
'''

BLOCKED_DUMP = '''\
"thread-name" #42 daemon prio=5 os_prio=0 tid=0x00007f8b8c00a800 nid=0x1234 waiting for monitor entry [0x00007f8b8bffe000]
   java.lang.Thread.State: BLOCKED (on object monitor)
        at com.demo.Service.process(Service.java:42)
        - waiting to lock <0x000000076ab089b0> (a java.lang.Object)
        at com.demo.Controller.handle(Controller.java:20)
'''

TRUNCATED_DUMP = '''\
"thread-name" #42 daemon prio=5 os_prio=0 tid=0x00007f8b8c00a800 nid=0x1234 waiting on condition [0x00007f8b8bffe000]
   java.lang.Thread.State: WAITING (parking)
'''

NATIVE_AND_UNKNOWN_DUMP = '''\
"mixed-thread" #10 prio=5 tid=0x00007f8b8c00b000 nid=0x5678 runnable [0x00007f8b8cffe000]
   java.lang.Thread.State: RUNNABLE
        at com.demo.NativeWorker.doWork(Native Method)
        at com.demo.UnknownWorker.process(Unknown Source)
        at com.demo.App.main(App.java:10)
'''

MINIMAL_HEADER_DUMP = '''\
"simple-thread" #1 prio=5 tid=0x00007f8b8c00c000 nid=0x9abc in Object.wait() [0x00007f8b8dffe000]
   java.lang.Thread.State: TIMED_WAITING (on object monitor)
        at java.lang.Object.wait(Native Method)
        at com.demo.Sleeper.sleep(Sleeper.java:30)
'''

MULTI_THREAD_DUMP = '''\
"main" #1 prio=5 tid=0x00007f8b8c00a000 nid=0x1000 runnable [0x00007f8b8affe000]
   java.lang.Thread.State: RUNNABLE
        at com.demo.Main.main(Main.java:10)

"worker-1" #2 daemon prio=5 tid=0x00007f8b8c00b000 nid=0x1001 waiting on condition [0x00007f8b8bffe000]
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        at com.demo.Worker.run(Worker.java:20)
'''


# --- Tests: standard dump ------------------------------------------------


class TestParseStandardDump:
    def test_thread_name(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert result.thread_name == "http-nio-8080-exec-1"

    def test_thread_state(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert result.thread_state == "WAITING"

    def test_parse_status_full(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert result.parse_status == ParseStatus.FULL

    def test_frame_count(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert len(result.frames) == 8

    def test_frame_ordering(self):
        result = parse_thread_dump(STANDARD_DUMP)
        methods = [f.method for f in result.frames]
        assert methods == [
            "park",
            "park",
            "await",
            "take",
            "getTask",
            "runWorker",
            "run",
            "run",
        ]

    def test_first_frame_is_native(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert result.frames[0].is_native is True
        assert result.frames[0].class_name == "sun.misc.Unsafe"
        assert result.frames[0].method == "park"

    def test_frame_with_line_number(self):
        result = parse_thread_dump(STANDARD_DUMP)
        park_frame = result.frames[1]  # LockSupport.park(LockSupport.java:175)
        assert park_frame.class_name == "java.util.concurrent.locks.LockSupport"
        assert park_frame.method == "park"
        assert park_frame.file_name == "LockSupport.java"
        assert park_frame.line_number == 175

    def test_lock_hints_captured(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert len(result.lock_hints) >= 1
        parking_hints = [h for h in result.lock_hints if h.hint_type == "parking"]
        assert len(parking_hints) == 1
        assert parking_hints[0].lock_address == "0x000000076ab089b0"

    def test_raw_text_preserved(self):
        result = parse_thread_dump(STANDARD_DUMP)
        assert result.raw_text == STANDARD_DUMP


# --- Tests: blocked dump ------------------------------------------------


class TestParseBlockedDump:
    def test_thread_name(self):
        result = parse_thread_dump(BLOCKED_DUMP)
        assert result.thread_name == "thread-name"

    def test_thread_state(self):
        result = parse_thread_dump(BLOCKED_DUMP)
        assert result.thread_state == "BLOCKED"

    def test_parse_status_full(self):
        result = parse_thread_dump(BLOCKED_DUMP)
        assert result.parse_status == ParseStatus.FULL

    def test_frame_count(self):
        result = parse_thread_dump(BLOCKED_DUMP)
        assert len(result.frames) == 2

    def test_waiting_to_lock_hint(self):
        result = parse_thread_dump(BLOCKED_DUMP)
        waiting_hints = [h for h in result.lock_hints if h.hint_type == "waiting_to_lock"]
        assert len(waiting_hints) == 1
        assert waiting_hints[0].lock_address == "0x000000076ab089b0"
        assert waiting_hints[0].lock_class == "java.lang.Object"

    def test_frames_in_order(self):
        result = parse_thread_dump(BLOCKED_DUMP)
        assert result.frames[0].class_name == "com.demo.Service"
        assert result.frames[0].method == "process"
        assert result.frames[1].class_name == "com.demo.Controller"
        assert result.frames[1].method == "handle"


# --- Tests: truncated dump ----------------------------------------------


class TestParseTruncatedDump:
    def test_status_partial(self):
        result = parse_thread_dump(TRUNCATED_DUMP)
        assert result.parse_status == ParseStatus.PARTIAL

    def test_thread_name_extracted(self):
        result = parse_thread_dump(TRUNCATED_DUMP)
        assert result.thread_name == "thread-name"

    def test_thread_state_extracted(self):
        result = parse_thread_dump(TRUNCATED_DUMP)
        assert result.thread_state == "WAITING"

    def test_no_frames(self):
        result = parse_thread_dump(TRUNCATED_DUMP)
        assert result.frames == []


# --- Tests: native and unknown source frames ----------------------------


class TestNativeAndUnknownFrames:
    def test_native_frame_preserved(self):
        result = parse_thread_dump(NATIVE_AND_UNKNOWN_DUMP)
        native = [f for f in result.frames if f.is_native]
        assert len(native) == 1
        assert native[0].class_name == "com.demo.NativeWorker"
        assert native[0].method == "doWork"
        assert native[0].file_name is None

    def test_unknown_source_preserved(self):
        result = parse_thread_dump(NATIVE_AND_UNKNOWN_DUMP)
        unknown = [f for f in result.frames if f.is_unknown_source]
        assert len(unknown) == 1
        assert unknown[0].class_name == "com.demo.UnknownWorker"
        assert unknown[0].method == "process"
        assert unknown[0].file_name is None

    def test_regular_frame_intact(self):
        result = parse_thread_dump(NATIVE_AND_UNKNOWN_DUMP)
        regular = [f for f in result.frames if not f.is_native and not f.is_unknown_source]
        assert len(regular) == 1
        assert regular[0].file_name == "App.java"
        assert regular[0].line_number == 10


# --- Tests: minimal header (no daemon/priority) -------------------------


class TestMinimalHeader:
    def test_parses_without_daemon_keyword(self):
        result = parse_thread_dump(MINIMAL_HEADER_DUMP)
        assert result.thread_name == "simple-thread"
        assert result.thread_state == "TIMED_WAITING"
        assert result.parse_status == ParseStatus.FULL

    def test_frame_count(self):
        result = parse_thread_dump(MINIMAL_HEADER_DUMP)
        assert len(result.frames) == 2


# --- Tests: malformed / safe input --------------------------------------


class TestMalformedInput:
    def test_empty_string(self):
        result = parse_thread_dump("")
        assert result.parse_status == ParseStatus.RAW
        assert result.thread_name is None
        assert result.frames == []

    def test_none_like_empty(self):
        result = parse_thread_dump("   \n  \n  ")
        assert result.parse_status == ParseStatus.RAW

    def test_random_text(self):
        result = parse_thread_dump("hello world, this is not a thread dump")
        assert result.parse_status == ParseStatus.RAW

    def test_partial_header_no_body(self):
        result = parse_thread_dump('"some-thread" #1')
        # Has a header line — partial
        assert result.thread_name == "some-thread"
        assert result.parse_status == ParseStatus.PARTIAL

    def test_garbage_lines_around_valid(self):
        text = '''\
"worker" #5 daemon prio=5 tid=0x00007f8b8c00a800 nid=0x1234 runnable [0x00007f8b8bffe000]
   java.lang.Thread.State: RUNNABLE
!!! garbage line !!!
        at com.demo.App.run(App.java:10)
random noise
'''
        result = parse_thread_dump(text)
        assert result.thread_name == "worker"
        assert result.thread_state == "RUNNABLE"
        assert len(result.frames) == 1
        assert result.parse_status == ParseStatus.FULL

    def test_does_not_raise_on_any_input(self):
        """The parser must never raise — all inputs return a result."""
        inputs = [
            "",
            "x" * 10000,
            "\x00\x01\x02",
            '"thread" #1\n\n\n',
            "at com.Foo.bar(Foo.java:1)",  # frames without header
            "java.lang.Thread.State: RUNNABLE",
        ]
        for raw in inputs:
            result = parse_thread_dump(raw)
            assert isinstance(result, ThreadDumpResult)


# --- Tests: parse_thread_dump_all ---------------------------------------


class TestParseAll:
    def test_multiple_threads(self):
        results = parse_thread_dump_all(MULTI_THREAD_DUMP)
        assert len(results) == 2
        assert results[0].thread_name == "main"
        assert results[1].thread_name == "worker-1"

    def test_single_thread(self):
        results = parse_thread_dump_all(STANDARD_DUMP)
        assert len(results) == 1
        assert results[0].thread_name == "http-nio-8080-exec-1"

    def test_empty_input(self):
        results = parse_thread_dump_all("")
        assert len(results) == 1
        assert results[0].parse_status == ParseStatus.RAW


# --- Tests: dataclass defaults ------------------------------------------


class TestDataclassDefaults:
    def test_thread_frame_defaults(self):
        f = ThreadFrame(raw_text="test")
        assert f.class_name is None
        assert f.method is None
        assert f.file_name is None
        assert f.line_number is None
        assert f.is_native is False
        assert f.is_unknown_source is False

    def test_lock_hint_defaults(self):
        h = LockHint(raw_text="test")
        assert h.hint_type == ""
        assert h.lock_address is None
        assert h.lock_class is None

    def test_thread_dump_result_defaults(self):
        r = ThreadDumpResult()
        assert r.thread_name is None
        assert r.thread_state is None
        assert r.frames == []
        assert r.lock_hints == []
        assert r.raw_text == ""
        assert r.parse_status == ParseStatus.RAW


# --- Tests: existing stack_parser contract unchanged ---------------------


class TestStackParserUnchanged:
    """Verify the existing exception stack parser still works identically."""

    def test_stack_parser_basic(self):
        from diagnose_tool.analyzer.stack_parser import parse_stack

        raw = """java.lang.NullPointerException
    at com.demo.OrderService.processOrder(OrderService.java:42)
    at com.demo.Controller.orderController(OrderController.java:20)"""
        result = parse_stack(raw)
        assert result.total_lines == 3
        assert len(result.frames) >= 1

    def test_stack_parser_imports_unchanged(self):
        from diagnose_tool.analyzer.stack_parser import (
            ParsedStack,
            StackFrame,
            StackParser,
            StackParserOptions,
            parse_stack,
        )
        # All public names still importable
        assert StackParser is not None
        assert ParsedStack is not None
        assert StackFrame is not None
        assert StackParserOptions is not None
        assert parse_stack is not None
