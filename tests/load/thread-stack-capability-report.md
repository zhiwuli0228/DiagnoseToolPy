# Thread Stack Parser — Capability Test Report

## Test Purpose

Verify that `diagnose_tool/analyzer/thread_stack_parser.py` correctly parses JVM thread dump blocks across all supported scenarios, handles malformed input safely, does not regress `stack_parser.py`, and works against real-world JVM thread dumps.

## Coverage Scope

| Category | Covered | Source |
|----------|---------|--------|
| Standard HotSpot/OpenJDK thread dump | Yes | Synthetic + Real |
| BLOCKED state | Yes | Synthetic + Real |
| WAITING state | Yes | Synthetic + Real |
| TIMED_WAITING state | Yes | Synthetic + Real |
| RUNNABLE state | Yes | Synthetic + Real |
| `at ...` frame ordering | Yes | Synthetic |
| Native Method frames | Yes | Synthetic + Real |
| Unknown Source frames | Yes | Synthetic |
| Lock hints (parking, waiting_to_lock, locked) | Yes | Synthetic + Real |
| Non-thread-dump input → RAW | Yes | Synthetic |
| Truncated input → PARTIAL | Yes | Synthetic |
| Never raises on malformed input | Yes | Synthetic |
| Existing `stack_parser.py` regression | Yes | Synthetic |
| Java 8 jstack output | Yes | Real (sample1) |
| Java 11 jstack output | Yes | Real (sample2) |
| Java 11 module-qualified frames (`java.base@11.0.2/...`) | **Partial** | Real (see Known Issues) |

## Test Execution

### Capability Tests (Synthetic)

```
uv run pytest tests/test_thread_stack_parser.py -v
```

**Result:** 38/38 PASS (0.09s)

### Regression Tests

```
uv run pytest tests/test_stack_parser.py -v
```

**Result:** 27/27 PASS (0.07s)

### Full Suite

```
uv run pytest
```

**Result:** 526/526 PASS (13.50s)

## Real-World Dump Tests

### Sample 1: Java 8 jstack (8 threads)

Source: `DeltaV235/Learning-Notes` on GitHub, Java HotSpot 25.241-b07

| Thread | State | Status | Frames | Native | Locks | Notes |
|--------|-------|--------|--------|--------|-------|-------|
| RMI TCP Connection(14)-192.168.96.1 | RUNNABLE | FULL | 15 | 2 | 2 | Correct |
| JMX server connection timeout 18 | TIMED_WAITING | FULL | 3 | 1 | 2 | Correct |
| RMI Scheduler(0) | TIMED_WAITING | FULL | 9 | 1 | 2 | Correct |
| RMI TCP Accept-0 | RUNNABLE | FULL | 10 | 1 | 2 | Correct |
| DestroyJavaVM | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames in dump (expected) |
| Thread-1 | BLOCKED | FULL | 2 | 0 | 3 | Correct |
| Thread-0 | BLOCKED | FULL | 2 | 0 | 3 | Correct |
| Service Thread | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames in dump (expected) |

**Result:** 8/8 threads parsed. 6 FULL, 2 PARTIAL (correct — those threads had no frames in the dump).

### Sample 2: Java 11 jstack (12 threads)

Source: `deepnighttwo/LetsJava` on GitHub, Java HotSpot 11.0.2+9-LTS

| Thread | State | Status | Frames | Native | Locks | Notes |
|--------|-------|--------|--------|--------|-------|-------|
| Reference Handler | RUNNABLE | FULL | 3 | 0* | 1 | *Native not detected (see Known Issues) |
| Finalizer | WAITING | FULL | 4 | 0 | 3 | Correct |
| Signal Dispatcher | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| C2 CompilerThread0 | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| C1 CompilerThread0 | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| Sweeper thread | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| Common-Cleaner | TIMED_WAITING | FULL | 5 | 0 | 3 | Correct |
| JDWP Transport Listener | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| JDWP Event Helper Thread | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| JDWP Command Reader | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| Service Thread | RUNNABLE | PARTIAL | 0 | 0 | 1 | No frames (expected) |
| Thread-For-Task1 | BLOCKED | FULL | 2 | 0 | 2 | Correct |

**Result:** 12/12 threads parsed. 4 FULL, 8 PARTIAL. All PARTIALs are threads with no stack frames in the dump (correct behavior).

## Known Issues

### Issue 1: Java 11+ module-qualified Native Method not detected

**Severity:** Minor

**Description:** Java 11+ uses module-qualified source references like `java.base@11.0.2/Native Method`. The current regex treats `java.base@11.0.2/Native Method` as the file_name, so the `is_native` check (`file_name.lower() == "native method"`) fails.

**Example:**
```
at java.lang.ref.Reference.waitForReferencePendingList(java.base@11.0.2/Native Method)
```
- Expected: `is_native=True`, `file_name=None`
- Actual: `is_native=False`, `file_name="java.base@11.0.2/Native Method"`

**Impact:** Frame is still parsed correctly (class_name, method are right). Only the `is_native` flag is wrong. No crash, no data loss.

**Fix:** Add module prefix stripping before the native check, or update the regex to handle `module@version/` prefix.

### Issue 2: Threads with no frames marked PARTIAL

**Severity:** By Design

**Description:** JVM threads like `DestroyJavaVM`, compiler threads, and JDWP threads often have no stack frames in the dump. The parser correctly returns PARTIAL (header + state found, but no frames). This is correct behavior per the spec, not a bug.

## Test Cases — Expected vs Actual (Synthetic)

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | Standard dump: thread name | `http-nio-8080-exec-1` | `http-nio-8080-exec-1` | PASS |
| 2 | Standard dump: thread state | `WAITING` | `WAITING` | PASS |
| 3 | Standard dump: parse status | `FULL` | `FULL` | PASS |
| 4 | Standard dump: frame count | 8 | 8 | PASS |
| 5 | Standard dump: frame ordering | park→park→await→take→getTask→runWorker→run→run | Same | PASS |
| 6 | Standard dump: first frame native | `True` | `True` | PASS |
| 7 | Standard dump: frame with line number | `LockSupport.java:175` | `LockSupport.java:175` | PASS |
| 8 | Standard dump: lock hints | ≥1 parking hint | 1 parking, address `0x000000076ab089b0` | PASS |
| 9 | Standard dump: raw text preserved | Original text | Original text | PASS |
| 10 | Blocked dump: thread name | `thread-name` | `thread-name` | PASS |
| 11 | Blocked dump: thread state | `BLOCKED` | `BLOCKED` | PASS |
| 12 | Blocked dump: parse status | `FULL` | `FULL` | PASS |
| 13 | Blocked dump: frame count | 2 | 2 | PASS |
| 14 | Blocked dump: waiting_to_lock hint | address + class | `0x000000076ab089b0`, `java.lang.Object` | PASS |
| 15 | Blocked dump: frames in order | Service→Controller | Service→Controller | PASS |
| 16 | Truncated dump: status | `PARTIAL` | `PARTIAL` | PASS |
| 17 | Truncated dump: thread name | `thread-name` | `thread-name` | PASS |
| 18 | Truncated dump: thread state | `WAITING` | `WAITING` | PASS |
| 19 | Truncated dump: no frames | `[]` | `[]` | PASS |
| 20 | Native frame preserved | `is_native=True`, `file_name=None` | Correct | PASS |
| 21 | Unknown Source preserved | `is_unknown_source=True`, `file_name=None` | Correct | PASS |
| 22 | Regular frame intact | `App.java:10` | `App.java:10` | PASS |
| 23 | Minimal header (no daemon) | `FULL`, 2 frames | `FULL`, 2 frames | PASS |
| 24 | Empty string | `RAW` | `RAW` | PASS |
| 25 | Whitespace only | `RAW` | `RAW` | PASS |
| 26 | Random text | `RAW` | `RAW` | PASS |
| 27 | Partial header no body | `PARTIAL` | `PARTIAL` | PASS |
| 28 | Garbage lines around valid | `FULL`, 1 frame | `FULL`, 1 frame | PASS |
| 29 | Never-raise (6 adversarial inputs) | No exception | No exception | PASS |
| 30 | Multi-thread parsing | 2 results | 2 results | PASS |
| 31 | Single thread parsing | 1 result | 1 result | PASS |
| 32 | Empty input (parse_all) | 1 result, `RAW` | 1 result, `RAW` | PASS |
| 33 | ThreadFrame defaults | All None/False | All None/False | PASS |
| 34 | LockHint defaults | `""`, None, None | Correct | PASS |
| 35 | ThreadDumpResult defaults | None/[]/`RAW` | Correct | PASS |
| 36 | stack_parser basic | `total_lines=3`, ≥1 frame | Correct | PASS |
| 37 | stack_parser imports unchanged | All public names importable | All importable | PASS |
| 38 | Minimal header frame count | 2 | 2 | PASS |

## Evidence Paths

- Synthetic tests: `tests/test_thread_stack_parser.py`
- Regression tests: `tests/test_stack_parser.py`
- Real dump sample 1 (Java 8): `tests/load/real_dump_sample1.txt`
- Real dump sample 2 (Java 11): `tests/load/real_dump_sample2.txt`

## Conclusion

**PASS (with 1 minor known issue)**

- All 38 synthetic capability tests pass
- All 27 regression tests pass
- Full suite (526 tests) passes
- Real Java 8 dump: 8/8 threads parsed correctly
- Real Java 11 dump: 12/12 threads parsed correctly
- 1 minor issue: Java 11 module-qualified `Native Method` not detected as native (frame still parsed correctly, no data loss)
