# Windows Kernel — FDE Reference (High-Level)

> Preservation reference — high-level notes and documentation placeholders.  
> Administrative/archival use only.

---

## Overview

Windows' FDE (BitLocker) is implemented through a kernel-mode filter driver stack. The encryption
is transparent to the file system and applications; the Windows kernel manages I/O interception
and key lifecycle through a combination of kernel drivers and the Windows Security Center / TPM
stack.

---

## Key Kernel Components

| Component | Description |
|-----------|-------------|
| `fvevol.sys` | Full Volume Encryption Volume filter driver — core BitLocker driver |
| `fveapi.dll` | BitLocker management API (userspace interface to kernel driver) |
| `tpm.sys` | TPM kernel driver (communicates with TPM hardware) |
| `tcblaunch.exe` | Trusted Computing Base launch process (pre-OS measured boot) |
| Windows Boot Manager (`bootmgr`) | Measures boot chain PCRs; presents BitLocker recovery if PCRs mismatch |
| WinPE / WinRE | Windows Recovery Environment; used for BitLocker recovery |

---

## Driver I/O Stack Position

```
Applications / File System (NTFS/ReFS)
        │
[ fvevol.sys — Volume filter driver (intercepts all block I/O) ]
        │  (encrypts writes / decrypts reads using VMK)
        │
[ Disk class driver / Storage stack ]
        │
[ Physical device (disk / NVMe / SATA) ]
```

The Volume Master Key (VMK) is kept in kernel memory only while the volume is unlocked.
The VMK itself is protected by one or more key protectors (TPM, PIN, Recovery Key).

---

## Measured Boot and PCRs

Windows implements Measured Boot through UEFI and the TPM:

1. UEFI firmware measures itself into PCR0.
2. UEFI measures the Windows Boot Manager into PCR4.
3. Windows Boot Manager measures the OS loader into PCR4/PCR8.
4. Secure Boot state is recorded in PCR7.
5. BitLocker seals the VMK protector to the expected PCR values.

If any measured component changes (firmware update, Secure Boot policy change), the PCR values
change and BitLocker enters recovery mode.

---

## Virtualization-Based Security (VBS) / Hypervisor-Protected Code Integrity (HVCI)

Windows 10/11 can use VBS to isolate the BitLocker key material in a secure hypervisor partition
(Virtual Secure Mode — VSM). In this configuration:

- The VMK is sealed within VSM, not directly accessible from the normal kernel ring-0.
- Even a kernel-level exploit cannot directly extract the key.
- Requires UEFI Secure Boot + TPM + HVCI-capable hardware.

---

## 32-bit (Legacy32) Notes

- BitLocker is available on 32-bit Windows 7/8/10 (x86) with the same driver (`fvevol.sys`).
- Windows 11 dropped 32-bit support entirely.
- 32-bit Windows kernel uses 32-bit `LARGE_INTEGER` time (Windows does not have a single `time_t`
  in the POSIX sense; FILETIME is 64-bit even on 32-bit Windows — no 2038 issue for FILETIME).
- However, legacy C runtime `time_t` on 32-bit MSVC was 32-bit before VS2005; code compiled with
  older toolchains may be affected.

---

## Documentation References (Placeholders)

Replace `PLACEHOLDER_SHA256` after downloading and hashing each document.

| Resource | URL (text reference) | SHA-256 |
|----------|---------------------|---------|
| BitLocker Architecture (Microsoft Docs) | `https://learn.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-overview` | `PLACEHOLDER_SHA256` |
| Windows Measured Boot | `https://learn.microsoft.com/en-us/windows/security/hardware-security/tpm/how-windows-uses-the-tpm` | `PLACEHOLDER_SHA256` |
| Windows Driver Kit (WDK) Crypto | `https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/` | `PLACEHOLDER_SHA256` |
| Secure Boot and Measured Boot | `https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/oem-secure-boot` | `PLACEHOLDER_SHA256` |
| VBS / HVCI Overview | `https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/oem-vbs` | `PLACEHOLDER_SHA256` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`../platforms/windows/bitlocker.md`](../platforms/windows/bitlocker.md)
- [`linux-kernel.md`](linux-kernel.md)
- [`../matrix.md`](../matrix.md)
