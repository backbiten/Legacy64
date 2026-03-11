"""``legacyai init`` – initialise repository directories and config."""

from __future__ import annotations

import importlib.resources
import shutil
from pathlib import Path

import yaml

from legacyai.repo import DEFAULT_CONFIG, _CONFIG_FILENAME

_REQUIRED_DIRS = [
    "objects/sha256",
    "artifacts/legacy64",
    "artifacts/legacy32",
    "bindings/source-patch",
    "patches",
    "schemas",
]

_SCHEMA_FILES = [
    "artifact.schema.json",
    "source-patch-binding.schema.json",
]


def run(args, repo_root: Path) -> int:
    """Create directory scaffold and write default config.

    Returns exit code (0 = success).
    """
    created_dirs: list[str] = []
    for rel in _REQUIRED_DIRS:
        d = repo_root / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append(rel)
        # Ensure a .gitkeep exists in otherwise empty directories.
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists() and not any(
            f for f in d.iterdir() if not f.name.startswith(".")
        ):
            gitkeep.touch()

    if created_dirs:
        print("Created directories:")
        for d in created_dirs:
            print(f"  {d}/")
    else:
        print("All required directories already exist.")

    # Copy bundled schema files into the repo's schemas/ directory.
    schemas_dir = repo_root / "schemas"
    for schema_name in _SCHEMA_FILES:
        dest = schemas_dir / schema_name
        if not dest.exists():
            pkg_schema = importlib.resources.files("legacyai") / "schemas" / schema_name
            with importlib.resources.as_file(pkg_schema) as src:
                shutil.copy2(src, dest)
            print(f"Wrote schema   : schemas/{schema_name}")

    cfg_path = repo_root / _CONFIG_FILENAME
    if not cfg_path.exists():
        with open(cfg_path, "w", encoding="utf-8") as fh:
            yaml.dump(DEFAULT_CONFIG, fh, default_flow_style=False, sort_keys=True)
        print(f"Wrote default config: {cfg_path.relative_to(repo_root)}")
    else:
        print(f"Config already exists: {cfg_path.relative_to(repo_root)}")

    print("Repository initialised.")
    return 0
