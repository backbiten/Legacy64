# FileVault 2 (macOS FDE)

> Preservation reference — defensive/administrative use only.

---

## Overview

FileVault 2 (introduced in macOS 10.7 Lion) provides full-volume encryption for macOS. It encrypts
the entire startup disk using AES-XTS (128-bit on Intel, 256-bit on Apple Silicon / T2).

---

## Supported macOS Versions

| macOS Version      | FileVault Support | Notes |
|--------------------|-------------------|-------|
| 10.7 Lion          | ✅ FileVault 2    | First version with full-volume FDE |
| 10.8 – 10.12       | ✅                | |
| 10.13 High Sierra  | ✅                | APFS support added |
| 10.14 – 11 (Intel) | ✅                | T2 chip macs: hardware-backed |
| 12+ (Apple Silicon)| ✅ (default on)   | Secure Enclave; AES-256; always encrypted |
| 12+ (Intel T2)     | ✅                | T2 enforces encryption at hardware level |

---

## Architecture

- **Volume format:** HFS+ (pre-10.13) or APFS (10.13+)
- **Cipher:** AES-XTS-128 (Intel without T2), AES-256 (T2 / Apple Silicon — hardware-level)
- **Key hierarchy:**
  - User password unlocks the Volume Master Key (VMK)
  - VMK decrypts the Volume Encryption Key (VEK)
  - Recovery Key (shown once at setup; store securely) is an alternative VMK protector
  - Institutional recovery key via MDM (escrow)
- **Apple Silicon / Secure Enclave:** Encryption key is hardware-fused; FileVault acts as an
  additional authorization layer over always-encrypted storage.

---

## Enabling FileVault

**GUI:** System Settings → Privacy & Security → FileVault → Turn On

**Terminal:**
```sh
# Enable FileVault (generates recovery key; prompts for user password)
sudo fdesetup enable

# Check status
fdesetup status

# List users authorized to unlock
fdesetup list
```

---

## Verification

```sh
fdesetup status
# Expected: FileVault is On.

diskutil apfs list
# Look for: FileVault: Yes (Unlocked)
```

---

## Recovery

1. Restart, hold `⌘R` to enter macOS Recovery.
2. Choose "Forgot password?" or enter the 28-character personal recovery key when prompted.
3. If using MDM institutional recovery: IT provides the institutional key.

---

## iCloud Recovery Key Escrow

macOS offers to store the recovery key in iCloud. This is convenient but means the key is held by
Apple under your Apple ID credentials. For high-security environments, **do not use iCloud escrow**;
store the recovery key offline.

---

## 32-bit (Legacy32) Notes

macOS dropped 32-bit application support in Catalina (10.15). FileVault on macOS is not relevant
to 32-bit x86/i386 hardware — Apple never shipped macOS on 32-bit-only hardware with FileVault 2.
Preserved here for architecture reference completeness.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| FileVault overview (Apple) | `https://support.apple.com/en-us/HT204837` |
| fdesetup man page | `https://ss64.com/mac/fdesetup.html` (mirror ref) |
| Apple Platform Security guide | `https://support.apple.com/guide/security/welcome/web` |
| MDM FileVault management | `https://support.apple.com/guide/deployment/manage-filevault-dep82064ec40/web` |

> Record provenance for any downloaded copies using [`../../_source_record_template.md`](../../_source_record_template.md).

---

## See Also

- [`../../kernels/darwin-xnu.md`](../../kernels/darwin-xnu.md)
- [`../../matrix.md`](../../matrix.md)
