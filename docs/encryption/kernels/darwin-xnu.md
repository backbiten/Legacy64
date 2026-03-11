# Darwin / XNU Kernel — FDE Reference (High-Level)

> Preservation reference — high-level notes and documentation placeholders.  
> Administrative/archival use only.

---

## Overview

macOS's FDE (FileVault 2) is implemented within the Darwin/XNU kernel through the I/O Kit storage
stack. On Intel Macs without a T2 chip, the XNU kernel manages encryption transparently; on T2
and Apple Silicon Macs, the Secure Enclave Processor (SEP) handles key management at the hardware
level.

---

## XNU Architecture Relevant to FDE

```
Applications / File System (APFS / HFS+)
        │
[ CoreStorage (Intel pre-APFS) or APFS encryption layer ]
        │
[ IOStorage (I/O Kit storage stack) ]
        │  — IOFilterScheme subclass intercepts I/O —
        │
[ AES hardware (AES engine) / Software AES via CommonCrypto ]
        │
[ Physical device (NVMe / SATA) ]
```

---

## Key Components

| Component | Role |
|-----------|------|
| `APFS.kext` | Apple File System kernel extension; handles per-volume and per-file encryption |
| `CoreStorage.kext` | Legacy full-volume encryption framework (HFS+ era, macOS 10.7–10.12) |
| `AppleAPFSUserClient` | Userspace interface for APFS management (diskutil, fdesetup) |
| `IOAESAccelerator` / `AppleAES` | Hardware AES engine driver (Intel T2, Apple Silicon) |
| Secure Enclave Processor (SEP) | Hardware crypto boundary on T2/Apple Silicon; stores VEK |
| `AppleKeyStore.kext` | Interface to the SEP for key management |
| Effaceable Storage | Write-once-erase area where the SEP stores key material |

---

## APFS Encryption Architecture

APFS (Apple File System, 2017+) supports:
- **Volume encryption:** All files in a volume encrypted with the Volume Encryption Key (VEK).
- **Per-file encryption:** Individual files can have different encryption keys (FileVault uses volume-level).
- **Key wrapping:** VEK is wrapped with a Key Encryption Key (KEK) derived from the user password; KEK is unsealed by SEP on T2/Apple Silicon.

On Apple Silicon (M1, M2, M3...):
- All NAND storage is always encrypted at the hardware level (Media Key in SEP).
- FileVault adds a software-level key layer controlled by the user password.
- Even with FileVault off, data is encrypted with a hardware media key (not user-controlled).

---

## Intel Mac (without T2)

On pre-T2 Intel Macs (pre-2018):
- CoreStorage (HFS+) or APFS handles encryption in software.
- AES-XTS-128 via the CPU's AES-NI instructions.
- Key derived from user password using PBKDF2 (CoreStorage era) or system-integrated method (APFS).
- No hardware key boundary; key is in kernel memory while unlocked.

---

## T2 Chip (2018–2020 Intel Macs)

The Apple T2 Security Chip:
- Acts as a Secure Enclave Processor.
- All storage I/O passes through the T2 which encrypts/decrypts on the fly (AES-256).
- FileVault activates the key protection layer over the always-encrypted T2 storage.
- T2 enforces Secure Boot and does not release keys if Secure Boot is compromised.

---

## 32-bit (Legacy32) Notes

macOS has never run on 32-bit-only x86 hardware. The first Intel Macs (2006) were 32/64-bit
capable (Core Duo) but macOS required 64-bit kernel support from Lion (10.7) onward. FileVault 2
is therefore not applicable to 32-bit x86 preservation.

Preserved here for architectural completeness and comparison with Linux and Windows kernels.

---

## Documentation References (Placeholders)

Replace `PLACEHOLDER_SHA256` after downloading and hashing each document.

| Resource | URL (text reference) | SHA-256 |
|----------|---------------------|---------|
| Apple Platform Security Guide | `https://support.apple.com/guide/security/welcome/web` | `PLACEHOLDER_SHA256` |
| APFS Reference (Apple) | `https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf` | `PLACEHOLDER_SHA256` |
| XNU source (open source) | `https://github.com/apple-oss-distributions/xnu` | `PLACEHOLDER_SHA256` |
| Apple T2 Security Chip | `https://www.apple.com/mac/docs/Apple_T2_Security_Chip_Overview.pdf` | `PLACEHOLDER_SHA256` |
| FileVault (fdesetup man page) | `https://ss64.com/mac/fdesetup.html` | `PLACEHOLDER_SHA256` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`../platforms/macos/filevault.md`](../platforms/macos/filevault.md)
- [`linux-kernel.md`](linux-kernel.md)
- [`../matrix.md`](../matrix.md)
