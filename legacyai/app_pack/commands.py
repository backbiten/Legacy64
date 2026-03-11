"""
legacyai.app_pack.commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Implements the ``legacyai app-pack`` subcommands:

- ``list``          — list all available packs
- ``show <pack>``   — display manifest details
- ``generate ...``  — generate an install script
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from legacyai.app_pack import loader, generator


# ---------------------------------------------------------------------------
# ANSI colour helpers (gracefully degrade on non-TTY)
# ---------------------------------------------------------------------------

def _supports_colour() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class _C:
    """Minimal ANSI colour codes."""

    _USE = _supports_colour()

    RESET  = "\033[0m"  if _USE else ""
    BOLD   = "\033[1m"  if _USE else ""
    CYAN   = "\033[96m" if _USE else ""
    GREEN  = "\033[92m" if _USE else ""
    YELLOW = "\033[93m" if _USE else ""
    DIM    = "\033[2m"  if _USE else ""


def _print_section(title: str) -> None:
    print(f"\n{_C.BOLD}{_C.CYAN}{title}{_C.RESET}")
    print(f"{_C.DIM}{'─' * 60}{_C.RESET}")


def _print_kv(key: str, value: str, indent: int = 2) -> None:
    pad = " " * indent
    print(f"{pad}{_C.BOLD}{key}:{_C.RESET} {value}")


def _print_list_item(bullet: str, text: str) -> None:
    print(f"  {_C.CYAN}{bullet}{_C.RESET} {text}")


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def cmd_list() -> int:
    """List all available app-pack manifests."""
    packs = loader.list_packs()

    if not packs:
        print(
            f"{_C.YELLOW}No app-pack manifests found under app-packs/.{_C.RESET}\n"
            "  Make sure you are running legacyai from the repository root,\n"
            "  or that the app-packs/ directory exists."
        )
        return 1

    _print_section("Available App-Packs")
    print(
        f"  {'ID':<14} {'PLATFORM':<10} DESCRIPTION"
    )
    print(f"  {'-'*14} {'-'*10} {'-'*44}")
    for pack in packs:
        desc = pack["description"]
        if len(desc) > 50:
            desc = desc[:47] + "..."
        print(
            f"  {_C.GREEN}{pack['id']:<14}{_C.RESET}"
            f" {pack['platform']:<10}"
            f" {desc}"
        )

    print(f"\n  {_C.DIM}Tip: run 'legacyai app-pack show <pack-id>' for details.{_C.RESET}")
    print(f"  {_C.DIM}     run 'legacyai app-pack generate --help' to create scripts.{_C.RESET}\n")
    return 0


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def cmd_show(pack_id: str, os_filter: Optional[str] = None) -> int:
    """Display the details of one app-pack (across platforms or filtered)."""
    packs = loader.list_packs()

    # Find all manifests matching pack_id (potentially multiple platforms)
    matches = [p for p in packs if p["id"] == pack_id]
    if os_filter:
        matches = [p for p in matches if p["platform"] == os_filter]

    if not matches:
        qualifier = f" on '{os_filter}'" if os_filter else ""
        print(
            f"{_C.YELLOW}No app-pack named '{pack_id}'{qualifier} found.{_C.RESET}\n"
            "  Run 'legacyai app-pack list' to see available packs."
        )
        return 1

    for meta in matches:
        manifest = loader.load_manifest(meta["path"])
        _render_manifest(manifest)

    return 0


def _render_manifest(manifest: Dict[str, Any]) -> None:
    pack_id    = manifest.get("id", "?")
    platform   = manifest.get("platform", "?")
    desc       = manifest.get("description", "").strip()
    licensing  = manifest.get("licensing_notes", "").strip()
    apps: List[Dict[str, Any]] = manifest.get("apps", [])

    _print_section(f"App-Pack: {pack_id}  [{platform}]")
    if desc:
        _print_kv("Description", desc)
    if licensing:
        _print_kv("Licensing", licensing)

    print(f"\n  {_C.BOLD}Applications ({len(apps)}):{_C.RESET}")
    for app in apps:
        name   = app.get("name", app.get("id", "?"))
        adesc  = app.get("description", "").strip()
        _print_list_item("•", f"{_C.BOLD}{name}{_C.RESET}")
        if adesc:
            wrapped = adesc.replace("\n", " ")
            print(f"    {_C.DIM}{wrapped[:120]}{_C.RESET}")

    print()


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def cmd_generate(
    os_name: str,
    distro: Optional[str],
    pack_id: str,
    output_path: str,
) -> int:
    """Generate an install script for the given pack and write it to disk."""
    # Locate manifest
    try:
        manifest_path = loader.find_manifest(pack_id, os_name)
    except FileNotFoundError as exc:
        print(f"{_C.YELLOW}Error: {exc}{_C.RESET}")
        return 1

    # Load + validate
    try:
        manifest = loader.load_manifest(manifest_path)
    except Exception as exc:
        print(f"{_C.YELLOW}Error loading manifest: {exc}{_C.RESET}")
        return 1

    # Validate distro for Linux
    if os_name == "linux" and not distro:
        print(
            f"{_C.YELLOW}Error: --distro is required for --os linux.{_C.RESET}\n"
            "  Valid choices: debian_ubuntu, fedora_rhel, arch_manjaro"
        )
        return 1

    # Generate
    try:
        script = generator.generate_script(manifest, os_name, distro)
    except ValueError as exc:
        print(f"{_C.YELLOW}Error generating script: {exc}{_C.RESET}")
        return 1

    # Write
    try:
        out = generator.write_script(script, output_path)
    except OSError as exc:
        print(f"{_C.YELLOW}Error writing file: {exc}{_C.RESET}")
        return 1

    # Determine script type for UX messaging
    ext = out.suffix.lower()
    script_type = "PowerShell" if ext == ".ps1" else "Bash/Shell"
    run_hint = (
        f"pwsh ./{out.name}  (or right-click > 'Run with PowerShell')"
        if ext == ".ps1"
        else f"bash ./{out.name}"
    )

    print(f"\n{_C.GREEN}{_C.BOLD}✅  Script generated successfully!{_C.RESET}")
    _print_kv("File", str(out))
    _print_kv("Type", script_type)
    _print_kv("Pack", pack_id)
    _print_kv("Platform", os_name + (f" / {distro}" if distro else ""))
    print(
        f"\n  {_C.BOLD}Next steps:{_C.RESET}\n"
        f"  1. {_C.DIM}Review the generated script before running it:{_C.RESET}\n"
        f"     cat {out}\n"
        f"  2. {_C.DIM}Run the script to install all apps (requires network):{_C.RESET}\n"
        f"     {run_hint}\n"
    )
    return 0
