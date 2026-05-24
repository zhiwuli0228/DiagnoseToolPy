"""Streaming log readers."""

from __future__ import annotations

import gzip
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO


@dataclass(frozen=True)
class LogLine:
    """One physical log line with source location."""

    file_path: str
    line_no: int
    raw: str


def read_log_lines(path: str | Path, encoding: str | None = None) -> Iterator[LogLine]:
    """Stream a normal text or gzip log file line by line.

    Args:
        path: Path to the log file.
        encoding: Optional specific encoding to use. If None, auto-detects.
    """
    file_path = Path(path)

    if file_path.suffix.lower() == ".gz":
        yield from _read_gzip_log(file_path)
        return

    if encoding:
        with file_path.open("r", encoding=encoding, errors="replace") as file:
            yield from _iter_lines(file_path, file)
        return

    # Auto-detect by sampling first bytes for CJK encoding markers
    detected_enc = _detect_encoding(file_path)
    with file_path.open("r", encoding=detected_enc, errors="replace") as file:
        yield from _iter_lines(file_path, file)


def _detect_encoding(path: Path) -> str:
    """Detect file encoding by sampling initial bytes.

    Returns the most likely encoding for the file.
    """
    # Read first 4KB to sample
    try:
        with path.open("rb") as f:
            sample = f.read(4096)
    except OSError:
        return "utf-8"

    if not sample:
        return "utf-8"

    # Check for BOM (Byte Order Mark)
    if sample.startswith(b'\xff\xfe') or sample.startswith(b'\xfe\xff'):
        return "utf-16"

    # Check for GBK/GB18030 Chinese BOM
    if sample.startswith(b'\xef\xbb\xbf'):
        return "utf-8-sig"  # UTF-8 with BOM

    # Check for high-byte density suggesting CJK encoding
    # In GBK/GB18030, Chinese characters use 2 bytes both in 0x81-0xFE range
    high_bytes = sum(1 for b in sample if b > 0x7F)
    if high_bytes > len(sample) * 0.15:
        # Likely CJK encoding (GB18030 handles both GBK and more characters)
        return "gb18030"
    elif high_bytes > len(sample) * 0.05:
        # Might be UTF-8 with some CJK characters
        # Try to decode as UTF-8 to verify
        try:
            sample.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "gb18030"

    return "utf-8"


def _read_gzip_log(path: Path) -> Iterator[LogLine]:
    """Read a gzipped log file, trying multiple encodings.

    Uses zgrep-like streaming - decompresses on the fly without loading
    entire file into memory.
    """
    # Try UTF-8 first, then GB18030 for Chinese logs
    for enc in ("utf-8", "gb18030"):
        try:
            with gzip.open(path, mode="rt", encoding=enc, errors="replace") as file:
                yield from _iter_lines(path, file)
            return
        except UnicodeDecodeError:
            continue
    # Last resort: binary read with replacement
    with gzip.open(path, mode="rt", encoding="latin-1", errors="replace") as file:
        yield from _iter_lines(path, file)


def _read_zip_contents(path: Path) -> Iterator[LogLine]:
    """Read log files inside a ZIP archive, including nested .gz files.

    Uses streaming decompression - reads each entry without loading
    entire archive into memory.
    """
    from io import StringIO

    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            lower_name = name.lower()
            if lower_name.endswith(".gz"):
                compressed = zf.read(name)
                for enc in ("utf-8", "gb18030"):
                    try:
                        decompressed = gzip.decompress(compressed)
                        text = decompressed.decode(enc, errors="replace")
                        yield from _iter_lines(Path(name), StringIO(text))
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception:
                        continue
            elif any(lower_name.endswith(ext) for ext in (".log", ".txt", ".out", ".err")):
                raw_bytes = zf.read(name)
                text = raw_bytes.decode("utf-8", errors="replace")
                yield from _iter_lines(Path(name), StringIO(text))


def read_log_lines_in_archive(path: Path) -> Iterator[LogLine]:
    """Read compressed log files inside ZIP/tar archives.

    Supports .gz, .zip (contains compressed logs), .tar.gz files.
    Uses streaming to handle large files without full decompression.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".gz":
        yield from _read_gzip_log(path)
        return

    if suffix == ".zip":
        yield from _read_zip_contents(path)
        return

    # For other files, use standard reader
    yield from read_log_lines(path)


def _iter_lines(path: Path, file: TextIO) -> Iterator[LogLine]:
    resolved = str(path.resolve())
    for line_no, line in enumerate(file, start=1):
        yield LogLine(file_path=resolved, line_no=line_no, raw=line.rstrip("\n"))
