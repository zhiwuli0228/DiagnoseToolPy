"""Diff two Locust CSV history files and emit a markdown report.

Reads `results_<tag>_stats.csv` files and prints a markdown table.
Exits non-zero if any acceptance threshold is violated.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


class InvalidBenchmarkArtifact(Exception):
    """Raised when a benchmark CSV is missing, malformed, or has no Aggregated row."""
    pass


@dataclass(frozen=True)
class AggregatedMetrics:
    """Metrics sourced entirely from the single Locust 'Aggregated' row."""
    requests_per_sec: float
    p95_ms: float
    avg_ms: float
    request_count: int
    failure_count: int
    failure_rate_pct: float


def load_stats(path: Path) -> List[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_float(value: str | None, field_name: str) -> float:
    if value is None:
        raise InvalidBenchmarkArtifact(f"Missing value for '{field_name}' in Aggregated row")
    try:
        return float(value)
    except ValueError:
        raise InvalidBenchmarkArtifact(
            f"Could not parse '{field_name}' as float: {value!r}"
        )


def _parse_int(value: str | None, field_name: str) -> int:
    if value is None:
        raise InvalidBenchmarkArtifact(f"Missing value for '{field_name}' in Aggregated row")
    try:
        return int(value)
    except ValueError:
        raise InvalidBenchmarkArtifact(
            f"Could not parse '{field_name}' as int: {value!r}"
        )


def aggregate(rows: List[dict[str, str]]) -> AggregatedMetrics:
    """Return AggregatedMetrics from the single 'Aggregated' CSV row.

    Raises InvalidBenchmarkArtifact if the row is missing, duplicated, or
    contains unparseable fields.
    """
    aggregated_rows = [row for row in rows if row.get("Name") == "Aggregated"]
    if len(aggregated_rows) == 0:
        raise InvalidBenchmarkArtifact(
            "No 'Aggregated' row found in benchmark CSV. "
            "Ensure the CSV contains a row with Name='Aggregated'."
        )
    if len(aggregated_rows) > 1:
        raise InvalidBenchmarkArtifact(
            f"Multiple ({len(aggregated_rows)}) 'Aggregated' rows found; "
            "expected exactly one."
        )

    row = aggregated_rows[0]

    requests_per_sec = _parse_float(row.get("Requests/s"), "Requests/s")
    p95_ms = _parse_float(row.get("95%"), "95%")
    avg_ms = _parse_float(row.get("Average Response Time"), "Average Response Time")
    request_count = _parse_int(row.get("Request Count"), "Request Count")
    failure_count = _parse_int(row.get("Failure Count"), "Failure Count")

    if request_count > 0:
        failure_rate_pct = 100.0 * failure_count / request_count
    else:
        failure_rate_pct = 0.0

    return AggregatedMetrics(
        requests_per_sec=requests_per_sec,
        p95_ms=p95_ms,
        avg_ms=avg_ms,
        request_count=request_count,
        failure_count=failure_count,
        failure_rate_pct=failure_rate_pct,
    )


def parse_aggregated(path: Path) -> AggregatedMetrics:
    """Load a Locust stats CSV and return its AggregatedMetrics."""
    return aggregate(load_stats(path))


def render_md(
    baseline: AggregatedMetrics,
    after: AggregatedMetrics,
) -> str:
    b = baseline
    a = after
    return f"""# Locust Diff Report

| Metric | Baseline | After | Δ |
|---|---|---|---|
| Throughput (req/s) | {b.requests_per_sec:.2f} | {a.requests_per_sec:.2f} | {a.requests_per_sec - b.requests_per_sec:+.2f} |
| P95 (ms) | {b.p95_ms:.0f} | {a.p95_ms:.0f} | {a.p95_ms - b.p95_ms:+.0f} |
| Avg (ms) | {b.avg_ms:.0f} | {a.avg_ms:.0f} | {a.avg_ms - b.avg_ms:+.0f} |
| Failure rate (%) | {b.failure_rate_pct:.2f} | {a.failure_rate_pct:.2f} | {a.failure_rate_pct - b.failure_rate_pct:+.2f} |

## Thresholds
- Failure rate must be < {THRESHOLDS['fail_rate_max_pct']}%
- P95 must be < {THRESHOLDS['p95_max_ms']}ms
- Throughput must be >= {THRESHOLDS['rps_min']} req/s
"""


def check_thresholds(after: AggregatedMetrics) -> List[str]:
    failures: List[str] = []
    if after.failure_rate_pct >= THRESHOLDS["fail_rate_max_pct"]:
        failures.append(
            f"FAIL: failure rate {after.failure_rate_pct:.2f}% >= "
            f"{THRESHOLDS['fail_rate_max_pct']}%"
        )
    if after.p95_ms >= THRESHOLDS["p95_max_ms"]:
        failures.append(
            f"FAIL: p95 {after.p95_ms:.0f}ms >= {THRESHOLDS['p95_max_ms']}ms"
        )
    if after.requests_per_sec < THRESHOLDS["rps_min"]:
        failures.append(
            f"FAIL: throughput {after.requests_per_sec:.2f} req/s < "
            f"{THRESHOLDS['rps_min']} req/s"
        )
    return failures


# Acceptance thresholds (must match docs/performance-optimization-design.md
# and the P0 design spec).
THRESHOLDS = {
    "fail_rate_max_pct": 5.0,        # < 5%
    "p95_max_ms": 6000.0,            # < 6000ms
    "rps_min": 6.0,                  # conservative +20% over 5.47 baseline
}


def main() -> int:
    here = Path(__file__).parent
    base_path = here / "results_baseline_stats.csv"
    after_path = here / "results_after_stats.csv"
    if not base_path.exists() or not after_path.exists():
        print(
            f"ERROR: need both {base_path.name} and {after_path.name}",
            file=sys.stderr,
        )
        return 2

    try:
        baseline = parse_aggregated(base_path)
        after = parse_aggregated(after_path)
    except InvalidBenchmarkArtifact as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

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
