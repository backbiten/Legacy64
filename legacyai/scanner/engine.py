"""Scan engine — orchestrates QC and QA checks into a structured report.

Scan reports are written to ``reports/<artifact-id>.json`` and follow the
schema defined below.  All timestamps are UTC ISO-8601.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from legacyai import __version__
from legacyai.scanner.qc import QCResult, run_qc_checks, qc_status, detect_file_type
from legacyai.scanner.qa import Finding, run_qa_checks, qa_status

SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Report data model
# ---------------------------------------------------------------------------


@dataclass
class ScanReport:
    """Complete scan report for one artifact / file."""

    schema_version: str
    timestamp: str
    tool_version: str
    artifact_id: Optional[str]
    object_hash: str            # "sha256:<hex>" or "sha256:unknown"
    file_path: str
    file_size: int
    file_type: str
    qc_status: str              # "PASS" | "FAIL"
    qc_checks: List[Dict[str, str]]
    qa_status: str              # "PASS" | "WARN" | "FAIL"
    qa_findings: List[Dict[str, str]]
    decision: str               # "PASS" | "WARN" | "FAIL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "timestamp": self.timestamp,
            "tool_version": self.tool_version,
            "artifact_id": self.artifact_id,
            "object_hash": self.object_hash,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "qc": {
                "status": self.qc_status,
                "checks": self.qc_checks,
            },
            "qa": {
                "status": self.qa_status,
                "findings": self.qa_findings,
            },
            "decision": self.decision,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @property
    def passed(self) -> bool:
        return self.decision == "PASS"

    @property
    def warned(self) -> bool:
        return self.decision == "WARN"

    @property
    def failed(self) -> bool:
        return self.decision == "FAIL"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _decision(qc_st: str, qa_st: str) -> str:
    """Combine QC and QA statuses into a final decision."""
    if qc_st == "FAIL" or qa_st == "FAIL":
        return "FAIL"
    if qa_st == "WARN":
        return "WARN"
    return "PASS"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ScanEngine:
    """Runs QC + QA checks and produces a :class:`ScanReport`."""

    def scan(
        self,
        file_path: Path,
        artifact_id: Optional[str] = None,
        expected_hash: Optional[str] = None,
    ) -> ScanReport:
        """Scan *file_path* and return a :class:`ScanReport`.

        Parameters
        ----------
        file_path:
            Path to the file to scan.
        artifact_id:
            Optional artifact ID to embed in the report.
        expected_hash:
            If provided (``'sha256:<hex>'``), QC-002 verifies the file hash.
        """
        file_path = Path(file_path)

        try:
            file_size = file_path.stat().st_size
        except OSError:
            file_size = -1

        file_type = detect_file_type(file_path)

        # Build object hash (best-effort; don't fail if file is unreadable)
        if expected_hash:
            object_hash = expected_hash
        else:
            try:
                from legacyai.store import Store  # local import to avoid cycle
                hex_hash = Store.hash_file(file_path)
                object_hash = f"sha256:{hex_hash}"
            except Exception:
                object_hash = "sha256:unknown"

        qc_results: List[QCResult] = run_qc_checks(file_path, expected_hash)
        qa_findings: List[Finding] = run_qa_checks(file_path)

        q_status = qc_status(qc_results)
        a_status = qa_status(qa_findings)
        dec = _decision(q_status, a_status)

        return ScanReport(
            schema_version=SCHEMA_VERSION,
            timestamp=_now_iso(),
            tool_version=__version__,
            artifact_id=artifact_id,
            object_hash=object_hash,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_type,
            qc_status=q_status,
            qc_checks=[
                {
                    "id": r.check_id,
                    "name": r.name,
                    "status": r.status,
                    "details": r.details,
                }
                for r in qc_results
            ],
            qa_status=a_status,
            qa_findings=[
                {
                    "rule_id": f.rule_id,
                    "name": f.name,
                    "severity": f.severity,
                    "details": f.details,
                }
                for f in qa_findings
            ],
            decision=dec,
        )
