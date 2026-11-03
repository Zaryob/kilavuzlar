---
translation_key: guide-sanallastirma-macos-linux-usbip
lang: tr
title: "macOS'ta Linux USB/IP altyapısını test etmek"
permalink: /sanallastirma/macos-linux-usbip/
status: duzenlendi
reviewed: 2026-11-03
scope: macOS üzerinde vhci_hcd kısıtları, QEMU USB passthrough (-device usb-host) ve Linux VM'leri arasında USB/IP testi.
---

# macOS'ta Linux USB/IP altyapısını test etmek

USB/IP protokolü, bir bilgisayara bağlı fiziksel USB aygıtlarını (kamera, seri dönüştürücü,
güvenlik dongle'ı) TCP/IP ağı üzerinden başka bir makineye yerel bir donanım gibi bağlamayı sağlar.

Gömülü sistemler ve bulut testleri için kritik olan bu altyapıyı macOS üzerinde yerel
olarak test etmeye çalışan mühendisler, macOS çekirdeğinin mimari engellerine çarpar.
Bu kılavuzda macOS'taki **`vhci_hcd` kısıtlamalarını** ve **QEMU sanallaştırması ile
eksiksiz bir USB/IP test laboratuvarının** nasıl kurulacağını ele alacağız.

## 1. Neden USB/IP macOS üzerinde yerel (Native) çalışamaz?

Linux ortamında USB/IP iki çekirdek modülü üzerinden yürütülür:

1. **`usbip-host.ko` (Sunucu / Stub Sürücüsü):** Fiziksel aygıtı Linux `usbcore` alt sisteminden ayırır (unbind) ve URB (**USB Request Block**) paketlerini TCP (port 3240) üzerinden ağa aktarır.
2. **`vhci-hcd.ko` (İstemci / Sanal Ana Bilgisayar Denetleyicisi):** İstemci tarafında sanal bir USB Host Controller (HCI) emüle eder. Ağdan gelen paketleri yerel çekirdeğe sanki anakarta bir USB aygıtı takılmış gibi sunar.

### macOS Çekirdek Engelleri:

- **Mimari Uyuşmazlığı:** macOS (Darwin/XNU), Linux'un `usbcore` veya `struct urb` yapılarını kullanmaz; Apple'ın I/O Kit ve DriverKit mimarisini kullanır. macOS'ta `vhci-hcd` veya `usbip-host` eşdeğeri bir çekirdek sürücüsü yoktur.
- **KEXT Deprecation ve Sistem Güvenliği:** Modern macOS sürümlerinde (Sonoma, Sequoia) üçüncü taraf çekirdek uzantıları (KEXT) kullanımdan kaldırılmıştır. Apple Silicon üzerinde KEXT yüklemek için makinenin "Reduced Security" moduna alınması gerekir.
- **DriverKit Sınırları:** Apple'ın sunduğu modern `USBDriverKit` API'si yalnızca spesifik kullanıcı seviyesi aygıt sürücülerine (örneğin özel bir USB kulaklık) izin verir; sanal bir USB Host Controller (HCI) oluşturmaya veya veri yolu paketlerini TCP'ye tünellemeye izin vermez.

Bu nedenlerle **macOS ne yerel bir USB/IP sunucusu ne de USB/IP istemcisi olabilir**.

## 2. Çözüm: QEMU ile macOS üzerinde USB/IP test mimarisi

macOS'un doğrudan USB/IP çalıştıramaması, Mac üzerinde bu altyapıyı geliştiremeyeceğimiz
anlamına gelmez. Standart çözüm, macOS üzerinde **QEMU ve sanal Linux makineleri** kullanmaktır:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                               macOS Host                                │
│                                                                         │
│  ┌───────────────────────────┐           ┌───────────────────────────┐  │
│  │    QEMU VM 1 (Sunucu)     │           │    QEMU VM 2 (İstemci)    │  │
│  │   (IP: 192.168.64.10)     │           │    (IP: 192.168.64.11)    │  │
│  │                           │           │                           │  │
│  │  ┌─────────────────────┐  │  TCP 3240 │  ┌─────────────────────┐  │  │
│  │  │ usbip-host.ko       │  │◄──────────┼──│ vhci-hcd.ko         │  │  │
│  │  │ usbipd servisi      │  │ (USB/IP)  │  │ usbip attach        │  │  │
│  │  └─────────────────────┘  │           │  └─────────────────────┘  │  │
│  │             ▲             │           │             │             │  │
│  │             │             │           │             ▼             │  │
│  │  [QEMU USB Passthrough]   │           │    [Sanal Kök Hub]        │  │
│  │  [-device usb-host]       │           │    [Görünen lsusb aygıtı] │  │
│  └─────────────┬─────────────┘           └───────────────────────────┘  │
└────────────────┼────────────────────────────────────────────────────────┘
                 ▼
     [Mac'e Takılı Fiziksel USB]
```

### QEMU USB Passthrough Mekanizması:

QEMU, macOS'in kullanıcı seviyesi `libusb` / IOKit arayüzünü kullanarak Mac'e takılı
gerçek bir USB aygıtını doğrudan sanal makinenin sanal USB veriyoluna (`-device usb-host`)
devredebilir. Böylece fiziksel aygıt Mac tarafından serbest bırakılır ve VM 1'in Linux çekirdeğine bağlanır.

## 3. Ön koşullar ve kurulum

Mac terminalinde QEMU ve libusb kütüphanelerini kurun:

```bash
brew install qemu libusb
```

Mac'inize takılı USB aygıtının Satıcı (Vendor) ve Ürün (Product) kimliklerini tespit edin:

```bash
system_profiler SPUSBDataType
```

Örnek çıktı:

```text
FT232R USB UART:
  Product ID: 0x6001
  Vendor ID: 0x0403  (Future Technology Devices International Limited)
```

## 4. QEMU Sanal Makinelerini Başlatma

### Sunucu Sanal Makinesi (VM 1):

Sunucu makinesine Mac'teki gerçek USB aygıtını passthrough ile bağlayın ve USB/IP portunu
(`3240`) dışarıya açın:

```bash
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive file=server.qcow2,if=virtio \
    -netdev user,id=net0,hostfwd=tcp::3240-:3240,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -device qemu-xhci,id=xhci \
    -device usb-host,vendorid=0x0403,productid=0x6001 \
    -nographic
```

*(Not: Eğer elinizde fiziksel USB donanımı yoksa, `-device usb-host` yerine QEMU'nun sanal USB diskini bağlayarak protokolü test edebilirsiniz: `-drive file=test_disk.raw,if=none,id=u1 -device usb-storage,drive=u1`)*

### İstemci Sanal Makinesi (VM 2):

İkinci terminalde istemci sanal makinesini başlatın:

```bash
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive file=client.qcow2,if=virtio \
    -netdev user,id=net0,hostfwd=tcp::2223-:22 \
    -device virtio-net-pci,netdev=net0 \
    -nographic
```

## 5. Sunucuda USB/IP yapılandırması (VM 1)

Sunucu Linux terminaline SSH ile bağlanın (`ssh -p 2222 ubuntu@localhost`):

### 1. Araçları kurun ve çekirdek modüllerini yükleyin:

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic linux-tools-$(uname -r) hwdata usbutils
sudo modprobe usbip-core
sudo modprobe usbip-host
```

### 2. USB/IP arka plan servisini (daemon) başlatın:

```bash
sudo usbipd -D
```

### 3. Yerel aygıtları listeleyin:

```bash
usbip list -l
```

Beklenen çıktı:

```text
 - busid 1-1 (0403:6001)
   Future Technology Devices International, Ltd : FT232 Serial (UART) IC (0403:6001)
```

### 4. Aygıtı USB/IP stub sürücüsüne bağlayın (bind):

```bash
sudo usbip bind -b 1-1
```

Aygıt artık yerel işletim sisteminden ayrılmış ve ağ üzerinden paylaşıma açılmıştır.

## 6. İstemcide USB/IP yapılandırması (VM 2)

İstemci Linux terminaline bağlanın (`ssh -p 2223 ubuntu@localhost`):

### 1. Araçları kurun ve `vhci-hcd` sanal denetleyicisini yükleyin:

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic linux-tools-$(uname -r) usbutils
sudo modprobe vhci-hcd
```

### 2. Sunucuda paylaşılan aygıtları sorgulayın:

```bash
usbip list -r 10.0.2.2
```

*(QEMU kullanıcı ağı varsayılanında ana makine ağ geçidi `10.0.2.2` adresindedir).*

Beklenen çıktı:

```text
Exportable USB devices
======================
 - 10.0.2.2
      1-1: Future Technology Devices International, Ltd : FT232 Serial (0403:6001)
         : /sys/devices/platform/xhci-hcd.0/usb1/1-1
         : (Defined at Interface level) (00/00/00)
```

### 3. Uzaktaki aygıtı yerel sanal denetleyiciye bağlayın (attach):

```bash
sudo usbip attach -r 10.0.2.2 -b 1-1
```

## 7. Doğrulama ve temiz ayırma

İstemci makinede `lsusb` çalıştırın:

```bash
lsusb
```

Beklenen çıktı:

```text
Bus 001 Device 002: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

`dmesg` çıktısında `vhci_hcd` sürücüsünün aygıtı tanıdığını ve `/dev/ttyUSB0` seri portunun
açıldığını görebilirsiniz:

```bash
dmesg | tail -n 10
```

Bağlantı durumunu kontrol etmek için:

```bash
usbip port
```

### Bağlantıyı kesme (Teardown):

İstemcide portu serbest bırakın:

```bash
sudo usbip detach -p 00
```

Sunucuda aygıtı yerel kullanıma geri döndürmek için:

```bash
sudo usbip unbind -b 1-1
```

## Pratik alternatif: Lima (`limactl`)

Komut satırından karmaşık QEMU parametreleriyle uğraşmak istemiyorsanız, macOS için geliştirilmiş
**Lima** aracı tek bir YAML dosyasıyla USB passthrough ve köprülenmiş Linux sanal makineleri
açmanıza imkan tanır.

## Kaynaklar ve doğrulama ortamı

- [Linux Kernel USB/IP Documentation](https://docs.kernel.org/usb/usbip_protocol.html)
- [QEMU USB Emulation & Passthrough Reference](https://www.qemu.org/docs/master/system/devices/usb.html)
- [Apple DriverKit USBDriverKit Reference](https://developer.apple.com/documentation/usbdriverkit)

Bu kılavuz, Apple Silicon Mac (macOS Sonoma 14.5) üzerinde QEMU 9.0 (`-device usb-host`),
Ubuntu 24.04 sanal makineleri ve FTDI USB-UART donanımı ile test edilmiştir.
