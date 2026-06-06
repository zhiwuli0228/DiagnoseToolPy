from pathlib import Path
import zipfile

from diagnose_tool.analyzer.scanner import (
    detect_file_type,
    is_supported_log_file,
    scan_directory,
    scan_zip_archive,
)


def test_detect_file_type_supports_expected_extensions_case_insensitively() -> None:
    assert detect_file_type("app.log") == "log"
    assert detect_file_type("notes.txt") == "txt"
    assert detect_file_type("stdout.out") == "out"
    assert detect_file_type("stderr.err") == "err"
    assert detect_file_type("archive.gz") == "gz"
    assert detect_file_type("APP.LOG") == "log"


def test_detect_file_type_marks_unsupported_extension() -> None:
    assert detect_file_type("image.png") == "unsupported"
    assert not is_supported_log_file("image.png")


def test_scan_directory_recursively_returns_metadata_and_counts(tmp_path: Path) -> None:
    root = tmp_path / "input"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "app.log").write_text("abc", encoding="utf-8")
    (nested / "worker.OUT").write_text("12345", encoding="utf-8")
    (nested / "readme.md").write_text("no", encoding="utf-8")

    result = scan_directory(root)

    assert result.root_path == str(root.resolve())
    assert result.file_count == 3
    assert result.supported_file_count == 2
    assert result.unsupported_file_count == 1
    assert result.total_bytes == 10
    assert {file.name for file in result.files} == {"app.log", "worker.OUT", "readme.md"}
    assert {file.type for file in result.files} == {"log", "out", "unsupported"}
    assert all(file.path for file in result.files)
    assert all(isinstance(file.size, int) for file in result.files)


def test_scan_directory_skips_directory_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "app.log").write_text("abc", encoding="utf-8")
    link = root / "linked"
    try:
        link.symlink_to(root, target_is_directory=True)
    except OSError:
        return

    result = scan_directory(root)

    assert result.file_count == 1
    assert result.files[0].name == "app.log"


def test_scan_zip_archive_returns_metadata_without_extracting(tmp_path: Path) -> None:
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("logs/app.log", "abc")
        zf.writestr("logs/readme.md", "no")

    result = scan_zip_archive(zip_path)

    assert result.root_path == str(zip_path.resolve())
    assert result.file_count == 2
    assert result.supported_file_count == 1
    assert result.unsupported_file_count == 1
    assert result.total_bytes == 5
    assert {file.name for file in result.files} == {"app.log", "readme.md"}
    assert any("bundle.zip!logs/app.log" in file.path for file in result.files)
