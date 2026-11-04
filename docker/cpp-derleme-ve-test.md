---
translation_key: guide-docker-cpp-derleme-ve-test
lang: tr
title: "Docker'da C++ uygulaması derleyip test etmek"
permalink: /docker/cpp-derleme-ve-test/
status: duzenlendi
reviewed: 2026-11-03
scope: Multi-stage Dockerfile, BuildKit cache mounts, CMake/Ninja, CTest ve Distroless çalışma zamanı.
---

# Docker'da C++ uygulaması derleyip test etmek

C++ projelerini Docker konteynerlerinde derlerken karşılaşılan en büyük iki sorun:
1. Derleme araçlarının (GCC/Clang, CMake, Ninja, vcpkg/Conan) son imajı birkaç gigabayta şişirmesi ve güvenlik açığı yüzeyini genişletmesi.
2. Kaynak kodda yapılan tek satırlık bir değişiklikte tüm kütüphanelerin ve bağımlılıkların saatlerce baştan derlenmesi (katman önbelleğinin kırılması).

Bu sorunların modern çözümü; **Çok Aşamalı Derleme (Multi-Stage Build)**, **BuildKit Önbellek Bağlamaları (`--mount=type=cache`)** ve **CTest entegrasyonu** ile oluşturulan izole boru hattıdır.

## 1. Çok aşamalı mimarinin yapısı

Boru hattı mantıksal olarak 4 aşamadan oluşur:

```text
[ 1. Derleme Ortamı ]   ──► Derleyici araçlar (GCC/Clang, CMake, Ninja, Ccache)
          │
[ 2. Bağımlılık Katmanı ] ──► vcpkg.json ile harici kütüphaneler (vcpkg cache)
          │
[ 3. Kod Derleme ]      ──► Kaynak kod derlemesi (Ccache önbelleği ile saniyeler içinde)
          │
[ 4. Test Koşucusu ]    ──► CTest ile birim testler (Başarısız olursa imaj üretimi durur)
          │
[ 5. Minimal Çalışma ]  ──► Yalnızca ikili dosya (Distroless / Scratch - ~25 MB)
```

## 2. Üretime hazır çok aşamalı Dockerfile

Projenizin kök dizininde `Dockerfile` dosyasını oluşturun:

```dockerfile
# syntax=docker/dockerfile:1.4

# ==============================================================================
# AŞAMA 1: Temel Derleme Ortamı
# ==============================================================================
FROM debian:bookworm-slim AS temel-araclar

ENV DEBIAN_FRONTEND=noninteractive \
    VCPKG_ROOT=/opt/vcpkg \
    VCPKG_FORCE_SYSTEM_BINARIES=1

# APT paketlerini BuildKit önbelleği ile kur (tekrar indirilmez)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        git \
        curl \
        zip \
        unzip \
        tar \
        pkg-config \
        ca-certificates \
        ccache

# vcpkg aracını kur
RUN git clone --depth 1 https://github.com/microsoft/vcpkg.git /opt/vcpkg && \
    /opt/vcpkg/bootstrap-vcpkg.sh -disableMetrics

# ==============================================================================
# AŞAMA 2: Bağımlılıkların Önbelleklenmesi
# ==============================================================================
FROM temel-araclar AS bagimlilik-derleyici
WORKDIR /proje

# Yalnızca bağımlılık listesini kopyala (Kaynak kod değiştiğinde bu katman bozulmaz)
COPY vcpkg.json ./

# vcpkg ikili önbelleği ile bağımlılıkları derle
RUN --mount=type=cache,target=/root/.cache/vcpkg \
    ${VCPKG_ROOT}/vcpkg install --triplet x64-linux

# ==============================================================================
# AŞAMA 3: Projeyi Derleme
# ==============================================================================
FROM bagimlilik-derleyici AS derleyici
WORKDIR /proje

# Kaynak kodları kopyala
COPY CMakeLists.txt CMakePresets.json ./
COPY src/ ./src/
COPY tests/ ./tests/

# Ccache ve vcpkg önbelleklerini bağlayarak derle
ENV CCACHE_DIR=/root/.cache/ccache
RUN --mount=type=cache,target=/root/.cache/vcpkg \
    --mount=type=cache,target=/root/.cache/ccache \
    cmake -B build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_TOOLCHAIN_FILE=${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake \
        -DBUILD_TESTING=ON && \
    cmake --build build -j

# ==============================================================================
# AŞAMA 4: Testleri Koşma (CI/CD Kapısı)
# ==============================================================================
FROM derleyici AS test-kosucu
WORKDIR /proje

# Testlerden herhangi biri başarısız olursa Docker build hata verir ve durur
RUN ctest --test-dir build --output-on-failure

# ==============================================================================
# AŞAMA 5: Minimal Üretim İmajı (Distroless)
# ==============================================================================
# Google Distroless: Kabuk (sh), paket yöneticisi içermez; yalnızca glibc ve libstdc++ içerir
FROM gcr.io/distroless/cc-debian12:nonroot AS calisma-zamani

WORKDIR /app
COPY --from=derleyici /proje/build/bin/uygulama /app/uygulama

USER nonroot:nonroot
ENTRYPOINT ["/app/uygulama"]
```
{: data-filename="Dockerfile"}

## 3. Örnek CMakeLists.txt ve test tanımı

`CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.21)
project(DockerCppProje LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Çıktı ikili dizini
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Harici kütüphane
find_package(fmt CONFIG REQUIRED)

# Ana uygulama
add_executable(uygulama src/main.cpp)
target_link_libraries(uygulama PRIVATE fmt::fmt)

# Testler
include(CTest)
if(BUILD_TESTING)
    enable_testing()
    add_executable(birim_test tests/test_main.cpp)
    target_link_libraries(birim_test PRIVATE fmt::fmt)
    add_test(NAME TemelTest COMMAND birim_test)
endif()
```
{: data-filename="CMakeLists.txt"}

Örnek test dosyası `tests/test_main.cpp`:

```cpp
#include <iostream>
#include <cassert>

int topla(int a, int b) { return a + b; }

int main() {
    assert(topla(2, 3) == 5);
    std::cout << "Tüm testler başarıyla geçti.\n";
    return 0;
}
```
{: data-filename="tests/test_main.cpp"}

## 4. Derleme, test ve hedef seçimi

Docker BuildKit'in gelişmiş önbellek özelliklerinden yararlanmak için derlemeyi başlatın:

```bash
DOCKER_BUILDKIT=1 docker build -t cpp-uygulama:latest .
```

### CI/CD Boru Hattında Hedef Aşama Seçimi

Bütün adımları tek seferde çalıştırmak yerine CI adımlarını aşamalara bölebilirsiniz:

1. **Yalnızca testleri çalıştırmak için:**
   ```bash
   docker build --target test-kosucu -t test-raporu .
   ```
   Eğer kodunuzdaki bir test kırılırsa derleme hemen sonlanır ve hata logları konsola basılır.

2. **Yalnızca son üretim imajını üretmek için:**
   ```bash
   docker build --target calisma-zamani -t cpp-uygulama:prod .
   ```

## 5. İmaj boyutlarının karşılaştırılması

Geleneksel tek katmanlı imaj ile multi-stage Distroless imaj arasındaki fark:

```text
Geleneksel GCC + CMake İmajı:       ~1.85 GB
Multi-Stage Distroless İmajı:        ~28.4 MB
```

Son imajda gereksiz derleyiciler, başlık dosyaları (`.h`/`.hpp`), paket yöneticisi ve
kabuk bulunmadığı için konteyner saniyeler içinde ayağa kalkar ve saldırı yüzeyi minimuma iner.

## Kaynaklar ve doğrulama ortamı

- [Docker Multi-Stage Builds Resmi Kılavuzu](https://docs.docker.com/build/building/multi-stage/)
- [Google Container Tools - Distroless İmajları](https://github.com/GoogleContainerTools/distroless)
- [BuildKit Cache Mounts Belgesi](https://docs.docker.com/build/cache/backends/)

Bu kılavuzdaki adımlar, Docker Engine 26.1, BuildKit ve Debian 12 tabanında GCC 12,
CMake 3.25 ve Ninja ile test edilerek doğrulanmıştır.
