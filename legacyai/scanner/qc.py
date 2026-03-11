"""QC (Quality Control) — deterministic, fact-based checks.

Each check is identified by a rule ID of the form QC-NNN and returns a
:class:`QCResult` with status PASS or FAIL plus human-readable details.

No network access is performed; all checks are purely local.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class QCResult:
    """Result of a single QC check."""

    check_id: str
    name: str
    status: str  # "PASS" | "FAIL"
    details: str


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_file_readable(file_path: Path) -> QCResult:
    """QC-001 — File exists and can be opened for reading."""
    cid = "QC-001"
    name = "File readable"
    try:
        with open(file_path, "rb") as fh:
            fh.read(1)
        return QCResult(cid, name, "PASS", f"File is readable: {file_path}")
    except OSError as exc:
        return QCResult(cid, name, "FAIL", str(exc))


def check_hash_matches(file_path: Path, expected_hash: Optional[str]) -> QCResult:
    """QC-002 — SHA-256 hash matches the stored object hash (when provided)."""
    cid = "QC-002"
    name = "Hash integrity"
    if expected_hash is None:
        return QCResult(cid, name, "PASS", "No expected hash supplied — skipped")
    if not expected_hash.startswith("sha256:"):
        return QCResult(cid, name, "FAIL", f"Unsupported hash scheme: {expected_hash}")
    expected_hex = expected_hash[len("sha256:"):]
    try:
        actual_hex = _sha256_of_file(file_path)
    except OSError as exc:
        return QCResult(cid, name, "FAIL", f"Cannot read file: {exc}")
    if actual_hex == expected_hex:
        return QCResult(cid, name, "PASS", f"SHA-256 matches: {actual_hex}")
    return QCResult(
        cid,
        name,
        "FAIL",
        f"Hash mismatch — expected {expected_hex}, got {actual_hex}",
    )


# Maximum file size allowed without a warning (1 GiB).
_MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024


def check_file_size(file_path: Path) -> QCResult:
    """QC-003 — File size is within reasonable bounds."""
    cid = "QC-003"
    name = "File size"
    try:
        size = file_path.stat().st_size
    except OSError as exc:
        return QCResult(cid, name, "FAIL", str(exc))
    if size == 0:
        return QCResult(cid, name, "FAIL", "File is empty (0 bytes)")
    if size > _MAX_FILE_SIZE:
        return QCResult(
            cid,
            name,
            "FAIL",
            f"File is {size} bytes, exceeds limit of {_MAX_FILE_SIZE} bytes",
        )
    return QCResult(cid, name, "PASS", f"File size: {size} bytes")


# ---------------------------------------------------------------------------
# Magic-byte / file-type detection
# ---------------------------------------------------------------------------

# (magic_bytes, offset, label)
_MAGIC_TABLE = [
    (b"\x7fELF", 0, "ELF executable"),
    (b"MZ", 0, "PE executable (Windows)"),
    (b"\xcf\xfa\xed\xfe", 0, "Mach-O 64-bit LE"),
    (b"\xce\xfa\xed\xfe", 0, "Mach-O 32-bit LE"),
    (b"\xfe\xed\xfa\xcf", 0, "Mach-O 64-bit BE"),
    (b"\xfe\xed\xfa\xce", 0, "Mach-O 32-bit BE"),
    (b"PK\x03\x04", 0, "ZIP archive"),
    (b"PK\x05\x06", 0, "ZIP archive (empty)"),
    (b"\x1f\x8b", 0, "gzip stream"),
    (b"BZh", 0, "bzip2 stream"),
    (b"\xfd7zXZ\x00", 0, "xz stream"),
    (b"7z\xbc\xaf'\x1c", 0, "7-zip archive"),
    (b"Rar!\x1a\x07", 0, "RAR archive"),
    (b"%PDF-", 0, "PDF document"),
    (b"\xff\xd8\xff", 0, "JPEG image"),
    (b"\x89PNG\r\n\x1a\n", 0, "PNG image"),
    (b"GIF87a", 0, "GIF87 image"),
    (b"GIF89a", 0, "GIF89 image"),
]


def detect_file_type(file_path: Path) -> str:
    """Return a human-readable file-type label derived from magic bytes."""
    try:
        with open(file_path, "rb") as fh:
            header = fh.read(16)
    except OSError:
        return "unreadable"
    for magic, offset, label in _MAGIC_TABLE:
        if header[offset : offset + len(magic)] == magic:
            return label
    # TAR detection (magic at offset 257)
    try:
        with open(file_path, "rb") as fh:
            fh.seek(257)
            tar_magic = fh.read(8)
        # POSIX ustar\0 and GNU "ustar  \0" (two spaces + null)
        if tar_magic[:5] == b"ustar":
            return "tar archive"
    except OSError:
        pass
    # Fallback: try to decode as UTF-8 text
    try:
        with open(file_path, "r", encoding="utf-8", errors="strict") as fh:
            fh.read(512)
        return "text/UTF-8"
    except (OSError, UnicodeDecodeError):
        pass
    return "binary/unknown"


def check_file_type(file_path: Path) -> QCResult:
    """QC-004 — Detect and record the file type via magic bytes."""
    cid = "QC-004"
    name = "File type detection"
    file_type = detect_file_type(file_path)
    return QCResult(cid, name, "PASS", f"Detected type: {file_type}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_qc_checks(
    file_path: Path, expected_hash: Optional[str] = None
) -> List[QCResult]:
    """Run all QC checks against *file_path* and return results."""
    return [
        check_file_readable(file_path),
        check_hash_matches(file_path, expected_hash),
        check_file_size(file_path),
        check_file_type(file_path),
    ]


def qc_status(results: List[QCResult]) -> str:
    """Aggregate QC results into PASS or FAIL."""
    return "FAIL" if any(r.status == "FAIL" for r in results) else "PASS"
