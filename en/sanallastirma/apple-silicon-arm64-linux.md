---
title: Virtualising ARM64 Linux on an Apple Silicon Mac
permalink: /en/sanallastirma/apple-silicon-arm64-linux/
status: duzenlendi
reviewed: 2026-11-03
scope: QEMU, Hypervisor.framework (HVF), EDK2 UEFI and Ubuntu ARM64 cloud-init on
  macOS Sonoma/Sequoia.
lang: en
translation_key: guide-sanallastirma-apple-silicon-arm64-linux
translation_of: /sanallastirma/apple-silicon-arm64-linux/
translated: '2026-11-03'
---

# Virtualising ARM64 Linux on an Apple Silicon Mac

Apple Silicon Macs (M1/M2/M3/M4) use ARM64 (AArch64). This allows ARM64 Linux guests to run with hardware virtualisation, avoiding the substantial overhead of x86 emulation.

This guide creates a headless ARM64 Ubuntu VM using open source **QEMU**, Apple’s **`Hypervisor.framework` (HVF)**, SSH access and automatic Cloud-Init configuration.

## 1. Architecture and HVF acceleration

On macOS, QEMU uses `Hypervisor.framework` through `-accel hvf`. Guest instructions execute directly on Apple Silicon cores rather than being emulated in software.

### Main QEMU options

- `-accel hvf`: enables Apple’s hypervisor API.
- `-cpu host`: exposes host ARM CPU capabilities to the guest.
- `-M virt,highmem=on,gic-version=3`: selects the standard ARM virtual machine model. `highmem=on` supports memory above 4 GB; `gic-version=3` enables the ARMv8 GICv3 interrupt controller.

## 2. Memory pages: 16 KB on macOS vs 4 KB on Linux

An architectural difference often confuses developers:

- **Host macOS / Darwin:** uses **16 KB** memory pages (`PAGE_SIZE = 16384`).
- **Standard Ubuntu/Debian ARM64 guest:** the kernels discussed here use **4 KB** pages (`CONFIG_ARM64_4K_PAGES=y`).

### Why this does not prevent virtualisation

ARMv8-A provides two-stage address translation:
1. **Stage 1 — guest kernel:** translates a Guest Virtual Address (GVA) to a Guest Physical Address (GPA), using the guest’s **4 KB** granularity.
2. **Stage 2 — HVF hypervisor:** translates the GPA to a Host Physical Address (HPA), using the hypervisor’s **16 KB** granularity.

The two stages can use different granule sizes. With guest memory correctly aligned to the host’s requirements, standard 4 KB Ubuntu images can run on Apple Silicon without a kernel patch.

## 3. Firmware: EDK2 ARM64 UEFI

The ARM64 setup does not use a legacy PC BIOS; it requires **UEFI**.

Homebrew’s QEMU package includes EDK2 firmware:
- Read-only code flash: `/opt/homebrew/share/qemu/edk2-aarch64-code.fd`
- Writable NVRAM template: `/opt/homebrew/share/qemu/edk2-arm-vars.fd`

Make a separate NVRAM copy for each VM so its UEFI boot order and settings persist.

## 4. Prerequisites and installation

Install QEMU using Homebrew in the macOS terminal:

```bash
brew install qemu
```

## 5. Guest image and Cloud-Init automation

Instead of working through an interactive installation ISO, use an official Ubuntu cloud image and Cloud-Init, as cloud providers do.

### Step 1: Create a working directory and download the image

```bash
mkdir -p ~/qemu-linux/cidata && cd ~/qemu-linux
curl -LO https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img
```

### Step 2: Create the virtual disk and UEFI NVRAM

```bash
# 25 GB boyutunda dinamik qcow2 diski oluştur
qemu-img create -f qcow2 -b noble-server-cloudimg-arm64.img -F qcow2 disk.qcow2 25G

# UEFI değişken şablonunu kopyala
cp /opt/homebrew/share/qemu/edk2-arm-vars.fd efi_vars.fd
```

### Step 3: Configure Cloud-Init

Create a NoCloud ISO to define the `ubuntu` username, example password `sifre123` and sudo access at first boot.

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

Build the ISO with macOS’s `hdiutil`:

```bash
hdiutil makehybrid -iso -joliet -default-volume-name cidata -o cloud-init.iso cidata/
```

## 6. VM startup script

Save the following command as `baslat.sh`:

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

### Options explained

- `-m 4G -smp 4`: allocates 4 GB RAM and four virtual CPUs.
- `virtio-blk-pci` and `virtio-net-pci`: paravirtualised disk and network devices.
- `hostfwd=tcp::2222-:22`: forwards Mac port `2222` to guest SSH port `22`.
- `-nographic`: uses the terminal’s serial console without opening a graphical window.

## 7. Start the VM and connect over SSH

Make the script executable and run it:

```bash
chmod +x baslat.sh
./baslat.sh
```

UEFI and Linux boot logs appear in the terminal. Cloud-Init should finish configuration after roughly 20 seconds.

Open another Mac terminal and connect over SSH:

```bash
ssh -p 2222 ubuntu@localhost
```

Enter the example password `sifre123`.

Check the guest kernel and architecture:

```bash
uname -a
getconf PAGESIZE
```

Expected output:

```text
Linux ubuntu-vm 6.8.0-31-generic #31-Ubuntu SMP PREEMPT_DYNAMIC arm64 aarch64 GNU/Linux
4096
```

To exit QEMU immediately, press `Ctrl + A` and then `x` in the serial-console terminal.

## Sources and verification environment

- [QEMU documentation — Arm system emulation](https://www.qemu.org/docs/master/system/target-arm.html)
- [Apple Hypervisor framework documentation](https://developer.apple.com/documentation/hypervisor)
- [Ubuntu cloud images](https://cloud-images.ubuntu.com/)

This guide was tested and verified on an Apple M2 Max Mac running macOS Sonoma 14.5, Homebrew QEMU 9.0.0 and an Ubuntu 24.04 ARM64 cloud image.
