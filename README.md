# Legacy64

**AMD64 software, firmware, and hardware documentation — preserved, verifiable, and offline-first.**

Legacy64 is a content-addressed artifact archive for the AMD64 (x86-64) ecosystem.
Its mission is long-term preservation of binaries, source archives, firmware images, and
documentation that target or document the AMD64 architecture.

---

## Core design principles

| Principle | Meaning |
|---|---|
| **AMD64 is first-class** | `legacy64` (AMD64/x86-64) is the primary lane. It is not derived from legacy32. |
| **legacy32 is first-class** | `legacy32` (x86/IA-32) artifacts are preserved independently, without conversion. |
| **No implicit conversion** | There is no 32→64 or 64→32 rewrite. Relationships between lanes are expressed explicitly as *binding records*. |
| **Content-addressed storage** | Every artifact is stored under `objects/sha256/<first2>/<fullhash>`. Hashes are the ground truth. |
| **Offline-first** | The entire archive, CLI, and validation pipeline runs without network access. |
| **Human-readable records** | All metadata is plain YAML; all schemas are plain JSON Schema. |

---

## Repository layout

```
Legacy64/
├── objects/sha256/         # Content-addressed artifact store (immutable blobs)
├── artifacts/
│   ├── legacy64/           # AMD64 artifact records (*.yml)
│   └── legacy32/           # x86 artifact records (*.yml)
├── bindings/
│   └── source-patch/       # Source-patch binding records (*.yml)
├── patches/                # Patch files referenced by bindings
├── schemas/                # JSON Schema for artifact and binding records
└── tooling/legacyai/       # Python CLI source
```

---

## Quickstart

### Prerequisites

```bash
pip install ./tooling/legacyai
```

Or for development:

```bash
pip install -e "./tooling/legacyai[dev]"
```

### 1 — Initialise

```bash
legacyai init
```

Creates the required directory structure and writes `.legacyai.yml` (default config).

### 2 — Add an artifact

```bash
# AMD64 binary
legacyai add firmware.rom --lane legacy64 --type firmware --name "BIOS v2.1" --version "2.1.0"

# x86 source archive
legacyai add libc-2.17.tar.gz --lane legacy32 --type src --name "glibc" --version "2.17"
```

The file is hashed (SHA-256), copied into `objects/sha256/`, and an artifact YAML record is
written under `artifacts/<lane>/`.

### 3 — Verify the repository

```bash
legacyai verify
```

Checks that every artifact record:
- points to a stored object
- has a matching hash (object integrity)
- validates against the artifact JSON schema

Also checks all binding records.

### 4 — Create a source-patch binding

A binding documents the *relationship* between a legacy32 and a legacy64 artifact that share
an upstream source — for example the same upstream tarball built with different toolchains.
**No conversion is performed.**

```bash
legacyai bind source-patch \
  --source "v2.17" \
  --legacy32 <legacy32-artifact-id> \
  --legacy64 <legacy64-artifact-id> \
  --patch patches/align-types.patch
```

The binding record is written to `bindings/source-patch/`.

---

## Artifact record format

```yaml
id: <uuid-v4>
lane: legacy64          # or legacy32
type: bin               # bin | src | firmware | doc
filename: firmware.rom
sha256: <64-hex-chars>
size: 1048576
imported_at: "2024-01-15T12:00:00+00:00"
name: "BIOS v2.1"      # optional
version: "2.1.0"       # optional
```

See `schemas/artifact.schema.json` for the full schema.

## Binding record format

```yaml
id: <uuid-v4>
type: source-patch
source:
  ref: v2.17
legacy32_artifact: <uuid-v4>
legacy64_artifact: <uuid-v4>
patch_file: patches/align-types.patch
patch_sha256: <64-hex-chars>
created_at: "2024-01-15T12:01:00+00:00"
build_profiles:
  legacy32:
    toolchain: gcc-13.2
    triplet: i686-pc-linux-gnu
    build_flags: ["-O2", "-m32"]
  legacy64:
    toolchain: gcc-13.2
    triplet: x86_64-linux-gnu
    build_flags: ["-O2"]
```

See `schemas/source-patch-binding.schema.json` for the full schema.

---

## AI companion (`legacyai`)

The `legacyai` CLI is the AI-assisted backend for this archive.  It handles:

- **Compartmentalisation** — keeps legacy32 and legacy64 lanes strictly separate.
- **Binding proposal** — records the *relationship* between lanes via source-patch bindings,
  never by rewriting or converting artifacts.
- **Verification** — deterministic hash checks and schema validation ensure the archive
  remains self-consistent.
- **Offline operation** — all operations work without network access.

The CLI is written in Python and can be invoked as:

```bash
legacyai <command>
# or
python -m legacyai <command>
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidance on artifact redistribution policy,
legal considerations, and how to contribute records, bindings, and patches.

---

## License

The tooling in `tooling/legacyai/` is MIT licensed.
Individual artifacts stored in `objects/` retain their original licenses.
Artifact *records* (metadata in `artifacts/`) are CC0.
