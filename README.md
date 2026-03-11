# Legacy64
Bringing back old AMD 64 bit because someone in the department of system D ditched it

---

## Documentation

### Full Disk Encryption (FDE) Reference Collection

A preservation-oriented, docs-first collection covering FDE across major platforms and
Linux distributions — organized for both Legacy32 and Legacy64 architectures.

> **Scope:** Defensive and administrative use only. No guidance for bypassing encryption.

| Section | Link |
|---------|------|
| Overview & threat model | [`docs/encryption/overview.md`](docs/encryption/overview.md) |
| Feature matrix (all platforms/distros) | [`docs/encryption/matrix.md`](docs/encryption/matrix.md) |
| Provenance template | [`docs/encryption/_source_record_template.md`](docs/encryption/_source_record_template.md) |
| **Platforms** | |
| Windows — BitLocker | [`docs/encryption/platforms/windows/bitlocker.md`](docs/encryption/platforms/windows/bitlocker.md) |
| macOS — FileVault 2 | [`docs/encryption/platforms/macos/filevault.md`](docs/encryption/platforms/macos/filevault.md) |
| Linux — LUKS / dm-crypt | [`docs/encryption/platforms/linux/luks-dmcrypt.md`](docs/encryption/platforms/linux/luks-dmcrypt.md) |
| Linux — TPM-backed unlock | [`docs/encryption/platforms/linux/tpm.md`](docs/encryption/platforms/linux/tpm.md) |
| **Distributions** | |
| Debian | [`docs/encryption/distros/debian.md`](docs/encryption/distros/debian.md) |
| Ubuntu | [`docs/encryption/distros/ubuntu.md`](docs/encryption/distros/ubuntu.md) |
| Linux Mint | [`docs/encryption/distros/linux-mint.md`](docs/encryption/distros/linux-mint.md) |
| Zorin OS | [`docs/encryption/distros/zorin-os.md`](docs/encryption/distros/zorin-os.md) |
| Tails | [`docs/encryption/distros/tails.md`](docs/encryption/distros/tails.md) |
| Fedora | [`docs/encryption/distros/fedora.md`](docs/encryption/distros/fedora.md) |
| RHEL / Red Hat | [`docs/encryption/distros/rhel.md`](docs/encryption/distros/rhel.md) |
| Manjaro | [`docs/encryption/distros/manjaro.md`](docs/encryption/distros/manjaro.md) |
| Coral Linux (unresolved ⚠️ TODO) | [`docs/encryption/distros/unknown-coral-linux.md`](docs/encryption/distros/unknown-coral-linux.md) |
| **Kernels** | |
| Linux kernel — crypto subsystem | [`docs/encryption/kernels/linux-kernel.md`](docs/encryption/kernels/linux-kernel.md) |
| Windows kernel — FDE overview | [`docs/encryption/kernels/windows-kernel.md`](docs/encryption/kernels/windows-kernel.md) |
| Darwin / XNU kernel — FDE overview | [`docs/encryption/kernels/darwin-xnu.md`](docs/encryption/kernels/darwin-xnu.md) |

→ [Full encryption docs index](docs/encryption/README.md)

