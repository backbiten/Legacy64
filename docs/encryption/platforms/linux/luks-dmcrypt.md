# LUKS / dm-crypt (Linux FDE)

> Preservation reference — defensive/administrative use only.

---

## Overview

**dm-crypt** is the Linux kernel's device-mapper crypto target.  
**LUKS** (Linux Unified Key Setup) is the on-disk key management format layered on top of dm-crypt.  
**cryptsetup** is the userspace tool that manages LUKS containers.

LUKS2 (cryptsetup 2.0+, kernel 4.x+) is the current standard format. LUKS1 is legacy but still
widely supported.

---

## Component Stack

```
User data (files)
     │
[ File system: ext4 / xfs / btrfs / ... ]
     │
[ dm-crypt virtual block device  /dev/mapper/<name> ]
     │
[ LUKS2 header + key slots  /dev/sdX (or /dev/nvmeXnY) ]
     │
[ Physical block device ]
```

---

## LUKS2 Key Features

- **Cipher:** AES-XTS-plain64 (default; 256-bit key = XTS-128 effective)
- **PBKDF:** Argon2id (default in LUKS2); PBKDF2 (LUKS1 and legacy LUKS2)
- **Key slots:** Up to 32 (LUKS2) — each can hold a different passphrase, key file, or token
- **Tokens:** Plugin slots for TPM2 (via `systemd-cryptenroll`), FIDO2, PKCS#11 smart cards, Tang/Clevis
- **Integrity:** Optional per-sector HMAC/AEAD via `--integrity` flag (dm-integrity integration)
- **Detached header:** Header can be stored separately from the data device

---

## Common cryptsetup Commands

```sh
# Format a device with LUKS2 (destructive)
sudo cryptsetup luksFormat --type luks2 /dev/sdX

# Open (map) a LUKS device
sudo cryptsetup open /dev/sdX my_volume

# Mount the decrypted device
sudo mount /dev/mapper/my_volume /mnt/data

# Check LUKS header info
sudo cryptsetup luksDump /dev/sdX

# Add a new key slot (e.g., backup passphrase)
sudo cryptsetup luksAddKey /dev/sdX

# Remove a key slot (dangerous — verify other slots work first)
sudo cryptsetup luksKillSlot /dev/sdX <slot_number>

# Close (unmap) the device
sudo cryptsetup close my_volume
```

---

## Verification

```sh
# Confirm device is a LUKS container
sudo cryptsetup isLuks /dev/sdX && echo "Is LUKS" || echo "Not LUKS"

# Check encryption status of a mapped device
sudo cryptsetup status my_volume

# Verify LUKS header integrity (LUKS2 only)
sudo cryptsetup luksDump /dev/sdX | grep -E "Version|Cipher|UUID"
```

---

## /etc/crypttab

Persistent mapping at boot is configured in `/etc/crypttab`:

```
# <name>     <device>       <keyfile>  <options>
my_volume    /dev/sdX       none       luks
```

---

## /etc/fstab Integration

After crypttab decrypts the device, fstab mounts it:

```
/dev/mapper/my_volume  /mnt/data  ext4  defaults  0  2
```

---

## 32-bit (Legacy32) Notes

- dm-crypt / LUKS fully supports 32-bit (i386/i686) kernels.
- AES-NI absent on most 32-bit hardware: software AES via kernel crypto API; functional but slower.
- LUKS2 header format is architecture-neutral; a LUKS2 volume created on 64-bit can be opened on 32-bit.
- Argon2id memory cost may need tuning on low-RAM 32-bit systems (`--pbkdf-memory`).

---

## Backup the LUKS Header

```sh
# Back up LUKS header (critical — header corruption = data loss)
sudo cryptsetup luksHeaderBackup /dev/sdX --header-backup-file luks-header-backup.img
sha256sum luks-header-backup.img  # Record this hash
```

Store the backup **off the encrypted device**. A damaged LUKS header without a backup means the
data is unrecoverable even with the correct passphrase.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| cryptsetup man page | `https://linux.die.net/man/8/cryptsetup` |
| LUKS on-disk format spec | `https://gitlab.com/cryptsetup/LUKS2-docs` |
| dm-crypt kernel docs | `https://www.kernel.org/doc/html/latest/admin-guide/device-mapper/dm-crypt.html` |
| Arch Wiki — dm-crypt | `https://wiki.archlinux.org/title/dm-crypt` |
| cryptsetup FAQ | `https://gitlab.com/cryptsetup/cryptsetup/-/wikis/FrequentlyAskedQuestions` |

> Record provenance for any downloaded copies using [`../../_source_record_template.md`](../../_source_record_template.md).

---

## See Also

- [`tpm.md`](tpm.md) — TPM-backed unlock with systemd-cryptenroll
- [`../../kernels/linux-kernel.md`](../../kernels/linux-kernel.md)
- [`../../matrix.md`](../../matrix.md)
