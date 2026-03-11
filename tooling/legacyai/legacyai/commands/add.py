"""``legacyai add`` – import an artifact into the content-addressed store."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from legacyai import repo as _repo
from legacyai.store import store_object


def run(args, repo_root: Path) -> int:
    """Hash and store *args.path*, write an artifact YAML record.

    Returns exit code (0 = success).
    """
    config = _repo.load_config(repo_root)
    src = Path(args.path).resolve()

    if not src.exists():
        print(f"error: file not found: {src}")
        return 1
    if not src.is_file():
        print(f"error: not a regular file: {src}")
        return 1

    print(f"Hashing {src.name} …")
    objects = _repo.objects_root(repo_root, config)
    digest, dest = store_object(src, objects)
    size = src.stat().st_size

    artifact_id = str(uuid.uuid4())
    record: dict = {
        "id": artifact_id,
        "lane": args.lane,
        "type": args.type,
        "filename": src.name,
        "sha256": digest,
        "size": size,
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.name:
        record["name"] = args.name
    if args.version:
        record["version"] = args.version

    lane_dir = _repo.artifacts_dir(repo_root, config, args.lane)
    lane_dir.mkdir(parents=True, exist_ok=True)
    record_path = lane_dir / f"{artifact_id}.yml"
    with open(record_path, "w", encoding="utf-8") as fh:
        yaml.dump(record, fh, default_flow_style=False, sort_keys=True)

    rel_record = record_path.relative_to(repo_root)
    rel_object = dest.relative_to(repo_root)
    print(f"Stored object : {rel_object}")
    print(f"Artifact record: {rel_record}")
    print(f"Artifact ID   : {artifact_id}")
    print(f"SHA-256       : {digest}")
    return 0
