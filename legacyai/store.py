"""Content-addressed store helpers for legacyai."""

import hashlib
from pathlib import Path


def compute_sha256(path: Path) -> str:
    """Return the hex-encoded SHA-256 digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    """Return the hex-encoded SHA-256 digest of a bytes object."""
    return hashlib.sha256(data).hexdigest()
