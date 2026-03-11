# Manjaro — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Manjaro is an Arch Linux–based distribution using the Calamares installer. FDE is offered as an
opt-in during installation. Manjaro uses a rolling release model, so version numbers refer to
ISO release snapshots.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt |
| Installer | Calamares |
| Installer option | ✅ "Encrypt system" checkbox in partitioning step |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (LUKS2) |
| TPM-backed unlock | ⚠️ Manual only (not in Calamares) |
| 32-bit (i386) | ❌ Dropped; Manjaro is 64-bit (x86_64/aarch64) only |
| Swap | ✅ Encrypted swap partition (when using LVM option in Calamares) |

---

## Installer Path (Calamares)

1. Boot Manjaro live environment.
2. Launch the installer.
3. At the "Partitions" step, choose **Erase disk**.
4. Check **Encrypt system**.
5. Enter a passphrase and confirm.
6. Optionally check **Swap to file** or use **LVM** for encrypted swap.
7. Proceed with installation.

**Note:** Calamares' FDE option uses LUKS2 by default in Manjaro 21.x+.

---

## Post-Install Verification

```sh
# Check crypttab
cat /etc/crypttab

# Verify LUKS header
sudo cryptsetup luksDump /dev/<device>

# Check active mapping
sudo cryptsetup status <mapping-name>
```

---

## TPM-Backed Unlock (Manual)

Manjaro does not configure TPM-backed unlock via Calamares. Post-install (rolling release with
modern systemd):

```sh
sudo pacman -S tpm2-tools tpm2-tss
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/<device>
sudo mkinitcpio -P
```

Retain passphrase slot. Reboot and verify.

---

## Arch Wiki (Applies to Manjaro)

Manjaro is Arch-based; the Arch Wiki is the authoritative reference for LUKS/dm-crypt configuration:

- `https://wiki.archlinux.org/title/dm-crypt/Encrypting_an_entire_system`
- `https://wiki.archlinux.org/title/dm-crypt/Device_encryption`

---

## 32-bit (Legacy32) Notes

Manjaro has never officially supported 32-bit x86. For Arch-based 32-bit preservation, see the
`archlinux32` project: `https://archlinux32.org/`. Archlinux32 supports i486 and pentium4 targets
with current packages including cryptsetup/LUKS2.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| Manjaro Documentation | `https://wiki.manjaro.org/index.php/Main_Page` |
| Calamares Documentation | `https://calamares.io/docs/` |
| Arch Wiki — dm-crypt | `https://wiki.archlinux.org/title/dm-crypt` |
| Archlinux32 | `https://archlinux32.org/` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../platforms/linux/tpm.md`](../platforms/linux/tpm.md)
- [`../matrix.md`](../matrix.md)
