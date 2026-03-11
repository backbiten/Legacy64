# RHEL / Red Hat Enterprise Linux — Full Disk Encryption

> Preservation reference — defensive/administrative use only.

---

## Overview

Red Hat Enterprise Linux (RHEL) uses the Anaconda installer and supports LUKS2 + dm-crypt FDE.
RHEL is an enterprise distribution with long support cycles (10 years); FDE is a standard feature
for regulated and high-security deployments.

RHEL also supports **Tang + Clevis** for network-based auto-unlock, suitable for server environments
where physical TPM is absent or impractical.

---

## FDE Support Summary

| Property | Value |
|----------|-------|
| Mechanism | LUKS2 + dm-crypt |
| Installer | Anaconda |
| Installer option | ✅ "Encrypt my data" in disk partitioning |
| Default cipher | AES-XTS-plain64 (256-bit key) |
| Default PBKDF | Argon2id (RHEL 8.3+) |
| TPM-backed unlock | ✅ (`systemd-cryptenroll`, Tang/Clevis) |
| Network unlock | ✅ Tang/Clevis (`clevis-dracut`, `clevis-luks`) |
| 32-bit (i386) | ❌ RHEL 7 was last version with limited 32-bit support |
| FIPS mode | ✅ RHEL supports FIPS 140-2/3 validated crypto modules |

---

## Installer Path

1. Boot RHEL installer.
2. At "Installation Destination," select target disk.
3. Choose **Automatic** partitioning.
4. Check **Encrypt my data**.
5. Set passphrase and click "Done."

For custom partitioning: set LUKS encryption per-partition in the manual partitioning screen.

---

## FIPS Mode

RHEL can be put into FIPS mode, which enforces FIPS 140-2/3 validated algorithms:

```sh
# Enable FIPS mode (requires reboot)
sudo fips-mode-setup --enable
sudo reboot

# Verify FIPS mode
sudo fips-mode-setup --check
```

In FIPS mode, LUKS uses the FIPS-validated AES and SHA implementations from OpenSSL/kernel FIPS module.

---

## Tang/Clevis Network Auto-Unlock

```sh
# Install Clevis
sudo dnf install clevis-luks clevis-dracut

# Bind LUKS device to Tang server
sudo clevis luks bind -d /dev/<device> tang '{"url":"http://tang-server.example.com"}'

# Regenerate initramfs
sudo dracut --force

# Test unlock
sudo clevis luks unlock -d /dev/<device>
```

The device unlocks automatically at boot if the Tang server is reachable on the network.

---

## Post-Install Verification

```sh
# Check LUKS header
sudo cryptsetup luksDump /dev/<device>

# List bound Clevis tokens
sudo clevis luks list -d /dev/<device>

# Check Clevis + Tang status
sudo clevis luks report -d /dev/<device>
```

---

## 32-bit (Legacy32) Notes

- RHEL 7 provided limited i386 packages for application compatibility but not full i386 installer.
- RHEL 5/6 supported i386 installations with dm-crypt (LUKS1).
- Preserved RHEL 5/6 i386 installations represent FDE capability in the RPM ecosystem on 32-bit.
- Year-2038: RHEL 5/6/7 on i386 will experience `time_t` overflow; Red Hat published advisories
  on `time_t` widening; see RHEL Knowledge Base for patches.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| RHEL 9 — Security Hardening (FDE) | `https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/security_hardening/encrypting-block-devices-using-luks_security-hardening` |
| RHEL — Tang/Clevis | `https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/security_hardening/configuring-automated-unlocking-of-encrypted-volumes-using-policy-based-decryption_security-hardening` |
| RHEL FIPS Mode | `https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/security_hardening/assembly_installing-the-system-in-fips-mode_security-hardening` |
| Clevis GitHub | `https://github.com/latchset/clevis` |
| Tang GitHub | `https://github.com/latchset/tang` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`fedora.md`](fedora.md)
- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../platforms/linux/tpm.md`](../platforms/linux/tpm.md)
- [`../matrix.md`](../matrix.md)
