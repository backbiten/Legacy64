# Fedora — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Fedora uses the Anaconda installer and supports LUKS2 + dm-crypt FDE as an opt-in during
installation. Fedora is upstream for RHEL and is often the first Red Hat family distro to adopt
newer FDE features (e.g., TPM2 enrollment via `systemd-cryptenroll`).

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt |
| Installer | Anaconda |
| Installer option | ✅ "Encrypt my data" checkbox in Custom / Automatic Partitioning |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (Fedora 33+) |
| TPM-backed unlock | ✅ Available post-install (Fedora 38+) and via Anaconda in later releases |
| 32-bit (i386) | ❌ Dropped in Fedora 31 |
| Swap | ✅ Encrypted with LVM or via `zram` (Fedora default) |

---

## Installer Path (Automatic Partitioning)

1. Boot Fedora installer.
2. At "Installation Destination," select your disk.
3. Choose **Automatic** partitioning.
4. Check **Encrypt my data**.
5. Set a passphrase when prompted.
6. Click "Done" and proceed.

---

## Installer Path (Custom Partitioning)

1. At "Installation Destination," choose **Custom**.
2. Create partitions (boot, swap, root, etc.).
3. For each encrypted partition: select the mount point, choose **LUKS** as the device type.
4. Set passphrase for each LUKS device (or use the same passphrase; Anaconda will ask).

---

## Post-Install Verification

```sh
# List LUKS mappings
sudo dmsetup ls --target crypt

# Check LUKS header
sudo cryptsetup luksDump /dev/<device>

# Check PCR-based TPM enrollment (if enrolled)
sudo systemd-cryptenroll /dev/<device>
```

---

## TPM-Backed Unlock

Fedora 38+ supports TPM2-backed enrollment:

```sh
# Install tpm2 tools if not present
sudo dnf install tpm2-tools

# Enroll TPM2 key slot (PCR 7 = Secure Boot state)
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/<device>

# Regenerate initramfs to include TPM token support
sudo dracut --force
```

Reboot to verify. Retain passphrase slot for recovery.

---

## 32-bit (Legacy32) Notes

- Fedora 30 was the last Fedora release with i686 (32-bit) support.
- Archived Fedora 30 i686 ISOs represent the end of Red Hat–family 32-bit FDE support.
- SHA-256 hash of Fedora 30 i686 ISO should be captured from `https://archives.fedoraproject.org/`.
- Year-2038: Fedora 30 i686 kernel uses 32-bit `time_t`; kernel patches and glibc updates are
  required for post-2038 operation.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Fedora Anaconda FDE | `https://docs.fedoraproject.org/en-US/fedora/latest/install-guide/install/Installing_Using_Anaconda/` |
| Fedora Security Guide | `https://docs.fedoraproject.org/en-US/fedora/latest/security-guide/` |
| Fedora — Disk Encryption | `https://fedoraproject.org/wiki/Disk_Encryption_User_Guide` |
| systemd-cryptenroll (Fedora) | `https://fedoramagazine.org/use-systemd-cryptenroll-with-fido-u2f-or-tpm2-to-decrypt-your-disk/` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`rhel.md`](rhel.md)
- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../platforms/linux/tpm.md`](../platforms/linux/tpm.md)
- [`../matrix.md`](../matrix.md)
