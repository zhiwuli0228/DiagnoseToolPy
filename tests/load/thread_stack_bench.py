"""Load benchmark for thread_stack_parser.

Generates synthetic thread dump blocks and measures parse throughput,
latency percentiles, memory peak, and status distribution.

Usage:
    uv run python tests/load/thread_stack_bench.py [--blocks N]
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from diagnose_tool.analyzer.thread_stack_parser import (
    ParseStatus,
    parse_thread_dump,
    parse_thread_dump_all,
)


# ---------------------------------------------------------------------------
# Synthetic data generators
# ---------------------------------------------------------------------------

_STATES = ["RUNNABLE", "BLOCKED", "WAITING", "TIMED_WAITING", "NEW", "TERMINATED"]


def _make_thread_block(index: int, state: str | None = None) -> str:
    """Generate a realistic single-thread dump block."""
    st = state or _STATES[index % len(_STATES)]
    name = f"worker-{index:06d}"

    frames = []
    for depth in range(8):
        cls = f"com.example.module{depth}.Service{index % 10}"
        method = f"handle{depth}"
        if depth == 0 and index % 5 == 0:
            frames.append(f"        at {cls}.{method}(Native Method)")
        elif depth == 1 and index % 7 == 0:
            frames.append(f"        at {cls}.{method}(Unknown Source)")
        else:
            frames.append(f"        at {cls}.{method}(Service{index % 10}.java:{42 + depth})")

    lock_hint = ""
    if st == "BLOCKED":
        lock_hint = f"\n        - waiting to lock <0x{index:016x}> (a java.lang.Object)"
    elif st == "WAITING":
        lock_hint = f"\n        - parking to wait for <0x{index:016x}> (a java.util.concurrent.locks.ReentrantLock)"

    header = f'"{name}" #{index} daemon prio=5 tid=0x{index:016x} nid=0x{index:x} {st.lower()} [0x{index:016x}]'
    state_line = f"   java.lang.Thread.State: {st}"
    body = "\n".join(frames)
    return f"{header}\n{state_line}\n{body}{lock_hint}"


def make_synthetic_dump(n_blocks: int) -> str:
    """Generate a full thread dump with *n_blocks* threads."""
    blocks = [_make_thread_block(i) for i in range(n_blocks)]
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_bench(n_blocks: int) -> dict:
    """Run the benchmark and return a result dict."""
    raw = make_synthetic_dump(n_blocks)
    raw_bytes = len(raw.encode("utf-8"))

    gc.collect()
    tracemalloc.start()

    durations_us: list[float] = []
    statuses: dict[str, int] = {"FULL": 0, "PARTIAL": 0, "RAW": 0}
    failures = 0

    t0 = time.perf_counter()
    results = parse_thread_dump_all(raw)
    t1 = time.perf_counter()

    for r in results:
        # Re-parse individually to measure per-block time
        pass

    total_seconds = t1 - t0

    # Per-block timing (re-parse individually for accurate per-block stats)
    for block_text in raw.split("\n\n"):
        block_text = block_text.strip()
        if not block_text:
            continue
        s = time.perf_counter()
        try:
            r = parse_thread_dump(block_text)
            e = time.perf_counter()
            durations_us.append((e - s) * 1_000_000)
            statuses[r.parse_status.value] = statuses.get(r.parse_status.value, 0) + 1
        except Exception:
            failures += 1

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    durations_us.sort()
    n = len(durations_us)
    p50 = durations_us[int(n * 0.50)] if n else 0
    p95 = durations_us[int(n * 0.95)] if n else 0
    p99 = durations_us[int(n * 0.99)] if n else 0
    avg_us = statistics.mean(durations_us) if n else 0

    return {
        "n_blocks": n_blocks,
        "raw_bytes": raw_bytes,
        "total_seconds": round(total_seconds, 4),
        "avg_us": round(avg_us, 2),
        "p50_us": round(p50, 2),
        "p95_us": round(p95, 2),
        "p99_us": round(p99, 2),
        "peak_memory_bytes": peak_mem,
        "failures": failures,
        "result_count": len(results),
        "status_distribution": statuses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Thread stack parser load benchmark")
    parser.add_argument("--blocks", type=int, nargs="+", default=[100, 1000, 10000],
                        help="Number of thread blocks per run")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON path")
    args = parser.parse_args()

    all_results = []
    for n in args.blocks:
        print(f"Running {n} blocks...", end=" ", flush=True)
        result = run_bench(n)
        all_results.append(result)
        print(f"done in {result['total_seconds']}s (p95={result['p95_us']}us, failures={result['failures']})")

    output = {"benchmarks": all_results, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(__file__).resolve().parent / "thread_stack_bench.json"

    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
