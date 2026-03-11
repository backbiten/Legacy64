# Linux Mint — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Linux Mint is Ubuntu/Debian-based and uses the Ubiquity installer (same as Ubuntu 20.04/22.04).
FDE support is inherited from the Ubuntu base; it uses LUKS2 + dm-crypt.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt (via Ubiquity) |
| Installer option | ✅ "Encrypt the new Linux Mint installation" |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (LUKS2) |
| TPM-backed unlock | ⚠️ Manual only (not in Mint installer) |
| 32-bit (i386) | ❌ Dropped (Mint 20+ is 64-bit only) |
| Base | Ubuntu LTS (22.04 base for Mint 21.x) |

---

## Installer Path

1. Boot Linux Mint live environment.
2. Launch "Install Linux Mint."
3. At "Installation type," choose **Erase disk and install Linux Mint**.
4. Check **Encrypt the new Linux Mint installation for security**.
5. Choose a strong passphrase and optionally overwrite empty space.
6. Proceed with installation.

**Note:** Linux Mint 20.x/21.x uses Ubiquity with the same FDE options as Ubuntu 20.04/22.04.

---

## Post-Install Verification

```sh
# Check crypttab for LUKS mapping name
cat /etc/crypttab

# Verify LUKS on the device
sudo cryptsetup luksDump /dev/<device>

# Check active mapping
sudo cryptsetup status <mapping-name>
```

---

## TPM-Backed Unlock (Manual)

Linux Mint does not configure TPM-backed unlock at install time. Post-install:

```sh
sudo apt install systemd tpm2-tools
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/<device>
sudo update-initramfs -u -k all
```

Retain passphrase slot as recovery fallback.

---

## 32-bit (Legacy32) Notes

- Linux Mint 19.x (Ubuntu 18.04 base) was the last version with 32-bit support.
- Mint 19.x used Ubiquity with LUKS1 (pre-LUKS2 era); upgrade to cryptsetup 2.x for LUKS2 header.
- Archived Mint 19.x i386 installs can be opened with current `cryptsetup` on any arch.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Linux Mint Installation Guide | `https://linuxmint-installation-guide.readthedocs.io/` |
| Linux Mint User Guide | `https://linuxmint.com/documentation.php` |
| Ubuntu FDE (base installer) | `https://ubuntu.com/tutorials/install-ubuntu-desktop#6-installation-type` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`ubuntu.md`](ubuntu.md)
- [`debian.md`](debian.md)
- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../matrix.md`](../matrix.md)
