from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).parent / "load" / "requirement_acceptance.py"
SPEC = importlib.util.spec_from_file_location("requirement_acceptance", MODULE_PATH)
assert SPEC and SPEC.loader
requirement_acceptance = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = requirement_acceptance
SPEC.loader.exec_module(requirement_acceptance)


def test_load_suites_reads_profiles(tmp_path: Path) -> None:
    config_path = tmp_path / "suites.yaml"
    config_path.write_text(
        """
suites:
  - id: current
    description: current requirement
    profiles:
      - smoke_scan_sample
      - directory_concurrency_baseline
""".strip(),
        encoding="utf-8",
    )

    suites = requirement_acceptance.load_suites(config_path)

    assert "current" in suites
    assert suites["current"].profiles == (
        "smoke_scan_sample",
        "directory_concurrency_baseline",
    )


def test_summarize_suite_aggregates_profile_results(tmp_path: Path) -> None:
    suite = requirement_acceptance.AcceptanceSuite(
        id="current",
        description="current requirement",
        profiles=("smoke_scan_sample", "directory_concurrency_baseline"),
    )
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    for profile_id, passed in [
        ("smoke_scan_sample", True),
        ("directory_concurrency_baseline", False),
    ]:
        (artifacts_dir / f"{profile_id}.json").write_text(
            json.dumps(
                {
                    "summary": {
                        "passed": passed,
                        "metrics": {},
                        "checks": [
                            {"name": f"{profile_id}.check", "passed": passed},
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )

    summary = requirement_acceptance.summarize_suite(artifacts_dir, suite)

    assert summary["suite_id"] == "current"
    assert summary["passed"] is False
    assert [profile["profile_id"] for profile in summary["profiles"]] == [
        "smoke_scan_sample",
        "directory_concurrency_baseline",
    ]


def test_summarize_suite_rejects_non_boolean_passed(tmp_path: Path) -> None:
    suite = requirement_acceptance.AcceptanceSuite(
        id="current",
        description="current requirement",
        profiles=("smoke_scan_sample",),
    )
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "smoke_scan_sample.json").write_text(
        json.dumps({"summary": {"passed": "false", "metrics": {}, "checks": []}}),
        encoding="utf-8",
    )

    try:
        requirement_acceptance.summarize_suite(artifacts_dir, suite)
    except requirement_acceptance.AcceptanceConfigError as exc:
        assert "must be a boolean" in str(exc)
    else:
        raise AssertionError("summarize_suite should reject non-boolean passed values")


def test_finalize_suite_run_skips_summary_when_benchmark_failed(tmp_path: Path) -> None:
    suite = requirement_acceptance.AcceptanceSuite(
        id="current",
        description="current requirement",
        profiles=("smoke_scan_sample",),
    )
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    result = requirement_acceptance.finalize_suite_run(artifacts_dir, suite, benchmark_exit_code=7)

    assert result["passed"] is False
    assert result["summary_written"] is False
    assert result["benchmark_exit_code"] == 7
    assert not (artifacts_dir / "acceptance-summary.json").exists()
    assert not (artifacts_dir / "acceptance-summary.md").exists()


def test_repo_acceptance_suite_matches_current_requirement() -> None:
    suite = requirement_acceptance.get_suite(
        Path(__file__).parent / "load" / "acceptance_suites.yaml",
        "current_large_log_cluster_requirement",
    )

    assert suite.profiles == (
        "smoke_scan_sample",
        "directory_concurrency_baseline",
    )
