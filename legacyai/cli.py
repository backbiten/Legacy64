"""legacyai – command-line interface.

Usage
-----
    legacyai patch add <patchfile> [--tag TAG] [--name NAME]
    legacyai patch list

    legacyai patchset create <id> [--description DESC]
                                  [--baseline ARTIFACT_ID]
                                  [--source-hash HASH]
                                  [--output ARTIFACT_ID]
                                  [--tag TAG]
    legacyai patchset add <id> --patch <patch-id> --order <n> [--note NOTE]
    legacyai patchset list
    legacyai patchset show <id>

    legacyai bind source-patch --source <artifact-id>
                               [--tag TAG]
                               [--patchset PATCHSET_ID]
                               [--patch PATCH_ID]
                               [--output ARTIFACT_ID]

    legacyai verify [--root DIR]
"""

import argparse
import sys
from pathlib import Path

import yaml

from .patch import add_patch, list_patches
from .patchset import (
    add_patch_to_patchset,
    create_patchset,
    list_patchsets,
    load_patchset,
)
from .bind import bind_source_patch, list_bindings
from .verify import verify


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _root(args) -> Path:
    return Path(getattr(args, "root", None) or ".").resolve()


def _print_yaml(obj: dict) -> None:
    print(yaml.dump(obj, default_flow_style=False, allow_unicode=True), end="")


# ---------------------------------------------------------------------------
# patch sub-commands
# ---------------------------------------------------------------------------

def cmd_patch_add(args) -> int:
    root = _root(args)
    patchfile = Path(args.patchfile)
    if not patchfile.exists():
        print(f"ERROR: patch file not found: {patchfile}", file=sys.stderr)
        return 1
    tags = args.tag or []
    record = add_patch(root, patchfile, tags=tags, name=args.name)
    print(f"Imported patch: {record['id']}")
    _print_yaml(record)
    return 0


def cmd_patch_list(args) -> int:
    root = _root(args)
    records = list_patches(root)
    if not records:
        print("No patches found.")
        return 0
    for r in records:
        tags = ", ".join(r.get("tags") or [])
        tag_str = f"  [{tags}]" if tags else ""
        print(f"{r['id'][:12]}  {r['name']}{tag_str}")
    return 0


# ---------------------------------------------------------------------------
# patchset sub-commands
# ---------------------------------------------------------------------------

def cmd_patchset_create(args) -> int:
    root = _root(args)
    tags = args.tag or []
    try:
        record = create_patchset(
            root,
            args.id,
            description=args.description,
            baseline_artifact_id=args.baseline,
            expected_source_hash=args.source_hash,
            output_artifact_id=args.output,
            tags=tags,
        )
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Created patchset: {record['id']}")
    _print_yaml(record)
    return 0


def cmd_patchset_add(args) -> int:
    root = _root(args)
    try:
        record = add_patch_to_patchset(
            root,
            args.id,
            patch_id=args.patch,
            order=args.order,
            note=args.note,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Updated patchset: {record['id']}")
    _print_yaml(record)
    return 0


def cmd_patchset_list(args) -> int:
    root = _root(args)
    records = list_patchsets(root)
    if not records:
        print("No patchsets found.")
        return 0
    for r in records:
        tags = ", ".join(r.get("tags") or [])
        tag_str = f"  [{tags}]" if tags else ""
        patch_count = len(r.get("patches") or [])
        patch_word = "patch" if patch_count == 1 else "patches"
        print(
            f"{r['id']}  ({patch_count} {patch_word}){tag_str}"
        )
    return 0


def cmd_patchset_show(args) -> int:
    root = _root(args)
    try:
        record = load_patchset(root, args.id)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    _print_yaml(record)
    return 0


# ---------------------------------------------------------------------------
# bind sub-commands
# ---------------------------------------------------------------------------

def cmd_bind_source_patch(args) -> int:
    root = _root(args)
    tags = args.tag or []
    patch_ids = args.patch or []
    record = bind_source_patch(
        root,
        source_artifact_id=args.source,
        tags=tags,
        patchset_id=args.patchset,
        patch_ids=patch_ids,
        output_artifact_id=args.output,
    )
    print(f"Created binding: {record['id']}")
    _print_yaml(record)
    return 0


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

def cmd_verify(args) -> int:
    root = _root(args)
    errors, checked, ok = verify(root)
    print(f"Checked {checked} item(s): {ok} OK, {len(errors)} error(s).")
    for err in errors:
        print(f"  {err}")
    return 0 if not errors else 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legacyai",
        description="Offline-first preservation tooling for Legacy64/Legacy32 archives.",
    )
    parser.add_argument(
        "--root",
        metavar="DIR",
        default=None,
        help="Archive root directory (default: current directory)",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ------------------------------------------------------------------
    # patch
    # ------------------------------------------------------------------
    patch_p = sub.add_parser("patch", help="Manage patch files")
    patch_sub = patch_p.add_subparsers(dest="patch_command", metavar="SUBCOMMAND")
    patch_sub.required = True

    pa = patch_sub.add_parser("add", help="Import a patch file into the archive")
    pa.add_argument("patchfile", help="Path to the .patch / .diff file")
    pa.add_argument(
        "--tag",
        action="append",
        metavar="TAG",
        default=None,
        help="Tag to apply (may be specified multiple times; e.g. --tag y2038)",
    )
    pa.add_argument("--name", metavar="NAME", default=None, help="Human-readable name")

    pl = patch_sub.add_parser("list", help="List imported patches")

    # ------------------------------------------------------------------
    # patchset
    # ------------------------------------------------------------------
    patchset_p = sub.add_parser("patchset", help="Manage patch series (patchsets)")
    patchset_sub = patchset_p.add_subparsers(
        dest="patchset_command", metavar="SUBCOMMAND"
    )
    patchset_sub.required = True

    pc = patchset_sub.add_parser(
        "create", help="Create a new patchset record"
    )
    pc.add_argument(
        "id",
        metavar="ID",
        help="Patchset identifier, e.g. y2038:fix-time_t-overflow",
    )
    pc.add_argument("--description", metavar="DESC", default=None)
    pc.add_argument(
        "--baseline",
        metavar="ARTIFACT_ID",
        default=None,
        help="ID of the baseline artifact this patchset targets",
    )
    pc.add_argument(
        "--source-hash",
        metavar="HASH",
        default=None,
        help="Expected SHA-256 of the baseline source archive",
    )
    pc.add_argument(
        "--output",
        metavar="ARTIFACT_ID",
        default=None,
        help="ID of the derived artifact produced after applying the patchset",
    )
    pc.add_argument(
        "--tag",
        action="append",
        metavar="TAG",
        default=None,
        help="Additional tag (may be specified multiple times)",
    )

    padd = patchset_sub.add_parser(
        "add", help="Add a patch reference to a patchset"
    )
    padd.add_argument("id", metavar="ID", help="Patchset identifier")
    padd.add_argument(
        "--patch", required=True, metavar="PATCH_ID", help="Patch ID (SHA-256)"
    )
    padd.add_argument(
        "--order",
        required=True,
        type=int,
        metavar="N",
        help="Sequence position (1-based) in the series",
    )
    padd.add_argument("--note", metavar="NOTE", default=None)

    plist = patchset_sub.add_parser("list", help="List all patchsets")
    pshow = patchset_sub.add_parser("show", help="Show details of a patchset")
    pshow.add_argument("id", metavar="ID", help="Patchset identifier")

    # ------------------------------------------------------------------
    # bind
    # ------------------------------------------------------------------
    bind_p = sub.add_parser("bind", help="Create artifact bindings")
    bind_sub = bind_p.add_subparsers(dest="bind_command", metavar="SUBCOMMAND")
    bind_sub.required = True

    bsp = bind_sub.add_parser(
        "source-patch",
        help="Bind a source artifact to one or more patches / a patchset",
    )
    bsp.add_argument(
        "--source",
        required=True,
        metavar="ARTIFACT_ID",
        help="Source artifact ID (baseline)",
    )
    bsp.add_argument(
        "--tag",
        action="append",
        metavar="TAG",
        default=None,
        help="Tag (may be specified multiple times)",
    )
    bsp.add_argument(
        "--patchset",
        metavar="PATCHSET_ID",
        default=None,
        help="Patchset ID, e.g. y2038:fix-time_t-overflow",
    )
    bsp.add_argument(
        "--patch",
        action="append",
        metavar="PATCH_ID",
        default=None,
        help="Patch ID to reference (may be specified multiple times)",
    )
    bsp.add_argument(
        "--output",
        metavar="ARTIFACT_ID",
        default=None,
        help="ID of the derived artifact produced after patching",
    )

    # ------------------------------------------------------------------
    # verify
    # ------------------------------------------------------------------
    sub.add_parser(
        "verify",
        help="Verify archive integrity (hashes, references, patchsets, bindings)",
    )

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "patch":
        if args.patch_command == "add":
            return cmd_patch_add(args)
        if args.patch_command == "list":
            return cmd_patch_list(args)

    elif args.command == "patchset":
        if args.patchset_command == "create":
            return cmd_patchset_create(args)
        if args.patchset_command == "add":
            return cmd_patchset_add(args)
        if args.patchset_command == "list":
            return cmd_patchset_list(args)
        if args.patchset_command == "show":
            return cmd_patchset_show(args)

    elif args.command == "bind":
        if args.bind_command == "source-patch":
            return cmd_bind_source_patch(args)

    elif args.command == "verify":
        return cmd_verify(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
