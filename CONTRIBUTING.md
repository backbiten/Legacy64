# Contributing to Legacy64

Thank you for helping preserve AMD64-era software and documentation.
Please read this guide before adding artifacts or records.

---

## Legal and redistribution policy

Legacy64 is a **preservation archive**, not a distribution platform.
Contributors are responsible for ensuring that any artifact they add may be
legally stored and shared.

### What you MUST do before adding an artifact

1. **Verify redistribution rights.** Only add artifacts if *at least one* of the
   following applies:
   - The artifact's license explicitly permits redistribution (e.g. GPL, MIT, BSD,
     public domain / CC0).
   - The rights-holder has granted explicit permission for archival purposes.
   - The artifact is in the public domain (documented and verifiable).

2. **Document provenance.** Fill in `source_url` and optionally `description` in the
   artifact YAML record so others can verify the origin.

3. **Do not add proprietary binaries** without clear redistribution rights, even if
   they are "abandonware."  Abandonware does not have a defined legal status.

### When you cannot redistribute the artifact itself

Store only the **metadata + hash** — do NOT run `legacyai add` with the actual file:

- Create the artifact YAML record manually under `artifacts/<lane>/`.
- Set `sha256` to the known hash of the artifact.
- Set `size` to the known size.
- Leave the `objects/` store empty for this record (note it in `description`).
- Add acquisition instructions in the `description` field:
  ```yaml
  description: >
    Not redistributable. Obtain from <URL> and verify SHA-256 matches the
    hash recorded here before use.
  ```

`legacyai verify` will report missing objects for such records; this is expected and
intentional — the hash record is still valuable.

---

## Adding artifacts

```bash
# 1. Import the file (only if redistributable)
legacyai add <path> --lane legacy64|legacy32 --type bin|src|firmware|doc \
    [--name "human name"] [--version "x.y.z"]

# 2. Verify the repo is still consistent
legacyai verify

# 3. Commit
git add artifacts/ objects/ bindings/ patches/
git commit -m "add: <artifact name> (<lane>)"
```

---

## Adding bindings

Bindings document relationships between legacy32 and legacy64 artifacts that share
an upstream source.  **No conversion is implied.**

```bash
legacyai bind source-patch \
    --source "<upstream ref>" \
    --legacy32 <artifact-id> \
    --legacy64 <artifact-id> \
    [--patch patches/your-diff.patch]
```

Edit the generated YAML to fill in `build_profiles` (toolchain, flags, triplet).

---

## Commit message conventions

| Prefix | Use for |
|---|---|
| `add:` | New artifact record or object |
| `bind:` | New binding record |
| `fix:` | Correction to a record (wrong hash, typo, etc.) |
| `schema:` | Changes to JSON schemas |
| `tooling:` | Changes to `tooling/legacyai/` |
| `docs:` | README, CONTRIBUTING, or other documentation |

---

## Code contributions

- Python ≥ 3.9, standard library preferred.
- Format with `ruff format` before opening a PR.
- All tests must pass: `pytest tooling/legacyai/tests/`.
- Schema changes must be backwards-compatible or bumped with a version note.

---

## Questions

Open a GitHub Issue for any redistribution questions before adding an artifact.
When in doubt, store only metadata + hash.
