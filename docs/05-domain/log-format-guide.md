# Log Format Guide

## Primary Supported Format

```text
时间 级别 [[服务内部模块]线程名] [类名信息] message
```

Example:

```text
2026-05-16 10:01:01.123 ERROR [[order-core]worker-1] [com.demo.OrderService] query failed
```

## Why This Is Hard

The header contains nested brackets:

```text
[[order-core]worker-1]
```

Do not parse bracket fields using simple `split("[")` or `split("]")`.

## Parsing Strategy

1. Parse timestamp and level using regex.
2. Parse bracket groups using balanced bracket scanning.
3. Parse first bracket group as module/thread.
4. Parse second bracket group as logger.
5. Treat remaining content as message.
6. If parsing fails, preserve raw content.

## Expected Fields

- timestamp
- level
- module
- thread
- logger
- message
- raw
- file_path
- line_no
- parse_status

## Parse Status

- `FULL`: full parse succeeded
- `PARTIAL`: timestamp/level or some fields parsed
- `RAW`: preserve raw content only

## Multiline Stack Trace

Lines not matching a log start pattern should be appended to the previous event.

Example:

```text
2026-05-16 10:01:01 ERROR [[task]worker] [com.demo.Task] failed
java.lang.RuntimeException: failed
    at com.demo.A.method(A.java:10)
Caused by: java.io.IOException
    at com.demo.B.method(B.java:20)
```

## JVM Thread Dump Parsing

A separate parser (`diagnose_tool/analyzer/thread_stack_parser.py`) handles HotSpot/OpenJDK thread dump blocks. This parser is independent from the exception stack parser (`stack_parser.py`).

### Input Format

The parser recognizes thread dump blocks produced by `jstack` or HotSpot VM diagnostics:

```text
"worker-1" #15 prio=5 os_prio=0 tid=0x00007f8b0c123800 nid=0x1a2b waiting on condition [0x00007f8b0c0fe000]
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x000000076ab00000> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
        at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
```

Supported elements:
- Quoted thread header line (thread name, thread ID, priority, OS priority, native ID, state hint, address range)
- `java.lang.Thread.State:` line (e.g., `RUNNABLE`, `WAITING`, `TIMED_WAITING`, `BLOCKED`, `NEW`, `TERMINATED`)
- `at ...` stack frames (fully qualified class.method and source location)
- Lock/wait hints (`- waiting to lock`, `- parking to wait for`, `- locked`, etc.)

### Output

`parse_thread_dump(raw_text)` returns a `ThreadDumpResult` dataclass:

- `thread_name` - extracted thread name (string or None)
- `thread_state` - parsed `Thread.State` value (string or None)
- `frames` - ordered list of `ThreadFrame` objects (`class_name`, `method`, `source`)
- `lock_hints` - list of `LockHint` objects (`kind`, `target`)
- `raw_text` - original input preserved
- `parse_status` - `ParseStatus` enum

`parse_thread_dump_all(raw_text)` returns a list of `ThreadDumpResult` for multi-thread dumps.

### Parse Status

The same `ParseStatus` enum is reused, but in the thread dump context:

- `FULL` - thread name, state, and at least one frame were extracted
- `PARTIAL` - some fields parsed (e.g., thread name but no frames)
- `RAW` - input not recognized as a thread dump block; raw content preserved

### Behavior on Malformed Input

The parser is conservative: it never raises on malformed or unrecognized input. If the input does not match the expected thread dump structure, the result carries `RAW` status with `raw_text` intact. Partial matches yield `PARTIAL` status with whatever fields could be extracted.
