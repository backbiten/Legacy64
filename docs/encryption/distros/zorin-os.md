# Zorin OS — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Zorin OS is an Ubuntu-based distribution targeting users transitioning from Windows or macOS.
It uses the Ubiquity installer and inherits Ubuntu's FDE capabilities via LUKS2 + dm-crypt.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt (via Ubiquity) |
| Installer option | ✅ "Encrypt the new Zorin OS installation" |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (LUKS2) |
| TPM-backed unlock | ⚠️ Manual only |
| 32-bit (i386) | ❌ Zorin OS 16+ is 64-bit only |
| Base | Ubuntu LTS (22.04 base for Zorin OS 17) |

---

## Installer Path

1. Boot Zorin OS live environment.
2. Launch the installer.
3. At "Installation type," choose **Erase disk and install Zorin OS**.
4. Check **Encrypt the new Zorin OS installation for security**.
5. Enter and confirm a passphrase.
6. Complete installation.

---

## Post-Install Verification

```sh
# Check crypttab
cat /etc/crypttab

# Check LUKS status
sudo cryptsetup luksDump /dev/<device>

# Verify active mapping
sudo cryptsetup status <mapping-name>
```

---

## 32-bit (Legacy32) Notes

Zorin OS has not offered 32-bit installer images since Zorin OS 15 (Ubuntu 18.04 base).
32-bit preservation is handled through the Ubuntu 18.04 base; see [`ubuntu.md`](ubuntu.md).

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Zorin OS Documentation | `https://help.zorin.com/` |
| Zorin OS Release Notes | `https://zorin.com/os/` |
| Ubuntu FDE (base installer) | `https://ubuntu.com/tutorials/install-ubuntu-desktop` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`ubuntu.md`](ubuntu.md)
- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../matrix.md`](../matrix.md)
