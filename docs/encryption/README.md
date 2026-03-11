# Encryption Documentation — Index

Full Disk Encryption (FDE) preservation reference for Legacy32 and Legacy64 architectures.

> **Scope:** Preservation and defensive/administrative use only.  
> See [`overview.md`](overview.md) for the full safety and scope statement.

---

## Contents

### Core
- [`overview.md`](overview.md) — What FDE is, threat model, key management, recovery, verification philosophy, and safety framing
- [`matrix.md`](matrix.md) — Feature matrix: FDE support across platforms, distros, and versions
- [`_source_record_template.md`](_source_record_template.md) — Provenance capture template for any referenced/stored artifact

### Platforms
| Platform | File |
|----------|------|
| Windows — BitLocker | [`platforms/windows/bitlocker.md`](platforms/windows/bitlocker.md) |
| macOS — FileVault 2 | [`platforms/macos/filevault.md`](platforms/macos/filevault.md) |
| Linux — LUKS / dm-crypt | [`platforms/linux/luks-dmcrypt.md`](platforms/linux/luks-dmcrypt.md) |
| Linux — TPM-backed unlock | [`platforms/linux/tpm.md`](platforms/linux/tpm.md) |

### Distributions
| Distribution | File |
|-------------|------|
| Debian | [`distros/debian.md`](distros/debian.md) |
| Ubuntu | [`distros/ubuntu.md`](distros/ubuntu.md) |
| Linux Mint | [`distros/linux-mint.md`](distros/linux-mint.md) |
| Zorin OS | [`distros/zorin-os.md`](distros/zorin-os.md) |
| Tails | [`distros/tails.md`](distros/tails.md) |
| Fedora | [`distros/fedora.md`](distros/fedora.md) |
| RHEL / Red Hat | [`distros/rhel.md`](distros/rhel.md) |
| Manjaro | [`distros/manjaro.md`](distros/manjaro.md) |
| Coral Linux (unresolved) | [`distros/unknown-coral-linux.md`](distros/unknown-coral-linux.md) ⚠️ TODO |

### Kernels
| Kernel | File |
|--------|------|
| Linux kernel — crypto subsystem | [`kernels/linux-kernel.md`](kernels/linux-kernel.md) |
| Windows kernel — FDE overview | [`kernels/windows-kernel.md`](kernels/windows-kernel.md) |
| Darwin / XNU kernel — FDE overview | [`kernels/darwin-xnu.md`](kernels/darwin-xnu.md) |

---

## Quick Reference

**I want to enable FDE on...**
- Windows → [`platforms/windows/bitlocker.md`](platforms/windows/bitlocker.md)
- macOS → [`platforms/macos/filevault.md`](platforms/macos/filevault.md)
- Debian / Ubuntu / Mint / Zorin → [`platforms/linux/luks-dmcrypt.md`](platforms/linux/luks-dmcrypt.md) + distro page
- Fedora / RHEL → [`distros/fedora.md`](distros/fedora.md) or [`distros/rhel.md`](distros/rhel.md)
- Tails → [`distros/tails.md`](distros/tails.md)

**I want TPM-backed auto-unlock on Linux →** [`platforms/linux/tpm.md`](platforms/linux/tpm.md)

**I want to compare FDE support across distros →** [`matrix.md`](matrix.md)

**I want to record provenance for a downloaded doc/ISO →** [`_source_record_template.md`](_source_record_template.md)
