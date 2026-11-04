---
translation_key: guide-sanallastirma-apple-silicon-arm64-linux
lang: tr
title: "Apple Silicon Mac üzerinde ARM64 Linux sanallaştırmak"
permalink: /sanallastirma/apple-silicon-arm64-linux/
status: duzenlendi
reviewed: 2026-11-03
scope: macOS Sonoma/Sequoia üzerinde QEMU, Hypervisor.framework (HVF), EDK2 UEFI ve Ubuntu ARM64 cloud-init.
---

# Apple Silicon Mac üzerinde ARM64 Linux sanallaştırmak

Apple Silicon (M1/M2/M3/M4) işlemcili Mac bilgisayarlar, ARM64 (AArch64) mimarisine
dayanır. Bu mimari, x86 emülasyonunun yarattığı ağır performans kaybı olmadan, ARM64
Linux işletim sistemlerinin yerel donanım hızında çalıştırılmasına olanak tanır.

Bu kılavuzda Apple'ın yerel **`Hypervisor.framework` (HVF)** altyapısını kullanarak,
açık kaynaklı **QEMU** ile sıfırdan başsız (headless), SSH erişimli ve Cloud-Init
ile otomatik yapılandırılan bir ARM64 Ubuntu sanal makinesinin nasıl kurulacağını ele alacağız.

## 1. Mimari temeller ve donanım hızlandırma (HVF)

QEMU, macOS üzerinde donanım hızlandırması için Apple'ın `Hypervisor.framework` (`-accel hvf`)
katmanını kullanır. Böylece işlemci talimatları yazılımsal olarak taklit edilmez; doğrudan
Apple Silicon çekirdeklerinde çalıştırılır.

### Temel QEMU parametreleri:

- `-accel hvf`: Apple'ın hipervizör API'sini etkinleştirir.
- `-cpu host`: Ana makinenin ARM çekirdek yeteneklerini doğrudan sanal makineye aktarır.
- `-M virt,highmem=on,gic-version=3`: ARM sanallaştırma için standart anakart modeli. `highmem=on` 4 GB üzeri RAM adreslemesini sağlar. `gic-version=3`, ARMv8 donanımsal kesme denetleyicisini (GICv3) etkinleştirir.

## 2. Mimari fark: 16 KB (macOS) vs 4 KB (Linux) bellek sayfası bilmecesi

Apple Silicon ve Linux çekirdekleri arasında geliştiricilerin sıkça kafasını karıştıran
kritik bir mimari fark vardır:

- **Ana Makine (macOS / Darwin):** Belleği **16 KB** sayfa boyutuyla (`PAGE_SIZE = 16384`) yönetir.
- **Standart Linux Misafiri (Ubuntu/Debian ARM64):** Varsayılan çekirdekler **4 KB** sayfa boyutuyla (`CONFIG_ARM64_4K_PAGES=y`) derlenmiştir.

### Bu uyumsuzluk neden sanallaştırmada sorun yaratmaz?

ARMv8-A mimarisi iki aşamalı bir adres çevirisi (Two-Stage Address Translation) sunar:
1. **Aşama 1 (Stage 1 - Misafir Çekirdek):** Misafir Sanal Adresini (GVA) Misafir Fiziksel Adresine (GPA) çevirir. Linux çekirdeği bunu **4 KB** tanecikliğinde yönetir.
2. **Aşama 2 (Stage 2 - HVF Hipervizör):** Misafir Fiziksel Adresini (GPA) Ana Makine Fiziksel Adresine (HPA) çevirir. Apple'ın hipervizörü bunu **16 KB** tanecikliğinde yönetir.

ARM mimarisinde Aşama 1 ve Aşama 2 tanecik boyutları birbirinden tamamen bağımsızdır.
QEMU misafir belleğini 16 KB sınırlarına hizaladığı sürece, standart 4 KB Ubuntu imajları
Apple Silicon üzerinde hiçbir kernel yamasına gerek kalmadan mükemmel kararlılıkla çalışır.

## 3. Firmware: EDK2 ARM64 UEFI

ARM64 platformunda eski BIOS (Legacy PC BIOS) bulunmaz; sistemin başlaması için **UEFI** şarttır.

Homebrew ile kurulan QEMU paketinde gerekli EDK2 ikilileri yer alır:
- Kod (Read-Only Flash): `/opt/homebrew/share/qemu/edk2-aarch64-code.fd`
- Değişkenler (NVRAM / Read-Write Flash): `/opt/homebrew/share/qemu/edk2-arm-vars.fd`

NVRAM şablonu her sanal makine için yerel bir kopyaya alınmalıdır; böylece sanal makinenin
UEFI önyükleme sırası ve ayarları kalıcı olarak saklanır.

## 4. Ön koşullar ve kurulum

macOS terminalinde Homebrew ile QEMU'yu kurun:

```bash
brew install qemu
```

## 5. Misafir imajı ve Cloud-Init otomasyonu

İnteraktif kurulum ISO'larıyla (klavye seçimi, saat dilimi vb.) vakit kaybetmek yerine,
bulut sağlayıcılarının kullandığı resmi Ubuntu Cloud Image ve Cloud-Init kullanılır.

### 1. Adım: Çalışma dizini ve imaj indirme

```bash
mkdir -p ~/qemu-linux/cidata && cd ~/qemu-linux
curl -LO https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img
```

### 2. Adım: Sanal disk ve UEFI NVRAM oluşturma

```bash
# 25 GB boyutunda dinamik qcow2 diski oluştur
qemu-img create -f qcow2 -b noble-server-cloudimg-arm64.img -F qcow2 disk.qcow2 25G

# UEFI değişken şablonunu kopyala
cp /opt/homebrew/share/qemu/edk2-arm-vars.fd efi_vars.fd
```

### 3. Adım: Cloud-Init yapılandırması

Sanal makine açılır açılmaz kullanıcı adı (`ubuntu`), şifre (`sifre123`) ve sudo yetkilerini
otomatik tanımlamak için NoCloud ISO'su üretilir:

`cidata/user-data`:

```yaml
#cloud-config
password: sifre123
chpasswd: { expire: False }
ssh_pwauth: True
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: False
```

`cidata/meta-data`:

```yaml
instance-id: qemu-arm64-01
local-hostname: ubuntu-vm
```

macOS'in yerleşik `hdiutil` aracıyla ISO dosyasına dönüştürün:

```bash
hdiutil makehybrid -iso -joliet -default-volume-name cidata -o cloud-init.iso cidata/
```

## 6. Sanal makineyi başlatma betiği

Aşağıdaki başlatma komutunu `baslat.sh` adıyla kaydedin:

```bash
#!/usr/bin/env bash
exec qemu-system-aarch64 \
    -accel hvf \
    -cpu host \
    -M virt,highmem=on,gic-version=3 \
    -m 4G \
    -smp 4 \
    -drive if=pflash,format=raw,readonly=on,file=/opt/homebrew/share/qemu/edk2-aarch64-code.fd \
    -drive if=pflash,format=raw,file=efi_vars.fd \
    -device virtio-blk-pci,drive=hd0 \
    -drive if=none,id=hd0,file=disk.qcow2,format=qcow2 \
    -device virtio-blk-pci,drive=cloudinit \
    -drive if=none,id=cloudinit,file=cloud-init.iso,format=raw \
    -netdev user,id=net0,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -nographic
```
{: data-filename="baslat.sh"}

### Parametrelerin detayları:
- `-m 4G -smp 4`: 4 GB RAM ve 4 sanal CPU çekirdeği tahsis eder.
- `virtio-blk-pci` ve `virtio-net-pci`: Yüksek hızlı paravirtualized disk ve ağ sürücüleri.
- `hostfwd=tcp::2222-:22`: Mac üzerindeki `2222` portunu sanal makinenin SSH portuna (`22`) bağlar.
- `-nographic`: Grafik penceresi açmaz; seri konsolu doğrudan terminale bağlar.

## 7. Çalıştırma ve SSH bağlantısı

Betiğe çalıştırma izni verip başlatın:

```bash
chmod +x baslat.sh
./baslat.sh
```

Terminalde UEFI ve Linux açılış logları akacaktır. Yaklaşık 20 saniye sonra Cloud-Init
kurulumu tamamlar.

İkinci bir terminal açarak Mac'inizden sanal makineye SSH ile bağlanın:

```bash
ssh -p 2222 ubuntu@localhost
```

Şifre olarak `sifre123` girin.

Sanal makinede çekirdeği ve mimariyi doğrulayın:

```bash
uname -a
getconf PAGESIZE
```

Beklenen çıktı:

```text
Linux ubuntu-vm 6.8.0-31-generic #31-Ubuntu SMP PREEMPT_DYNAMIC arm64 aarch64 GNU/Linux
4096
```

Çıkmak için seri konsol terminalinde `Ctrl + A` tuşuna basıp ardından `x` harfine basmanız
QEMU'yu anında kapatacaktır.

## Kaynaklar ve doğrulama ortamı

- [QEMU Documentation - System Emulation for Arm](https://www.qemu.org/docs/master/system/target-arm.html)
- [Apple Developer Documentation - Hypervisor Framework](https://developer.apple.com/documentation/hypervisor)
- [Ubuntu Cloud Images Resmi Dağıtım Portalı](https://cloud-images.ubuntu.com/)

Bu kılavuz, Apple M2 Max işlemcili bir Mac (macOS Sonoma 14.5), Homebrew QEMU 9.0.0
ve Ubuntu 24.04 ARM64 Cloud Image ile test edilerek doğrulanmıştır.
