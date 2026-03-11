"""QA (Quality Assurance) — heuristic, rule-based checks.

Rules are identified by QA-NNN.  Each rule returns zero or more
:class:`Finding` objects with a severity of INFO, WARN, or FAIL.

Design principles
-----------------
* Pure Python — standard library only.
* No network access.
* Every finding is explainable: rule ID + human-readable description.
* Conservative: prefer WARN over FAIL where certainty is lower.
* Fail-safe: exceptions inside individual rules are caught and reported
  as WARN rather than crashing the scan.
"""

import io
import math
import re
import struct
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single QA finding produced by a rule."""

    rule_id: str
    name: str
    severity: str  # "INFO" | "WARN" | "FAIL"
    details: str


Rule = Callable[[Path], List[Finding]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_READ_LIMIT = 10 * 1024 * 1024  # 10 MiB for in-memory analysis


def _read_head(path: Path, n: int = _READ_LIMIT) -> bytes:
    """Read up to *n* bytes from *path* without raising."""
    try:
        with open(path, "rb") as fh:
            return fh.read(n)
    except OSError:
        return b""


def _shannon_entropy(data: bytes) -> float:
    """Return Shannon entropy in bits/byte (0–8)."""
    if not data:
        return 0.0
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    length = len(data)
    entropy = 0.0
    for c in counts:
        if c:
            p = c / length
            entropy -= p * math.log2(p)
    return entropy


def _safe_rule(rule_id: str, rule_name: str, fn: Rule) -> Rule:
    """Wrap a rule function so that unexpected exceptions become WARN findings."""

    def wrapper(path: Path) -> List[Finding]:
        try:
            return fn(path)
        except Exception as exc:  # pylint: disable=broad-except
            return [
                Finding(
                    rule_id,
                    rule_name,
                    "WARN",
                    f"Rule raised an unexpected error: {exc}",
                )
            ]

    return wrapper


# ---------------------------------------------------------------------------
# QA-001 — ELF binary detection
# ---------------------------------------------------------------------------


def _rule_elf(path: Path) -> List[Finding]:
    data = _read_head(path, 4)
    if data[:4] == b"\x7fELF":
        return [
            Finding(
                "QA-001",
                "ELF binary detected",
                "WARN",
                "File has ELF magic bytes — contains native executable code.",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# QA-002 — PE binary detection
# ---------------------------------------------------------------------------


def _rule_pe(path: Path) -> List[Finding]:
    data = _read_head(path, 2)
    if data[:2] == b"MZ":
        return [
            Finding(
                "QA-002",
                "PE binary detected",
                "WARN",
                "File has MZ/PE magic bytes — Windows Portable Executable.",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# QA-003 — Mach-O binary detection
# ---------------------------------------------------------------------------

_MACHO_MAGIC = {
    b"\xcf\xfa\xed\xfe": "Mach-O 64-bit LE",
    b"\xce\xfa\xed\xfe": "Mach-O 32-bit LE",
    b"\xfe\xed\xfa\xcf": "Mach-O 64-bit BE",
    b"\xfe\xed\xfa\xce": "Mach-O 32-bit BE",
}


def _rule_macho(path: Path) -> List[Finding]:
    data = _read_head(path, 4)
    label = _MACHO_MAGIC.get(data[:4])
    if label:
        return [
            Finding(
                "QA-003",
                "Mach-O binary detected",
                "WARN",
                f"File has Mach-O magic bytes ({label}) — macOS/iOS executable.",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# QA-004 — Shebang / executable script detection
# ---------------------------------------------------------------------------


def _rule_shebang(path: Path) -> List[Finding]:
    data = _read_head(path, 256)
    if data[:2] == b"#!":
        line_end = data.find(b"\n")
        shebang = data[: line_end if line_end != -1 else 256].decode(
            "utf-8", errors="replace"
        )
        return [
            Finding(
                "QA-004",
                "Executable script (shebang)",
                "WARN",
                f"File starts with a shebang line: {shebang!r}",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# QA-005 — ZIP archive inspection
# ---------------------------------------------------------------------------

_SUSPICIOUS_NAMES = re.compile(
    r"""
    (?i)                     # case-insensitive
    autorun\.inf$            # autorun file
    | \.lnk$                 # Windows shortcut
    | (?<!\.)\.exe\b         # .exe (direct)
    | \.[a-z]{2,4}\.exe$    # double-extension ending in .exe
    | \.[a-z]{2,4}\.bat$    # double-extension ending in .bat
    | \.[a-z]{2,4}\.cmd$    # double-extension ending in .cmd
    | \.[a-z]{2,4}\.vbs$    # double-extension ending in .vbs
    | \.[a-z]{2,4}\.ps1$    # double-extension ending in .ps1
    | \.[a-z]{2,4}\.scr$    # double-extension ending in .scr
    """,
    re.VERBOSE,
)

_ZIP_FILE_LIMIT = 1000
_ZIP_SIZE_LIMIT = 1 * 1024 * 1024 * 1024  # 1 GiB uncompressed total
_ZIP_RATIO_LIMIT = 500  # per-entry compression ratio


def _check_zip_name(name: str) -> Optional[Finding]:
    """Return a Finding if *name* matches a suspicious pattern."""
    if _SUSPICIOUS_NAMES.search(name):
        return Finding(
            "QA-005",
            "Suspicious filename in ZIP",
            "FAIL",
            f"Entry name matches suspicious pattern: {name!r}",
        )
    # Hidden files (Unix dot-files) — lower severity
    basename = name.rstrip("/").rsplit("/", 1)[-1]
    if basename.startswith(".") and basename not in (".", ".."):
        return Finding(
            "QA-005",
            "Hidden file in ZIP",
            "WARN",
            f"Entry appears to be a hidden file: {name!r}",
        )
    return None


def _rule_zip(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    if not zipfile.is_zipfile(path):
        return findings
    try:
        with zipfile.ZipFile(path, "r") as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile as exc:
        return [Finding("QA-005", "Corrupt ZIP", "WARN", str(exc))]

    # Entry count check
    if len(infos) > _ZIP_FILE_LIMIT:
        findings.append(
            Finding(
                "QA-005",
                "ZIP entry count excessive",
                "WARN",
                f"Archive contains {len(infos)} entries (limit {_ZIP_FILE_LIMIT}).",
            )
        )

    total_uncompressed = 0
    for info in infos:
        name_finding = _check_zip_name(info.filename)
        if name_finding:
            findings.append(name_finding)

        total_uncompressed += info.file_size

        # Per-entry compression ratio (zip bomb indicator)
        if info.compress_size > 0:
            ratio = info.file_size / info.compress_size
            if ratio > _ZIP_RATIO_LIMIT:
                findings.append(
                    Finding(
                        "QA-005",
                        "Extreme compression ratio in ZIP entry",
                        "FAIL",
                        f"Entry {info.filename!r}: ratio {ratio:.0f}:1 "
                        f"(compressed={info.compress_size}, "
                        f"uncompressed={info.file_size}). Possible zip bomb.",
                    )
                )

    # Total uncompressed size check
    if total_uncompressed > _ZIP_SIZE_LIMIT:
        findings.append(
            Finding(
                "QA-005",
                "ZIP total uncompressed size excessive",
                "WARN",
                f"Total uncompressed size {total_uncompressed} bytes "
                f"exceeds limit {_ZIP_SIZE_LIMIT} bytes.",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# QA-006 — TAR archive inspection
# ---------------------------------------------------------------------------

_TAR_FILE_LIMIT = 1000
_TAR_SIZE_LIMIT = 1 * 1024 * 1024 * 1024  # 1 GiB


def _rule_tar(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    if not tarfile.is_tarfile(path):
        return findings
    try:
        with tarfile.open(path, "r:*") as tf:
            members = tf.getmembers()
    except (tarfile.TarError, EOFError) as exc:
        return [Finding("QA-006", "Corrupt TAR", "WARN", str(exc))]

    if len(members) > _TAR_FILE_LIMIT:
        findings.append(
            Finding(
                "QA-006",
                "TAR entry count excessive",
                "WARN",
                f"Archive contains {len(members)} entries (limit {_TAR_FILE_LIMIT}).",
            )
        )

    total_size = 0
    for m in members:
        # Path traversal check
        if m.name.startswith("/") or ".." in m.name.split("/"):
            findings.append(
                Finding(
                    "QA-006",
                    "Path traversal in TAR",
                    "FAIL",
                    f"Entry name could escape archive root: {m.name!r}",
                )
            )
        # Suspicious filenames (reuse ZIP checker on the basename)
        name_finding = _check_zip_name(m.name)
        if name_finding:
            findings.append(
                Finding(
                    "QA-006",
                    name_finding.name.replace("ZIP", "TAR"),
                    name_finding.severity,
                    name_finding.details.replace("ZIP", "TAR"),
                )
            )
        total_size += m.size

    if total_size > _TAR_SIZE_LIMIT:
        findings.append(
            Finding(
                "QA-006",
                "TAR total uncompressed size excessive",
                "WARN",
                f"Total size {total_size} bytes exceeds limit {_TAR_SIZE_LIMIT} bytes.",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# QA-007 — High entropy / obfuscation detection
# ---------------------------------------------------------------------------

_ENTROPY_THRESHOLD = 7.2  # bits/byte; compressed/encrypted data is typically >7.5
_BASE64_MIN_RUN = 200     # minimum length of a suspicious base64 run
_BASE64_RE = re.compile(
    ("[A-Za-z0-9+/]{" + str(_BASE64_MIN_RUN) + ",}={0,2}").encode()
)


def _rule_entropy(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    data = _read_head(path)
    if not data:
        return findings

    entropy = _shannon_entropy(data)
    if entropy >= _ENTROPY_THRESHOLD:
        findings.append(
            Finding(
                "QA-007",
                "High entropy content",
                "WARN",
                f"Shannon entropy {entropy:.2f} bits/byte (threshold {_ENTROPY_THRESHOLD}). "
                "File may be compressed, encrypted, or obfuscated.",
            )
        )

    # Long base64 blobs (even inside low-entropy files, obfuscated scripts
    # often embed payload as a base64 string)
    matches = _BASE64_RE.findall(data)
    if matches:
        longest = max(len(m) for m in matches)
        findings.append(
            Finding(
                "QA-007",
                "Long base64-encoded run",
                "WARN",
                f"Found {len(matches)} base64 run(s); longest is {longest} bytes. "
                "May indicate an encoded/obfuscated payload.",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# QA-008 — Embedded executable detection
# ---------------------------------------------------------------------------

_EXEC_MAGIC = [
    (b"\x7fELF", "ELF"),
    (b"MZ", "PE/MZ"),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit LE"),
    (b"\xce\xfa\xed\xfe", "Mach-O 32-bit LE"),
]

# Only scan these "outer" file types for embedded executables
_SCAN_FOR_EMBEDDED = {
    "ZIP archive",
    "PDF document",
    "text/UTF-8",
    "binary/unknown",
}


def _rule_embedded_exec(path: Path) -> List[Finding]:
    from legacyai.scanner.qc import detect_file_type  # local import to avoid cycle

    findings: List[Finding] = []
    outer_type = detect_file_type(path)

    # If the file itself IS an executable, skip (QA-001/002/003 already fired)
    if outer_type in ("ELF executable", "PE executable (Windows)") or outer_type.startswith(
        "Mach-O"
    ):
        return findings

    data = _read_head(path)
    if not data:
        return findings

    for magic, label in _EXEC_MAGIC:
        offset = 0
        while True:
            idx = data.find(magic, offset)
            if idx == -1:
                break
            # Skip the very first bytes (already covered by QA-001/002/003)
            if idx > 0:
                findings.append(
                    Finding(
                        "QA-008",
                        "Embedded executable magic bytes",
                        "WARN",
                        f"Found {label} magic bytes at offset {idx} "
                        f"inside a file of type '{outer_type}'.",
                    )
                )
            offset = idx + len(magic)

    return findings


# ---------------------------------------------------------------------------
# QA-009 — Credential / secret pattern detection
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: List[Tuple[str, str, str]] = [
    # (pattern_name, regex, severity)
    ("AWS access key ID", r"AKIA[0-9A-Z]{16}", "FAIL"),
    ("AWS secret access key", r"(?i)aws.{0,10}secret.{0,10}[=:]\s*[A-Za-z0-9+/]{40}", "FAIL"),
    ("PEM private key header", r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "FAIL"),
    ("Generic API key", r"(?i)api[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}", "WARN"),
    ("Generic password field", r"(?i)password\s*[=:]\s*['\"][^'\"]{4,}", "WARN"),
    ("Generic token field", r"(?i)(?:token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}", "WARN"),
    ("GitHub personal access token", r"gh[pousr]_[A-Za-z0-9_]{36,}", "FAIL"),
    ("Slack webhook URL", r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+", "FAIL"),
]

_COMPILED_SECRETS = [
    (name, re.compile(pattern.encode(), re.IGNORECASE), sev)
    for name, pattern, sev in _SECRET_PATTERNS
]


def _rule_secrets(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    data = _read_head(path)
    if not data:
        return findings
    for name, pattern, severity in _COMPILED_SECRETS:
        matches = pattern.findall(data)
        if matches:
            findings.append(
                Finding(
                    "QA-009",
                    f"Potential credential: {name}",
                    severity,
                    f"Found {len(matches)} match(es) for pattern '{name}'. "
                    "Review before sharing.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Rule registry and runner
# ---------------------------------------------------------------------------

_RULES: List[Tuple[str, str, Rule]] = [
    ("QA-001", "ELF binary", _rule_elf),
    ("QA-002", "PE binary", _rule_pe),
    ("QA-003", "Mach-O binary", _rule_macho),
    ("QA-004", "Shebang script", _rule_shebang),
    ("QA-005", "ZIP inspection", _rule_zip),
    ("QA-006", "TAR inspection", _rule_tar),
    ("QA-007", "High entropy / obfuscation", _rule_entropy),
    ("QA-008", "Embedded executable", _rule_embedded_exec),
    ("QA-009", "Credential / secret patterns", _rule_secrets),
]


def run_qa_checks(file_path: Path) -> List[Finding]:
    """Run all QA rules against *file_path* and return a flat list of findings."""
    findings: List[Finding] = []
    for rule_id, rule_name, rule_fn in _RULES:
        safe = _safe_rule(rule_id, rule_name, rule_fn)
        findings.extend(safe(file_path))
    return findings


def qa_status(findings: List[Finding]) -> str:
    """Aggregate QA findings into PASS, WARN, or FAIL."""
    severities = {f.severity for f in findings}
    if "FAIL" in severities:
        return "FAIL"
    if "WARN" in severities:
        return "WARN"
    return "PASS"
