---
translation_key: guide-docker-scratch-ile-statik-uygulama
lang: tr
title: scratch ile statik Docker uygulaması
permalink: /docker/scratch-ile-statik-uygulama/
status: duzenlendi
reviewed: 2026-11-02
scope: Linux konteynerinde GCC ile statik derlenen bir C++ konsol uygulaması.
redirect_from:
  - /docker/scratch_ile_statik_docker_uygulaması_oluşturmak.html
---

# scratch ile statik Docker uygulaması

`scratch`, dosya sistemi boş başlayan bir imaj oluşturur. Kabuk, paket yöneticisi
ve paylaşımlı kütüphaneler içermez. Basit bir C++ uygulamasını statik derleyerek
bu tabanda çalıştırabiliriz.

## Uygulama

Boş bir dizinde `hello.cc` oluşturun:

```cpp
#include <iostream>

int main() {
    std::cout << "Merhaba, dünya!\n";
    return 0;
}
```
{: data-filename="hello.cc"}

## Dockerfile

Derleme araçları ilk aşamada kalır; son imaja yalnızca uygulama kopyalanır.
Böylece macOS veya Windows üzerinde yanlışlıkla Linux dışı bir ikili derlemekten
kaçınırız.

```dockerfile
FROM gcc:14 AS build
WORKDIR /src
COPY hello.cc .
RUN g++ -O2 -static -o hello hello.cc

FROM scratch
COPY --from=build /src/hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"]
```
{: data-filename="Dockerfile"}

## Derleme ve çalıştırma

Docker'ın Linux konteynerleri çalıştırdığı bir ortamda:

```bash
docker build --tag hello-scratch .
docker run --rm hello-scratch
```

Beklenen çıktı:

```text
Merhaba, dünya!
```

## Sınırlar ve doğrulama

Statik derleme her uygulamanın tüm çalışma zamanı ihtiyaçlarını ortadan kaldırmaz.
Sertifikalar, saat dilimi verileri ve uygulamanın okuyacağı dosyalar ayrıca
gerekebilir. Bu örnek yalnızca konsola yazan bir program içindir.

`scratch` davranışı [Docker taban imaj belgesi](https://docs.docker.com/build/building/base-images/)
ile karşılaştırıldı. Örnek, Docker Engine 29.6.2 üzerinde Linux/ARM64 hedefinde
derlendi ve çalıştırıldı; `Merhaba, dünya!` çıktısı alındı.
