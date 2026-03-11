# Ubuntu — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Ubuntu supports FDE via LUKS2 + dm-crypt through its installer (Ubiquity / new Flutter-based
installer). Ubuntu 23.10+ introduced experimental TPM-backed FDE in the new installer; Ubuntu 24.04
LTS made it available as a supported option.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt |
| Installer option | ✅ "Encrypt the new Ubuntu installation for security" |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (LUKS2) |
| TPM-backed unlock | ✅ Ubuntu 24.04+ (new installer); ⚠️ manual for older |
| 32-bit (i386) | ❌ Dropped in Ubuntu 19.10 |
| Swap encryption | ✅ (via encrypted swap file or partition) |

---

## Installer Path (Ubiquity — Ubuntu 22.04 LTS and earlier)

1. Boot Ubuntu installer.
2. At "Installation type," choose **Erase disk and install Ubuntu**.
3. Check **Encrypt the new Ubuntu installation for security**.
4. Enter a security key (passphrase); optionally check "Overwrite empty disk space."
5. **Note:** Ubuntu's Ubiquity installer uses a single LUKS passphrase; no TPM integration at install time.

---

## Installer Path (New Installer — Ubuntu 23.10+)

1. Boot Ubuntu installer.
2. At "Type of installation," choose **Use entire disk**.
3. Choose **Advanced features** → **Use LVM and encrypt the new Ubuntu installation** (LUKS passphrase), or **TPM-backed full disk encryption** (Ubuntu 24.04+ on compatible hardware).
4. If passphrase: enter and confirm passphrase; record recovery key shown.
5. If TPM: installer handles enrollment automatically; save the recovery key.

---

## Post-Install Verification

```sh
# Check active LUKS mappings
ls -la /dev/mapper/

# Verify LUKS on the encrypted partition
sudo cryptsetup luksDump /dev/sdX   # replace with actual device (check /etc/crypttab)

# Check encryption status
sudo cryptsetup status dm-name-from-crypttab
```

---

## TPM Unlock (Manual, Ubuntu 22.04)

```sh
sudo apt install tpm2-tools
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/sdX
sudo update-initramfs -u -k all
```

Reboot and verify. Retain at least one passphrase slot for recovery.

---

## 32-bit (Legacy32) Notes

Ubuntu dropped i386 as a supported architecture in 19.10. For 32-bit Ubuntu preservation:
- Ubuntu 18.04 LTS (Bionic) was the last LTS with i386 installer images.
- LUKS1/LUKS2 from an archived 18.04 i386 install can be opened with current `cryptsetup`.
- Year-2038: Ubuntu 18.04 i386 will experience `time_t` overflow on 2038-01-19; kernel patches
  required for continued operation.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Ubuntu FDE docs | `https://ubuntu.com/tutorials/install-ubuntu-desktop#6-installation-type` |
| Ubuntu 24.04 TPM FDE | `https://ubuntu.com/blog/tpm-backed-full-disk-encryption-is-coming-to-ubuntu` |
| Ubuntu cryptsetup | `https://help.ubuntu.com/community/Full_Disk_Encryption_Howto_2019` |
| Ubuntu Wiki — Security | `https://wiki.ubuntu.com/Security/Features#Disk_Encryption` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`debian.md`](debian.md)
- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../platforms/linux/tpm.md`](../platforms/linux/tpm.md)
- [`../matrix.md`](../matrix.md)
