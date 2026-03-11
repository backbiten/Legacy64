"""Verification logic for legacyai.

``verify`` inspects all patches, patchsets and bindings in the archive and
reports any integrity problems:

- Patchset metadata references must point to existing patch records.
- Patch files on disk must match the stored hash.
- Baseline artifact IDs referenced by patchsets/bindings must have a
  corresponding ``artifacts/<id>.yml`` file.
- Binding patch_ids must resolve to known patches.
- Binding patchset_ids must point to existing patchset records.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import yaml

from .store import compute_sha256


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except (yaml.YAMLError, OSError):
        return None


def _find_patch_meta(patches_dir: Path, patch_id: str) -> Optional[Path]:
    """Return the first .yml path whose stem starts with *patch_id*."""
    for p in patches_dir.glob("*.yml"):
        if p.stem.startswith(patch_id):
            return p
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class VerificationError:
    """Represents a single verification finding."""

    def __init__(self, category: str, path: str, message: str):
        self.category = category
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"[{self.category}] {self.path}: {self.message}"


def verify(repo_root: Path) -> Tuple[List[VerificationError], int, int]:
    """Run all integrity checks.

    Returns
    -------
    (errors, checked, ok)
        A list of :class:`VerificationError` objects plus counts of total
        items checked and items that passed.
    """
    errors: List[VerificationError] = []
    checked = 0
    ok = 0

    patches_dir = repo_root / "patches"
    patchsets_root = repo_root / "patchsets"
    bindings_root = repo_root / "bindings"
    artifacts_dir = repo_root / "artifacts"

    # ------------------------------------------------------------------
    # 1. Verify patch files
    # ------------------------------------------------------------------
    if patches_dir.exists():
        for meta_file in sorted(patches_dir.glob("*.yml")):
            record = _load_yaml(meta_file)
            if record is None:
                errors.append(
                    VerificationError("patch", str(meta_file), "Cannot parse YAML")
                )
                checked += 1
                continue

            checked += 1
            patch_file = repo_root / record.get("file", "")
            if not patch_file.exists():
                errors.append(
                    VerificationError(
                        "patch",
                        str(meta_file),
                        f"Patch file missing: {patch_file}",
                    )
                )
                continue

            actual_hash = compute_sha256(patch_file)
            expected_hash = record.get("hash", "")
            if actual_hash != expected_hash:
                errors.append(
                    VerificationError(
                        "patch",
                        str(meta_file),
                        f"Hash mismatch: expected {expected_hash}, got {actual_hash}",
                    )
                )
                continue

            ok += 1

    # ------------------------------------------------------------------
    # 2. Verify patchset records
    # ------------------------------------------------------------------
    if patchsets_root.exists():
        for meta_file in sorted(patchsets_root.rglob("*.yml")):
            record = _load_yaml(meta_file)
            if record is None:
                errors.append(
                    VerificationError(
                        "patchset", str(meta_file), "Cannot parse YAML"
                    )
                )
                checked += 1
                continue

            checked += 1
            patchset_ok = True

            # Check each patch reference
            for entry in record.get("patches") or []:
                pid = entry.get("patch_id", "")
                if not pid:
                    errors.append(
                        VerificationError(
                            "patchset",
                            str(meta_file),
                            "Patch entry missing 'patch_id'",
                        )
                    )
                    patchset_ok = False
                    continue

                patch_meta = _find_patch_meta(patches_dir, pid)
                if patch_meta is None:
                    errors.append(
                        VerificationError(
                            "patchset",
                            str(meta_file),
                            f"Referenced patch '{pid}' not found in patches/",
                        )
                    )
                    patchset_ok = False

            # Check baseline artifact
            baseline_id = record.get("baseline_artifact_id")
            if baseline_id:
                artifact_meta = artifacts_dir / f"{baseline_id}.yml"
                if not artifact_meta.exists():
                    errors.append(
                        VerificationError(
                            "patchset",
                            str(meta_file),
                            f"Baseline artifact '{baseline_id}' not found in artifacts/",
                        )
                    )
                    patchset_ok = False

            # Check output artifact
            output_id = record.get("output_artifact_id")
            if output_id:
                artifact_meta = artifacts_dir / f"{output_id}.yml"
                if not artifact_meta.exists():
                    errors.append(
                        VerificationError(
                            "patchset",
                            str(meta_file),
                            f"Output artifact '{output_id}' not found in artifacts/",
                        )
                    )
                    patchset_ok = False

            if patchset_ok:
                ok += 1

    # ------------------------------------------------------------------
    # 3. Verify binding records
    # ------------------------------------------------------------------
    if bindings_root.exists():
        for meta_file in sorted(bindings_root.rglob("*.yml")):
            record = _load_yaml(meta_file)
            if record is None:
                errors.append(
                    VerificationError(
                        "binding", str(meta_file), "Cannot parse YAML"
                    )
                )
                checked += 1
                continue

            checked += 1
            binding_ok = True

            # Check each referenced patch_id
            for pid in record.get("patch_ids") or []:
                patch_meta = _find_patch_meta(patches_dir, pid)
                if patch_meta is None:
                    errors.append(
                        VerificationError(
                            "binding",
                            str(meta_file),
                            f"Referenced patch '{pid}' not found in patches/",
                        )
                    )
                    binding_ok = False

            # Check referenced patchset
            patchset_id = record.get("patchset_id")
            if patchset_id:
                if ":" in patchset_id:
                    ns, name = patchset_id.split(":", 1)
                else:
                    ns, name = "y2038", patchset_id
                patchset_meta = patchsets_root / ns / f"{name}.yml"
                if not patchset_meta.exists():
                    errors.append(
                        VerificationError(
                            "binding",
                            str(meta_file),
                            f"Referenced patchset '{patchset_id}' not found",
                        )
                    )
                    binding_ok = False

            # Check source artifact
            source_id = record.get("source_artifact_id")
            if source_id:
                artifact_meta = artifacts_dir / f"{source_id}.yml"
                if not artifact_meta.exists():
                    errors.append(
                        VerificationError(
                            "binding",
                            str(meta_file),
                            f"Source artifact '{source_id}' not found in artifacts/",
                        )
                    )
                    binding_ok = False

            # Check output artifact
            output_id = record.get("output_artifact_id")
            if output_id:
                artifact_meta = artifacts_dir / f"{output_id}.yml"
                if not artifact_meta.exists():
                    errors.append(
                        VerificationError(
                            "binding",
                            str(meta_file),
                            f"Output artifact '{output_id}' not found in artifacts/",
                        )
                    )
                    binding_ok = False

            if binding_ok:
                ok += 1

    return errors, checked, ok
