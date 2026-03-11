# TPM-Backed LUKS Unlock (Linux)

> Preservation reference — defensive/administrative use only.  
> This page covers administrative and defensive concepts for TPM-backed disk encryption.

---

## Overview

A Trusted Platform Module (TPM) is a hardware chip (or firmware-emulated equivalent) that can
store cryptographic keys in a way that is bound to the system's firmware and boot state. When
combined with LUKS2, the TPM can automatically release the disk encryption key at boot — with no
passphrase prompt — but only if the measured boot chain matches the expected state.

This provides **convenience without sacrificing security**: the key is never stored in plaintext
on disk, and it cannot be transferred to another machine.

---

## Components

| Component | Role |
|-----------|------|
| TPM 2.0 chip (or firmware TPM / fTPM) | Hardware key store; seals key to PCR values |
| UEFI Secure Boot | Measures and authenticates boot chain components |
| `tpm2-tools` | Userspace TPM management utilities |
| `systemd-cryptenroll` | Enrolls LUKS2 key slots backed by TPM2, FIDO2, or PKCS#11 |
| `systemd-cryptsetup` | Reads `/etc/crypttab` and calls enrolled tokens at boot |

---

## Platform Configuration Registers (PCRs)

PCRs are TPM hash registers that record measurements of the boot chain. The TPM seals a key to a
set of PCR values; the key is only released when the current PCR values match the sealed values.

| PCR | Typically Measures |
|-----|--------------------|
| 0   | UEFI firmware / BIOS code |
| 2   | UEFI drivers, option ROMs |
| 4   | EFI boot manager, bootloader |
| 7   | Secure Boot policy and certificate database |
| 11  | systemd-boot / unified kernel image (UKI) measurements |
| 12  | Kernel command line (systemd-boot) |
| 14  | MOK (Machine Owner Key) database |

**Common PCR selection for LUKS unsealing:**
- Minimal: PCR 7 (Secure Boot state) — survives kernel/initrd updates
- Balanced: PCR 0+7 — survives kernel updates, not firmware updates
- Strict: PCR 0+4+7 — requires re-enrollment after bootloader updates

---

## Enrolling a TPM2 Token with systemd-cryptenroll

```sh
# Enroll a TPM2 key slot (binds to PCR 7 by default)
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/sdX

# Also retain passphrase slot for recovery (slot 0 by default)
# Do NOT remove all passphrase slots until TPM unlock is verified

# Test TPM unlock (as root, read key without a passphrase prompt)
sudo cryptsetup open --test-passphrase /dev/sdX
```

---

## /etc/crypttab for TPM-backed unlock

```
# <name>     <device>     <keyfile>  <options>
root_crypt   /dev/sdX     -          luks,tpm2-device=auto
```

The `tpm2-device=auto` option instructs `systemd-cryptsetup` to try the enrolled TPM2 token first,
falling back to passphrase if the TPM is unavailable or PCRs have changed.

---

## Recovery Procedure

If the TPM seal is broken (firmware update, Secure Boot change, hardware replacement):

1. Boot with a recovery medium (USB).
2. Open the LUKS volume using the passphrase: `sudo cryptsetup open /dev/sdX recovery_vol`
3. Mount and access data.
4. Re-enroll the TPM token: `sudo systemd-cryptenroll --wipe-slot=tpm2 --tpm2-device=auto /dev/sdX`
5. Reboot and verify automatic unlock.

**Always keep at least one passphrase key slot** as a recovery fallback.

---

## FIDO2 Token Enrollment (Alternative)

```sh
# Enroll a FIDO2 security key (e.g., YubiKey)
sudo systemd-cryptenroll --fido2-device=auto /dev/sdX
```

Requires the key to be present and tapped at boot. Suitable for high-security laptops.

---

## Tang/Clevis (Network-Based Unlock)

Tang + Clevis provides network-based TPM-less auto-unlock, suitable for server environments:
- **Tang** server holds a key fragment; running on a trusted network.
- **Clevis** client (on the encrypted host) reconstructs the LUKS key when network-reachable.
- Key is not released if the host is off-network (e.g., stolen and moved).

Reference: `https://github.com/latchset/tang` and `https://github.com/latchset/clevis`

---

## 32-bit (Legacy32) Notes

- TPM 2.0 is a firmware/hardware feature; it is not architecture-specific.
- `systemd-cryptenroll` runs on 32-bit Linux where systemd is present (Debian i386 ships systemd).
- Most 32-bit hardware predates TPM 2.0; TPM 1.2 is not supported by `systemd-cryptenroll`.
- Legacy32 systems without TPM should use passphrase + key-file unlock.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| systemd-cryptenroll man page | `https://www.freedesktop.org/software/systemd/man/systemd-cryptenroll.html` |
| TPM2 and LUKS (systemd blog) | `https://systemd.io/TPM2_PCR_MEASUREMENTS_BOOT/` |
| tpm2-tools | `https://github.com/tpm2-software/tpm2-tools` |
| Tang/Clevis | `https://github.com/latchset/tang` |
| Clevis LUKS integration | `https://github.com/latchset/clevis#luks` |

> Record provenance for any downloaded copies using [`../../_source_record_template.md`](../../_source_record_template.md).

---

## See Also

- [`luks-dmcrypt.md`](luks-dmcrypt.md)
- [`../../kernels/linux-kernel.md`](../../kernels/linux-kernel.md)
- [`../../matrix.md`](../../matrix.md)
