# Full Disk Encryption (FDE) — Overview

> **Scope:** Preservation and defensive/administrative use only.  
> This collection does **not** provide guidance for bypassing encryption or gaining unauthorized access.

---

## What is Full Disk Encryption?

Full Disk Encryption (FDE) protects data at rest by encrypting every sector of a storage device.
Without the correct credentials (passphrase, key file, TPM-backed key, or recovery key), the data
is unreadable even if the physical drive is removed.

FDE operates below the file-system layer. The OS kernel presents a virtual decrypted block device
to the rest of the stack; the raw device remains ciphertext on disk at all times.

---

## Basic Threat Model

| Threat                             | FDE Mitigates? | Notes                                   |
|------------------------------------|----------------|-----------------------------------------|
| Physical theft of device/drive     | ✅ Yes          | Core use case                           |
| Forensic imaging without key       | ✅ Yes          | Ciphertext only without key             |
| Insider/supply-chain tampering     | ⚠️ Partial     | Secure Boot + Measured Boot needed too  |
| Live OS attack (running system)    | ❌ No           | Keys are in memory; FDE does not help   |
| Malware on running system          | ❌ No           | Encryption is transparent while booted |
| Weak passphrases / lost keys       | ❌ No           | Key management is out-of-scope for FDE  |

---

## Key Management

- **Passphrase / PIN** — user-memorized secret; weakest link if too short.
- **Recovery key** — long random string generated at setup; store offline, never in cloud unless you control the cloud.
- **Key file** — file on removable media; physical security required.
- **TPM-backed** — hardware-sealed key released only after Secure Boot chain validates; transparent unlock. See [`platforms/linux/tpm.md`](platforms/linux/tpm.md).
- **Hardware security key (FIDO2 / YubiKey)** — challenge-response unlock; requires supported stack.

**Key management principles:**
1. Always generate and store at least one recovery key offline.
2. Test recovery before relying on FDE.
3. Rotate keys after known compromise or personnel changes.
4. Document escrow procedures for organizational deployments.

---

## Recovery

- **Recovery key** must be stored separately from the encrypted device.
- For organizations: consider split-knowledge escrow (two parties each hold half).
- For individuals: printed copy in a physically secure location is better than a cloud note.
- Test the recovery path on a non-production system first.

---

## Backups

FDE encrypts the disk, not the backup destination. Back up **before** and **after** enabling FDE.
Backups of an FDE-enabled disk may be:
- **Encrypted image** (same key): portable but tied to key; test restoration.
- **Decrypted backup** (files copied to backup target): backup target must have its own protection.

---

## Verification Philosophy

Encryption is not "set and forget." Verify:
1. The correct sectors are encrypted (check via OS tooling; see per-platform docs).
2. The recovery key actually works (test on a spare or in a VM first).
3. Firmware/Secure Boot state has not changed (especially for TPM-backed unlock).
4. Backup can be restored and decrypted independently.

---

## Architecture Notes (Legacy32 / Legacy64)

- **32-bit (Legacy32):** LUKS2/dm-crypt supports 32-bit kernels; some distros dropped i386 support. AES-NI is absent on many 32-bit CPUs — software AES is slower but functional. Year-2038 time_t overflow does not directly affect FDE but may affect expiry timestamps in key metadata.
- **64-bit (Legacy64):** Full hardware AES acceleration on x86_64 (AES-NI); all major platforms support FDE.

---

## Preservation and Defensive Use Only

This documentation tree exists to **preserve knowledge** about FDE across platforms and distributions
for archival, research, and administrative reference. It is intended for:

- System administrators enabling FDE on machines they manage.
- Researchers studying OS/kernel crypto subsystems.
- Archivists documenting the state of FDE support across distros and versions.

**It is not intended to:**
- Provide instructions for bypassing, circumventing, or removing encryption without authorization.
- Assist in accessing data that the accessor does not have legal authority to access.
- Serve as an attack guide or penetration-testing tutorial.

If you are locked out of your own data: consult your OS vendor's official recovery documentation.

---

## Related Pages

- [`matrix.md`](matrix.md) — Feature matrix across platforms and distros
- [`_source_record_template.md`](_source_record_template.md) — Provenance capture template
- [`platforms/`](platforms/) — Platform-specific FDE details
- [`distros/`](distros/) — Distribution-specific notes
- [`kernels/`](kernels/) — Kernel-level crypto subsystem references
