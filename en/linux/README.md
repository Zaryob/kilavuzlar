---
title: Linux
permalink: /en/linux/
nav_order: 4
lang: en
translation_key: guide-linux-README
translation_of: /linux/
translated: '2026-11-03'
---

# Linux

System administration, kernel tools and performance-profiling guides.

1. [Expanding an LVM volume without losing data](lvm-bolumunu-buyutmek.md): online expansion with lsblk, pvresize, lvextend and resize2fs.
2. [Finding CPU bottlenecks with perf](perf-ile-cpu-darbogazi.md): profiling, call graphs and flame graph analysis.
3. [Installing OpenClaw on NVIDIA Jetson Orin Nano](jetson-orin-nano-openclaw-kurulumu.md): local AI assistant with Ollama, Qwen 3.5 2B, and system services in an 8 GB ARM64 environment.
4. [Ubuntu kernel configurations](ubuntu-kernel-konfigurasyonlari.md): generic, lowlatency, and HWE architectures, installation, and GRUB management.
5. [Linux thread scheduling architecture](thread-scheduling-yapisi.md): 1:1 NPTL model, sched_class hierarchy, CFS/EEVDF vruntime calculation, context switching, and SMP load balancing.
6. [Headless kernel switching](headless-kernel-degisimi.md): one-shot transition between generic, lowlatency, and HWE variants using grub-reboot, panic handling, and recordfail safety configurations.
