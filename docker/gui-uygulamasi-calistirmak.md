---
translation_key: guide-docker-gui-uygulamasi-calistirmak
lang: tr
title: "Docker içinde GUI uygulaması çalıştırmak"
permalink: /docker/gui-uygulamasi-calistirmak/
status: duzenlendi
reviewed: 2026-11-09
scope: Linux ortamında X11 ve Wayland görüntü sunucuları, GPU hızlandırma (/dev/dri) ve güvenli soket yetkilendirmesi.
---

# Docker içinde GUI uygulaması çalıştırmak

Docker konteynerleri doğası gereği arka plan servisleri ve konsol araçları için başsız
(headless) tasarlanmıştır. Ancak geliştirme ortamlarını izole etmek, eski kütüphanelere bağımlı
grafiksel araçları çalıştırmak veya GUI testlerini otomatikleştirmek için masaüstü
uygulamalarını (Qt, GTK, Electron) konteyner içinde çalıştırmak gerekebilir.

Bir konteynerin pencere açabilmesi için ana makinenin görüntü sunucusuyla (Display Server /
Compositor) iletişim kurması gerekir. Bu kılavuzda hem geleneksel **X11** hem de modern
**Wayland** ortamlarında güvenli, donanım hızlandırmalı (GPU) ve doğru izinlerle GUI
uygulaması çalıştırmayı ele alacağız.

## 1. X11 ile GUI uygulaması çalıştırma

X11 mimarisinde konteynerdeki uygulama **X istemcisi**, ana makinedeki grafik ortam ise
**X sunucusu** rolündedir.

### İletişim kanalı: Unix Domain Soketi

X11 sunucuları yerel bağlantılarda yüksek hız ve düşük gecikme için Unix domain soketlerini
kullanır. Bu soketler ana makinede `/tmp/.X11-unix/` dizininde bulunur:

- Soket yolu: `-v /tmp/.X11-unix:/tmp/.X11-unix:ro`
- Ekran numarası: `-e DISPLAY=$DISPLAY` (genellikle `:0`)

### Kimlik doğrulama: `xhost +` tehlikesi ve güvenli `XAUTHORITY`

#### Neden `xhost +` kullanılmamalıdır?
İnternetteki birçok rehber `xhost +local:docker` veya `xhost +` komutunu önerir.
Bu komut X11 erişim kontrolünü tamamen kapatır. X11 protokolünde istemciler arasında
tecrit olmadığı için, konteyner içindeki zararlı bir yazılım ana makinedeki diğer
pencerelerin klavye girdilerini dinleyebilir (keylogger), ekran görüntüsü alabilir veya
sahte giriş olayları (`XSendEvent`) üretebilir.

#### Güvenli yöntem: XAUTHORITY (MIT-MAGIC-COOKIE-1)
Güvenli yol, X sunucusunun ürettiği 16 baytlık gizli anahtarı (cookie) izole bir dosyaya
kopyalayarak konteynere vermektir.

Konteynerin rastgele hostname alması nedeniyle oluşabilecek kimlik doğrulama hatalarını
(`No protocol specified`) engellemek için adres ailesi `ffff` (FamilyWild - joker aile)
olarak ayarlanır:

```bash
# Güvenli geçici xauth dosyası oluşturma
XAUTH=/tmp/.docker.xauth
touch "$XAUTH"
xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "$XAUTH" nmerge -
chmod 600 "$XAUTH"
```

### MIT-SHM hataları ve IPC ad alanı

X11 uygulamaları yüksek çözünürlüklü görüntüleri soket üzerinden bayt bayt kopyalamak yerine
paylaşımlı bellek (`shmget`/`shmat`) ile aktarır. Konteyner izole bir IPC ad alanında
çalıştığında `BadShmAttach` veya `BadAccess` hatası vererek çöker.

**Çözüm:** Konteynere `--ipc=host` parametresi eklemektir.

### X11 Konteyner çalıştırma komutu

```bash
docker run --rm \
  -e DISPLAY="$DISPLAY" \
  -e XAUTHORITY=/tmp/.docker.xauth \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v "$XAUTH":/tmp/.docker.xauth:ro \
  --user "$(id -u):$(id -g)" \
  --ipc=host \
  gui-test glxgears
```

## 2. Wayland ile yerel (Native) GUI uygulaması çalıştırma

Ubuntu 22.04/24.04, Fedora ve güncel Linux masaüstü ortamlarında (GNOME, KDE Plasma)
varsayılan görüntü sunucusu Wayland'dir. Wayland istemcileri X11'deki güvenlik açıklarını
barındırmaz; pencereler doğrudan compositor tarafından yönetilir.

### Soket ve yetkilendirme (`XDG_RUNTIME_DIR`)

Wayland soketi ana makinede `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY` altında (örneğin
`/run/user/1000/wayland-0`) yer alır.

Genellikle `0700` iznine sahip olan soketin kendisi değil, çalışma dizinidir. Erişim; UID eşlemesine, yeteneklere ve compositor politikasına da bağlıdır. Konteyner root kullanıcısının mutlaka reddedileceği söylenemez. Bu örnekte ana makinenin UID/GID’sini kullanın.

**Çözüm:** Konteyneri ana makine kullanıcısının UID ve GID'siyle çalıştırmaktır:
`--user $(id -u):$(id -g)`

### Donanım GPU hızlandırma (`/dev/dri`)

Wayland uygulamaları pencere tamponlarını (buffer) doğrudan GPU belleğinde tahsis eder.
Yazılımsal çizim (software rasterization) yüksek CPU tüketir ve akıcılığı bozar:

- GPU aygıt düğümlerini bağlayın: `--device /dev/dri:/dev/dri`
- Sayısal GID’yi gerçek render aygıtından okuyun; grup adları ve 107 gibi tahmini GID’ler taşınabilir değildir.

### Paylaşımlı bellek (`/dev/shm`) sınırı

Docker varsayılan olarak `/dev/shm` boyutunu **64 MB** ile sınırlar. Modern bir tarayıcı,
Qt6 veya GTK4 arayüzü yüksek çözünürlükte tampon açtığında yetersiz bellekten ötürü
çöker (`SIGBUS`). Çözüm `--shm-size=2gb` parametresidir.

### Wayland Konteyner çalıştırma komutu

```bash
set -eu
RENDER_NODE="${RENDER_NODE:-/dev/dri/renderD128}"
RENDER_GID="$(stat -c '%g' "$RENDER_NODE")"
case "$RENDER_GID" in ''|*[!0-9]*) echo "Invalid render GID" >&2; exit 1 ;; esac
: "${XDG_RUNTIME_DIR:?Run in a Linux Wayland session}"
: "${WAYLAND_DISPLAY:?Set the Wayland socket name}"
test -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  -e WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
  -v "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY":"$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY":ro \
  --device /dev/dri:/dev/dri \
  --group-add "$RENDER_GID" \
  --shm-size=2gb \
  gui-test vkcube-wayland
```

## 3. Örnek uygulama: glxgears / vkcube-wayland test imajı

Grafik hızlandırmayı ve ekran bağlantısını test etmek için basit bir `Dockerfile`:

```dockerfile
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    mesa-utils \
    vulkan-tools \
    mesa-vulkan-drivers \
    libgl1-mesa-dri \
    wayland-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

CMD ["wayland-info"]
```
{: data-filename="Dockerfile"}

İmajı derleyin:

```bash
docker build -t gui-test .
```

X11 komutunda `gui-test glxgears` kullanın; bu bir X11/GLX istemcisidir, yerel Wayland testi değildir. Wayland soket bağlamasıyla `gui-test wayland-info`, `/dev/dri` veya render grubu gerektirmeden protokol bağlantısını sınar. `gui-test vkcube-wayland` için yukarıdaki GPU seçeneklerini ekleyin. Başarılı bağlantı FPS ölçümü veya donanım hızlandırma kanıtı değildir.

## 4. Sık karşılaşılan sorunlar ve çözümleri

| Hata Mesajı | Olası Neden | Çözüm |
| :--- | :--- | :--- |
| `No protocol specified` / `Can't open display` | XAUTHORITY cookie uyuşmazlığı | `xauth nlist` ile wildcard (`ffff`) cookie üretip bağlayın. |
| `X Error of failed request: BadShmAttach` | Konteyner IPC izolasyonu | `docker run` komutuna `--ipc=host` ekleyin. |
| `Permission denied` (Wayland soketinde) | UID eşlemesi, soket izinleri veya compositor politikası | `--user $(id -u):$(id -g)` parametresini kullanın. |
| `Failed to initialize graphics backend` | GPU aygıt düğümü eksik | `--device /dev/dri:/dev/dri` ve `--group-add "$RENDER_GID"` ekleyin. |
| Uygulama aniden `SIGBUS` ile kapanıyor | Yetersiz `/dev/shm` boyutu | `--shm-size=2gb` tanımlayın. |

## Kaynaklar ve doğrulama ortamı

- [Docker Resmi Belgesi - Runtime Privilege and Linux Capabilities](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities)
- [Wayland Protokol Mimarisi](https://wayland.freedesktop.org/docs/html/)
- [X.Org Kimlik Doğrulama Belgeleri (Xsecurity)](https://www.x.org/releases/X11R7.6/doc/man/man7/Xsecurity.7.xhtml)

8–9 Kasım 2026: imaj, sayısal GID kabuk yolları ve başsız Weston üzerinden `wayland-info` ile `vkcube-wayland --c 10` (yazılımsal llvmpipe) kontrol edildi. Fiziksel Intel/AMD GPU, X11 masaüstü veya FPS ölçümü doğrulanmadı.
