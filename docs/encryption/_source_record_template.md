# Source Record Template

Use this template to document provenance for any external source referenced or stored in this
collection (documentation pages, PDFs, ISOs, package indexes, etc.).

Copy this file, rename it to reflect the artifact (e.g., `ubuntu-24.04-fde-release-notes.md`),
fill in the fields, and commit it alongside or in place of the artifact.

---

## Source Record

```yaml
# Required fields
title: ""                         # Human-readable title of the source
source_url: ""                    # Original URL (text reference; does not need to be live)
access_date: "YYYY-MM-DD"         # Date this URL was accessed / snapshot was taken
content_type: ""                  # e.g. "official documentation", "release notes", "ISO image",
                                  #      "PDF manual", "source tarball", "package index"

# Identification
sha256: "PLACEHOLDER"             # SHA-256 hex digest of the stored file; replace after download
                                  # Leave as "PLACEHOLDER" if file is not stored locally
file_name: ""                     # Local file name relative to this record (if stored)
file_size_bytes: null             # File size in bytes (if stored)

# Licensing / redistribution
license: ""                       # e.g. "CC-BY-4.0", "GPL-2.0", "proprietary — no redistribution",
                                  #      "public domain", "unknown — verify before redistributing"
redistribution_permitted: null    # true / false / null (unknown)
redistribution_note: ""           # Any additional restrictions or conditions

# Context
platform: ""                      # e.g. "Linux", "Windows", "macOS", "cross-platform"
distro: ""                        # e.g. "Ubuntu", "Debian", "Fedora", "N/A"
version: ""                       # Version string this source applies to
arch: ""                          # e.g. "x86_64", "i386", "aarch64", "all"
topics:                           # Tags for discovery
  - "fde"
  # - "luks"
  # - "bitlocker"
  # - "filevault"

# Preservation notes
archived_at: ""                   # e.g. Wayback Machine URL or internal archive path (optional)
notes: ""                         # Any additional provenance or quality notes
```

---

## Verification Instructions

To verify a stored file against the recorded SHA-256:

```sh
# Linux / macOS
sha256sum <file_name>

# Windows (PowerShell)
Get-FileHash <file_name> -Algorithm SHA256
```

Compare the output to the `sha256` field above. If they do not match, do **not** use the file —
re-download from the original source and update this record.

---

## Example (Filled In)

```yaml
title: "Ubuntu 24.04 LTS — Full Disk Encryption with TPM2 (Official Docs)"
source_url: "https://ubuntu.com/tutorials/install-ubuntu-desktop#6-installation-type"
access_date: "2026-03-11"
content_type: "official documentation"

sha256: "PLACEHOLDER"
file_name: ""
file_size_bytes: null

license: "CC-BY-SA-3.0"
redistribution_permitted: true
redistribution_note: "Canonical documentation; attribution required."

platform: "Linux"
distro: "Ubuntu"
version: "24.04 LTS"
arch: "x86_64"
topics:
  - "fde"
  - "luks"
  - "tpm"

archived_at: ""
notes: "Captures installer FDE option at time of access."
```
