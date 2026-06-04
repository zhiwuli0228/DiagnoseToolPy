"""Diff two Locust CSV history files and emit a markdown report.

Reads `results_<tag>_stats.csv` files and prints a markdown table.
Exits non-zero if any acceptance threshold is violated.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Acceptance thresholds (must match docs/performance-optimization-design.md
# and the P0 design spec).
THRESHOLDS = {
    "fail_rate_max_pct": 5.0,        # < 5%
    "p95_max_ms": 6000.0,            # < 6000ms
    "rps_min": 6.0,                  # conservative +20% over 5.47 baseline
}


def load_stats(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def aggregate(rows: List[Dict[str, str]]) -> Tuple[float, float, float, float]:
    """Return (total_rps, p95_ms, fail_rate_pct, avg_ms)."""
    total_requests = 0
    total_failures = 0
    weighted_p95 = 0.0
    weighted_avg = 0.0
    for row in rows:
        if row.get("Name") == "Aggregated":
            continue
        try:
            n = int(row["Request Count"])
        except (KeyError, ValueError):
            continue
        if n == 0:
            continue
        total_requests += n
        total_failures += int(row.get("Failure Count", 0) or 0)
        weighted_p95 += float(row.get("95%", 0) or 0) * n
        weighted_avg += float(row.get("Average Response Time", 0) or 0) * n
    if total_requests == 0:
        return (0.0, 0.0, 0.0, 0.0)
    p95 = weighted_p95 / total_requests
    avg = weighted_avg / total_requests
    fail_pct = 100.0 * total_failures / total_requests
    # RPS = total_requests / wall-clock seconds. Locust CSV doesn't store
    # wall time, so read from the Aggregated row directly to avoid
    # double-counting per-endpoint rows.
    rps = 0.0
    for row in rows:
        if row.get("Name") == "Aggregated":
            try:
                rps = float(row.get("Requests/s", 0) or 0)
            except ValueError:
                rps = 0.0
            break
    return (rps, p95, fail_pct, avg)


def render_md(baseline: Tuple[float, float, float, float],
              after: Tuple[float, float, float, float]) -> str:
    b_rps, b_p95, b_fail, b_avg = baseline
    a_rps, a_p95, a_fail, a_avg = after
    return f"""# Locust Diff Report

| Metric | Baseline | After | Δ |
|---|---|---|---|
| Throughput (req/s) | {b_rps:.2f} | {a_rps:.2f} | {a_rps - b_rps:+.2f} |
| P95 (ms) | {b_p95:.0f} | {a_p95:.0f} | {a_p95 - b_p95:+.0f} |
| Avg (ms) | {b_avg:.0f} | {a_avg:.0f} | {a_avg - b_avg:+.0f} |
| Failure rate (%) | {b_fail:.2f} | {a_fail:.2f} | {a_fail - b_fail:+.2f} |

## Thresholds
- Failure rate must be < {THRESHOLDS['fail_rate_max_pct']}%
- P95 must be < {THRESHOLDS['p95_max_ms']}ms
- Throughput must be >= {THRESHOLDS['rps_min']} req/s
"""


def check_thresholds(after: Tuple[float, float, float, float]) -> List[str]:
    a_rps, a_p95, a_fail, _ = after
    failures: List[str] = []
    if a_fail >= THRESHOLDS["fail_rate_max_pct"]:
        failures.append(f"FAIL: failure rate {a_fail:.2f}% >= {THRESHOLDS['fail_rate_max_pct']}%")
    if a_p95 >= THRESHOLDS["p95_max_ms"]:
        failures.append(f"FAIL: p95 {a_p95:.0f}ms >= {THRESHOLDS['p95_max_ms']}ms")
    if a_rps < THRESHOLDS["rps_min"]:
        failures.append(f"FAIL: throughput {a_rps:.2f} req/s < {THRESHOLDS['rps_min']} req/s")
    return failures


def main() -> int:
    here = Path(__file__).parent
    base_path = here / "results_baseline_stats.csv"
    after_path = here / "results_after_stats.csv"
    if not base_path.exists() or not after_path.exists():
        print(f"ERROR: need both {base_path.name} and {after_path.name}", file=sys.stderr)
        return 2
    baseline = aggregate(load_stats(base_path))
    after = aggregate(load_stats(after_path))
    md = render_md(baseline, after)
    out = here / "results_diff.md"
    out.write_text(md, encoding="utf-8")
    print(md)
    failures = check_thresholds(after)
    if failures:
        print("\nThreshold violations:", file=sys.stderr)
        for f in failures:
            print(" -", f, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
