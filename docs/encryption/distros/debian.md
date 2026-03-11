# Debian — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Debian supports FDE via LUKS2 + dm-crypt, configurable during installation through the guided
partitioner. Debian is known for stability and long support cycles; it supports both 32-bit (i386)
and 64-bit (amd64) architectures.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt |
| Installer option | ✅ Guided partitioner ("Guided — use entire disk and set up encrypted LVM") |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (LUKS2) |
| TPM-backed unlock | ⚠️ Manual (`systemd-cryptenroll`; not in installer) |
| 32-bit (i386) | ✅ Supported |
| Swap encryption | ✅ (optional; encrypted swap via LVM or random key) |

---

## Installer Path (Guided FDE)

1. Boot the Debian installer.
2. At "Partition disks," choose **Guided — use entire disk and set up encrypted LVM**.
3. Enter and confirm a strong passphrase.
4. Complete partitioning and proceed with installation.
5. After install, record and store the LUKS header backup:
   ```sh
   sudo cryptsetup luksHeaderBackup /dev/sdX --header-backup-file debian-luks-header.img
   sha256sum debian-luks-header.img
   ```

---

## Post-Install Verification

```sh
# Confirm the root device is LUKS-encrypted
sudo cryptsetup status sda5_crypt   # name varies; check /etc/crypttab

# Check LUKS version and cipher
sudo cryptsetup luksDump /dev/sdX
```

---

## TPM-Backed Unlock (Post-Install, Manual)

```sh
sudo apt install systemd-cryptsetup-generator tpm2-tools
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/sdX
sudo update-initramfs -u
```

Reboot and verify automatic unlock. Keep a passphrase slot as recovery fallback.

---

## 32-bit (Legacy32) Notes

- Debian i386 is fully supported through Debian 11 (Bullseye); Debian 12 (Bookworm) retains i386
  but with reduced package set.
- LUKS2 and dm-crypt work on 32-bit kernels.
- `systemd-cryptenroll` is available on i386 Debian 12+.
- Year-2038 note: Debian i386 kernel time_t overflow is January 19, 2038. Monitor Debian i386
  kernel patches for `time_t` widening.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Debian Installer — encrypted LVM | `https://www.debian.org/releases/stable/amd64/ch06s03.en.html#di-partition` |
| Debian Wiki — Disk Encryption | `https://wiki.debian.org/DiskEncryption` |
| Debian Wiki — LUKS | `https://wiki.debian.org/Cryptsetup` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../platforms/linux/tpm.md`](../platforms/linux/tpm.md)
- [`../matrix.md`](../matrix.md)
