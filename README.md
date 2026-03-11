# Legacy64

Bringing back old AMD 64 bit because someone in the department of system D ditched it.

Legacy64 is an **offline-first, read-only archive** for 64-bit (and 32-bit) legacy
operating system artefacts, documentation, and preservation-grade patch series.

## Y2038 Preservation

32-bit systems face the **Year-2038 problem** – a `time_t` overflow on
**2038-01-19**.  This repository stores immutable baseline snapshots and
forward-applied patch/diff series so that fixes remain auditable and
reproducible long after the event date.

→ See [docs/y2038.md](docs/y2038.md) for a full description of the problem,
the preservation approach, and the recommended workflow.

## Tooling – `legacyai`

`legacyai` is a pure-Python, strictly-offline CLI for managing the archive.

```
pip install -e .
```

Key commands:

| Command | Purpose |
|---------|---------|
| `legacyai patch add <file> [--tag y2038]` | Import a patch file |
| `legacyai patchset create y2038:<name>` | Create a named patchset |
| `legacyai patchset add y2038:<name> --patch <id> --order <n>` | Add a patch to a patchset |
| `legacyai bind source-patch --source <id> --patchset <ps-id>` | Bind source artifact to patchset |
| `legacyai verify` | Verify all hashes and references |

## Directory layout

```
patches/              Raw .patch files + YAML metadata
patchsets/y2038/      Y2038-specific patchset records
bindings/             Artifact binding records
artifacts/            Artifact metadata
objects/              Content-addressed object store
schemas/              JSON Schema definitions
docs/                 Documentation
```

