"""Automated analysis benchmark runner for large log datasets."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class BenchmarkConfigError(RuntimeError):
    """Raised when benchmark config is malformed."""


class BenchmarkRunError(RuntimeError):
    """Raised when a benchmark request fails."""


@dataclass(frozen=True)
class BenchmarkDefaults:
    host: str
    poll_interval_seconds: int
    cluster_timeout_seconds: int
    request_timeout_seconds: int
    warmup_seconds: int
    output_dir: str


@dataclass(frozen=True)
class BenchmarkThresholds:
    scan_p95_ms_max: float
    scan_failure_rate_max_pct: float
    cluster_submit_p95_ms_max: float
    cluster_submit_failure_rate_max_pct: float
    cluster_completion_rate_min_pct: float
    cluster_wall_time_max_seconds: float


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    description: str
    source_path: str
    kind: str
    prepare_from_zip: str | None = None
    expected_min_bytes: int | None = None


@dataclass(frozen=True)
class ScenarioSpec:
    type: str
    datasets: tuple[str, ...]


@dataclass(frozen=True)
class ProfileSpec:
    id: str
    description: str
    concurrency: int
    iterations: int
    scenarios: tuple[ScenarioSpec, ...]


@dataclass(frozen=True)
class BenchmarkConfig:
    defaults: BenchmarkDefaults
    thresholds: BenchmarkThresholds
    datasets: dict[str, DatasetSpec]
    profiles: dict[str, ProfileSpec]


@dataclass
class ScenarioRun:
    profile_id: str
    scenario_type: str
    dataset_id: str
    worker_id: int
    iteration: int
    success: bool
    started_at: str
    finished_at: str
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def load_config(path: Path) -> BenchmarkConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise BenchmarkConfigError("config root must be a mapping")

    defaults_raw = _require_mapping(raw, "defaults")
    thresholds_raw = _require_mapping(raw, "thresholds")
    datasets_raw = _require_list(raw, "datasets")
    profiles_raw = _require_list(raw, "profiles")

    defaults = BenchmarkDefaults(
        host=str(defaults_raw["host"]),
        poll_interval_seconds=int(defaults_raw["poll_interval_seconds"]),
        cluster_timeout_seconds=int(defaults_raw["cluster_timeout_seconds"]),
        request_timeout_seconds=int(defaults_raw["request_timeout_seconds"]),
        warmup_seconds=int(defaults_raw.get("warmup_seconds", 0)),
        output_dir=str(defaults_raw["output_dir"]),
    )
    thresholds = BenchmarkThresholds(
        scan_p95_ms_max=float(thresholds_raw["scan_p95_ms_max"]),
        scan_failure_rate_max_pct=float(thresholds_raw["scan_failure_rate_max_pct"]),
        cluster_submit_p95_ms_max=float(thresholds_raw["cluster_submit_p95_ms_max"]),
        cluster_submit_failure_rate_max_pct=float(thresholds_raw["cluster_submit_failure_rate_max_pct"]),
        cluster_completion_rate_min_pct=float(thresholds_raw["cluster_completion_rate_min_pct"]),
        cluster_wall_time_max_seconds=float(thresholds_raw["cluster_wall_time_max_seconds"]),
    )

    datasets: dict[str, DatasetSpec] = {}
    for item in datasets_raw:
        if not isinstance(item, dict):
            raise BenchmarkConfigError("each dataset must be a mapping")
        spec = DatasetSpec(
            id=str(item["id"]),
            description=str(item.get("description", item["id"])),
            source_path=str(item["source_path"]),
            kind=str(item.get("kind", "path")),
            prepare_from_zip=str(item["prepare_from_zip"]) if item.get("prepare_from_zip") else None,
            expected_min_bytes=int(item["expected_min_bytes"]) if item.get("expected_min_bytes") is not None else None,
        )
        source_path = Path(spec.source_path)
        if not source_path.exists() and not spec.prepare_from_zip:
            raise BenchmarkConfigError(
                f"dataset {spec.id!r} source path does not exist: {spec.source_path}"
            )
        datasets[spec.id] = spec

    profiles: dict[str, ProfileSpec] = {}
    for item in profiles_raw:
        if not isinstance(item, dict):
            raise BenchmarkConfigError("each profile must be a mapping")
        scenarios_raw = _require_list(item, "scenarios")
        scenarios = []
        for scenario in scenarios_raw:
            if not isinstance(scenario, dict):
                raise BenchmarkConfigError("each scenario must be a mapping")
            dataset_ids = tuple(str(value) for value in scenario["datasets"])
            for dataset_id in dataset_ids:
                if dataset_id not in datasets:
                    raise BenchmarkConfigError(
                        f"profile {item['id']} references unknown dataset {dataset_id!r}"
                    )
            scenarios.append(
                ScenarioSpec(
                    type=str(scenario["type"]),
                    datasets=dataset_ids,
                )
            )
        spec = ProfileSpec(
            id=str(item["id"]),
            description=str(item.get("description", item["id"])),
            concurrency=int(item["concurrency"]),
            iterations=int(item["iterations"]),
            scenarios=tuple(scenarios),
        )
        profiles[spec.id] = spec

    return BenchmarkConfig(
        defaults=defaults,
        thresholds=thresholds,
        datasets=datasets,
        profiles=profiles,
    )


def _require_mapping(container: dict[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    if not isinstance(value, dict):
        raise BenchmarkConfigError(f"{key!r} must be a mapping")
    return value


def _require_list(container: dict[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, list):
        raise BenchmarkConfigError(f"{key!r} must be a list")
    return value


class BenchmarkClient:
    def __init__(self, host: str, timeout_seconds: int) -> None:
        self._host = host.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url=f"{self._host}{path}",
            headers={"Accept": "application/json"},
            method="GET",
        )
        return self._do_json(request)

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url=f"{self._host}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        return self._do_json(request)

    def _do_json(self, request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise BenchmarkRunError(
                f"{request.method} {request.full_url} returned {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise BenchmarkRunError(
                f"{request.method} {request.full_url} failed: {exc.reason}"
            ) from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise BenchmarkRunError(
                f"{request.method} {request.full_url} returned invalid JSON"
            ) from exc

        if not isinstance(data, dict):
            raise BenchmarkRunError(
                f"{request.method} {request.full_url} returned non-object JSON"
            )
        return data


def preflight(client: BenchmarkClient) -> None:
    health = client.get_json("/health")
    if health.get("status") != "ok":
        raise BenchmarkRunError("preflight failed: /health did not return status=ok")


def run_profile(
    config: BenchmarkConfig,
    profile: ProfileSpec,
    output_root: Path,
) -> dict[str, Any]:
    client = BenchmarkClient(config.defaults.host, config.defaults.request_timeout_seconds)
    preflight(client)

    if config.defaults.warmup_seconds > 0:
        time.sleep(config.defaults.warmup_seconds)

    run_started = _utc_now()
    all_runs: list[ScenarioRun] = []
    lock = threading.Lock()

    def worker(worker_id: int) -> list[ScenarioRun]:
        worker_runs: list[ScenarioRun] = []
        worker_client = BenchmarkClient(
            config.defaults.host,
            config.defaults.request_timeout_seconds,
        )
        for iteration in range(1, profile.iterations + 1):
            for scenario in profile.scenarios:
                for dataset_id in scenario.datasets:
                    dataset = config.datasets[dataset_id]
                    worker_runs.append(
                        execute_scenario(
                            worker_client,
                            config.defaults,
                            profile.id,
                            scenario,
                            dataset,
                            worker_id,
                            iteration,
                        )
                    )
        with lock:
            all_runs.extend(worker_runs)
        return worker_runs

    with ThreadPoolExecutor(max_workers=profile.concurrency) as executor:
        futures = [executor.submit(worker, idx + 1) for idx in range(profile.concurrency)]
        for future in as_completed(futures):
            future.result()

    run_finished = _utc_now()
    summary = summarize_profile(profile, all_runs, config.thresholds)
    result = {
        "profile_id": profile.id,
        "description": profile.description,
        "host": config.defaults.host,
        "started_at": run_started,
        "finished_at": run_finished,
        "runs": [scenario_run_to_dict(run) for run in all_runs],
        "summary": summary,
    }

    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{profile.id}.json"
    md_path = output_root / f"{profile.id}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(result), encoding="utf-8")
    return result


def execute_scenario(
    client: BenchmarkClient,
    defaults: BenchmarkDefaults,
    profile_id: str,
    scenario: ScenarioSpec,
    dataset: DatasetSpec,
    worker_id: int,
    iteration: int,
) -> ScenarioRun:
    started_monotonic = time.perf_counter()
    started_at = _utc_now()
    details: dict[str, Any] = {}
    try:
        if scenario.type == "source_scan":
            details = run_source_scan(client, dataset)
        elif scenario.type == "cluster_task":
            details = run_cluster_task(client, dataset, defaults)
        else:
            raise BenchmarkRunError(f"unsupported scenario type: {scenario.type}")
        success = True
        error = None
    except BenchmarkRunError as exc:
        success = False
        error = str(exc)
        # Preserve any measured submit metrics (e.g. submit_ms on timeout)
        # so summary statistics stay finite even when the task fails.
        metrics = getattr(exc, "metrics", None)
        if metrics is not None:
            details = metrics.to_details()
    except Exception as exc:
        success = False
        error = str(exc)
        metrics = getattr(exc, "metrics", None)
        if metrics is not None:
            details = metrics.to_details()

    finished_at = _utc_now()
    duration_ms = round((time.perf_counter() - started_monotonic) * 1000, 2)
    return ScenarioRun(
        profile_id=profile_id,
        scenario_type=scenario.type,
        dataset_id=dataset.id,
        worker_id=worker_id,
        iteration=iteration,
        success=success,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        details=details,
        error=error,
    )


def run_source_scan(client: BenchmarkClient, dataset: DatasetSpec) -> dict[str, Any]:
    response = client.post_json("/api/source/scan", {"path": dataset.source_path})
    return {
        "file_count": response.get("file_count"),
        "supported_file_count": response.get("supported_file_count"),
        "unsupported_file_count": response.get("unsupported_file_count"),
        "total_bytes": response.get("total_bytes"),
        "is_zip": response.get("is_zip", False),
    }


class ClusterSubmitMetrics:
    """Carries measured cluster-submit metrics out of `run_cluster_task`.

    Even when the task later times out, the submit succeeded, so `submit_ms`
    is a real observation that must survive into the scenario summary.
    """

    def __init__(
        self,
        submit_ms: float,
        wall_time_seconds: float,
        last_status: str | None,
        last_progress: object,
        poll_count: int,
        task_id: str | None,
    ) -> None:
        self.submit_ms = submit_ms
        self.wall_time_seconds = wall_time_seconds
        self.last_status = last_status
        self.last_progress = last_progress
        self.poll_count = poll_count
        self.task_id = task_id

    def to_details(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "submit_ms": self.submit_ms,
            "wall_time_seconds": self.wall_time_seconds,
            "last_status": self.last_status,
            "last_progress": self.last_progress,
            "poll_count": self.poll_count,
        }


def run_cluster_task(
    client: BenchmarkClient,
    dataset: DatasetSpec,
    defaults: BenchmarkDefaults,
) -> dict[str, Any]:
    submit_started = time.perf_counter()
    response = client.post_json("/api/cluster", {"source_path": dataset.source_path})
    submit_ms = round((time.perf_counter() - submit_started) * 1000, 2)

    task_id = response.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise BenchmarkRunError("cluster submit returned empty task_id")

    poll_started = time.perf_counter()
    deadline = poll_started + defaults.cluster_timeout_seconds
    polls = 0
    last_status = None
    last_progress = None
    cluster_count = None

    while time.perf_counter() < deadline:
        polls += 1
        status_response = client.get_json(f"/api/cluster/{task_id}")
        last_status = status_response.get("status")
        last_progress = status_response.get("progress")
        if last_status == "done":
            clusters = status_response.get("clusters")
            cluster_count = len(clusters) if isinstance(clusters, list) else 0
            return {
                "task_id": task_id,
                "submit_ms": submit_ms,
                "wall_time_seconds": round(time.perf_counter() - submit_started, 2),
                "poll_count": polls,
                "final_status": last_status,
                "final_progress": last_progress,
                "cluster_count": cluster_count,
            }
        time.sleep(defaults.poll_interval_seconds)

    metrics = ClusterSubmitMetrics(
        submit_ms=submit_ms,
        wall_time_seconds=round(time.perf_counter() - submit_started, 2),
        last_status=last_status,
        last_progress=last_progress,
        poll_count=polls,
        task_id=task_id,
    )
    error = BenchmarkRunError(
        f"cluster task {task_id} timed out after {defaults.cluster_timeout_seconds}s "
        f"(last_status={last_status!r}, last_progress={last_progress!r})"
    )
    error.metrics = metrics  # type: ignore[attr-defined]
    raise error


def summarize_profile(
    profile: ProfileSpec,
    runs: list[ScenarioRun],
    thresholds: BenchmarkThresholds,
) -> dict[str, Any]:
    by_type: dict[str, list[ScenarioRun]] = {}
    for run in runs:
        by_type.setdefault(run.scenario_type, []).append(run)

    checks: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    source_runs = by_type.get("source_scan", [])
    if source_runs:
        durations = [run.duration_ms for run in source_runs]
        failures = [run for run in source_runs if not run.success]
        p95 = percentile(durations, 95)
        failure_rate = ratio_pct(len(failures), len(source_runs))
        metrics["source_scan"] = {
            "count": len(source_runs),
            "success_count": len(source_runs) - len(failures),
            "failure_count": len(failures),
            "p95_ms": p95,
            "avg_ms": round(statistics.fmean(durations), 2),
            "failure_rate_pct": failure_rate,
        }
        checks.extend([
            _check(
                "source_scan.p95_ms",
                p95 <= thresholds.scan_p95_ms_max,
                actual=p95,
                expected=f"<= {thresholds.scan_p95_ms_max}",
            ),
            _check(
                "source_scan.failure_rate_pct",
                failure_rate <= thresholds.scan_failure_rate_max_pct,
                actual=failure_rate,
                expected=f"<= {thresholds.scan_failure_rate_max_pct}",
            ),
        ])

    cluster_runs = by_type.get("cluster_task", [])
    if cluster_runs:
        submit_successes = [run for run in cluster_runs if run.success]
        # Submit latency is a measured observation whenever a submit call
        # returned a task_id, even if the task later failed or timed out.
        # Fall back to the overall duration only when the runner could not
        # record the submit at all (e.g. transport error during submit).
        submit_durations = [
            float(run.details.get("submit_ms", run.duration_ms))
            for run in cluster_runs
            if "submit_ms" in run.details
        ]
        failures = [run for run in cluster_runs if not run.success]
        completion_rate = ratio_pct(len(submit_successes), len(cluster_runs))
        wall_times = [
            float(run.details.get("wall_time_seconds", 0))
            for run in cluster_runs
            if "wall_time_seconds" in run.details
        ]
        p95_submit = percentile(submit_durations, 95) if submit_durations else math.inf
        max_wall = max(wall_times) if wall_times else math.inf
        failure_rate = ratio_pct(len(failures), len(cluster_runs))
        metrics["cluster_task"] = {
            "count": len(cluster_runs),
            "success_count": len(submit_successes),
            "failure_count": len(failures),
            "submit_p95_ms": p95_submit,
            "submit_avg_ms": round(statistics.fmean(submit_durations), 2) if submit_durations else None,
            "completion_rate_pct": completion_rate,
            "failure_rate_pct": failure_rate,
            "max_wall_time_seconds": max_wall if wall_times else None,
        }
        checks.extend([
            _check(
                "cluster_task.submit_p95_ms",
                p95_submit <= thresholds.cluster_submit_p95_ms_max,
                actual=p95_submit,
                expected=f"<= {thresholds.cluster_submit_p95_ms_max}",
            ),
            _check(
                "cluster_task.failure_rate_pct",
                failure_rate <= thresholds.cluster_submit_failure_rate_max_pct,
                actual=failure_rate,
                expected=f"<= {thresholds.cluster_submit_failure_rate_max_pct}",
            ),
            _check(
                "cluster_task.completion_rate_pct",
                completion_rate >= thresholds.cluster_completion_rate_min_pct,
                actual=completion_rate,
                expected=f">= {thresholds.cluster_completion_rate_min_pct}",
            ),
            _check(
                "cluster_task.max_wall_time_seconds",
                max_wall <= thresholds.cluster_wall_time_max_seconds,
                actual=max_wall,
                expected=f"<= {thresholds.cluster_wall_time_max_seconds}",
            ),
        ])

    passed = all(item["passed"] for item in checks) if checks else True
    return {
        "profile_id": profile.id,
        "concurrency": profile.concurrency,
        "iterations": profile.iterations,
        "metrics": metrics,
        "checks": checks,
        "passed": passed,
    }


def _check(name: str, passed: bool, actual: Any, expected: str) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "actual": actual,
        "expected": expected,
    }


def scenario_run_to_dict(run: ScenarioRun) -> dict[str, Any]:
    return {
        "profile_id": run.profile_id,
        "scenario_type": run.scenario_type,
        "dataset_id": run.dataset_id,
        "worker_id": run.worker_id,
        "iteration": run.iteration,
        "success": run.success,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "duration_ms": run.duration_ms,
        "details": run.details,
        "error": run.error,
    }


def render_markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"# Analysis Benchmark Report: {result['profile_id']}",
        "",
        f"- Host: {result['host']}",
        f"- Started: {result['started_at']}",
        f"- Finished: {result['finished_at']}",
        f"- Result: {'PASS' if summary['passed'] else 'FAIL'}",
        "",
        "## Checks",
        "",
        "| Check | Result | Actual | Expected |",
        "|---|---|---:|---|",
    ]
    for check in summary["checks"]:
        lines.append(
            f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | "
            f"{check['actual']} | {check['expected']} |"
        )

    lines.extend(["", "## Metrics", ""])
    for name, metric in summary["metrics"].items():
        lines.append(f"### {name}")
        lines.append("")
        for key, value in metric.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    failures = [run for run in result["runs"] if not run["success"]]
    lines.extend(["## Failures", ""])
    if failures:
        for failure in failures:
            lines.append(
                f"- {failure['scenario_type']} {failure['dataset_id']} "
                f"(worker={failure['worker_id']}, iteration={failure['iteration']}): {failure['error']}"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def percentile(values: list[float], pct: int) -> float:
    if not values:
        return math.inf
    if len(values) == 1:
        return round(values[0], 2)
    ordered = sorted(values)
    index = math.ceil((pct / 100) * len(ordered)) - 1
    index = max(0, min(index, len(ordered) - 1))
    return round(ordered[index], 2)


def ratio_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run automated analysis benchmarks.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("analysis_benchmarks.yaml")),
        help="Path to the benchmark YAML config.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Profile id to run. May be provided multiple times. Defaults to all profiles.",
    )
    parser.add_argument(
        "--host",
        help="Override host from config, e.g. http://127.0.0.1:18080",
    )
    parser.add_argument(
        "--output-dir",
        help="Override output directory from config.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_path = Path(args.config)
    config = load_config(config_path)
    if args.host or args.output_dir:
        config = BenchmarkConfig(
            defaults=BenchmarkDefaults(
                host=args.host or config.defaults.host,
                poll_interval_seconds=config.defaults.poll_interval_seconds,
                cluster_timeout_seconds=config.defaults.cluster_timeout_seconds,
                request_timeout_seconds=config.defaults.request_timeout_seconds,
                warmup_seconds=config.defaults.warmup_seconds,
                output_dir=args.output_dir or config.defaults.output_dir,
            ),
            thresholds=config.thresholds,
            datasets=config.datasets,
            profiles=config.profiles,
        )

    selected_profiles = args.profiles or list(config.profiles.keys())
    output_root = Path(config.defaults.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    summary_index = {
        "generated_at": _utc_now(),
        "host": config.defaults.host,
        "profiles": [],
    }
    any_failures = False

    for profile_id in selected_profiles:
        if profile_id not in config.profiles:
            raise BenchmarkConfigError(f"unknown profile {profile_id!r}")
        result = run_profile(config, config.profiles[profile_id], output_root)
        summary_index["profiles"].append(
            {
                "profile_id": profile_id,
                "passed": result["summary"]["passed"],
                "json_report": str(output_root / f"{profile_id}.json"),
                "markdown_report": str(output_root / f"{profile_id}.md"),
            }
        )
        any_failures = any_failures or (not result["summary"]["passed"])

    index_path = output_root / "index.json"
    index_path.write_text(json.dumps(summary_index, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if any_failures else 0


if __name__ == "__main__":
    sys.exit(main())
