"""legacyai — Legacy64 artifact management and offline safety/QC/QA scanning CLI.

Usage examples
--------------
    legacyai init
    legacyai add firmware.bin --id my-firmware
    legacyai add firmware.bin --id my-firmware --scan
    legacyai scan my-firmware
    legacyai list
    legacyai export my-firmware /tmp/out/firmware.bin
    legacyai quarantine list
    legacyai quarantine promote my-firmware
    legacyai quarantine reject my-firmware

All operations are strictly offline — no network access is performed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from legacyai import __version__
from legacyai.store import Store, StoreError
from legacyai.quarantine import Quarantine
from legacyai.scanner.engine import ScanEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_store(args: argparse.Namespace) -> Store:
    """Return a Store rooted at ``args.repo`` or discovered from cwd."""
    if getattr(args, "repo", None):
        return Store(Path(args.repo))
    return Store.find_root()


def _print_report_summary(report_dict: dict) -> None:
    """Print a human-friendly summary of a scan report to stdout."""
    dec = report_dict.get("decision", "?")
    icon = {"PASS": "✔", "WARN": "⚠", "FAIL": "✘"}.get(dec, "?")
    print(f"\n  Decision : {icon}  {dec}")
    print(f"  File     : {report_dict.get('file_path')}")
    print(f"  Type     : {report_dict.get('file_type')}")
    print(f"  Hash     : {report_dict.get('object_hash')}")
    print(f"  Size     : {report_dict.get('file_size')} bytes")

    qc = report_dict.get("qc", {})
    print(f"\n  QC [{qc.get('status', '?')}]")
    for check in qc.get("checks", []):
        status_icon = "✔" if check["status"] == "PASS" else "✘"
        print(f"    {status_icon} [{check['id']}] {check['name']}: {check['details']}")

    qa = report_dict.get("qa", {})
    print(f"\n  QA [{qa.get('status', '?')}]")
    findings = qa.get("findings", [])
    if findings:
        for f in findings:
            sev_icon = {"FAIL": "✘", "WARN": "⚠", "INFO": "ℹ"}.get(f["severity"], "?")
            print(
                f"    {sev_icon} [{f['rule_id']}] {f['name']} "
                f"({f['severity']}): {f['details']}"
            )
    else:
        print("    (no findings)")
    print()


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    repo_path = Path(getattr(args, "repo", None) or Path.cwd())
    store = Store(repo_path)
    store.init()
    print(f"Initialized Legacy64 repository at: {repo_path}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    store = _get_store(args)
    source = Path(args.file)
    if not source.exists():
        print(f"Error: file not found: {source}", file=sys.stderr)
        return 1

    artifact_id = getattr(args, "id", None) or source.name
    do_scan = not args.no_scan  # default is ON

    print(f"Adding artifact '{artifact_id}' from '{source}' …")

    # If scanning is enabled, scan BEFORE storing
    if do_scan:
        engine = ScanEngine()
        report = engine.scan(source, artifact_id=artifact_id)
        report_dict = report.to_dict()

        # Save report
        store.reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = store.write_report(artifact_id, report_dict)
        print(f"  Scan report: {report_path}")
        _print_report_summary(report_dict)

        if report.failed:
            # Quarantine
            q = Quarantine(store)
            q.quarantine(
                source,
                artifact_id,
                reason=f"Scan FAIL — decision: {report.decision}",
                report_path=str(report_path),
            )
            print(
                f"  [QUARANTINE] Artifact '{artifact_id}' quarantined due to scan FAIL.\n"
                f"  Use 'legacyai quarantine promote {artifact_id}' to override.",
                file=sys.stderr,
            )
            return 1

        scan_status = report.decision  # "PASS" or "WARN"
        object_hash = report.object_hash
    else:
        # No scan — store immediately
        object_hash = store.store_object(source)
        scan_status = "UNCHECKED"

    # Store the object (idempotent if already stored by engine)
    if not do_scan:
        pass  # already stored above
    else:
        # Object was not yet copied; do it now (idempotent)
        stored_hash = store.store_object(source)
        if stored_hash != object_hash:
            # Shouldn't happen unless file changed between scan and store
            print(
                f"Warning: hash changed between scan and store "
                f"({object_hash} → {stored_hash})",
                file=sys.stderr,
            )
            object_hash = stored_hash

    artifact = {
        "id": artifact_id,
        "source_path": str(source),
        "object_hash": object_hash,
        "added_at": store.now_iso(),
        "scan_status": scan_status,
        "report_path": str(store.report_path(artifact_id)) if do_scan else "",
    }
    store.write_artifact(artifact)
    print(f"  Artifact '{artifact_id}' added (scan_status={scan_status}).")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    store = _get_store(args)
    artifact_id = args.artifact_id

    try:
        artifact = store.read_artifact(artifact_id)
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    object_hash = artifact.get("object_hash", "")
    try:
        file_path = store.object_path(object_hash)
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    engine = ScanEngine()
    report = engine.scan(file_path, artifact_id=artifact_id, expected_hash=object_hash)
    report_dict = report.to_dict()

    report_path = store.write_report(artifact_id, report_dict)
    print(f"Scan report saved: {report_path}")
    _print_report_summary(report_dict)

    # Update artifact scan_status
    artifact["scan_status"] = report.decision
    artifact["report_path"] = str(report_path)
    store.write_artifact(artifact)

    return 0 if not report.failed else 1


def cmd_list(args: argparse.Namespace) -> int:
    store = _get_store(args)
    ids = store.list_artifacts()
    if not ids:
        print("No artifacts found.")
        return 0
    print(f"{'ID':<40}  {'SCAN STATUS':<15}  HASH")
    print("-" * 80)
    for aid in ids:
        try:
            a = store.read_artifact(aid)
            status = a.get("scan_status", "?")
            h = a.get("object_hash", "?")
        except StoreError:
            status = "ERROR"
            h = ""
        print(f"{aid:<40}  {status:<15}  {h}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    store = _get_store(args)
    artifact_id = args.artifact_id
    dest = Path(args.output)

    try:
        artifact = store.read_artifact(artifact_id)
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    object_hash = artifact.get("object_hash", "")
    try:
        file_path = store.object_path(object_hash)
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    no_rescan = getattr(args, "no_rescan", False)

    if not no_rescan:
        print(f"Re-scanning '{artifact_id}' before export …")
        engine = ScanEngine()
        report = engine.scan(file_path, artifact_id=artifact_id, expected_hash=object_hash)
        report_dict = report.to_dict()
        report_path = store.write_report(artifact_id, report_dict)
        _print_report_summary(report_dict)

        # Update scan_status
        artifact["scan_status"] = report.decision
        artifact["report_path"] = str(report_path)
        store.write_artifact(artifact)

        if report.failed:
            print(
                f"Export BLOCKED — artifact '{artifact_id}' failed re-scan (FAIL).\n"
                "Review the report and quarantine or reject the artifact.",
                file=sys.stderr,
            )
            return 1
        if report.warned:
            print(f"Warning: artifact '{artifact_id}' has WARN findings. Proceeding with export.")
    else:
        print("Skipping re-scan (--no-rescan specified).")

    dest.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(file_path, dest)
    print(f"Exported '{artifact_id}' → '{dest}'")
    return 0


def cmd_quarantine_list(args: argparse.Namespace) -> int:
    store = _get_store(args)
    q = Quarantine(store)
    ids = q.list_ids()
    if not ids:
        print("Quarantine is empty.")
        return 0
    print(f"{'ID':<40}  {'REASON':<40}  QUARANTINED AT")
    print("-" * 100)
    for qid in ids:
        try:
            rec = q.get_record(qid)
            reason = rec.get("reason", "?")[:40]
            when = rec.get("quarantined_at", "?")
        except StoreError:
            reason = "ERROR"
            when = ""
        print(f"{qid:<40}  {reason:<40}  {when}")
    return 0


def cmd_quarantine_promote(args: argparse.Namespace) -> int:
    store = _get_store(args)
    q = Quarantine(store)
    artifact_id = args.artifact_id
    try:
        artifact = q.promote(artifact_id)
        print(f"Artifact '{artifact_id}' promoted from quarantine.")
        print(f"  object_hash: {artifact['object_hash']}")
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_quarantine_reject(args: argparse.Namespace) -> int:
    store = _get_store(args)
    q = Quarantine(store)
    artifact_id = args.artifact_id
    try:
        q.reject(artifact_id)
        print(f"Artifact '{artifact_id}' rejected and removed from quarantine.")
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legacyai",
        description=(
            "Legacy64 — offline artifact management and safety/QC/QA scanning.\n"
            "All operations are strictly offline; no network access is performed."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"legacyai {__version__}"
    )
    parser.add_argument(
        "--repo",
        metavar="DIR",
        default=None,
        help="Path to Legacy64 repository root (default: auto-discover from cwd).",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # init
    p_init = sub.add_parser("init", help="Initialise a new Legacy64 repository.")
    p_init.set_defaults(func=cmd_init)

    # add
    p_add = sub.add_parser(
        "add",
        help="Add a file to the artifact store.",
        description=(
            "Hashes the file and stores it in the content-addressed object store.\n"
            "By default a QC/QA scan is performed; if the scan FAIL the artifact\n"
            "is quarantined instead of being promoted to the normal store."
        ),
    )
    p_add.add_argument("file", help="Path to the file to add.")
    p_add.add_argument("--id", metavar="ARTIFACT_ID", help="Artifact ID (default: filename).")
    p_add.add_argument(
        "--no-scan",
        action="store_true",
        default=False,
        help="Skip QC/QA scan (not recommended; artifact stored as UNCHECKED).",
    )
    p_add.set_defaults(func=cmd_add)

    # scan
    p_scan = sub.add_parser(
        "scan",
        help="Scan an existing artifact and save a report.",
        description="Runs QC and QA checks on the stored object for ARTIFACT_ID.",
    )
    p_scan.add_argument("artifact_id", metavar="ARTIFACT_ID")
    p_scan.set_defaults(func=cmd_scan)

    # list
    p_list = sub.add_parser("list", help="List all artifacts.")
    p_list.set_defaults(func=cmd_list)

    # export
    p_export = sub.add_parser(
        "export",
        help="Export an artifact to a file path (re-scans by default).",
        description=(
            "Copies the stored object to OUTPUT.  By default the artifact is\n"
            "re-scanned; if the re-scan returns FAIL the export is blocked."
        ),
    )
    p_export.add_argument("artifact_id", metavar="ARTIFACT_ID")
    p_export.add_argument("output", metavar="OUTPUT", help="Destination file path.")
    p_export.add_argument(
        "--no-rescan",
        action="store_true",
        default=False,
        help="Skip the pre-export re-scan (not recommended).",
    )
    p_export.set_defaults(func=cmd_export)

    # quarantine
    p_q = sub.add_parser("quarantine", help="Manage the quarantine.")
    q_sub = p_q.add_subparsers(dest="quarantine_command", metavar="SUBCOMMAND")

    q_list = q_sub.add_parser("list", help="List quarantined artifacts.")
    q_list.set_defaults(func=cmd_quarantine_list)

    q_promote = q_sub.add_parser(
        "promote",
        help="Promote a quarantined artifact to the normal store.",
    )
    q_promote.add_argument("artifact_id", metavar="ARTIFACT_ID")
    q_promote.set_defaults(func=cmd_quarantine_promote)

    q_reject = q_sub.add_parser(
        "reject",
        help="Permanently delete a quarantined artifact.",
    )
    q_reject.add_argument("artifact_id", metavar="ARTIFACT_ID")
    q_reject.set_defaults(func=cmd_quarantine_reject)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "func", None):
        # Handle 'legacyai quarantine' with no subcommand
        if getattr(args, "command", None) == "quarantine":
            parser.parse_args(["quarantine", "--help"])
        else:
            parser.print_help()
        return 0

    try:
        return args.func(args)
    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
