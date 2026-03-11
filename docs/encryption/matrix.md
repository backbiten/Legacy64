# FDE Feature Matrix

Template for tracking Full Disk Encryption support across platforms, distributions, and versions.
Fill in cells as sources are verified; use `?` for unknown, `N/A` where not applicable.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Supported / Yes |
| ❌ | Not supported / No |
| ⚠️ | Partial / Caveats |
| `?` | Unknown — needs research |
| `N/A` | Not applicable |

---

## Platform / Distro Matrix

| Platform / Distro        | Version(s)   | FDE by Default | Installer FDE Option | Cipher (default) | Unlock Methods              | TPM-backed Unlock | 32-bit (i386) Supported | Official Docs Ref |
|--------------------------|--------------|----------------|----------------------|------------------|-----------------------------|-------------------|-------------------------|-------------------|
| **Windows**              |              |                |                      |                  |                             |                   |                         |                   |
| Windows 10 Pro/Ent       | 21H2+        | ⚠️ (Device Enc) | ✅ BitLocker         | AES-XTS-128/256  | PIN, USB, TPM, Recovery Key | ✅                | ❌ (64-bit only)         | [bitlocker.md](platforms/windows/bitlocker.md) |
| Windows 11 Pro/Ent       | 22H2+        | ⚠️ (Device Enc) | ✅ BitLocker         | AES-XTS-256      | PIN, USB, TPM, Recovery Key | ✅                | ❌                       | [bitlocker.md](platforms/windows/bitlocker.md) |
| **macOS**                |              |                |                      |                  |                             |                   |                         |                   |
| macOS 10.13+ (Intel)     | High Sierra+ | ⚠️ (prompt)    | ✅ FileVault 2       | AES-XTS-128      | Password, Recovery Key, iCloud | ⚠️ (T2 chip)   | N/A                     | [filevault.md](platforms/macos/filevault.md) |
| macOS 12+ (Apple Silicon)| Monterey+    | ✅ (default)   | ✅ FileVault 2       | AES-256          | Password, Recovery Key, iCloud | ✅ (Secure Enclave) | N/A                | [filevault.md](platforms/macos/filevault.md) |
| **Linux (General)**      |              |                |                      |                  |                             |                   |                         |                   |
| LUKS2 + dm-crypt         | Kernel 3.x+  | ❌             | ✅ (installer)       | AES-XTS-plain64  | Passphrase, Key file, TPM   | ✅ (systemd-cryptenroll) | ✅ (32-bit capable) | [luks-dmcrypt.md](platforms/linux/luks-dmcrypt.md) |
| **Debian**               |              |                |                      |                  |                             |                   |                         |                   |
| Debian 11 (Bullseye)     | 11.x         | ❌             | ✅ guided partitioner| AES-XTS-plain64  | Passphrase                  | ⚠️               | ✅                       | [distros/debian.md](distros/debian.md) |
| Debian 12 (Bookworm)     | 12.x         | ❌             | ✅                   | AES-XTS-plain64  | Passphrase, TPM (manual)    | ⚠️               | ✅                       | [distros/debian.md](distros/debian.md) |
| **Ubuntu**               |              |                |                      |                  |                             |                   |                         |                   |
| Ubuntu 22.04 LTS         | 22.04        | ❌             | ✅ installer opt-in  | AES-XTS-plain64  | Passphrase, Recovery Key    | ⚠️               | ❌ (amd64/arm64)         | [distros/ubuntu.md](distros/ubuntu.md) |
| Ubuntu 24.04 LTS         | 24.04        | ❌             | ✅ installer opt-in  | AES-XTS-plain64  | Passphrase, TPM             | ✅               | ❌                       | [distros/ubuntu.md](distros/ubuntu.md) |
| **Linux Mint**           |              |                |                      |                  |                             |                   |                         |                   |
| Linux Mint 21.x          | 21.x         | ❌             | ✅ (via Ubiquity)    | AES-XTS-plain64  | Passphrase                  | ⚠️               | ❌                       | [distros/linux-mint.md](distros/linux-mint.md) |
| **Zorin OS**             |              |                |                      |                  |                             |                   |                         |                   |
| Zorin OS 16/17           | 16–17        | ❌             | ✅                   | AES-XTS-plain64  | Passphrase                  | ⚠️               | ❌                       | [distros/zorin-os.md](distros/zorin-os.md) |
| **Tails**                |              |                |                      |                  |                             |                   |                         |                   |
| Tails 5.x / 6.x          | 5+           | ✅ (Persistent) | ✅ (Persistent Stor.) | LUKS2 AES-XTS  | Passphrase                  | ❌ (amnesic by design) | ❌                | [distros/tails.md](distros/tails.md) |
| **Fedora**               |              |                |                      |                  |                             |                   |                         |                   |
| Fedora 38–40             | 38–40        | ❌             | ✅ Anaconda opt-in   | AES-XTS-plain64  | Passphrase, TPM             | ✅               | ❌ (x86_64/aarch64)      | [distros/fedora.md](distros/fedora.md) |
| **RHEL / Red Hat**       |              |                |                      |                  |                             |                   |                         |                   |
| RHEL 8 / 9               | 8.x, 9.x     | ❌             | ✅ Anaconda opt-in   | AES-XTS-plain64  | Passphrase, TPM, Tang/Clevis | ✅              | ❌                       | [distros/rhel.md](distros/rhel.md) |
| **Manjaro**              |              |                |                      |                  |                             |                   |                         |                   |
| Manjaro (Calamares)      | current      | ❌             | ✅ Calamares opt-in  | AES-XTS-plain64  | Passphrase                  | ⚠️               | ❌                       | [distros/manjaro.md](distros/manjaro.md) |
| **Coral Linux**          | ?            | ?              | ?                    | ?                | ?                           | ?                 | ?                       | [distros/unknown-coral-linux.md](distros/unknown-coral-linux.md) |

---

## Notes

- "FDE by Default" means enabled without user intervention on a fresh install.
- "Installer FDE Option" means the official installer offers FDE as an opt-in or opt-out choice.
- "32-bit Supported" refers to i386/i686 architecture support for the distro's FDE stack.
- TPM columns refer to automated/transparent unlock (no passphrase prompt at boot).
- All version numbers and cipher defaults should be verified against official release notes.

---

## Updating This Matrix

1. Verify the source and record provenance using [`_source_record_template.md`](_source_record_template.md).
2. Update the relevant cell with the verified value and symbol.
3. Add a footnote row if caveats are complex.
4. Commit with a message referencing the source (e.g., `matrix: update Ubuntu 24.04 TPM support [verified YYYY-MM-DD]`).
