"""Quarantine management helpers.

Quarantine keeps suspect artifacts isolated from the normal object store.
Objects land in ``quarantine/objects/`` and metadata records in
``quarantine/records/``.  No automatic action is taken; the user must
explicitly promote or reject each entry.
"""

from pathlib import Path
from typing import Any, Dict, List

from legacyai.store import Store, StoreError


class Quarantine:
    """Manages the quarantine lifecycle for a :class:`~legacyai.store.Store`."""

    def __init__(self, store: Store) -> None:
        self.store = store

    # ------------------------------------------------------------------
    # Quarantine an artifact
    # ------------------------------------------------------------------

    def quarantine(
        self,
        source_path: Path,
        artifact_id: str,
        reason: str,
        report_path: str = "",
    ) -> Dict[str, Any]:
        """Copy *source_path* into the quarantine object store and write a record.

        Returns the quarantine record dict.
        """
        object_hash = self.store.store_object(source_path, quarantine=True)
        record: Dict[str, Any] = {
            "id": artifact_id,
            "source_path": str(source_path),
            "object_hash": object_hash,
            "quarantined_at": self.store.now_iso(),
            "reason": reason,
            "report_path": report_path,
        }
        self.store.write_quarantine_record(record)
        return record

    # ------------------------------------------------------------------
    # List quarantined artifacts
    # ------------------------------------------------------------------

    def list_ids(self) -> List[str]:
        return self.store.list_quarantined()

    def get_record(self, artifact_id: str) -> Dict[str, Any]:
        return self.store.read_quarantine_record(artifact_id)

    # ------------------------------------------------------------------
    # Promote (move into normal store)
    # ------------------------------------------------------------------

    def promote(self, artifact_id: str) -> Dict[str, Any]:
        """Move a quarantined artifact into the normal object store.

        Returns the new artifact record.
        """
        q_record = self.store.read_quarantine_record(artifact_id)
        q_hash = q_record["object_hash"]

        # Locate quarantined object
        q_obj_path = self.store.object_path(q_hash, quarantine=True)

        # Store in the normal objects tree
        normal_hash = self.store.store_object(q_obj_path, quarantine=False)

        # Write a normal artifact record
        artifact: Dict[str, Any] = {
            "id": artifact_id,
            "source_path": q_record.get("source_path", ""),
            "object_hash": normal_hash,
            "added_at": self.store.now_iso(),
            "scan_status": "PROMOTED_FROM_QUARANTINE",
            "promoted_at": self.store.now_iso(),
            "report_path": q_record.get("report_path", ""),
        }
        self.store.write_artifact(artifact)

        # Remove quarantine record (keep the blob for audit)
        self.store.delete_quarantine_record(artifact_id)

        return artifact

    # ------------------------------------------------------------------
    # Reject (permanently remove from quarantine)
    # ------------------------------------------------------------------

    def reject(self, artifact_id: str) -> None:
        """Permanently delete a quarantined artifact and its record."""
        q_record = self.store.read_quarantine_record(artifact_id)
        q_hash = q_record["object_hash"]

        # Remove the quarantined blob
        try:
            q_obj_path = self.store.object_path(q_hash, quarantine=True)
            q_obj_path.unlink(missing_ok=True)
            # Remove the (now empty) shard directory if possible
            try:
                q_obj_path.parent.rmdir()
            except OSError:
                pass
        except StoreError:
            pass  # Blob already missing — still remove the record

        self.store.delete_quarantine_record(artifact_id)
