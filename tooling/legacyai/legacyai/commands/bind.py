"""``legacyai bind source-patch`` – create a source-patch binding record."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from legacyai import repo as _repo
from legacyai.store import sha256_file, store_object


def run(args, repo_root: Path) -> int:
    """Create a source-patch binding between a legacy32 and legacy64 artifact.

    No conversion is performed.  The binding record captures the shared
    upstream source reference, an optional patch file, and build-profile
    placeholders for each lane.

    Returns exit code (0 = success).
    """
    config = _repo.load_config(repo_root)

    patch_file_rel: str | None = None
    patch_sha256: str | None = None

    if args.patch:
        src_patch = Path(args.patch).resolve()
        if not src_patch.exists():
            print(f"error: patch file not found: {src_patch}")
            return 1

        patches = _repo.patches_dir(repo_root, config)
        patches.mkdir(parents=True, exist_ok=True)
        dest_patch = patches / src_patch.name
        if not dest_patch.exists():
            shutil.copy2(src_patch, dest_patch)
            print(f"Stored patch   : {dest_patch.relative_to(repo_root)}")
        else:
            print(f"Patch exists   : {dest_patch.relative_to(repo_root)}")

        patch_sha256 = sha256_file(dest_patch)
        patch_file_rel = str(dest_patch.relative_to(repo_root))

    binding_id = str(uuid.uuid4())
    source_record: dict = {"ref": args.source}
    if getattr(args, "source_repo", None):
        source_record["repo"] = args.source_repo
    record: dict = {
        "id": binding_id,
        "type": "source-patch",
        "source": source_record,
        "legacy32_artifact": args.legacy32,
        "legacy64_artifact": args.legacy64,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "build_profiles": {
            "legacy32": {
                "toolchain": "",
                "triplet": "i686-pc-linux-gnu",
                "build_flags": [],
                "patches": [],
                "notes": "",
            },
            "legacy64": {
                "toolchain": "",
                "triplet": "x86_64-linux-gnu",
                "build_flags": [],
                "patches": [],
                "notes": "",
            },
        },
    }

    if patch_file_rel:
        record["patch_file"] = patch_file_rel
    if patch_sha256:
        record["patch_sha256"] = patch_sha256

    bindings = _repo.bindings_dir(repo_root, config, "source-patch")
    bindings.mkdir(parents=True, exist_ok=True)
    record_path = bindings / f"{binding_id}.yml"
    with open(record_path, "w", encoding="utf-8") as fh:
        yaml.dump(record, fh, default_flow_style=False, sort_keys=True)

    rel_record = record_path.relative_to(repo_root)
    print(f"Binding record : {rel_record}")
    print(f"Binding ID     : {binding_id}")
    print(f"Source ref     : {args.source}")
    print(f"legacy32       : {args.legacy32}")
    print(f"legacy64       : {args.legacy64}")
    return 0
