"""legacyai – Legacy64 preservation CLI entry point."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from legacyai import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legacyai",
        description=(
            "Legacy64 preservation CLI.\n"
            "Offline-first, content-addressed artifact store for AMD64 software, "
            "firmware, and documentation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"legacyai {__version__}")
    parser.add_argument(
        "--repo",
        metavar="DIR",
        default=None,
        help="Repository root (default: auto-detect from cwd)",
    )

    sub = parser.add_subparsers(dest="command", title="commands")

    # ── init ──────────────────────────────────────────────────────────────────
    sub.add_parser(
        "init",
        help="Initialise repository directories and default config",
    )

    # ── add ───────────────────────────────────────────────────────────────────
    add_p = sub.add_parser(
        "add",
        help="Import an artifact into the content-addressed store",
    )
    add_p.add_argument("path", metavar="FILE", help="Path to the artifact file")
    add_p.add_argument(
        "--lane",
        required=True,
        choices=["legacy64", "legacy32"],
        help="Preservation lane",
    )
    add_p.add_argument(
        "--type",
        required=True,
        choices=["bin", "src", "firmware", "doc"],
        help="Artifact type",
    )
    add_p.add_argument("--name", default=None, help="Human-readable artifact name")
    add_p.add_argument("--version", dest="version", default=None, help="Version string")

    # ── verify ────────────────────────────────────────────────────────────────
    sub.add_parser(
        "verify",
        help="Verify artifact records and stored objects",
    )

    # ── bind ──────────────────────────────────────────────────────────────────
    bind_p = sub.add_parser(
        "bind",
        help="Create a relationship binding between artifacts",
    )
    bind_sub = bind_p.add_subparsers(dest="bind_type", title="binding types")

    sp_p = bind_sub.add_parser(
        "source-patch",
        help=(
            "Bind a legacy32 and legacy64 artifact via a shared upstream source "
            "and optional patch file (no conversion)"
        ),
    )
    sp_p.add_argument(
        "--source",
        required=True,
        metavar="REF",
        help="Upstream source reference (git tag/commit, tarball URL, or object hash)",
    )
    sp_p.add_argument(
        "--source-repo",
        default=None,
        metavar="REPO",
        dest="source_repo",
        help="Upstream repository (owner/repo or full URL, optional)",
    )
    sp_p.add_argument(
        "--legacy32",
        required=True,
        metavar="ARTIFACT_ID",
        help="Artifact ID of the legacy32 record",
    )
    sp_p.add_argument(
        "--legacy64",
        required=True,
        metavar="ARTIFACT_ID",
        help="Artifact ID of the legacy64 record",
    )
    sp_p.add_argument(
        "--patch",
        default=None,
        metavar="PATCHFILE",
        help="Path to a patch file to associate with this binding",
    )

    return parser


def _resolve_repo_root(args) -> Path:
    from legacyai.repo import find_repo_root

    if args.repo:
        root = Path(args.repo).resolve()
        if not root.exists():
            print(f"error: --repo path does not exist: {root}", file=sys.stderr)
            sys.exit(1)
        return root
    try:
        return find_repo_root()
    except FileNotFoundError as exc:
        # For `init` we allow running without a pre-existing config.
        if getattr(args, "command", None) == "init":
            return Path(os.getcwd()).resolve()
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    repo_root = _resolve_repo_root(args)

    if args.command == "init":
        from legacyai.commands.init import run
        sys.exit(run(args, repo_root))

    elif args.command == "add":
        from legacyai.commands.add import run
        sys.exit(run(args, repo_root))

    elif args.command == "verify":
        from legacyai.commands.verify import run
        sys.exit(run(args, repo_root))

    elif args.command == "bind":
        if args.bind_type is None:
            # Print bind subcommand help
            parser.parse_args(["bind", "--help"])
        elif args.bind_type == "source-patch":
            from legacyai.commands.bind import run
            sys.exit(run(args, repo_root))
        else:
            print(f"error: unknown bind type: {args.bind_type}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"error: unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
