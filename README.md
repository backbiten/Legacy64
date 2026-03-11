# Legacy64

> Bringing back old AMD 64-bit because someone in the department of systemd ditched it.

Legacy64 is an offline artifact management system with a built-in safety/QC/QA scanning layer.
It is designed to preserve, catalogue, and safely share 64-bit legacy software artifacts without
spreading malware, spyware, or other unsafe payloads.

---

## Table of Contents

- [Quick start](#quick-start)
- [CLI reference](#cli-reference)
- [QC/QA model](#qcqa-model)
- [Quarantine behaviour](#quarantine-behaviour)
- [Offline guarantee](#offline-guarantee)
- [Directory layout](#directory-layout)
- [Extending the rule set](#extending-the-rule-set)

---

## Quick start

```bash
# Install (Python ≥ 3.8, no external dependencies)
pip install -e .

# Initialise a new repository in the current directory
legacyai init

# Add a file (scans by default; quarantines if scan FAIL)
legacyai add firmware.bin --id my-firmware

# View all stored artifacts
legacyai list

# Re-scan an artifact manually
legacyai scan my-firmware

# Export (re-scans before copying; blocks if FAIL)
legacyai export my-firmware /tmp/out/firmware.bin
```

---

## CLI reference

```
legacyai [--repo DIR] COMMAND [OPTIONS]

Commands
  init                        Initialise a new Legacy64 repository
  add FILE [--id ID]          Add a file to the artifact store
      [--no-scan]               Skip QC/QA scan (artifact stored as UNCHECKED)
  scan ARTIFACT_ID            Scan a stored artifact; save report
  list                        List all artifacts
  export ARTIFACT_ID OUTPUT   Export artifact (re-scans by default)
      [--no-rescan]             Skip the pre-export re-scan (not recommended)
  quarantine list             List quarantined artifacts
  quarantine promote ID       Move quarantined artifact to normal store
  quarantine reject  ID       Permanently delete quarantined artifact
```

---

## QC/QA model

Every artifact passes through two check stages before being accepted.

### Stage 1 — QC (Quality Control): deterministic checks

| Rule ID | Name                  | Action on fail |
|---------|-----------------------|----------------|
| QC-001  | File readable         | FAIL           |
| QC-002  | Hash integrity        | FAIL           |
| QC-003  | File size             | FAIL           |
| QC-004  | File type detection   | PASS (info)    |

QC aggregates to **PASS** only when every check passes.

### Stage 2 — QA (Quality Assurance): heuristic, rule-based checks

| Rule ID | Name                              | Default severity |
|---------|-----------------------------------|-----------------|
| QA-001  | ELF binary detected               | WARN            |
| QA-002  | PE binary detected                | WARN            |
| QA-003  | Mach-O binary detected            | WARN            |
| QA-004  | Executable script (shebang)       | WARN            |
| QA-005  | ZIP archive inspection            | WARN / FAIL     |
| QA-006  | TAR archive inspection            | WARN / FAIL     |
| QA-007  | High entropy / obfuscation        | WARN            |
| QA-008  | Embedded executable magic bytes   | WARN            |
| QA-009  | Credential / secret patterns      | WARN / FAIL     |

QA aggregates to **PASS** (no findings), **WARN** (warn-only findings), or **FAIL** (at
least one FAIL-severity finding).

### Final decision

| QC     | QA     | Decision |
|--------|--------|----------|
| PASS   | PASS   | **PASS** |
| PASS   | WARN   | **WARN** |
| PASS   | FAIL   | **FAIL** |
| FAIL   | *any*  | **FAIL** |

Reports are saved as JSON under `reports/<artifact-id>.json` and include the
timestamp, tool version, all check results with rule IDs, and the final decision.

---

## Quarantine behaviour

When `legacyai add --scan` produces a **FAIL** decision the artifact is **never
promoted to the normal store**.  Instead:

1. The object file is copied to `quarantine/objects/` (content-addressed).
2. A quarantine record is written to `quarantine/records/<artifact-id>.json`.
3. A full scan report is saved to `reports/<artifact-id>.json`.
4. `legacyai add` exits with a non-zero status code.

The artifact stays in quarantine until the operator explicitly acts:

```bash
# Review the quarantine
legacyai quarantine list

# Read the scan report
cat reports/<artifact-id>.json

# Override and promote (use with caution)
legacyai quarantine promote <artifact-id>

# Permanently delete
legacyai quarantine reject <artifact-id>
```

No automatic action ever deletes data; the user is always in control.

---

## Offline guarantee

Legacy64 is designed to be **strictly offline**:

- No DNS lookups, HTTP requests, or socket connections are made anywhere in the
  codebase.
- All checks are implemented using the Python standard library only — no external
  packages are required or installed.
- The CI pipeline (`python -m pytest`) runs with no network access beyond what
  GitHub Actions itself provides for installing Python.

If you want to verify this yourself, run the test suite with network access
disabled (e.g. using a network namespace or a firewall rule blocking the test
process).

---

## Directory layout

```
<repo-root>/
├── .legacy64             # Repository marker file
├── objects/              # Content-addressed blob store (SHA-256, aa/bbb…)
├── artifacts/            # Artifact metadata JSON records
├── reports/              # Scan report JSON files
└── quarantine/
    ├── objects/          # Quarantined blobs
    └── records/          # Quarantine metadata records
```

---

## Extending the rule set

All QA rules live in `legacyai/scanner/qa.py`.  Each rule is a plain Python
function with the signature `(path: Path) -> List[Finding]`.  To add a new rule:

1. Write the function, e.g. `_rule_custom`.
2. Append a tuple `("QA-010", "My rule name", _rule_custom)` to `_RULES`.
3. Add a test in `tests/test_qa.py`.

Rules are intentionally simple and explainable — every finding includes a
`rule_id` and a human-readable `details` string describing exactly what was found. 
