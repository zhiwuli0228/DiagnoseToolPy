"""Prepare benchmark datasets declared in analysis_benchmarks.yaml."""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

import yaml


class DatasetPreparationError(RuntimeError):
    """Raised when benchmark dataset preparation fails."""


def load_datasets(config_path: Path) -> list[dict]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DatasetPreparationError("config root must be a mapping")
    datasets = raw.get("datasets")
    if not isinstance(datasets, list):
        raise DatasetPreparationError("'datasets' must be a list")
    return datasets


def load_profiles(config_path: Path) -> list[dict]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DatasetPreparationError("config root must be a mapping")
    profiles = raw.get("profiles")
    if not isinstance(profiles, list):
        raise DatasetPreparationError("'profiles' must be a list")
    return profiles


def select_datasets_for_profiles(
    datasets: list[dict],
    profiles: list[dict],
    selected_profile_ids: list[str] | None,
) -> list[dict]:
    if not selected_profile_ids:
        return datasets

    dataset_map = {str(dataset["id"]): dataset for dataset in datasets}
    profile_map = {str(profile["id"]): profile for profile in profiles}
    selected_dataset_ids: list[str] = []

    for profile_id in selected_profile_ids:
        profile = profile_map.get(profile_id)
        if profile is None:
            raise DatasetPreparationError(f"unknown profile {profile_id!r}")
        scenarios = profile.get("scenarios")
        if not isinstance(scenarios, list):
            raise DatasetPreparationError(f"profile {profile_id!r} has invalid scenarios")
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                raise DatasetPreparationError(f"profile {profile_id!r} contains non-mapping scenario")
            dataset_ids = scenario.get("datasets")
            if not isinstance(dataset_ids, list):
                raise DatasetPreparationError(f"profile {profile_id!r} scenario datasets must be a list")
            for dataset_id in dataset_ids:
                dataset_id_str = str(dataset_id)
                if dataset_id_str not in dataset_map:
                    raise DatasetPreparationError(
                        f"profile {profile_id!r} references unknown dataset {dataset_id_str!r}"
                    )
                if dataset_id_str not in selected_dataset_ids:
                    selected_dataset_ids.append(dataset_id_str)

    return [dataset_map[dataset_id] for dataset_id in selected_dataset_ids]


def dataset_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for file_path in path.rglob("*"):
        if file_path.is_file():
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
    return total


def prepare_dataset(dataset: dict) -> dict:
    dataset_id = str(dataset["id"])
    source_path = Path(str(dataset["source_path"]))
    prepare_from_zip = dataset.get("prepare_from_zip")
    expected_min_bytes = int(dataset["expected_min_bytes"]) if dataset.get("expected_min_bytes") is not None else None

    if not prepare_from_zip:
        if not source_path.exists():
            raise DatasetPreparationError(
                f"dataset {dataset_id!r} source path does not exist and no prepare_from_zip is configured"
            )
        return {
            "dataset_id": dataset_id,
            "action": "validated",
            "source_path": str(source_path),
            "size_bytes": dataset_size_bytes(source_path),
        }

    archive_path = Path(str(prepare_from_zip))
    if not archive_path.exists():
        raise DatasetPreparationError(
            f"dataset {dataset_id!r} archive path does not exist: {archive_path}"
        )

    current_size = dataset_size_bytes(source_path)
    if source_path.exists() and (expected_min_bytes is None or current_size >= expected_min_bytes):
        return {
            "dataset_id": dataset_id,
            "action": "reused",
            "source_path": str(source_path),
            "size_bytes": current_size,
        }

    temp_path = source_path.parent / f"{source_path.name}.tmp-extract"
    if temp_path.exists():
        shutil.rmtree(temp_path)
    temp_path.mkdir(parents=True, exist_ok=True)

    try:
        safe_extract_zip(archive_path, temp_path)
        extracted_size = dataset_size_bytes(temp_path)
        if expected_min_bytes is not None and extracted_size < expected_min_bytes:
            raise DatasetPreparationError(
                f"dataset {dataset_id!r} extracted size {extracted_size} is smaller than expected_min_bytes {expected_min_bytes}"
            )
        if source_path.exists():
            shutil.rmtree(source_path)
        source_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.replace(source_path)
    except Exception:
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
        raise

    return {
        "dataset_id": dataset_id,
        "action": "prepared",
        "source_path": str(source_path),
        "size_bytes": dataset_size_bytes(source_path),
    }


def safe_extract_zip(archive_path: Path, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    with zipfile.ZipFile(archive_path, "r") as zf:
        for member in zf.infolist():
            member_path = target_dir / member.filename
            resolved_member = member_path.resolve()
            if not str(resolved_member).startswith(str(target_root)):
                raise DatasetPreparationError(
                    f"zip member escapes target directory: {member.filename}"
                )
            if member.is_dir():
                resolved_member.mkdir(parents=True, exist_ok=True)
                continue
            resolved_member.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, resolved_member.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare analysis benchmark datasets.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("analysis_benchmarks.yaml")),
        help="Path to benchmark YAML config.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Prepare only datasets referenced by the given profile. May be provided multiple times.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_path = Path(args.config)
    datasets = load_datasets(config_path)
    profiles = load_profiles(config_path)
    selected_datasets = select_datasets_for_profiles(datasets, profiles, args.profiles)
    results = [prepare_dataset(dataset) for dataset in selected_datasets]
    for result in results:
        print(
            f"{result['dataset_id']}: {result['action']} -> {result['source_path']} "
            f"({result['size_bytes']} bytes)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
