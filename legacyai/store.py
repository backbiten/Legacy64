"""Content-addressed object store and artifact metadata management.

Layout under the repo root::

    objects/          # SHA-256 content-addressed blobs (git-style aa/bbb...)
    artifacts/        # JSON metadata records keyed by artifact-id
    reports/          # JSON scan reports keyed by artifact-id
    quarantine/
        objects/      # Content-addressed blobs for quarantined items
        records/      # JSON quarantine records keyed by artifact-id
"""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class StoreError(Exception):
    """Raised on store-related failures."""


class Store:
    """Manages the Legacy64 content-addressed store on disk."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.objects_dir = self.root / "objects"
        self.artifacts_dir = self.root / "artifacts"
        self.reports_dir = self.root / "reports"
        self.quarantine_dir = self.root / "quarantine"
        self.quarantine_objects_dir = self.quarantine_dir / "objects"
        self.quarantine_records_dir = self.quarantine_dir / "records"

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Create all required directories and a .legacy64 marker file."""
        for d in (
            self.objects_dir,
            self.artifacts_dir,
            self.reports_dir,
            self.quarantine_objects_dir,
            self.quarantine_records_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)
        marker = self.root / ".legacy64"
        if not marker.exists():
            marker.write_text("# Legacy64 repository\n")

    @classmethod
    def find_root(cls, start: Optional[Path] = None) -> "Store":
        """Walk up from *start* (default: cwd) until a .legacy64 marker is found."""
        path = Path(start or Path.cwd()).resolve()
        for candidate in [path, *path.parents]:
            if (candidate / ".legacy64").exists():
                return cls(candidate)
        raise StoreError(
            "Not inside a Legacy64 repository. Run 'legacyai init' first."
        )

    # ------------------------------------------------------------------
    # Object storage
    # ------------------------------------------------------------------

    @staticmethod
    def hash_file(file_path: Path) -> str:
        """Return the SHA-256 hex digest of a file (no prefix)."""
        h = hashlib.sha256()
        with open(file_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _object_path(self, hex_hash: str, quarantine: bool = False) -> Path:
        base = self.quarantine_objects_dir if quarantine else self.objects_dir
        return base / hex_hash[:2] / hex_hash[2:]

    def store_object(self, file_path: Path, quarantine: bool = False) -> str:
        """Copy *file_path* into the object store; return 'sha256:<hex>'."""
        hex_hash = self.hash_file(file_path)
        dest = self._object_path(hex_hash, quarantine=quarantine)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)
        return f"sha256:{hex_hash}"

    def object_path(self, object_hash: str, quarantine: bool = False) -> Path:
        """Return the on-disk path for *object_hash* ('sha256:<hex>').

        Raises StoreError if the object is not found.
        """
        if not object_hash.startswith("sha256:"):
            raise StoreError(f"Unsupported hash scheme in '{object_hash}'")
        hex_hash = object_hash[len("sha256:"):]
        path = self._object_path(hex_hash, quarantine=quarantine)
        if not path.exists():
            raise StoreError(f"Object not found: {object_hash}")
        return path

    # ------------------------------------------------------------------
    # Artifact records
    # ------------------------------------------------------------------

    def _artifact_path(self, artifact_id: str) -> Path:
        return self.artifacts_dir / f"{artifact_id}.json"

    def write_artifact(self, record: Dict[str, Any]) -> None:
        """Persist an artifact record (must contain 'id')."""
        path = self._artifact_path(record["id"])
        path.write_text(json.dumps(record, indent=2))

    def read_artifact(self, artifact_id: str) -> Dict[str, Any]:
        path = self._artifact_path(artifact_id)
        if not path.exists():
            raise StoreError(f"Artifact not found: {artifact_id}")
        return json.loads(path.read_text())

    def list_artifacts(self) -> List[str]:
        """Return sorted list of all artifact IDs (excluding quarantined)."""
        if not self.artifacts_dir.exists():
            return []
        return sorted(p.stem for p in self.artifacts_dir.glob("*.json"))

    def delete_artifact(self, artifact_id: str) -> None:
        path = self._artifact_path(artifact_id)
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # Report storage
    # ------------------------------------------------------------------

    def report_path(self, artifact_id: str) -> Path:
        return self.reports_dir / f"{artifact_id}.json"

    def write_report(self, artifact_id: str, report: Dict[str, Any]) -> Path:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        path = self.report_path(artifact_id)
        path.write_text(json.dumps(report, indent=2))
        return path

    # ------------------------------------------------------------------
    # Quarantine records
    # ------------------------------------------------------------------

    def _quarantine_record_path(self, artifact_id: str) -> Path:
        return self.quarantine_records_dir / f"{artifact_id}.json"

    def write_quarantine_record(self, record: Dict[str, Any]) -> None:
        self.quarantine_records_dir.mkdir(parents=True, exist_ok=True)
        path = self._quarantine_record_path(record["id"])
        path.write_text(json.dumps(record, indent=2))

    def read_quarantine_record(self, artifact_id: str) -> Dict[str, Any]:
        path = self._quarantine_record_path(artifact_id)
        if not path.exists():
            raise StoreError(f"Quarantine record not found: {artifact_id}")
        return json.loads(path.read_text())

    def list_quarantined(self) -> List[str]:
        if not self.quarantine_records_dir.exists():
            return []
        return sorted(p.stem for p in self.quarantine_records_dir.glob("*.json"))

    def delete_quarantine_record(self, artifact_id: str) -> None:
        path = self._quarantine_record_path(artifact_id)
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
