"""Metadata-only server directory scanner."""

from __future__ import annotations

import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = frozenset({".log", ".txt", ".out", ".err", ".gz"})


@dataclass(frozen=True)
class ScannedFile:
    """Metadata for one discovered file."""

    path: str
    name: str
    size: int
    type: str


@dataclass(frozen=True)
class DirectoryScanResult:
    """Summary for a metadata-only directory scan."""

    root_path: str
    file_count: int
    supported_file_count: int
    unsupported_file_count: int
    total_bytes: int
    files: tuple[ScannedFile, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""

        data = asdict(self)
        data["files"] = [asdict(file) for file in self.files]
        return data


def detect_file_type(path: str | Path) -> str:
    """Return the supported file type for a path, or unsupported."""

    suffix = Path(path).suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return suffix.removeprefix(".")
    return "unsupported"


def is_supported_log_file(path: str | Path) -> bool:
    """Return whether the path has a supported log extension."""

    return detect_file_type(path) != "unsupported"


def scan_directory(root_path: str | Path) -> DirectoryScanResult:
    """Recursively scan file metadata without opening file contents."""

    root = Path(root_path).resolve()
    files: list[ScannedFile] = []
    total_bytes = 0
    supported_count = 0

    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue

        try:
            stat = path.stat()
        except OSError:
            continue

        file_type = detect_file_type(path)
        if file_type != "unsupported":
            supported_count += 1
        total_bytes += stat.st_size
        files.append(
            ScannedFile(
                path=str(path.resolve()),
                name=path.name,
                size=stat.st_size,
                type=file_type,
            )
        )

    return DirectoryScanResult(
        root_path=str(root),
        file_count=len(files),
        supported_file_count=supported_count,
        unsupported_file_count=len(files) - supported_count,
        total_bytes=total_bytes,
        files=tuple(files),
    )


def scan_zip_archive(zip_path: str | Path) -> DirectoryScanResult:
    """Scan ZIP metadata without extracting archive contents to disk."""

    archive_path = Path(zip_path).resolve()
    files: list[ScannedFile] = []
    total_bytes = 0
    supported_count = 0

    with zipfile.ZipFile(archive_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue

            file_type = detect_file_type(info.filename)
            if file_type != "unsupported":
                supported_count += 1
            total_bytes += info.file_size
            files.append(
                ScannedFile(
                    path=f"{archive_path}!{info.filename}",
                    name=Path(info.filename).name,
                    size=info.file_size,
                    type=file_type,
                )
            )

    return DirectoryScanResult(
        root_path=str(archive_path),
        file_count=len(files),
        supported_file_count=supported_count,
        unsupported_file_count=len(files) - supported_count,
        total_bytes=total_bytes,
        files=tuple(files),
    )
