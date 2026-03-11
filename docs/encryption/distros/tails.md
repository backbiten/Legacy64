# Tails — Full Disk Encryption (Persistent Storage)

> Preservation reference — defensive/administrative use only.

---

## Overview

Tails (The Amnesic Incognito Live System) is a security-focused live OS designed to leave no
traces. It does not install to disk by default. FDE applies to the **Persistent Storage** volume
on the Tails USB drive — an optional encrypted partition where users can store selected files and
settings across sessions.

Tails' FDE model is fundamentally different from other distros: the live OS itself is unencrypted
and read-only; only the persistent partition is encrypted.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt (Persistent Storage) |
| Default | ✅ Persistent Storage is encrypted by default if enabled |
| Cipher | LUKS2 AES-XTS-plain64 |
| PBKDF | Argon2id |
| TPM-backed unlock | ❌ By design — amnesic; TPM binding contradicts amnesia model |
| 32-bit (i386) | ❌ Tails 4.x dropped i386 |
| Live OS encryption | ❌ The bootable Tails image is not encrypted |
| Swap | ✅ Encrypted (RAM-only; no swap to disk by design) |

---

## Persistent Storage Setup

1. Boot Tails from USB.
2. From the Tails welcome screen, click **Configure persistent storage** (or from Applications → Tails → Persistent Storage).
3. Choose a strong passphrase.
4. Select which categories to persist (Tor Browser bookmarks, files, network settings, etc.).
5. Restart Tails and unlock persistent storage at the welcome screen.

**Note:** The passphrase is set once and cannot be recovered if forgotten — there is no recovery key by design (amnesic model). Write it down and store securely offline.

---

## Architecture Notes

- The Tails USB is partitioned as: `EFI + Tails system (read-only) + Persistent (LUKS2)`.
- The persistent volume uses the label `TailsData` and LUKS2.
- Inside the persistent volume: `btrfs` filesystem with subvolumes per feature.

---

## Verification

```sh
# Boot Tails, unlock persistent storage, then from a terminal:
sudo cryptsetup luksDump /dev/sdX3   # (partition number varies; check with lsblk)

# Verify open mapping
sudo cryptsetup status TailsData
```

---

## Threat Model Specific to Tails

- Tails provides **amnesia**: without unlocking persistent storage, nothing from previous sessions
  remains.
- Persistent storage adds convenience but also risk: if the USB is seized, the passphrase is the
  only protection.
- Tails advises against predictable passphrases; use a multi-word diceware passphrase.
- Physical memory attacks (cold boot): Tails erases memory on shutdown to mitigate.

---

## 32-bit (Legacy32) Notes

- Tails 4.x (released 2020) dropped i386 support.
- Tails 3.x supported i386; preservation of Tails 3.x ISOs documents the last 32-bit FDE-capable
  Tails releases.
- SHA-256 hashes of archived Tails 3.x ISOs should be recorded from Tails' official release page.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Tails — Persistent Storage | `https://tails.boum.org/doc/persistent_storage/index.en.html` |
| Tails — About Tails | `https://tails.boum.org/about/index.en.html` |
| Tails — Warnings | `https://tails.boum.org/doc/about/warnings/index.en.html` |
| Tails release downloads | `https://tails.boum.org/install/download/index.en.html` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../matrix.md`](../matrix.md)
