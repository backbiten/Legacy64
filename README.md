# Legacy64

> **Preserving 64-bit hardware and software for future generations.**

AMD64 (x86-64) marked a turning point in computing — bringing 64-bit addressing to mainstream desktop and server hardware. This project documents that era and keeps its software alive.

---

## Table of Contents

- [Background](#background)
- [Hardware](#hardware)
  - [AMD64 CPUs](#amd64-cpus)
  - [Intel EM64T CPUs](#intel-em64t-cpus)
  - [Chipsets & Motherboards](#chipsets--motherboards)
- [Software](#software)
  - [Operating Systems](#operating-systems)
  - [Compilers & Toolchains](#compilers--toolchains)
  - [Emulators & Virtual Machines](#emulators--virtual-machines)
- [Preservation Resources](#preservation-resources)
- [Contributing](#contributing)
- [License](#license)

---

## Background

In the early 2000s, AMD introduced the AMD64 architecture (also called x86-64), extending the classic IA-32 (x86) instruction set to 64-bit addressing and registers. This allowed programs to address more than 4 GB of RAM and use wider general-purpose registers, delivering significant performance improvements for many workloads.

Intel later adopted the same instruction set under the name **EM64T** (Extended Memory 64 Technology) and subsequently **Intel 64**.

This repository exists because legacy 64-bit systems — both hardware and software — are at risk of being lost as vendors drop support, binaries rot, and documentation disappears. We collect, document, and where possible mirror software so that this slice of computing history can be studied and run.

---

## Hardware

### AMD64 CPUs

| Processor | Family | Release Year | Socket | Notes |
|-----------|--------|-------------|--------|-------|
| AMD Opteron (Model 140–148) | K8 | 2003 | Socket 940 | First AMD64 server CPU |
| AMD Athlon 64 (ClawHammer) | K8 | 2003 | Socket 754 / 939 | First AMD64 desktop CPU |
| AMD Athlon 64 X2 (Toledo / Manchester) | K8 | 2005 | Socket 939 / AM2 | First AMD dual-core 64-bit |
| AMD Sempron 64 | K8 | 2004 | Socket 754 / 939 | Budget AMD64 |
| AMD Turion 64 | K8 | 2005 | Socket 754 | Mobile AMD64 |
| AMD Phenom / Phenom II | K10 | 2007–2008 | AM2+ / AM3 | Multi-core follow-on |

### Intel EM64T CPUs

| Processor | Family | Release Year | Socket | Notes |
|-----------|--------|-------------|--------|-------|
| Intel Pentium 4 (Prescott F) | NetBurst | 2004 | LGA775 | First Intel 64-bit desktop CPU |
| Intel Xeon (Nocona) | NetBurst | 2004 | LGA604 | First Intel 64-bit server CPU |
| Intel Core 2 Duo / Quad | Core | 2006–2007 | LGA775 | 64-bit + improved microarchitecture |
| Intel Core i7 (Nehalem) | Nehalem | 2008 | LGA1366 | Integrated memory controller |

### Chipsets & Motherboards

| Chipset | Vendor | Compatible CPUs | Notes |
|---------|--------|-----------------|-------|
| nForce3 / nForce4 | NVIDIA | Athlon 64, Opteron (Socket 939/940) | Popular enthusiast boards |
| AMD 8000 series (8111/8131) | AMD | Opteron | Server-grade |
| VIA K8T800 | VIA | Athlon 64 | Affordable alternative |
| Intel 925X / 915 | Intel | Pentium 4 EM64T | Early Intel 64-bit platform |
| Intel P35 / X38 | Intel | Core 2 Duo/Quad | Popular mid-range boards |

---

## Software

### Operating Systems

| OS | Version | Architecture | Notes |
|----|---------|-------------|-------|
| Linux (kernel 2.6.x) | 2.6.0+ | x86-64 | Full 64-bit support from early 2.6 series |
| Debian GNU/Linux | 3.1 (Sarge) | amd64 | First official Debian amd64 release (2005) |
| Ubuntu | 6.06 LTS | amd64 | Early long-term-support 64-bit desktop/server |
| Fedora Core | 4+ | x86-64 | Early RPM-based 64-bit distro |
| FreeBSD | 5.3+ | amd64 | First stable 64-bit FreeBSD |
| Windows XP x64 Edition | 2003 SP1 kernel | x86-64 | First mainstream Windows 64-bit desktop |
| Windows Server 2003 x64 | SP1+ | x86-64 | Server counterpart |
| Solaris 10 | 2005 | amd64 | Sun/Oracle Solaris on AMD64 |

### Compilers & Toolchains

| Tool | Version | Notes |
|------|---------|-------|
| GCC | 3.4 / 4.x | First well-supported AMD64 backend in 3.4 |
| binutils | 2.15+ | Assembler/linker for x86-64 ELF |
| NASM | 0.98+ | Flat assembler supporting 64-bit output |
| Microsoft Visual C++ | 2003 (7.1) / 2005 | First MSVC with AMD64/EM64T target |
| ICC (Intel C++ Compiler) | 8.x+ | Optimised code generation for Intel 64-bit |
| clang/LLVM | 2.0+ | Early LLVM 64-bit support |

### Emulators & Virtual Machines

| Software | Notes |
|----------|-------|
| QEMU | Full-system emulation; can emulate x86-64 on any host |
| VirtualBox | Type-2 hypervisor; supports 64-bit guests on 64-bit hosts |
| VMware Workstation | Commercial; solid AMD64 guest support since version 5 |
| Bochs | Pure software x86/x86-64 emulator; useful for low-level debugging |

---

## Preservation Resources

- **Internet Archive** — [archive.org](https://archive.org) hosts old OS ISOs, installers, and documentation.
- **WinWorld** — [winworldpc.com](https://winworldpc.com) collects abandonware OS images including early x64 Windows.
- **OldVersion.com** — Historic software versions for download.
- **Linux Kernel Archives** — [kernel.org](https://kernel.org/pub/) keeps every kernel release since 1.0.
- **FreeBSD FTP mirrors** — Historical releases at `ftp.freebsd.org/pub/FreeBSD/releases/`
- **Debian Archives** — [archive.debian.org](https://archive.debian.org) hosts every Debian release.
- **BIOS/Firmware dumps** — Communities such as [BIOS-Mods.com](https://www.bios-mods.com) preserve motherboard firmware.

---

## Contributing

Contributions of any size are welcome. You can help by:

1. **Adding hardware entries** — If you have accurate data about a 64-bit CPU, chipset, or board that isn't listed, open a PR.
2. **Adding software entries** — Document an OS, compiler, or tool that belongs in this list.
3. **Linking archived copies** — Point to verified archive.org or other mirrors for software listed here.
4. **Fixing inaccuracies** — Release years, socket names, chipset details — corrections are appreciated.

Please keep entries factual and cite sources where possible. Open an issue to discuss larger changes before investing significant effort.

---

## License

The documentation in this repository is released under the [Creative Commons CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) public domain dedication — use it freely.
