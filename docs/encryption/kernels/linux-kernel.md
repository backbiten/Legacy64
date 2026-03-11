# Linux Kernel — Crypto Subsystem (FDE Reference)

> Preservation reference — high-level overview for administrative/archival purposes.

---

## Overview

The Linux kernel provides a comprehensive cryptographic subsystem (`crypto/`) that underpins all
disk encryption operations. dm-crypt (and by extension LUKS) uses the kernel's crypto API to
perform bulk AES encryption/decryption on block I/O.

---

## Key Kernel Subsystems

| Subsystem | Location | Role |
|-----------|----------|------|
| `crypto/` | `crypto/` | Core crypto API: algorithms, templates, transforms |
| `drivers/md/dm-crypt.c` | `drivers/md/` | dm-crypt device-mapper target |
| `drivers/md/dm-integrity.c` | `drivers/md/` | Per-sector integrity (HMAC/AEAD) |
| `security/keys/` | `security/keys/` | Kernel keyring: key storage for LUKS tokens |
| `drivers/char/tpm/` | `drivers/char/tpm/` | TPM 1.2 and TPM 2.0 driver stack |

---

## Crypto API Architecture

```
userspace (cryptsetup / dm-crypt setup)
        │
[ /dev/mapper/<name>  — dm-crypt device-mapper target ]
        │  (submit_bio → crypt_convert → crypto API)
        │
[ Kernel Crypto API  (skcipher / aead / ahash) ]
        │
[ Algorithm implementations ]
  ├── Software: aes-generic, aes-ni-intel, chacha20-generic
  ├── SIMD-accelerated: aesni, vaes (AVX2/AVX512)
  ├── ARM: aes-arm64, aes-ce (Cortex-A crypto extensions)
  └── 32-bit: aes-i586, padlock-aes (VIA PadLock)
```

---

## Relevant Kernel Configs

```
CONFIG_DM_CRYPT=y           # dm-crypt block device
CONFIG_CRYPTO_AES=y         # AES generic implementation
CONFIG_CRYPTO_AES_NI_INTEL=y # AES-NI hardware acceleration (x86_64)
CONFIG_CRYPTO_XTS=y          # XTS mode (used by LUKS default)
CONFIG_CRYPTO_SHA256=y       # SHA-256 (PBKDF2 / Argon2 internal)
CONFIG_CRYPTO_ARGON2=y       # Argon2 PBKDF (kernel 5.17+)
CONFIG_KEYS=y                # Kernel keyring
CONFIG_TRUSTED_KEYS=y        # TPM-backed trusted keys
CONFIG_ENCRYPTED_KEYS=y      # Encrypted key type (AES-wrapped)
CONFIG_TCG_TPM=y             # TPM core driver
CONFIG_TCG_TIS=y             # TPM TIS/FIFO interface
CONFIG_TCG_CRB=y             # TPM CRB interface (TPM 2.0 most common)
```

---

## AES-NI and 32-bit

- **x86_64:** AES-NI (`aesni-intel` module) provides hardware AES in ~1 cycle per byte.
- **i386 (32-bit):** AES-NI assembly is not supported in 32-bit mode on most CPUs. Software AES
  (`aes-i586`) is used — functionally identical, ~10–20× slower on equivalent clock speeds.
- **VIA Padlock:** Some 32-bit VIA C3/C7 CPUs have hardware AES (`padlock-aes`); rare.

---

## Year 2038 and the Crypto Subsystem

The Linux kernel `time_t` / `ktime_t` widening effort addressed 32-bit time overflow:
- The kernel has been using `time64_t` internally since Linux 5.1 on most subsystems.
- The crypto subsystem itself does not rely heavily on `time_t`, but key expiry timestamps in
  userspace tools (cryptsetup, LUKS metadata) may use 32-bit time on 32-bit platforms.
- Verify: `cryptsetup luksDump` on a LUKS2 volume — the JSON metadata stores times as integers;
  check if the userspace library uses 32-bit or 64-bit for these fields on i386.

---

## Integrity Extensions (dm-integrity)

dm-integrity provides per-sector authentication tags (HMAC or AEAD), protecting against silent
data corruption and some replay attacks. Combined with dm-crypt:

```
dm-crypt (encryption) + dm-integrity (authentication) = LUKS2 with --integrity
```

This is more expensive (additional I/O for tags) but provides authenticated encryption.

---

## Official Documentation References

| Resource | URL (text reference) |
|----------|---------------------|
| kernel.org crypto API docs | `https://www.kernel.org/doc/html/latest/crypto/index.html` |
| dm-crypt kernel docs | `https://www.kernel.org/doc/html/latest/admin-guide/device-mapper/dm-crypt.html` |
| dm-integrity docs | `https://www.kernel.org/doc/html/latest/admin-guide/device-mapper/dm-integrity.html` |
| Kernel keyring docs | `https://www.kernel.org/doc/html/latest/security/keys/core.html` |
| Linux 5.1 time64 changes | `https://kernelnewbies.org/Linux_5.1` |

> Record provenance using [`../_source_record_template.md`](../_source_record_template.md).

---

## See Also

- [`../platforms/linux/luks-dmcrypt.md`](../platforms/linux/luks-dmcrypt.md)
- [`../platforms/linux/tpm.md`](../platforms/linux/tpm.md)
- [`../matrix.md`](../matrix.md)
