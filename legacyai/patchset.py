"""Patchset management for legacyai.

A *patchset* is an ordered collection of patches that together constitute a
named series of fixes.  Y2038-related patchsets live under
``patchsets/y2038/``.

Patchset IDs follow the convention ``<namespace>:<name>``,
e.g. ``y2038:fix-time_t-overflow``.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml


_NAMESPACE_DIR = {
    "y2038": "patchsets/y2038",
}
_DEFAULT_NAMESPACE = "y2038"


def _parse_id(patchset_id: str):
    """Split ``namespace:name`` → ``(namespace, name)``."""
    if ":" in patchset_id:
        namespace, name = patchset_id.split(":", 1)
    else:
        namespace = _DEFAULT_NAMESPACE
        name = patchset_id
    return namespace, name


def _patchset_path(repo_root: Path, patchset_id: str) -> Path:
    namespace, name = _parse_id(patchset_id)
    subdir = _NAMESPACE_DIR.get(namespace, f"patchsets/{namespace}")
    return repo_root / subdir / f"{name}.yml"


def create_patchset(
    repo_root: Path,
    patchset_id: str,
    description: Optional[str] = None,
    baseline_artifact_id: Optional[str] = None,
    expected_source_hash: Optional[str] = None,
    output_artifact_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    """Create a new patchset metadata record.

    Parameters
    ----------
    repo_root:
        Root directory of the Legacy64 archive.
    patchset_id:
        Identifier in the form ``y2038:<name>``.
    description:
        Human-readable description of the patchset.
    baseline_artifact_id:
        ID of the artifact that this patchset targets.
    expected_source_hash:
        Expected SHA-256 of the source archive at *baseline_artifact_id*.
    output_artifact_id:
        Optional ID of an artifact produced after applying this patchset.
    tags:
        Optional tags list (``["y2038"]`` is always included).

    Returns
    -------
    dict
        The patchset record that was written to disk.
    """
    namespace, name = _parse_id(patchset_id)
    meta_path = _patchset_path(repo_root, patchset_id)
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    if meta_path.exists():
        raise FileExistsError(
            f"Patchset '{patchset_id}' already exists at {meta_path}"
        )

    combined_tags = list(tags or [])
    if namespace not in combined_tags:
        combined_tags.insert(0, namespace)

    record = {
        "id": patchset_id,
        "namespace": namespace,
        "name": name,
        "description": description or "",
        "patches": [],
        "baseline_artifact_id": baseline_artifact_id,
        "expected_source_hash": expected_source_hash,
        "output_artifact_id": output_artifact_id,
        "tags": combined_tags,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(meta_path, "w", encoding="utf-8") as fh:
        yaml.dump(record, fh, default_flow_style=False, allow_unicode=True)

    return record


def add_patch_to_patchset(
    repo_root: Path,
    patchset_id: str,
    patch_id: str,
    order: int,
    note: Optional[str] = None,
) -> dict:
    """Append a patch reference to an existing patchset.

    Parameters
    ----------
    repo_root:
        Root directory of the Legacy64 archive.
    patchset_id:
        Patchset identifier, e.g. ``y2038:fix-time_t-overflow``.
    patch_id:
        Full or prefix SHA-256 of the patch to reference.
    order:
        Sequence position (1-based) of this patch in the series.
    note:
        Optional human-readable note about this patch's role.

    Returns
    -------
    dict
        The updated patchset record.
    """
    meta_path = _patchset_path(repo_root, patchset_id)
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Patchset '{patchset_id}' not found at {meta_path}"
        )

    with open(meta_path, encoding="utf-8") as fh:
        record = yaml.safe_load(fh)

    entry = {"order": order, "patch_id": patch_id}
    if note:
        entry["note"] = note

    patches_list = record.get("patches") or []
    # Replace if same order already exists, otherwise append.
    existing = [p for p in patches_list if p.get("order") != order]
    existing.append(entry)
    existing.sort(key=lambda p: p.get("order", 0))
    record["patches"] = existing

    with open(meta_path, "w", encoding="utf-8") as fh:
        yaml.dump(record, fh, default_flow_style=False, allow_unicode=True)

    return record


def list_patchsets(repo_root: Path) -> List[dict]:
    """Return all patchset records found under ``patchsets/``."""
    records: List[dict] = []
    patchsets_root = repo_root / "patchsets"
    if not patchsets_root.exists():
        return records
    for meta_file in sorted(patchsets_root.rglob("*.yml")):
        with open(meta_file, encoding="utf-8") as fh:
            records.append(yaml.safe_load(fh))
    return records


def load_patchset(repo_root: Path, patchset_id: str) -> dict:
    """Load and return the patchset record for *patchset_id*.

    Raises
    ------
    FileNotFoundError
        If the patchset record does not exist.
    """
    meta_path = _patchset_path(repo_root, patchset_id)
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Patchset '{patchset_id}' not found at {meta_path}"
        )
    with open(meta_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
