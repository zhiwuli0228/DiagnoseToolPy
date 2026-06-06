from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).parent / "load" / "analysis_benchmark.py"
SPEC = importlib.util.spec_from_file_location("analysis_benchmark", MODULE_PATH)
assert SPEC and SPEC.loader
analysis_benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analysis_benchmark
SPEC.loader.exec_module(analysis_benchmark)


def test_load_config_reads_profiles_and_datasets(tmp_path: Path) -> None:
    dataset_path = tmp_path / "a.zip"
    dataset_path.write_text("x", encoding="utf-8")
    config_path = tmp_path / "bench.yaml"
    config_path.write_text(
        """
defaults:
  host: http://127.0.0.1:18080
  poll_interval_seconds: 2
  cluster_timeout_seconds: 60
  request_timeout_seconds: 30
  warmup_seconds: 0
  output_dir: tests/load/artifacts
thresholds:
  scan_p95_ms_max: 1000
  scan_failure_rate_max_pct: 5
  cluster_submit_p95_ms_max: 2000
  cluster_submit_failure_rate_max_pct: 5
  cluster_completion_rate_min_pct: 95
  cluster_wall_time_max_seconds: 120
datasets:
  - id: a
    description: sample
    source_path: __DATASET_PATH__
    kind: zip
    expected_min_bytes: 1
profiles:
  - id: p1
    description: profile
    concurrency: 2
    iterations: 1
    scenarios:
      - type: source_scan
        datasets: [a]
""".replace("__DATASET_PATH__", dataset_path.as_posix()).strip(),
        encoding="utf-8",
    )

    config = analysis_benchmark.load_config(config_path)

    assert config.defaults.host == "http://127.0.0.1:18080"
    assert "a" in config.datasets
    assert "p1" in config.profiles
    assert config.profiles["p1"].scenarios[0].type == "source_scan"
    assert config.datasets["a"].expected_min_bytes == 1


def test_load_config_allows_prepare_from_zip_when_source_path_missing(tmp_path: Path) -> None:
    zip_path = tmp_path / "bundle.zip"
    zip_path.write_text("placeholder", encoding="utf-8")
    config_path = tmp_path / "bench.yaml"
    config_path.write_text(
        """
defaults:
  host: http://127.0.0.1:18080
  poll_interval_seconds: 2
  cluster_timeout_seconds: 60
  request_timeout_seconds: 30
  warmup_seconds: 0
  output_dir: tests/load/artifacts
thresholds:
  scan_p95_ms_max: 1000
  scan_failure_rate_max_pct: 5
  cluster_submit_p95_ms_max: 2000
  cluster_submit_failure_rate_max_pct: 5
  cluster_completion_rate_min_pct: 95
  cluster_wall_time_max_seconds: 120
datasets:
  - id: prepared
    description: sample
    source_path: __MISSING_PATH__
    kind: directory
    prepare_from_zip: __ZIP_PATH__
    expected_min_bytes: 10
profiles: []
"""
        .replace("__MISSING_PATH__", (tmp_path / "prepared-dir").as_posix())
        .replace("__ZIP_PATH__", zip_path.as_posix())
        .strip(),
        encoding="utf-8",
    )

    config = analysis_benchmark.load_config(config_path)

    assert config.datasets["prepared"].prepare_from_zip == zip_path.as_posix()
    assert config.datasets["prepared"].expected_min_bytes == 10


def test_load_config_rejects_missing_dataset_path(tmp_path: Path) -> None:
    config_path = tmp_path / "bench.yaml"
    config_path.write_text(
        """
defaults:
  host: http://127.0.0.1:18080
  poll_interval_seconds: 2
  cluster_timeout_seconds: 60
  request_timeout_seconds: 30
  warmup_seconds: 0
  output_dir: tests/load/artifacts
thresholds:
  scan_p95_ms_max: 1000
  scan_failure_rate_max_pct: 5
  cluster_submit_p95_ms_max: 2000
  cluster_submit_failure_rate_max_pct: 5
  cluster_completion_rate_min_pct: 95
  cluster_wall_time_max_seconds: 120
datasets:
  - id: missing
    description: sample
    source_path: C:/definitely-missing-path/bench.log
    kind: directory
profiles: []
""".strip(),
        encoding="utf-8",
    )

    try:
        analysis_benchmark.load_config(config_path)
    except analysis_benchmark.BenchmarkConfigError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("expected BenchmarkConfigError for missing dataset path")


def test_summarize_profile_flags_threshold_failure() -> None:
    profile = analysis_benchmark.ProfileSpec(
        id="scan_profile",
        description="scan",
        concurrency=1,
        iterations=1,
        scenarios=(),
    )
    thresholds = analysis_benchmark.BenchmarkThresholds(
        scan_p95_ms_max=100.0,
        scan_failure_rate_max_pct=5.0,
        cluster_submit_p95_ms_max=200.0,
        cluster_submit_failure_rate_max_pct=5.0,
        cluster_completion_rate_min_pct=95.0,
        cluster_wall_time_max_seconds=60.0,
    )
    runs = [
        analysis_benchmark.ScenarioRun(
            profile_id="scan_profile",
            scenario_type="source_scan",
            dataset_id="a",
            worker_id=1,
            iteration=1,
            success=True,
            started_at="2026-06-06T00:00:00+00:00",
            finished_at="2026-06-06T00:00:01+00:00",
            duration_ms=150.0,
        )
    ]

    summary = analysis_benchmark.summarize_profile(profile, runs, thresholds)

    assert summary["passed"] is False
    assert summary["metrics"]["source_scan"]["p95_ms"] == 150.0


def test_render_markdown_report_includes_failures() -> None:
    report = analysis_benchmark.render_markdown_report(
        {
            "profile_id": "cluster_profile",
            "host": "http://127.0.0.1:18080",
            "started_at": "2026-06-06T00:00:00+00:00",
            "finished_at": "2026-06-06T00:05:00+00:00",
            "summary": {
                "passed": False,
                "checks": [
                    {
                        "name": "cluster_task.completion_rate_pct",
                        "passed": False,
                        "actual": 50.0,
                        "expected": ">= 95.0",
                    }
                ],
                "metrics": {
                    "cluster_task": {
                        "count": 2,
                        "success_count": 1,
                        "failure_count": 1,
                    }
                },
            },
            "runs": [
                {
                    "scenario_type": "cluster_task",
                    "dataset_id": "large_zip",
                    "worker_id": 1,
                    "iteration": 1,
                    "success": False,
                    "error": "timed out",
                }
            ],
        }
    )

    assert "FAIL" in report
    assert "timed out" in report


def test_parse_args_supports_output_dir_override() -> None:
    args = analysis_benchmark.parse_args(
        ["--config", "bench.yaml", "--profile", "p1", "--host", "http://x", "--output-dir", "tmp/out"]
    )

    assert args.config == "bench.yaml"
    assert args.profiles == ["p1"]
    assert args.host == "http://x"
    assert args.output_dir == "tmp/out"


def test_benchmark_manifest_contains_smoke_profile() -> None:
    config = analysis_benchmark.load_config(
        Path(__file__).parent / "load" / "analysis_benchmarks.yaml"
    )

    assert "smoke_scan_sample" in config.profiles
    smoke = config.profiles["smoke_scan_sample"]
    assert smoke.concurrency == 1
    assert smoke.scenarios[0].datasets == ("sample_zip",)


def test_cluster_submit_metrics_preserved_on_timeout() -> None:
    """submit_ms survives into details even when the cluster task times out."""
    metrics = analysis_benchmark.ClusterSubmitMetrics(
        submit_ms=412.5,
        wall_time_seconds=15.0,
        last_status="scanning",
        last_progress=42,
        poll_count=8,
        task_id="cluster-x",
    )
    details = metrics.to_details()
    assert details["submit_ms"] == 412.5
    assert details["wall_time_seconds"] == 15.0
    assert details["last_status"] == "scanning"
    assert details["last_progress"] == 42
    assert details["poll_count"] == 8
    assert details["task_id"] == "cluster-x"


def test_summarize_profile_keeps_submit_ms_finite_on_timeout() -> None:
    """Summary p95_submit is finite when only timed-out tasks ran."""
    profile = analysis_benchmark.ProfileSpec(
        id="cluster_profile",
        description="cluster",
        concurrency=1,
        iterations=1,
        scenarios=(),
    )
    thresholds = analysis_benchmark.BenchmarkThresholds(
        scan_p95_ms_max=100.0,
        scan_failure_rate_max_pct=5.0,
        cluster_submit_p95_ms_max=2000.0,
        cluster_submit_failure_rate_max_pct=5.0,
        cluster_completion_rate_min_pct=95.0,
        cluster_wall_time_max_seconds=120.0,
    )
    runs = [
        analysis_benchmark.ScenarioRun(
            profile_id="cluster_profile",
            scenario_type="cluster_task",
            dataset_id="big",
            worker_id=1,
            iteration=1,
            success=False,
            started_at="2026-06-06T00:00:00+00:00",
            finished_at="2026-06-06T00:01:00+00:00",
            duration_ms=60_000.0,
            error="timed out",
            details={
                "task_id": "cluster-x",
                "submit_ms": 250.0,
                "wall_time_seconds": 60.0,
                "last_status": "scanning",
                "last_progress": 30,
                "poll_count": 30,
            },
        )
    ]

    summary = analysis_benchmark.summarize_profile(profile, runs, thresholds)

    cluster = summary["metrics"]["cluster_task"]
    assert cluster["submit_p95_ms"] == 250.0
    assert cluster["submit_avg_ms"] == 250.0
    assert cluster["max_wall_time_seconds"] == 60.0


def test_execute_scenario_records_submit_ms_when_run_cluster_task_times_out() -> None:
    """execute_scenario copies ClusterSubmitMetrics into details on timeout."""
    from unittest.mock import MagicMock

    client = MagicMock()
    dataset = analysis_benchmark.DatasetSpec(
        id="big",
        description="big",
        source_path="C:/tmp/big",
        kind="directory",
    )
    defaults = analysis_benchmark.BenchmarkDefaults(
        host="http://127.0.0.1:18080",
        poll_interval_seconds=0,
        cluster_timeout_seconds=1,
        request_timeout_seconds=30,
        warmup_seconds=0,
        output_dir="tests/load/artifacts",
    )
    scenario = analysis_benchmark.ScenarioSpec(
        type="cluster_task", datasets=("big",)
    )

    # Stub: post_json returns a task_id, get_json keeps reporting scanning
    client.post_json.return_value = {"task_id": "cluster-xyz"}
    client.get_json.return_value = {"status": "scanning", "progress": 5}

    run = analysis_benchmark.execute_scenario(
        client, defaults, "p", scenario, dataset, worker_id=1, iteration=1
    )

    assert run.success is False
    assert run.details["submit_ms"] >= 0
    assert run.details["task_id"] == "cluster-xyz"
    assert run.details["last_status"] == "scanning"
