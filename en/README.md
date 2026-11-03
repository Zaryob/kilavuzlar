---
title: Guides
permalink: /en/
nav_order: 1
lang: en
translation_key: guide-README
translation_of: /
translated: '2026-11-03'
---

# Guides

Süleyman Poyraz’s notes on software development and system administration. Guides are organised by topic and maintenance status.

## Docker

- [Multi-architecture images](docker/coklu-mimari-imajlar.md): building for AMD64 and ARM64 with Buildx.
- [A static application with scratch](docker/scratch-ile-statik-uygulama.md): compiling C++ statically and running it in an empty base image.
- [Running GUI applications](docker/gui-uygulamasi-calistirmak.md): X11, Wayland, display sockets, GPU acceleration and permissions.
- [Building and testing C++](docker/cpp-derleme-ve-test.md): multi-stage builds, CMake, CTest and dependency caching.
- [Why USB access fails](docker/usb-aygit-erisimi.md): device mapping, kernel modules and host limitations.

## Linux

- [Expanding an LVM volume without losing data](linux/lvm-bolumunu-buyutmek.md): online disk expansion with lsblk, pvresize, lvextend and resize2fs.
- [Finding CPU bottlenecks with perf](linux/perf-ile-cpu-darbogazi.md): profiling, call graphs and flame graph analysis.

## C++

- [Creating a portable CMake project](cpp/tasinabilir-cmake-projesi.md): targets, CMakePresets, toolchains and build types.
- [Managing dependencies with vcpkg](cpp/vcpkg-bagimlilik-yonetimi.md): vcpkg.json manifest mode and modern CMake integration.
- [Migrating from GCC to Clang](cpp/gcc-clang-gecis-problemleri.md): standard libraries, linker compatibility and compiler diagnostics.
- [Profiling with Tracy](cpp/tracy-ile-profilleme.md): instrumentation and real-time frame/zone analysis.

## Emacs

- [Using CMake and LLDB in Emacs](emacs/cmake-ve-lldb.md): modern debugging with Eglot, project.el, compile and dape.

## Virtualisation

- [ARM64 Linux on Apple Silicon](sanallastirma/apple-silicon-arm64-linux.md): QEMU, HVF acceleration, guest images and architecture differences.
- [Testing Linux USB/IP on macOS](sanallastirma/macos-linux-usbip.md): vhci_hcd limitations, QEMU USB passthrough and virtual Linux networking.

## Vim

- [Vim key combinations](vim/vim-tus-kombinasyonlari.md): movement, editing, search, macros and window management.

## Archive

[Linux and image-processing notes](arsiv/README.md) are retained separately with their original content. Each document states its scope and what must be completed before reuse.

Archived installation commands should not be assumed to have been tested on a current system. Maintained documents also distinguish source review from practical testing.

## Contributing

See the [contribution guide](CONTRIBUTING.md) for document and maintenance rules, and the [maintenance notes](BAKIM.md) for the most recent recorded review findings.
