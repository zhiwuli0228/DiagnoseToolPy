from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import zipfile


MODULE_PATH = Path(__file__).parent / "load" / "prepare_analysis_datasets.py"
SPEC = importlib.util.spec_from_file_location("prepare_analysis_datasets", MODULE_PATH)
assert SPEC and SPEC.loader
prepare_analysis_datasets = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare_analysis_datasets
SPEC.loader.exec_module(prepare_analysis_datasets)


def test_prepare_dataset_extracts_zip_when_target_missing(tmp_path: Path) -> None:
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("logs/app.log", "hello world")

    target_dir = tmp_path / "prepared" / "bundle"
    result = prepare_analysis_datasets.prepare_dataset(
        {
            "id": "prepared",
            "source_path": str(target_dir),
            "prepare_from_zip": str(zip_path),
            "expected_min_bytes": 5,
        }
    )

    assert result["action"] == "prepared"
    assert (target_dir / "logs" / "app.log").exists()
    assert result["size_bytes"] >= 11


def test_prepare_dataset_reuses_existing_target_when_large_enough(tmp_path: Path) -> None:
    target_dir = tmp_path / "prepared"
    target_dir.mkdir()
    (target_dir / "app.log").write_text("0123456789", encoding="utf-8")
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("logs/app.log", "hello")

    result = prepare_analysis_datasets.prepare_dataset(
        {
            "id": "prepared",
            "source_path": str(target_dir),
            "prepare_from_zip": str(zip_path),
            "expected_min_bytes": 10,
        }
    )

    assert result["action"] == "reused"
    assert result["size_bytes"] >= 10


def test_select_datasets_for_profiles_filters_to_referenced_ids() -> None:
    datasets = [
        {"id": "sample_zip", "source_path": "a", "kind": "zip"},
        {"id": "large_zip", "source_path": "b", "kind": "zip"},
    ]
    profiles = [
        {
            "id": "smoke",
            "scenarios": [
                {"type": "source_scan", "datasets": ["sample_zip"]},
            ],
        }
    ]

    selected = prepare_analysis_datasets.select_datasets_for_profiles(
        datasets,
        profiles,
        ["smoke"],
    )

    assert [item["id"] for item in selected] == ["sample_zip"]
