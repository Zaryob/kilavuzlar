---
translation_key: guide-docker-coklu-mimari-imajlar
lang: tr
title: Çok mimarili Docker imajları
permalink: /docker/coklu-mimari-imajlar/
status: duzenlendi
reviewed: 2026-11-02
scope: Docker, Buildx ve Linux konteynerleri; AMD64 ve ARM64.
redirect_from:
  - /docker/coklu_mimari_docker_imajları.html
---

# Çok mimarili Docker imajları

Aynı etiketten farklı işlemci mimarilerine uygun imajlar sunmak için Buildx
kullanılır. Örnekte `linux/amd64` ve `linux/arm64` hedeflenir.

## Ön koşullar

Çalışan bir Docker kurulumu ve Buildx gerekir:

```bash
docker version
docker buildx version
```

Docker Desktop emülasyon desteği sunar; eski Edge kanalına geçiş gerekmez.
Linux'ta destek kurulu BuildKit'e bağlıdır. Emülasyon çalışmıyorsa
[Docker'ın QEMU kurulum adımlarına](https://docs.docker.com/build/building/multi-platform/#install-qemu-manually)
bakın. Emülasyon altında derleme daha yavaş olabilir.

## Builder oluşturma

```bash
docker buildx create --name kilavuz-builder --driver docker-container --use
docker buildx inspect --bootstrap
```

`Platforms` çıktısında iki hedefi de arayın. Aynı adlı builder zaten varsa
`docker buildx use kilavuz-builder` ile seçin.

## Örnek Dockerfile

Boş bir çalışma dizininde `Dockerfile` oluşturun:

```dockerfile
FROM alpine:3.22
CMD ["uname", "-m"]
```
{: data-filename="Dockerfile"}

Taban imajın hedef mimarileri desteklemesi gerekir.

## Yerel deneme

Önce tek hedefi yerel imaj deposuna yükleyin:

```bash
docker buildx build --platform linux/arm64 --load -t mimari-deneme:arm64 .
docker run --rm --platform linux/arm64 mimari-deneme:arm64
```

Beklenen çıktı `aarch64` olur. Farklı mimaride çalıştırmak için emülasyon gerekir.

## Çok mimarili imajı yayımlama

`docker-container` çıktısı kendiliğinden yerel depoya yüklenmez. İki hedefi
birlikte bir registry'ye göndermek için aşağıdaki değişkene kendi Docker Hub
kullanıcı adınızı yazın. `--push` imajı hesabınıza yükler.

```bash
DOCKER_KULLANICI=hesabiniz
docker login
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "$DOCKER_KULLANICI/mimari-deneme:1" \
  --push .
docker buildx imagetools inspect "$DOCKER_KULLANICI/mimari-deneme:1"
```

Manifest çıktısında `linux/amd64` ve `linux/arm64` bulunmalıdır.

## Kaynaklar ve doğrulama

Anlatım [Docker çoklu platform belgesi](https://docs.docker.com/build/building/multi-platform/)
ve [Buildx komut başvurusu](https://docs.docker.com/reference/cli/docker/buildx/build/)
ile karşılaştırıldı. Docker Engine 29.6.2 ortamında AMD64 ve ARM64 hedeflerini
içeren yerel OCI arşivi üretildi; ARM64 imajı çalıştırıldığında `aarch64` çıktısı
alındı. Registry'ye yayımlama bu depo incelemesinde denenmedi.
