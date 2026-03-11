"""Binding management for legacyai.

A *source-patch* binding records the relationship between a source artifact
(baseline) and one or more patches / a patchset.  Bindings are written to
``bindings/source-patch/<id>.yml``.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml


def bind_source_patch(
    repo_root: Path,
    source_artifact_id: str,
    tags: Optional[List[str]] = None,
    patchset_id: Optional[str] = None,
    patch_ids: Optional[List[str]] = None,
    output_artifact_id: Optional[str] = None,
) -> dict:
    """Create a source-patch binding record.

    Parameters
    ----------
    repo_root:
        Root directory of the Legacy64 archive.
    source_artifact_id:
        ID of the source artifact (baseline) being patched.
    tags:
        Optional list of tags, e.g. ``["y2038"]``.
    patchset_id:
        Optional patchset this binding belongs to, e.g. ``y2038:fix-time_t``.
    patch_ids:
        Optional explicit list of patch IDs (SHA-256) to reference.
    output_artifact_id:
        Optional ID of the derived artifact produced after patching.

    Returns
    -------
    dict
        The binding record written to disk.
    """
    binding_dir = repo_root / "bindings" / "source-patch"
    binding_dir.mkdir(parents=True, exist_ok=True)

    binding_id = str(uuid.uuid4())
    dest = binding_dir / f"{binding_id}.yml"

    record = {
        "id": binding_id,
        "type": "source-patch",
        "source_artifact_id": source_artifact_id,
        "patch_ids": patch_ids if patch_ids is not None else [],
        "patchset_id": patchset_id,
        "output_artifact_id": output_artifact_id,
        "tags": tags if tags is not None else [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(dest, "w", encoding="utf-8") as fh:
        yaml.dump(record, fh, default_flow_style=False, allow_unicode=True)

    return record


def list_bindings(repo_root: Path, binding_type: str = "source-patch") -> List[dict]:
    """Return all binding records of *binding_type*."""
    binding_dir = repo_root / "bindings" / binding_type
    records: List[dict] = []
    if not binding_dir.exists():
        return records
    for meta_file in sorted(binding_dir.glob("*.yml")):
        with open(meta_file, encoding="utf-8") as fh:
            records.append(yaml.safe_load(fh))
    return records
