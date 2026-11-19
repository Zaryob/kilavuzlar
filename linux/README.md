---
translation_key: guide-linux-README
lang: tr
title: "Linux"
permalink: /linux/
nav_order: 4
redirect_from:
  - /linux/README.html
---

# Linux

Sistem yönetimi, çekirdek araçları ve performans profilleme kılavuzları.

1. [LVM bölümünü veri kaybetmeden büyütmek](lvm-bolumunu-buyutmek.md): lsblk, pvresize, lvextend ve resize2fs ile çevrimiçi disk genişletme.
2. [perf ile CPU darboğazı bulmak](perf-ile-cpu-darbogazi.md): Profilleme, çağrı grafikleri ve flame graph analizi.
3. [NVIDIA Jetson Orin Nano üzerinde OpenClaw kurulumu](jetson-orin-nano-openclaw-kurulumu.md): 8 GB ARM64 ortamında Ollama, Qwen 3.5 2B ve sistem servisleri ile yerel yapay zeka asistanı.
4. [Ubuntu çekirdek yapılandırmaları](ubuntu-kernel-konfigurasyonlari.md): generic, lowlatency ve HWE çekirdeklerinin mimarisi, kurulumu ve GRUB yönetimi.
5. [Linux thread scheduling yapısı](thread-scheduling-yapisi.md): 1:1 NPTL modeli, sched_class, CFS/EEVDF vruntime hesabı, bağlam değişimi ve SMP yük dengeleme.
6. [Headless sistemlerde çekirdek değişimi](headless-kernel-degisimi.md): grub-reboot ile bir sonraki açılışta tek seferlik generic, lowlatency ve HWE geçişi, panic ve recordfail güvenlik ayarları.
