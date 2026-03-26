# App-Packs — Legacy64

App-packs are curated manifests that describe a set of popular desktop
applications and generate ready-to-run install scripts for Linux, Windows,
and macOS.  No proprietary binaries are ever bundled in this repository;
scripts fetch from official sources at run-time.

---

## Table of Contents

1. [Purpose](#purpose)
2. [Legal Boundaries](#legal-boundaries)
3. [Offline vs Online Behaviour](#offline-vs-online-behaviour)
4. [Available Packs](#available-packs)
5. [CLI Reference](#cli-reference)
6. [Generated Script Examples](#generated-script-examples)
7. [How to Add New Apps or Packs](#how-to-add-new-apps-or-packs)
8. [Netflix Handling](#netflix-handling)
9. [Manifest Schema](#manifest-schema)

---

## Purpose

Legacy64 targets users of legacy 32- and 64-bit hardware and distributions.
Getting a usable desktop after a fresh install often requires hunting down
repositories, signing keys, and install commands across multiple sources.

App-packs solve that by:

- **Describing** which apps to install and how (per OS / distro family)
- **Generating** a single, reviewable install script — no "magic" execution
- **Documenting** where each app comes from and its licence

---

## Legal Boundaries

| Allowed | Not Allowed |
|---------|-------------|
| Manifests that reference official repos / CDNs | Bundling proprietary installers in this repo |
| Post-install notes with usage guidance | DRM circumvention instructions |
| Desktop shortcuts pointing to web services | Redistributing copyrighted software |
| Brew/winget/apt commands that fetch at run-time | Embedding licence-encumbered binaries |

Every manifest includes a `licensing_notes` field that explains its legal
status.  If you add an app, you **must** fill in that field honestly.

---

## Offline vs Online Behaviour

### The `legacyai` tool — offline

`legacyai` itself makes **no network calls**.  Running

```
legacyai app-pack generate --os linux --distro debian_ubuntu --pack desktop --output install.sh
```

reads only local YAML files and writes a local script.  No internet
connection is needed, no telemetry is sent, no packages are downloaded.

### The generated script — requires network at run-time

The *script* that `legacyai` produces will download software when you
run it (e.g., `apt-get install`, `winget install`, `brew install --cask`).
Those calls go to the official upstream servers for each application.

If you need a fully offline install (e.g., air-gapped systems), you must:

1. Pre-cache the packages on a local mirror.
2. Edit the generated script to point to that mirror before executing.

---

## Available Packs

| Pack ID  | Platforms          | Contents |
|----------|--------------------|----------|
| `desktop`| linux / windows / macos | Firefox, Signal, Tor Browser, Spotify, Netflix-ready setup |

List packs with:

```
legacyai app-pack list
```

---

## CLI Reference

### `legacyai app-pack list`

List all manifests found in `app-packs/`.

```
legacyai app-pack list
```

### `legacyai app-pack show <pack-id>`

Display the applications in a pack.

```
legacyai app-pack show desktop
legacyai app-pack show desktop --os linux
```

### `legacyai app-pack generate`

Generate a platform-specific install script.  The script is **written to
disk only** — it is never executed automatically.

```
# Linux — Debian / Ubuntu / Linux Mint / Zorin OS
legacyai app-pack generate \
  --os linux --distro debian_ubuntu \
  --pack desktop --output ~/install-desktop.sh

# Linux — Fedora / RHEL / Rocky / Alma
legacyai app-pack generate \
  --os linux --distro fedora_rhel \
  --pack desktop --output ~/install-desktop.sh

# Linux — Arch / Manjaro
legacyai app-pack generate \
  --os linux --distro arch_manjaro \
  --pack desktop --output ~/install-desktop.sh

# Windows (generates PowerShell .ps1)
legacyai app-pack generate \
  --os windows --pack desktop --output install-desktop.ps1

# macOS (generates bash/zsh .sh)
legacyai app-pack generate \
  --os macos --pack desktop --output install-desktop.sh
```

**Options**

| Option | Required | Description |
|--------|----------|-------------|
| `--os` | ✅ | `linux`, `windows`, or `macos` |
| `--distro` | Linux only | `debian_ubuntu`, `fedora_rhel`, `arch_manjaro` |
| `--pack` | ✅ | Pack identifier (e.g. `desktop`) |
| `--output` | ✅ | Output file path |

---

## Generated Script Examples

### Linux (Debian/Ubuntu)

```bash
#!/usr/bin/env bash
########################################################################
# Legacy64 — App-Pack Install Script
# Pack     : desktop
# Platform : Linux / Debian / Ubuntu / Linux Mint / Zorin OS
########################################################################

set -euo pipefail

# ── Firefox ──────────────────────────────────────────────────────────
echo "━━━ Installing: Firefox ━━━"
apt-get update -y
apt-get install -y firefox

# ── Signal Desktop ────────────────────────────────────────────────────
echo "━━━ Installing: Signal Desktop ━━━"
apt-get install -y wget gnupg
wget -qO- https://updates.signal.org/desktop/apt/keys.asc | gpg --dearmor ...
...
```

### Windows (PowerShell)

```powershell
$ErrorActionPreference = 'Stop'

# ── Firefox ──────────────────────────────────────────────────────────
Write-Host "=== Installing: Firefox ===" -ForegroundColor Cyan
winget install --id Mozilla.Firefox -e --accept-source-agreements ...
```

### macOS (Homebrew)

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── Homebrew ─────────────────────────────────────────────────────────
command -v brew >/dev/null 2>&1 || /bin/bash -c "$(curl ...)"

# ── Firefox ──────────────────────────────────────────────────────────
brew install --cask firefox
```

---

## Netflix Handling

Netflix **does not** ship a standalone Linux desktop application.
Legacy64 handles this correctly:

- The `netflix_ready` app entry installs or verifies a DRM-capable browser
  (Firefox with Widevine CDM).
- A desktop shortcut / `.webloc` / `.lnk` is created that opens
  `https://www.netflix.com` in Firefox.
- **No DRM circumvention is performed or documented.**
- Users must have a valid Netflix account.

To watch Netflix after running the generated script:
1. Open Firefox.
2. Navigate to `https://www.netflix.com`.
3. Sign in with your account.
4. When prompted, enable DRM in `Firefox Preferences > General > DRM Content`.

---

## How to Add New Apps or Packs

### Adding an app to an existing pack

1. Open the relevant manifest, e.g. `app-packs/linux/desktop.yml`.
2. Append a new entry under `apps:`, following the existing structure:

```yaml
- id: vlc
  name: VLC Media Player
  description: Open-source multimedia player.
  licensing_notes: LGPLv2.1 / GPLv2. Available in all major distros.
  post_install_notes: >
    VLC supports most media formats out of the box.
  distros:
    debian_ubuntu:
      package_manager: apt
      commands:
        - "apt-get install -y vlc"
    fedora_rhel:
      package_manager: dnf
      commands:
        - "dnf install -y vlc"
    arch_manjaro:
      package_manager: pacman
      commands:
        - "pacman -S --noconfirm vlc"
```

3. Validate the manifest against the schema:

```bash
python - <<'EOF'
import json, yaml, jsonschema
schema = json.load(open("schemas/app_pack.schema.json"))
data = yaml.safe_load(open("app-packs/linux/desktop.yml"))
jsonschema.validate(data, schema)
print("OK")
EOF
```

4. Run the tests:

```bash
python -m pytest tests/ -v
```

### Creating a new pack

1. Create a new YAML file, e.g. `app-packs/linux/server.yml`.
2. Set `id`, `description`, `platform`, and at least one `apps` entry.
3. The `id` field should match the filename stem (`server`).
4. Add tests if the pack has unusual install logic.

---

## Manifest Schema

The full schema is at [`schemas/app_pack.schema.json`](../schemas/app_pack.schema.json).

**Top-level fields**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique pack identifier (`[a-z0-9_-]+`) |
| `description` | string | ✅ | Human-readable description |
| `platform` | string | ✅ | `linux`, `windows`, or `macos` |
| `licensing_notes` | string | — | Legal note for the whole pack |
| `apps` | array | ✅ | List of app entries |

**App entry fields**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique within the pack |
| `name` | string | Display name |
| `description` | string | Short description |
| `licensing_notes` | string | Per-app licence note |
| `post_install_notes` | string | Shown in the script after install |
| `install` | object | Single install entry (Windows / macOS) |
| `distros` | object | Map of distro→install entry (Linux) |

**Install entry fields**

| Field | Type | Description |
|-------|------|-------------|
| `package_manager` | string | `apt`, `dnf`, `pacman`, `winget`, `brew`, etc. |
| `pre_install` | string[] | Commands to run before the main install |
| `commands` | string[] | Main install commands |
| `post_install` | string[] | Commands to run after install |
