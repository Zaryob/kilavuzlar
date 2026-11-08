---
translation_key: guide-sanallastirma-macos-linux-usbip
lang: tr
title: "macOS'ta Linux USB/IP altyapısını test etmek"
permalink: /sanallastirma/macos-linux-usbip/
status: duzenlendi
reviewed: 2026-11-09
scope: macOS üzerinde vhci_hcd kısıtları, QEMU USB passthrough (-device usb-host) ve Linux VM'leri arasında USB/IP testi.
---

# macOS’ta Linux USB/IP altyapısını test etmek

Linux USB/IP, TCP 3240 üzerinden sunucuda `usbip-host`, istemcide `vhci-hcd` modüllerini kullanır. Bu Linux çekirdek modülleri Darwin’de çalışmaz. Kılavuz iki Linux VM kullanır; bütün üçüncü taraf macOS USB/IP uygulamaları veya DriverKit yetenekleri hakkında mutlak bir iddia kurmaz.

## 1. Önyüklenebilir iki VM hazırlama

Apple Silicon Mac üzerinde QEMU/HVF ve Ubuntu 24.04 ARM64 bulut imajı gerekir. Aşağıdaki komutlar macOS’ta yeni bir laboratuvar dizininde çalışır. İmaj URL’si değişkendir; çalıştırma tarihinizi ve hash’ini kaydedin.

```bash
brew install qemu libusb
mkdir usbip-lab
cd usbip-lab
curl -fLO https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img
shasum -a 256 noble-server-cloudimg-arm64.img
```

Kurulum ayrı disk katmanları, cloud-init seed’leri ve yazılabilir UEFI değişken depoları üretir. İki VM aynı yazılabilir vars dosyasını paylaşmamalıdır. Özel SSH anahtarını yerelde tutun. `bash prepare.sh` komutunu bir kez çalıştırın:

```bash
set -eu
QEMU_SHARE="$(brew --prefix qemu)/share/qemu"
test -f "$QEMU_SHARE/edk2-aarch64-code.fd"
test -f "$QEMU_SHARE/edk2-arm-vars.fd"
# Run once in a new lab directory; keep each VM's state on subsequent boots.
ssh-keygen -t ed25519 -N "" -f lab_ed25519
for vm in server client; do
    qemu-img create -f qcow2 -F qcow2 \
        -b "$PWD/noble-server-cloudimg-arm64.img" "$vm.qcow2" 12G
    cp "$QEMU_SHARE/edk2-arm-vars.fd" "$vm-vars.fd"
    mkdir "seed-$vm"
    cat > "seed-$vm/meta-data" <<EOF
instance-id: kilavuzlar-$vm
local-hostname: $vm
EOF
    cat > "seed-$vm/user-data" <<EOF
#cloud-config
users:
  - default
ssh_authorized_keys:
  - $(cat lab_ed25519.pub)
ssh_pwauth: false
EOF
    hdiutil makehybrid -o "seed-$vm.iso" -iso -joliet \
        -default-volume-name cidata "seed-$vm"
done
```
{: data-filename="prepare.sh"}

## 2. İki VM’yi başlatıp boot kaydı alma

VM’ler ayrı user-mode ağlarda, normalde aynı `10.0.2.15` konuk adresini alır; ortak LAN üzerinde değildir. İstemcide `10.0.2.2:33240`, ana makinenin loopback yönlendirmesi üzerinden sunucuya ulaşır. Konuk sunucu 3240’ı dinler; host portu 33240 yerel çakışmayı azaltmak için seçilmiştir. SSH yönlendirmeleri de yalnız host loopback adresine bağlıdır.

```bash
set -eu
QEMU_SHARE="$(brew --prefix qemu)/share/qemu"
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive if=pflash,format=raw,readonly=on,file="$QEMU_SHARE/edk2-aarch64-code.fd" \
    -drive if=pflash,format=raw,file=server-vars.fd \
    -drive file=server.qcow2,if=virtio,format=qcow2 \
    -drive file=seed-server.iso,if=virtio,format=raw,readonly=on \
    -netdev user,id=net0,hostfwd=tcp:127.0.0.1:33240-:3240,hostfwd=tcp:127.0.0.1:2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -device qemu-xhci,id=xhci \
    -nographic
```
{: data-filename="start-server.sh"}


```bash
set -eu
QEMU_SHARE="$(brew --prefix qemu)/share/qemu"
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive if=pflash,format=raw,readonly=on,file="$QEMU_SHARE/edk2-aarch64-code.fd" \
    -drive if=pflash,format=raw,file=client-vars.fd \
    -drive file=client.qcow2,if=virtio,format=qcow2 \
    -drive file=seed-client.iso,if=virtio,format=raw,readonly=on \
    -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2223-:22 \
    -device virtio-net-pci,netdev=net0 \
    -nographic
```
{: data-filename="start-client.sh"}


```bash
bash start-server.sh > server-boot.log 2>&1 &
bash start-client.sh > client-boot.log 2>&1 &
# Wait for cloud-init/SSH to become ready on each VM.
ssh -i ./lab_ed25519 -p 2222 ubuntu@127.0.0.1 'cloud-init status --wait; uname -a; ip -4 addr'
ssh -i ./lab_ed25519 -p 2223 ubuntu@127.0.0.1 'cloud-init status --wait; uname -a; ip -4 addr'
```

QEMU sürecinin başlaması Ubuntu’nun boot ettiğini kanıtlamaz; `server-boot.log` ve `client-boot.log` dosyalarını saklayın. Yalnız yazılımsal USB testi için `qemu-img create -f raw test_disk.raw 64M` ile boş disk oluşturup sunucu komutuna boot öncesi `-drive file=test_disk.raw,if=none,id=u1,format=raw -device usb-storage,drive=u1` ekleyebilirsiniz. Bu, fiziksel passthrough doğrulaması değildir.

## 3. Fiziksel USB passthrough (donanım gerekir)

Gerçek üretici/ürün kimliklerini `system_profiler SPUSBDataType` ile bulun. Sunucu kapalıyken QEMU komutuna aşağıdaki seçeneği ekleyin (kimlikler yalnız FTDI örneğidir):

```text
-device usb-host,vendorid=0x0403,productid=0x6001
```

Aygıt macOS sürücüsü tarafından tutuluyor olabilir; libusb erişimi, sürücünün bırakması ve izinler gerçek aygıtla sınanmalıdır. QEMU’nun seçeneği kabul etmesi USB aktarım başarısı değildir.

## 4. Sunucuda paylaşma (VM 1)

Sunucu VM içinde çalıştırın. Çalışan çekirdekle eşleşen araçlar gerekir; bazı imajlarda ayrıca `linux-modules-extra-$(uname -r)` gerekir. Eşleşen paket bulunmazsa desteklenen generic çekirdeği kurup önce yeniden başlatın.

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic "linux-tools-$(uname -r)" "linux-modules-extra-$(uname -r)" usbutils
sudo modprobe usbip-host
sudo usbipd -D
usbip list -l
# Replace 1-1 with the actual busid listed above.
sudo usbip bind -b 1-1
```

## 5. İstemcide bağlama (VM 2)

İstemci VM içinde çalıştırın. Paylaşılan gerçek busid’yi kullanın; bu kalıcı aygıt kimliği değildir:

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic "linux-tools-$(uname -r)" "linux-modules-extra-$(uname -r)" usbutils
sudo modprobe vhci-hcd
usbip --tcp-port 33240 list -r 10.0.2.2
sudo usbip --tcp-port 33240 attach -r 10.0.2.2 -b 1-1
# USB enumeration is asynchronous; wait for the expected device to appear.
sudo udevadm settle
lsusb
sudo usbip port
sudo dmesg | tail -n 10
```

Fiziksel FTDI kabulü istemcide doğru VID:PID, seri aygıt oluşması ve gerçek seri veri aktarımı gerektirir; yalnız `lsusb` yeterli değildir. Sanal disk testinde mass-storage aygıtı beklenir, `/dev/ttyUSB0` değil. PCI/xHCI sysfs yolları ve bus numaraları değişir.

## 6. Ayırma ve kapatma

```bash
# Client: replace 00 with the port shown by sudo usbip port.
sudo usbip detach -p 00
# Server: use the actual exported busid.
sudo usbip unbind -b 1-1
```


```bash
# macOS: shut down each guest cleanly, retaining overlays and vars files.
ssh -i ./lab_ed25519 -p 2223 ubuntu@127.0.0.1 'sudo poweroff'
ssh -i ./lab_ed25519 -p 2222 ubuntu@127.0.0.1 'sudo poweroff'
```

## Kaynaklar ve doğrulama kapsamı

- [QEMU virt firmware](https://www.qemu.org/docs/master/system/arm/virt.html)
- [QEMU user-mode networking](https://www.qemu.org/docs/master/system/devices/net.html)
- [QEMU USB passthrough](https://www.qemu.org/docs/master/system/devices/usb.html)
- [Linux USB/IP protocol](https://docs.kernel.org/usb/usbip_protocol.html)
- [Ubuntu ARM64 cloud images](https://cloud-images.ubuntu.com/noble/current/)

8–9 Kasım 2026: QEMU 11.1.3/HVF üzerinde iki Ubuntu ARM64 konuk ayrı UEFI vars dosyalarıyla boot edildi ve ağ yolu kontrol edildi. Sanal 64 MiB USB diskin bind/list/attach, istemcide yazma-okuma ve detach/unbind adımları da çalıştırıldı. Fiziksel USB passthrough ve FTDI veri aktarımı **doğrulanmadı**. Bu koşu veya sanal USB disk testi fiziksel donanım kabulü oluşturmaz.
