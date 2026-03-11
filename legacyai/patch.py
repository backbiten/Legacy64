"""Patch management for legacyai.

Patches are imported into the ``patches/`` directory and stored by their
SHA-256 content hash.  A companion ``.yml`` metadata file is written
alongside each raw ``.patch`` file.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml

from .store import compute_sha256


def add_patch(
    repo_root: Path,
    patchfile: Path,
    tags: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> dict:
    """Import *patchfile* into the patches store and return its record.

    Parameters
    ----------
    repo_root:
        Root directory of the Legacy64 archive.
    patchfile:
        Path to the patch/diff file to import.
    tags:
        Optional list of tags, e.g. ``["y2038"]``.
    name:
        Human-readable name for the patch.  Defaults to the filename.

    Returns
    -------
    dict
        The patch metadata record that was written to ``patches/<sha>.yml``.
    """
    patches_dir = repo_root / "patches"
    patches_dir.mkdir(parents=True, exist_ok=True)

    sha = compute_sha256(patchfile)
    dest_patch = patches_dir / f"{sha}.patch"
    dest_meta = patches_dir / f"{sha}.yml"

    if not dest_patch.exists():
        shutil.copy2(patchfile, dest_patch)

    record = {
        "id": sha,
        "name": name if name is not None else patchfile.name,
        "file": str(dest_patch.relative_to(repo_root)),
        "hash": sha,
        "tags": tags if tags is not None else [],
        "added_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(dest_meta, "w", encoding="utf-8") as fh:
        yaml.dump(record, fh, default_flow_style=False, allow_unicode=True)

    return record


def list_patches(repo_root: Path) -> List[dict]:
    """Return all patch records found under ``patches/``."""
    patches_dir = repo_root / "patches"
    records: List[dict] = []
    if not patches_dir.exists():
        return records
    for meta_file in sorted(patches_dir.glob("*.yml")):
        with open(meta_file, encoding="utf-8") as fh:
            records.append(yaml.safe_load(fh))
    return records


def load_patch(repo_root: Path, patch_id: str) -> dict:
    """Load and return the patch record for *patch_id* (SHA-256 prefix or full hash).

    Raises
    ------
    FileNotFoundError
        If no matching patch record is found.
    """
    patches_dir = repo_root / "patches"
    for meta_file in patches_dir.glob("*.yml"):
        if meta_file.stem.startswith(patch_id):
            with open(meta_file, encoding="utf-8") as fh:
                return yaml.safe_load(fh)
    raise FileNotFoundError(
        f"No patch record matching id prefix '{patch_id}' found in patches/"
    )
