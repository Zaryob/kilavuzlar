---
translation_key: guide-docker-usb-aygit-erisimi
lang: tr
title: "Docker'da USB aygıt erişimi neden başarısız olur?"
permalink: /docker/usb-aygit-erisimi/
status: duzenlendi
reviewed: 2026-11-03
scope: Linux, macOS ve Windows (WSL2) üzerinde Docker aygıt eşleme (device mapping), cgroup kuralları ve çekirdek modülü kısıtlamaları.
---

# Docker'da USB aygıt erişimi neden başarısız olur?

Gömülü sistemler, IoT, robotik veya donanım geliştirme alanında çalışan mühendisler;
mikrodenetleyicileri (Arduino, STM32, ESP32) veya USB-Seri dönüştürücüleri (FTDI, CH340, CP2102)
Docker konteyneri içinde programlamaya çalıştıklarında sık sık erişim hatalarıyla karşılaşırlar.

Bu hataların temelinde üç ana etken yatar:
1. İşletim sistemi ve hipervizör katmanının USB veriyolunu izole etmesi (özellikle macOS ve Windows'ta).
2. Linux çekirdeğinin cgroup (Control Group) aygıt denetleyicisi ve konteyner dosya sistemi tecridi.
3. Donanımı süren çekirdek modüllerinin (kernel modules) konteyner içinde değil, ana makinede bulunması zorunluluğu.

## 1. Ana makine mimarisi kısıtlamaları: Linux vs macOS vs Windows

Docker konteynerleri sanal makine değildir; ana makinenin çekirdeğini paylaşırlar. Bu kural
işletim sistemlerine göre büyük farklılıklar doğurur:

### Yerel Linux Motoru

Doğrudan ana makinenin Linux çekirdeği çalışır. Çekirdeğin oluşturduğu aygıt düğümleri
(`/dev/ttyUSB0`, `/dev/bus/usb/...`), dosya sistemi bağlamaları ve cgroup izinleri ile
doğrudan konteynere aktarılabilir.

### macOS Üzerinde Docker Desktop

macOS'un çekirdeği XNU'dur (Darwin). Docker Desktop, macOS üzerinde Apple'ın
`Virtualization.framework` altyapısını kullanarak hafif bir **Linux Sanal Makinesi (VM)**
çalıştırır.

- **Sorun:** macOS hipervizör katmanı, Mac'in USB-C/Thunderbolt girişine takılan fiziksel USB aygıtlarını Linux sanal makinesine **doğrudan aktarmaz (passthrough yapmaz)**.
- macOS çekirdeği (IOKit) aygıtı kendisi sahiplenir. Linux VM'i ve dolayısıyla Docker konteyneri donanımı göremez.
- **Çözüm:** macOS üzerinde doğrudan `docker run --device` çalışmaz. Seri portlar için `socat` ile ağ köprüsü kurulmalı ya da bir Linux VM üzerinden **USB/IP** kullanılmalıdır.

### Windows Üzerinde Docker Desktop (WSL2)

Docker Desktop Windows'ta WSL2 (Windows Subsystem for Linux 2) sanal makinesinde çalışır.
Hyper-V mimarisi WSL2'ye varsayılan olarak USB iletimi sağlamaz.

- **Çözüm:** Microsoft'un resmi açık kaynaklı aracı **`usbipd-win`** kullanılmalıdır. Windows tarafında `usbipd bind` ve `usbipd attach --wsl` komutlarıyla USB aygıtı WSL2 çekirdeğine iliştirilir.

## 2. Aygıt eşleme ve güvenlik: `--device` vs `--privileged` vs cgroups

Linux üzerinde bir konteynerin aygıta erişebilmesi için çekirdek iki seviyede izin arar:
1. Konteynerin `/dev` dizininde o aygıta ait bir düğüm (`mknod` ile açılmış karakter/blok aygıtı).
2. Çekirdeğin cgroups (Control Groups) aygıt filtresinde o aygıtın `major:minor` numarasına okuma/yazma izni.

### `--device=/dev/ttyUSB0` (Statik eşleme)

Konteyner başlatılırken belirtilen aygıtın `major:minor` numarasını okur, konteyner içinde
aynı isimle bir düğüm oluşturur ve cgroup listesine izin ekler.
- **Kısıt:** Aygıtın konteyner çalıştırıldığı anda bilgisayara takılı olması şarttır.

### `--privileged` tehlikesi (Antipattern)

İnternetteki birçok rehber USB sorunlarını aşmak için `--privileged` bayrağını önerir.
Bu bayrak konteyner tecridini tamamen kaldırır:
- Konteynere `CAP_SYS_ADMIN` ve tüm çekirdek yetkilerini verir.
- cgroup filtresini `a *:* rwm` (tüm disklere ve belleğe tam erişim) yapar.
- AppArmor ve Seccomp profillerini kapatır.

> [!CAUTION]
> `--privileged` ile çalışan bir konteyner içindeki zararlı bir kod veya güvenlik açığı,
> ana makinenin sabit disklerine (`/dev/sda`), UEFI değişkenlerine ve ana belleğe (`/dev/mem`)
> doğrudan erişebilir. USB erişimi için asla `--privileged` kullanılmamalıdır!

### Modern ve güvenli çözüm: `--device-cgroup-rule`

Konteynere tüm yetkileri vermeden, sadece belirli USB aygıt sınıflarına joker karakterle
(wildcard) izin verebilirsiniz:

```bash
docker run --rm -it \
  --device-cgroup-rule='c 188:* rmw' \
  --device-cgroup-rule='c 166:* rmw' \
  --device-cgroup-rule='c 189:* rmw' \
  -v /dev:/dev \
  ubuntu:24.04
```

#### Önemli Linux karakter aygıtı sınıfları (Major Numbers):
- `188`: USB-Seri dönüştürücüler (`/dev/ttyUSB*`)
- `166`: ACM modem ve geliştirme kartları (`/dev/ttyACM*`)
- `189`: Ham USB veriyolu (`/dev/bus/usb/*/*` - libusb/hidapi için)

## 3. Dinamik USB takıp çıkarma sorunu (udev Hotplug problemi)

Geliştiricilerin en çok şaşırdığı durum şudur: *Konteyner ilk açıldığında cihaza bağlanır,
ancak USB kablosu sökülüp tekrar takıldığında konteyner cihazı kaybeder ve yeniden
başlatılana kadar bağlanamaz.*

### Sorunun kök nedeni:

1. USB aygıtı çıkarılıp takıldığında Linux çekirdeği yeni bir düğüm açar ve aygıt numarası artar (örneğin `/dev/bus/usb/001/004` iken `001/005` olur). Seri portlarda ise dosya sistemindeki **inode** tamamen silinip yeniden üretilir.
2. Konteynerin `/dev` dizini izole bir `tmpfs` bağlamasıdır. Ana makinedeki `udevd` servisi yeni düğümü yalnızca ana makinenin `/dev` dizininde açar; konteynerin mount namespace'i bu olaydan habersiz kalır.
3. `--device` ile bağlanan eski inode artık öksüz kalmıştır (`No such file or directory` veya `Input/output error`).

### Hotplug çözümü:

Dinamik aygıtları desteklemek için ana makinenin aygıt ağacı bir cilt olarak bağlanmalı
ve cgroup joker kuralı tanımlanmalıdır:

```bash
docker run --rm -it \
  --device-cgroup-rule='c 188:* rmw' \
  --device-cgroup-rule='c 166:* rmw' \
  -v /dev:/dev \
  my-embedded-app
```

## 4. Ana makine çekirdek sürücüsü (Kernel Module) eksikliği

Bir diğer yaygın yanılgı, aygıt sürücüsünün konteyner içine `apt-get install` ile
kurulabileceğinin sanılmasıdır.

- Konteynerler kendi çekirdeklerini çalıştırmazlar. Donanım sürücüleri (`.ko`) doğrudan çekirdeğe yüklenir.
- Konteyner içinden `modprobe` veya `insmod` çalıştırılamaz (`CAP_SYS_MODULE` kısıtlaması).
- Donanımı tanıyıp `/dev/ttyUSB0` düğümünü üreten sürücü **ana makinenin Linux çekirdeğinde** yüklü olmalıdır.

### Sık kullanılan çipler ve çekirdek modülleri:

- **`ch341`**: Yaygın Arduino klonları ve ESP8266 kartları (WCH CH340/CH341).
- **`cp210x`**: NodeMCU ve ESP32 geliştirme kartları (Silicon Labs CP2102).
- **`ftdi_sio`**: Endüstriyel seri dönüştürücüler ve JTAG programlayıcılar.
- **`cdc_acm`**: Orijinal Arduino Uno/Mega, Raspberry Pi Pico ve USB modemler.

### Ana makinede sürücü denetimi:

Aygıtı taktığınızda ana makinede çekirdek mesajlarını izleyin:

```bash
dmesg | tail -n 20
```

Beklenen sağlıklı çıktı örneği:

```text
usb 1-1: new full-speed USB device number 5 using xhci_hcd
ch341 1-1:1.0: ch341-uart converter detected
usb 1-1: ch341-uart converter now attached to ttyUSB0
```

Eğer yalnızca `new USB device found` yazıyor ancak `attached to tty...` satırı görünmüyorsa,
ana makinenizde ilgili sürücü modülü eksiktir (`sudo modprobe ch341` çalıştırılmalıdır).

## Sorun giderme matrisi

| Belirti / Hata | Kök Neden | Çözüm Yolu |
| :--- | :--- | :--- |
| macOS'ta aygıt hiç görünmüyor | Docker Desktop VM USB aktarımı yapmaz | USB/IP veya Linux VM köprüsü kullanın |
| Kablo sökülüp takılınca bağlantı kopuyor | udev hotplug konteynere yansımıyor | `-v /dev:/dev` ve `--device-cgroup-rule` kullanın |
| `Permission denied` (/dev/ttyUSB0) | Dialout grup izinleri eksik | `--group-add dialout` veya konteyneri root çalıştırın |
| `lsusb` var ama `/dev/ttyUSB0` yok | Ana makinede çekirdek sürücüsü eksik | Ana makinede `modprobe cp210x` / `ch341` yapın |

## Kaynaklar ve doğrulama ortamı

- [Linux Kernel Documentation - Devices and Cgroups](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Microsoft usbipd-win Deposu](https://github.com/dorssel/usbipd-win)
- [Docker Engine Device Specification](https://docs.docker.com/engine/reference/commandline/run/#device)

Bu kılavuz, Ubuntu 24.04 (Linux 6.8), macOS Sonoma (Docker Desktop 4.30) ve FTDI/CH340
donanımları üzerinde test edilerek doğrulanmıştır.
