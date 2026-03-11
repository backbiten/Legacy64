# Security Policy

## Threat model

Legacy64's scanning layer is designed to reduce the risk of unsafe artifacts
being added to the archive or shared with others.  It is **not** a replacement
for a full antivirus solution.

### What the scanner can detect

| Threat                                         | Rule(s)          |
|------------------------------------------------|------------------|
| Native executables (ELF, PE, Mach-O)           | QA-001 – QA-003  |
| Executable scripts (shebang)                   | QA-004           |
| Suspicious ZIP contents (autorun, .lnk, etc.)  | QA-005           |
| Path-traversal entries in TAR archives         | QA-006           |
| Compressed/encrypted / obfuscated payloads     | QA-007           |
| Executables embedded inside other file types   | QA-008           |
| Credentials and secrets accidentally included  | QA-009           |

### What the scanner cannot guarantee

- **No guarantee of no malware.**  Signature-based and behavioural detection
  are outside the scope of this tool.  For high-assurance environments use
  additional scanning (e.g. ClamAV, commercial AV, sandboxed dynamic analysis)
  on top of Legacy64.
- **Polymorphic or heavily obfuscated payloads** may evade heuristic checks.
- **Archive recursion** is limited to one level deep to avoid denial-of-service
  from nested zip-bombs; deeper nesting is flagged but not fully inspected.
- **Binary formats** are identified by magic bytes only; a file can spoof its
  magic header.

### Design principles

1. **Strictly offline** — no DNS, HTTP, or any outbound network call is made.
2. **Fail-safe** — exceptions inside individual rules become WARN findings
   rather than crashing the scan or silently passing.
3. **Explainable** — every finding carries a `rule_id` and human-readable
   `details`; there are no "black-box" scores.
4. **User in control** — failed artifacts are quarantined, never auto-deleted;
   only explicit `legacyai quarantine promote` or `reject` commands change state.
5. **Pure Python** — zero runtime dependencies beyond the standard library;
   no supply-chain risk from third-party packages.

## Reporting a vulnerability

If you discover a security issue in Legacy64 itself (e.g. a way to bypass the
gate or a path-traversal in the store), please open a GitHub issue tagged
**security** or contact the repository owner directly.  Do not include
live malware samples in issue reports.

## Disclaimer

> Legacy64 aims to **reduce** risk, not eliminate it.  Operators are responsible
> for performing additional due diligence appropriate to their threat model before
> distributing any artifact.
