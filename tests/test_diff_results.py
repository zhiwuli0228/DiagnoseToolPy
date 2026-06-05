"""Regression tests for tests/load/diff_results.py.

Covers design §6.1 (data model), §6.2 (error model), §6.3 (markdown
rendering) and §8 (verification) of
docs/performance-benchmark-remediation-design.md.

The tests use synthetic Locust CSV strings written to a tmp_path so that
they do not depend on the (potentially stale) results_*.csv files in
tests/load/.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

# The module under test is tests/load/diff_results.py — a script, not a
# package. Insert the directory on sys.path so we can import it directly.
_LOAD_DIR = Path(__file__).parent / "load"
sys.path.insert(0, str(_LOAD_DIR))

from diff_results import (  # noqa: E402  (sys.path manipulated above)
    AggregatedMetrics,
    InvalidBenchmarkArtifact,
    check_thresholds,
    parse_aggregated,
    render_md,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

# The actual Locust CSV header, taken verbatim from
# `head -1 tests/load/results_baseline_stats.csv`. Keep these names in
# sync with the real Locust output — the module under test reads by
# these exact strings.
_LOCUST_HEADER = [
    "Type",
    "Name",
    "Request Count",
    "Failure Count",
    "Median Response Time",
    "Average Response Time",
    "Min Response Time",
    "Max Response Time",
    "Average Content Size",
    "Requests/s",
    "Failures/s",
    "50%",
    "66%",
    "75%",
    "80%",
    "90%",
    "95%",
    "98%",
    "99%",
    "99.9%",
    "99.99%",
    "100%",
]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a synthetic Locust stats CSV to *path*.

    Each *row* must contain a value for every column in ``_LOCUST_HEADER``.
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_LOCUST_HEADER)
        writer.writeheader()
        for row in rows:
            # Defensive: every row must populate every column or the
            # parser will see None.
            assert set(row.keys()) == set(_LOCUST_HEADER), (
                f"row keys {sorted(row)} != header {sorted(_LOCUST_HEADER)}"
            )
            writer.writerow(row)


def _endpoint_row(
    name: str,
    *,
    request_count: int = 100,
    failure_count: int = 0,
    avg_ms: float = 5.0,
    p95_ms: float = 10.0,
    requests_per_sec: float = 10.0,
) -> dict[str, str]:
    """Build an endpoint row that satisfies the Locust header."""
    return {
        "Type": "GET",
        "Name": name,
        "Request Count": str(request_count),
        "Failure Count": str(failure_count),
        "Median Response Time": "5",
        "Average Response Time": f"{avg_ms:.4f}",
        "Min Response Time": "1",
        "Max Response Time": "10",
        "Average Content Size": "42",
        "Requests/s": f"{requests_per_sec:.4f}",
        "Failures/s": "0.0",
        "50%": "5",
        "66%": "5",
        "75%": "5",
        "80%": "6",
        "90%": "8",
        "95%": str(p95_ms),
        "98%": "15",
        "99%": "20",
        "99.9%": "50",
        "99.99%": "80",
        "100%": "100",
    }


def _aggregated_row(
    *,
    request_count: int = 200,
    failure_count: int = 0,
    avg_ms: float = 5.0,
    p95_ms: float = 10.0,
    requests_per_sec: float = 20.0,
) -> dict[str, str]:
    """Build an Aggregated row (Type is empty in real Locust output)."""
    return {
        "Type": "",
        "Name": "Aggregated",
        "Request Count": str(request_count),
        "Failure Count": str(failure_count),
        "Median Response Time": "5",
        "Average Response Time": f"{avg_ms:.4f}",
        "Min Response Time": "1",
        "Max Response Time": "10",
        "Average Content Size": "42",
        "Requests/s": f"{requests_per_sec:.4f}",
        "Failures/s": "0.0",
        "50%": "5",
        "66%": "5",
        "75%": "5",
        "80%": "6",
        "90%": "8",
        "95%": str(p95_ms),
        "98%": "15",
        "99%": "20",
        "99.9%": "50",
        "99.99%": "80",
        "100%": "100",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


# Test 1 (design §8): parse_aggregated must read from the Aggregated
# row, not from a weighted average of endpoint rows. We deliberately
# make the per-endpoint p95/avg/RPS values that would not naively
# average to the Aggregated row's values.
def test_uses_aggregated_row_not_weighted_endpoints(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    _write_csv(
        csv_path,
        [
            _endpoint_row(
                "/a", request_count=100, avg_ms=30.0, p95_ms=50, requests_per_sec=10.0
            ),
            _endpoint_row(
                "/b", request_count=100, avg_ms=70.0, p95_ms=100, requests_per_sec=10.0
            ),
            # Weighted p95/avg from endpoints would be (50+100)/2 = 75 / (30+70)/2 = 50
            # (coincidence in this case).  RPS weighted is also 20.0. We pick
            # Aggregated values that diverge to prove the parser doesn't sum.
            _aggregated_row(
                request_count=200, avg_ms=42.5, p95_ms=77, requests_per_sec=42.5
            ),
        ],
    )

    m = parse_aggregated(csv_path)

    # The Aggregated row values, NOT the weighted average of endpoints.
    assert m.p95_ms == 77.0, f"expected p95 from Aggregated row, got {m.p95_ms}"
    assert m.avg_ms == pytest.approx(42.5, rel=1e-3)
    assert m.requests_per_sec == pytest.approx(42.5, rel=1e-3)
    assert m.request_count == 200
    assert m.failure_count == 0
    assert m.failure_rate_pct == 0.0


# Test 2 (design §6.1 / §8): missing Aggregated row must raise.
def test_missing_aggregated_row_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    _write_csv(
        csv_path,
        [
            _endpoint_row("/a"),
            _endpoint_row("/b"),
        ],
    )

    with pytest.raises(InvalidBenchmarkArtifact) as excinfo:
        parse_aggregated(csv_path)

    assert "Aggregated" in str(excinfo.value)


# Test 3 (design §6.1): multiple Aggregated rows must raise.
def test_multiple_aggregated_rows_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    _write_csv(
        csv_path,
        [
            _aggregated_row(request_count=100, requests_per_sec=10.0),
            _aggregated_row(request_count=200, requests_per_sec=20.0),
        ],
    )

    with pytest.raises(InvalidBenchmarkArtifact) as excinfo:
        parse_aggregated(csv_path)

    msg = str(excinfo.value).lower()
    assert "multiple" in msg or "duplicate" in msg, str(excinfo.value)


# Test 4 (design §6.1): unparseable numeric field must raise.
def test_unparseable_numeric_field_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    bad = _aggregated_row()
    bad["Request Count"] = "not-a-number"  # will fail _parse_int
    _write_csv(csv_path, [bad])

    with pytest.raises(InvalidBenchmarkArtifact) as excinfo:
        parse_aggregated(csv_path)

    msg = str(excinfo.value).lower()
    assert "request count" in msg, str(excinfo.value)


# Test 5 (design §8): failure-rate threshold breach must be flagged.
def test_failure_rate_threshold_breach_returns_failure() -> None:
    # 10 failures out of 100 requests = 10% > 5% threshold.
    m = AggregatedMetrics(
        requests_per_sec=20.0,
        p95_ms=100.0,
        avg_ms=50.0,
        request_count=100,
        failure_count=10,
        failure_rate_pct=10.0,
    )
    failures = check_thresholds(m)
    assert failures, "expected at least one threshold violation"
    assert any("failure rate" in f.lower() for f in failures), failures


# Test 6 (design §8): throughput threshold breach must be flagged.
def test_throughput_threshold_breach_returns_failure() -> None:
    # 3.0 req/s < 6.0 req/s threshold.
    m = AggregatedMetrics(
        requests_per_sec=3.0,
        p95_ms=100.0,
        avg_ms=50.0,
        request_count=100,
        failure_count=0,
        failure_rate_pct=0.0,
    )
    failures = check_thresholds(m)
    assert failures, "expected at least one threshold violation"
    assert any(
        "throughput" in f.lower() or "req/s" in f.lower() or "rps" in f.lower()
        for f in failures
    ), failures


# Test 7 (design §6.3 / §8): rendered markdown must contain the exact
# values, with throughput/failure-rate formatted to 2 decimals and
# p95/avg formatted as integers.
def test_rendered_markdown_matches_aggregated_values() -> None:
    baseline = AggregatedMetrics(
        requests_per_sec=20.0,
        p95_ms=100,
        avg_ms=50,
        request_count=1000,
        failure_count=0,
        failure_rate_pct=0.0,
    )
    after = AggregatedMetrics(
        requests_per_sec=22.5,
        p95_ms=120,
        avg_ms=55,
        request_count=1100,
        failure_count=0,
        failure_rate_pct=0.0,
    )

    md = render_md(baseline, after)

    # Throughput is formatted with {x:.2f}.
    assert "20.00" in md
    assert "22.50" in md
    # P95 and Avg are formatted with {x:.0f}.
    assert "100" in md
    assert "120" in md
    assert "50" in md
    assert "55" in md
    # Delta throughput: 22.50 - 20.00 = +2.50
    assert "+2.50" in md
    # Delta P95: 120 - 100 = +20
    assert "+20" in md


# Test 8 (design §6.2 / §8): main() must exit 2 when the required
# stats files are missing. We patch sys.argv to avoid depending on the
# pre-existing CSVs in tests/load/ and then point diff_results at
# synthetic files by re-binding its module-level constants via
# monkeypatch.
def test_main_missing_stats_file_exits_two(tmp_path: Path, monkeypatch, capsys) -> None:
    # Import here so the sys.path manipulation above is in effect.
    import diff_results

    # Create empty dir with NO stats files.
    empty_dir = tmp_path / "no_stats"
    empty_dir.mkdir()

    # main() reads the script's own directory by default; we
    # monkey-patch the module-level Path resolution by stubbing the
    # file existence check via direct invocation through parse_aggregated
    # on a non-existent path. That covers the InvalidBenchmarkArtifact
    # path; the file-existence path is exercised by calling main() but
    # pointing it at empty_dir by patching Path(__file__).parent.
    #
    # Simplest portable approach: directly test the file-existence
    # branch by reading main's source path.
    here = Path(diff_results.__file__).parent
    base_path = here / "results_baseline_stats.csv"
    after_path = here / "results_after_stats.csv"

    # If the real artifacts happen to be present, move them aside
    # for the duration of the test.
    moved: list[tuple[Path, Path | None]] = []
    for p in (base_path, after_path):
        if p.exists():
            backup = p.with_suffix(p.suffix + ".bak_test")
            p.rename(backup)
            moved.append((p, backup))

    try:
        rc = diff_results.main()
        captured = capsys.readouterr()
        assert rc == 2, f"expected exit code 2, got {rc}; stderr={captured.err!r}"
        assert "ERROR" in captured.err
    finally:
        for original, backup in moved:
            if backup is not None and backup.exists():
                backup.rename(original)
