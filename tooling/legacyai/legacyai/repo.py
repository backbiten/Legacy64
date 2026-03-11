"""Helpers for locating the repository root and loading config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

_CONFIG_FILENAME = ".legacyai.yml"

DEFAULT_CONFIG: dict = {
    "version": 1,
    "objects_dir": "objects",
    "artifacts_dir": "artifacts",
    "bindings_dir": "bindings",
    "patches_dir": "patches",
    "schemas_dir": "schemas",
}


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk upward from *start* (default: cwd) to find the repo root.

    The root is identified by the presence of a ``.legacyai.yml`` config file
    or, as a fallback, a ``.git`` directory.

    Raises ``FileNotFoundError`` if neither is found.
    """
    here = Path(start or os.getcwd()).resolve()
    for directory in [here, *here.parents]:
        if (directory / _CONFIG_FILENAME).exists():
            return directory
        if (directory / ".git").exists():
            return directory
    raise FileNotFoundError(
        "No .legacyai.yml or .git found; run `legacyai init` first."
    )


def load_config(repo_root: Path) -> dict:
    """Load ``.legacyai.yml`` from *repo_root*, merging with defaults."""
    cfg_path = repo_root / _CONFIG_FILENAME
    config = dict(DEFAULT_CONFIG)
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh) or {}
        config.update(loaded)
    return config


def objects_root(repo_root: Path, config: dict) -> Path:
    return repo_root / config["objects_dir"]


def artifacts_dir(repo_root: Path, config: dict, lane: str) -> Path:
    return repo_root / config["artifacts_dir"] / lane


def bindings_dir(repo_root: Path, config: dict, binding_type: str) -> Path:
    return repo_root / config["bindings_dir"] / binding_type


def patches_dir(repo_root: Path, config: dict) -> Path:
    return repo_root / config["patches_dir"]


def schemas_dir(repo_root: Path, config: dict) -> Path:
    return repo_root / config["schemas_dir"]
