"""Content-addressed object store operations."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return the lowercase hex SHA-256 digest of *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def object_path(root: Path, digest: str) -> Path:
    """Return the canonical store path for *digest* under *root*.

    Layout: ``<root>/sha256/<first2>/<fullhash>``
    """
    return root / "sha256" / digest[:2] / digest


def store_object(src: Path, objects_root: Path) -> tuple[str, Path]:
    """Copy *src* into the content-addressed store under *objects_root*.

    Returns ``(digest, dest_path)``.  If the object already exists the copy
    is skipped (idempotent).
    """
    digest = sha256_file(src)
    dest = object_path(objects_root, digest)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        # Make stored objects read-only to signal immutability.
        dest.chmod(0o444)
    return digest, dest


def verify_object(objects_root: Path, digest: str) -> bool:
    """Return True if the stored object exists *and* its hash matches."""
    dest = object_path(objects_root, digest)
    if not dest.exists():
        return False
    actual = sha256_file(dest)
    return actual == digest
