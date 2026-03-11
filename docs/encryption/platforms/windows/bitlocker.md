# BitLocker (Windows FDE)

> Preservation reference — defensive/administrative use only.

---

## Overview

BitLocker Drive Encryption is Microsoft's built-in FDE solution, available on Pro, Enterprise, and
Education editions of Windows (Vista and later). It encrypts entire volumes using AES-XTS (Windows
10 1511+) or AES-CBC (older).

---

## Supported Windows Versions

| Windows Version     | BitLocker Available | Notes |
|---------------------|---------------------|-------|
| Vista / 7           | ✅ (Ultimate/Enterprise) | AES-CBC 128/256 |
| 8 / 8.1             | ✅ (Pro/Enterprise) | |
| 10 (all builds)     | ✅ (Pro/Enterprise/Education) | AES-XTS from 1511 |
| 11                  | ✅ (Pro/Enterprise/Education) | AES-XTS-256 default |
| Home editions       | ❌ (Device Encryption only, subset) | TPM required for Device Enc |

---

## Architecture

- **Driver:** `fvevol.sys` (Full Volume Encryption Volume filter driver)
- **Cipher (default, Win10 1511+):** AES-XTS-128 (OS/fixed data volumes); AES-XTS-256 optional
- **Cipher (removable drives):** AES-CBC-128 (for compatibility)
- **Key protectors:** TPM, TPM+PIN, TPM+USB, Recovery Password (48-digit), Recovery Key (file), Password, Certificate (smart card)
- **Management:** `manage-bde.exe`, Group Policy, Microsoft Endpoint Manager / Intune, PowerShell `BitLocker` module

---

## TPM Integration

BitLocker uses the TPM to seal the Volume Master Key (VMK) against the PCR values of the boot chain.
If the boot chain changes (firmware update, Secure Boot change, OS bootloader update), BitLocker
enters recovery mode and demands the 48-digit recovery password.

PCRs typically sealed (varies by policy):
- PCR 0: Core Root of Trust for Measurement (CRTM) / BIOS
- PCR 2: ROM code
- PCR 4: Boot Manager
- PCR 7: Secure Boot state
- PCR 11: BitLocker access control

---

## Enabling BitLocker

```
# PowerShell — enable on C: with TPM+PIN protector
Enable-BitLocker -MountPoint "C:" -TpmAndPinProtector -Pin (Read-Host -AsSecureString "Enter PIN")

# Add recovery password
Add-BitLockerKeyProtector -MountPoint "C:" -RecoveryPasswordProtector

# Back up recovery key to AD (domain-joined)
Backup-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId <id>
```

---

## Verification

```
# Check encryption status
manage-bde -status C:

# List protectors
manage-bde -protectors -get C:
```

Expected output includes: `Protection Status: Protection On`, `Encryption Method: XTS-AES 128` (or 256).

---

## Recovery

1. At boot, press `Esc` when prompted for PIN/password to enter recovery mode.
2. Enter the 48-digit recovery password.
3. After boot, investigate why normal unlock failed (PCR mismatch, firmware change, etc.).
4. Resume BitLocker after confirming system integrity.

---

## 32-bit (Legacy32) Notes

- BitLocker is available on 32-bit Windows 7/8/10 (x86) but Microsoft dropped 32-bit support in
  Windows 11 entirely.
- AES-NI is absent on many 32-bit CPUs; BitLocker will use software AES (slower but functional).
- Legacy32 preservation note: BitLocker state from a 32-bit Windows 10 volume can be read by a
  64-bit Windows 10 system (same FVEK format).

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| BitLocker overview | `https://learn.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-overview` |
| manage-bde reference | `https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/manage-bde` |
| BitLocker PowerShell | `https://learn.microsoft.com/en-us/powershell/module/bitlocker/` |
| TPM and BitLocker | `https://learn.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-and-tpm-other-faqs` |
| Recovery guide | `https://learn.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-recovery-guide-plan` |

> Record provenance for any downloaded copies using [`../../_source_record_template.md`](../../_source_record_template.md).

---

## See Also

- [`../../kernels/windows-kernel.md`](../../kernels/windows-kernel.md)
- [`../../matrix.md`](../../matrix.md)
