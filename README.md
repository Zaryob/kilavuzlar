---
translation_key: guide-README
lang: tr
title: "Kılavuzlar"
permalink: /
nav_order: 1
redirect_from:
  - /README.html
  - /c/
  - /c/README.html
  - /python/
  - /python/README.html
  - /rpi/
  - /rpi/README.html
---

# Kılavuzlar

Süleyman Poyraz'ın yazılım geliştirme ve sistem yönetimi notları.
Kılavuzlar konuya ve bakım durumuna göre ayrılır.

## Docker

- [Çok mimarili imaj oluşturma](docker/coklu-mimari-imajlar.md): Buildx ile AMD64 ve ARM64 için derleme.
- [scratch ile statik uygulama](docker/scratch-ile-statik-uygulama.md): C++ uygulamasını derleyip boş taban imajda çalıştırma.
- [GUI uygulaması çalıştırmak](docker/gui-uygulamasi-calistirmak.md): X11, Wayland, display socket, GPU hızlandırma ve izinler.
- [C++ uygulaması derleyip test etmek](docker/cpp-derleme-ve-test.md): Multi-stage build, CMake, CTest ve dependency caching.
- [USB aygıt erişimi neden başarısız olur?](docker/usb-aygit-erisimi.md): Aygıt eşleme, çekirdek modülleri ve host kısıtlamaları.

## Linux

- [LVM bölümünü veri kaybetmeden büyütmek](linux/lvm-bolumunu-buyutmek.md): lsblk, pvresize, lvextend ve resize2fs ile çevrimiçi disk genişletme.
- [perf ile CPU darboğazı bulmak](linux/perf-ile-cpu-darbogazi.md): Profilleme, çağrı grafikleri ve flame graph analizi.

## C++

- [CMake ile taşınabilir C++ projesi oluşturmak](cpp/tasinabilir-cmake-projesi.md): Target tabanlı mimari, CMakePresets, toolchain ve build türleri.
- [vcpkg ile C++ bağımlılıklarını yönetmek](cpp/vcpkg-bagimlilik-yonetimi.md): Manifest modu (vcpkg.json) ve modern CMake entegrasyonu.
- [GCC'den Clang'e geçerken karşılaşılan problemler](cpp/gcc-clang-gecis-problemleri.md): Standart kütüphane farkları, linker uyumu ve derleyici katılığı.
- [Tracy ile C++ uygulamasını profillemek](cpp/tracy-ile-profilleme.md): Enstrümantasyon, frame ve zone analizi ile gerçek zamanlı inceleme.

## Emacs

- [Emacs ile CMake ve LLDB kullanmak](emacs/cmake-ve-lldb.md): Eglot, project.el, compile ve dape ile modern hata ayıklama.

## Sanallaştırma

- [Apple Silicon Mac üzerinde ARM64 Linux sanallaştırmak](sanallastirma/apple-silicon-arm64-linux.md): QEMU, HVF hızlandırma, guest imajı ve mimari farkları.
- [macOS'ta Linux USB/IP altyapısını test etmek](sanallastirma/macos-linux-usbip.md): vhci_hcd kısıtları, QEMU USB passthrough ve sanal Linux ağı.

## Vim

- [Tuş kombinasyonları](vim/vim-tus-kombinasyonlari.md): hareket, düzenleme, arama, makrolar ve pencere yönetimi.

## Arşiv

[Linux ve görüntü işleme notları](arsiv/README.md), özgün içerikleri korunarak
ayrı bir bölümde tutulur. Her belgenin başında kapsamı ve yeniden kullanılmadan
önce tamamlanması gereken işler yazılıdır.

Arşivdeki kurulum komutları güncel bir sistemde denenmiş kabul edilmemelidir.
Düzenlenmiş belgelerde de kaynak kontrolü ile uygulamalı test ayrı belirtilir.

## Bu depoya katkı

Yeni belge ekleme ve bakım kuralları için [katkı rehberine](CONTRIBUTING.md),
son incelemenin bulguları için [bakım notlarına](BAKIM.md) bakın.
