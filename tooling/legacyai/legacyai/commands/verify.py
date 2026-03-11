"""``legacyai verify`` – validate all artifact records and stored objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from legacyai import repo as _repo
from legacyai.store import verify_object
from legacyai.validate import validate_artifact, validate_binding


def _check_artifacts(repo_root: Path, config: dict) -> tuple[int, int]:
    """Check all artifact records.

    Returns ``(pass_count, fail_count)``.
    """
    passed = failed = 0
    artifacts_root = repo_root / config["artifacts_dir"]
    schemas = _repo.schemas_dir(repo_root, config)
    objects = _repo.objects_root(repo_root, config)

    for lane in ("legacy64", "legacy32"):
        lane_dir = artifacts_root / lane
        if not lane_dir.exists():
            continue
        for yml_file in sorted(lane_dir.glob("*.yml")):
            label = str(yml_file.relative_to(repo_root))
            try:
                with open(yml_file, "r", encoding="utf-8") as fh:
                    record: dict[str, Any] = yaml.safe_load(fh) or {}

                # Schema validation
                validate_artifact(record, schemas if schemas.exists() else None)

                # Object existence + integrity
                digest = record.get("sha256", "")
                if not verify_object(objects, digest):
                    print(f"  FAIL  {label}: object missing or corrupted (sha256={digest})")
                    failed += 1
                    continue

                print(f"  OK    {label}")
                passed += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL  {label}: {exc}")
                failed += 1

    return passed, failed


def _check_bindings(repo_root: Path, config: dict) -> tuple[int, int]:
    """Check all binding records.

    Returns ``(pass_count, fail_count)``.
    """
    passed = failed = 0
    bindings_root = repo_root / config["bindings_dir"]
    schemas = _repo.schemas_dir(repo_root, config)
    patches = _repo.patches_dir(repo_root, config)

    for binding_type_dir in sorted(bindings_root.glob("*")):
        if not binding_type_dir.is_dir():
            continue
        for yml_file in sorted(binding_type_dir.glob("*.yml")):
            label = str(yml_file.relative_to(repo_root))
            try:
                with open(yml_file, "r", encoding="utf-8") as fh:
                    record: dict[str, Any] = yaml.safe_load(fh) or {}

                validate_binding(record, schemas if schemas.exists() else None)

                # Verify patch file if referenced
                patch_file = record.get("patch_file")
                patch_sha256 = record.get("patch_sha256")
                if patch_file:
                    patch_path = repo_root / patch_file
                    if not patch_path.exists():
                        print(f"  FAIL  {label}: patch file missing: {patch_file}")
                        failed += 1
                        continue
                    if patch_sha256:
                        from legacyai.store import sha256_file
                        actual = sha256_file(patch_path)
                        if actual != patch_sha256:
                            print(
                                f"  FAIL  {label}: patch hash mismatch "
                                f"(expected {patch_sha256}, got {actual})"
                            )
                            failed += 1
                            continue

                print(f"  OK    {label}")
                passed += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL  {label}: {exc}")
                failed += 1

    return passed, failed


def run(args, repo_root: Path) -> int:
    """Verify all artifact records and bindings.

    Returns exit code (0 = all pass, 1 = failures found).
    """
    config = _repo.load_config(repo_root)

    print("Verifying artifact records …")
    art_pass, art_fail = _check_artifacts(repo_root, config)

    print("Verifying binding records …")
    bind_pass, bind_fail = _check_bindings(repo_root, config)

    total_pass = art_pass + bind_pass
    total_fail = art_fail + bind_fail

    print(
        f"\nResult: {total_pass} passed, {total_fail} failed "
        f"({art_pass} artifacts, {bind_pass} bindings)"
    )
    return 0 if total_fail == 0 else 1
