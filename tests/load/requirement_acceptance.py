"""Requirement-level acceptance suite helpers for benchmark orchestration."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class AcceptanceConfigError(RuntimeError):
    """Raised when the acceptance suite config is invalid."""


@dataclass(frozen=True)
class AcceptanceSuite:
    id: str
    description: str
    profiles: tuple[str, ...]


def _require_bool(value: Any, *, context: str) -> bool:
    if isinstance(value, bool):
        return value
    raise AcceptanceConfigError(f"{context} must be a boolean")


def load_suites(config_path: Path) -> dict[str, AcceptanceSuite]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AcceptanceConfigError("suite config root must be a mapping")
    suites_raw = raw.get("suites")
    if not isinstance(suites_raw, list):
        raise AcceptanceConfigError("'suites' must be a list")

    suites: dict[str, AcceptanceSuite] = {}
    for item in suites_raw:
        if not isinstance(item, dict):
            raise AcceptanceConfigError("each suite must be a mapping")
        suite_id = str(item["id"])
        profiles = item.get("profiles")
        if not isinstance(profiles, list) or not profiles:
            raise AcceptanceConfigError(f"suite {suite_id!r} must define at least one profile")
        suites[suite_id] = AcceptanceSuite(
            id=suite_id,
            description=str(item.get("description", suite_id)),
            profiles=tuple(str(profile) for profile in profiles),
        )
    return suites


def get_suite(config_path: Path, suite_id: str) -> AcceptanceSuite:
    suites = load_suites(config_path)
    if suite_id not in suites:
        raise AcceptanceConfigError(f"unknown suite {suite_id!r}")
    return suites[suite_id]


def summarize_suite(artifacts_dir: Path, suite: AcceptanceSuite) -> dict[str, Any]:
    profiles_summary: list[dict[str, Any]] = []
    overall_passed = True

    for profile_id in suite.profiles:
        json_path = artifacts_dir / f"{profile_id}.json"
        if not json_path.exists():
            raise AcceptanceConfigError(
                f"missing benchmark profile output for suite {suite.id!r}: {json_path}"
            )
        data = json.loads(json_path.read_text(encoding="utf-8"))
        summary = data["summary"]
        if not isinstance(summary, dict):
            raise AcceptanceConfigError(f"summary for profile {profile_id!r} must be a mapping")
        passed = _require_bool(summary.get("passed"), context=f"summary.passed for profile {profile_id!r}")
        profiles_summary.append(
            {
                "profile_id": profile_id,
                "passed": passed,
                "metrics": summary.get("metrics", {}),
                "checks": summary.get("checks", []),
                "json_report": str(json_path),
                "markdown_report": str(artifacts_dir / f"{profile_id}.md"),
            }
        )
        overall_passed = overall_passed and passed

    return {
        "suite_id": suite.id,
        "description": suite.description,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_dir": str(artifacts_dir.resolve()),
        "passed": overall_passed,
        "profiles": profiles_summary,
    }


def finalize_suite_run(
    artifacts_dir: Path,
    suite: AcceptanceSuite,
    benchmark_exit_code: int,
) -> dict[str, Any]:
    if benchmark_exit_code != 0:
        return {
            "suite_id": suite.id,
            "description": suite.description,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts_dir": str(artifacts_dir.resolve()),
            "benchmark_exit_code": benchmark_exit_code,
            "passed": False,
            "summary_written": False,
            "profiles": [],
        }

    summary = summarize_suite(artifacts_dir, suite)
    (artifacts_dir / "acceptance-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifacts_dir / "acceptance-summary.md").write_text(
        render_markdown(summary),
        encoding="utf-8",
    )
    return {
        **summary,
        "benchmark_exit_code": benchmark_exit_code,
        "summary_written": True,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Acceptance Summary: {summary['suite_id']}",
        "",
        f"- Description: {summary['description']}",
        f"- Generated: {summary['generated_at']}",
        f"- Artifacts: {summary['artifacts_dir']}",
        f"- Result: {'PASS' if summary['passed'] else 'FAIL'}",
        "",
        "## Profiles",
        "",
        "| Profile | Result | Key Checks |",
        "|---|---|---|",
    ]

    for profile in summary["profiles"]:
        failed_checks = [check["name"] for check in profile["checks"] if not check["passed"]]
        check_summary = ", ".join(failed_checks) if failed_checks else "all checks passed"
        lines.append(
            f"| {profile['profile_id']} | {'PASS' if profile['passed'] else 'FAIL'} | {check_summary} |"
        )

    lines.extend(["", "## Review Pointers", ""])
    for profile in summary["profiles"]:
        lines.append(f"- `{profile['profile_id']}` JSON: `{profile['json_report']}`")
        lines.append(f"- `{profile['profile_id']}` Markdown: `{profile['markdown_report']}`")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Requirement acceptance suite helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profiles_parser = subparsers.add_parser("suite-profiles", help="Print suite profiles as JSON.")
    profiles_parser.add_argument("--config", required=True, help="Suite config path.")
    profiles_parser.add_argument("--suite", required=True, help="Suite id.")

    summarize_parser = subparsers.add_parser("summarize", help="Generate suite summary artifacts.")
    summarize_parser.add_argument("--config", required=True, help="Suite config path.")
    summarize_parser.add_argument("--suite", required=True, help="Suite id.")
    summarize_parser.add_argument("--artifacts-dir", required=True, help="Benchmark artifact directory.")

    finalize_parser = subparsers.add_parser(
        "finalize",
        help="Finalize benchmark artifacts and generate the acceptance summary only on success.",
    )
    finalize_parser.add_argument("--config", required=True, help="Suite config path.")
    finalize_parser.add_argument("--suite", required=True, help="Suite id.")
    finalize_parser.add_argument("--artifacts-dir", required=True, help="Benchmark artifact directory.")
    finalize_parser.add_argument(
        "--benchmark-exit-code",
        required=True,
        type=int,
        help="Exit code from the benchmark runner.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_path = Path(args.config)

    if args.command == "suite-profiles":
        suite = get_suite(config_path, args.suite)
        print(json.dumps({"suite_id": suite.id, "profiles": list(suite.profiles)}, ensure_ascii=False))
        return 0

    if args.command == "summarize":
        suite = get_suite(config_path, args.suite)
        artifacts_dir = Path(args.artifacts_dir)
        summary = summarize_suite(artifacts_dir, suite)
        print(json.dumps({"suite_id": suite.id, "passed": summary["passed"]}, ensure_ascii=False))
        return 0

    if args.command == "finalize":
        suite = get_suite(config_path, args.suite)
        artifacts_dir = Path(args.artifacts_dir)
        result = finalize_suite_run(artifacts_dir, suite, args.benchmark_exit_code)
        print(json.dumps(result, ensure_ascii=False))
        if args.benchmark_exit_code != 0:
            return args.benchmark_exit_code
        return 0 if result["passed"] else 1

    raise AcceptanceConfigError(f"unsupported command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
