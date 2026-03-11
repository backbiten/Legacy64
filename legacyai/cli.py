"""
legacyai CLI entry point.

Usage:
    legacyai app-pack list
    legacyai app-pack show <pack>
    legacyai app-pack generate --os <linux|windows|macos> [--distro <id>] --pack <id> --output <path>
"""

import argparse
import sys

from legacyai import __version__
from legacyai.app_pack import commands as ap_commands


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legacyai",
        description=(
            "Legacy64 — app-pack manifests and install-script generator for "
            "legacy 32/64-bit systems."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"legacyai {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # ── app-pack ──────────────────────────────────────────────────────────────
    ap_parser = subparsers.add_parser(
        "app-pack",
        help="Manage and generate app-pack install scripts.",
        description="Commands for listing, inspecting, and generating app-pack scripts.",
    )
    ap_sub = ap_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")
    ap_sub.required = True

    # app-pack list
    ap_sub.add_parser(
        "list",
        help="List all available app-packs.",
        description="List all available app-pack manifests found in the app-packs/ directory.",
    )

    # app-pack show <pack>
    show_parser = ap_sub.add_parser(
        "show",
        help="Show details of a specific app-pack.",
        description="Display the contents of an app-pack manifest.",
    )
    show_parser.add_argument(
        "pack",
        metavar="<pack-id>",
        help="The pack identifier (e.g. 'desktop').",
    )
    show_parser.add_argument(
        "--os",
        dest="os",
        choices=["linux", "windows", "macos"],
        default=None,
        help="Filter to a specific OS platform.",
    )

    # app-pack generate
    gen_parser = ap_sub.add_parser(
        "generate",
        help="Generate an install script from an app-pack.",
        description=(
            "Generate a platform-specific install script from an app-pack manifest. "
            "The script is written to disk but NOT executed. "
            "Running the generated script requires network access."
        ),
    )
    gen_parser.add_argument(
        "--os",
        required=True,
        choices=["linux", "windows", "macos"],
        metavar="<os>",
        help="Target operating system: linux, windows, or macos.",
    )
    gen_parser.add_argument(
        "--distro",
        default=None,
        metavar="<distro>",
        help=(
            "Linux distro family: debian_ubuntu, fedora_rhel, or arch_manjaro. "
            "Required when --os is linux."
        ),
    )
    gen_parser.add_argument(
        "--pack",
        required=True,
        metavar="<pack-id>",
        help="Pack identifier (e.g. 'desktop').",
    )
    gen_parser.add_argument(
        "--output",
        required=True,
        metavar="<path>",
        help="Output file path for the generated script.",
    )

    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "app-pack":
        if args.subcommand == "list":
            return ap_commands.cmd_list()
        elif args.subcommand == "show":
            return ap_commands.cmd_show(pack_id=args.pack, os_filter=args.os)
        elif args.subcommand == "generate":
            return ap_commands.cmd_generate(
                os_name=args.os,
                distro=args.distro,
                pack_id=args.pack,
                output_path=args.output,
            )

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
