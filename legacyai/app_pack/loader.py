"""
legacyai.app_pack.loader
~~~~~~~~~~~~~~~~~~~~~~~~
Discovers and parses app-pack YAML manifests, optionally validating them
against the JSON Schema in schemas/app_pack.schema.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    """Return the repository root (two levels above this file)."""
    return Path(__file__).resolve().parent.parent.parent


def _packs_dir() -> Path:
    return _repo_root() / "app-packs"


def _schema_path() -> Path:
    return _repo_root() / "schemas" / "app_pack.schema.json"


# ---------------------------------------------------------------------------
# Schema validation (optional — skipped gracefully if jsonschema absent)
# ---------------------------------------------------------------------------

def _load_schema() -> Optional[Dict[str, Any]]:
    """Load the JSON Schema, or return None if the file is missing."""
    path = _schema_path()
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_manifest(data: Dict[str, Any]) -> None:
    """
    Validate *data* against the app_pack JSON Schema.

    Raises ``jsonschema.ValidationError`` if invalid.
    Silently skips validation if ``jsonschema`` is not installed.
    """
    schema = _load_schema()
    if schema is None:
        return
    try:
        import jsonschema  # type: ignore

        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pass  # jsonschema not installed — skip silently


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def list_packs() -> List[Dict[str, Any]]:
    """
    Return a list of summary dicts for every manifest found under app-packs/.

    Each dict has keys: ``id``, ``platform``, ``description``, ``path``.
    """
    results: List[Dict[str, Any]] = []
    packs_dir = _packs_dir()
    if not packs_dir.exists():
        return results

    for manifest_path in sorted(packs_dir.rglob("*.yml")):
        try:
            data = load_manifest(manifest_path)
            results.append(
                {
                    "id": data.get("id", manifest_path.stem),
                    "platform": data.get("platform", "unknown"),
                    "description": data.get("description", "").strip(),
                    "path": str(manifest_path),
                }
            )
        except Exception:
            # Skip malformed manifests during listing
            pass

    return results


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_manifest(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse and return a YAML manifest from *path*.

    Also validates it against the schema when ``jsonschema`` is available.

    Parameters
    ----------
    path:
        Absolute or relative path to the ``.yml`` manifest file.

    Returns
    -------
    dict
        Parsed manifest data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file cannot be parsed as YAML.
    jsonschema.ValidationError
        If the manifest does not conform to the schema (and jsonschema is installed).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping at the top level in {path}")

    validate_manifest(data)
    return data


def find_manifest(pack_id: str, os_name: str) -> Path:
    """
    Locate the manifest file for *pack_id* on *os_name*.

    Parameters
    ----------
    pack_id:
        The pack identifier (e.g. ``"desktop"``).
    os_name:
        The OS/platform (``"linux"``, ``"windows"``, or ``"macos"``).

    Returns
    -------
    Path
        Resolved path to the manifest file.

    Raises
    ------
    FileNotFoundError
        If no matching manifest is found.
    """
    candidate = _packs_dir() / os_name / f"{pack_id}.yml"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"No manifest found for pack '{pack_id}' on '{os_name}'. "
        f"Expected: {candidate}"
    )
