"""Schema validation helpers."""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any

import jsonschema


def _load_schema(schema_name: str, schemas_root: Path | None) -> dict:
    """Load a JSON schema by filename.

    Looks in *schemas_root* first; falls back to the schemas bundled with
    the legacyai package.
    """
    if schemas_root is not None:
        candidate = schemas_root / schema_name
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as fh:
                return json.load(fh)

    # Fall back to bundled schemas (installed as package data).
    pkg_schemas = importlib.resources.files("legacyai") / "schemas" / schema_name
    with importlib.resources.as_file(pkg_schemas) as p:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)


def validate_artifact(record: dict[str, Any], schemas_root: Path | None = None) -> None:
    """Validate *record* against the artifact JSON Schema.

    Raises ``jsonschema.ValidationError`` on failure.
    """
    schema = _load_schema("artifact.schema.json", schemas_root)
    jsonschema.validate(instance=record, schema=schema)


def validate_binding(record: dict[str, Any], schemas_root: Path | None = None) -> None:
    """Validate *record* against the source-patch binding JSON Schema.

    Raises ``jsonschema.ValidationError`` on failure.
    """
    schema = _load_schema("source-patch-binding.schema.json", schemas_root)
    jsonschema.validate(instance=record, schema=schema)
