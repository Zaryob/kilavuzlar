---
translation_key: guide-docker-cpp-derleme-ve-test
lang: tr
title: "Docker'da C++ uygulaması derleyip test etmek"
permalink: /docker/cpp-derleme-ve-test/
status: duzenlendi
reviewed: 2026-11-09
scope: Multi-stage Dockerfile, BuildKit cache mounts, CMake/Ninja, CTest ve Distroless çalışma zamanı.
---

# Docker'da C++ uygulaması derleyip test etmek

C++ projelerini Docker konteynerlerinde derlerken karşılaşılan en büyük iki sorun:
1. Derleme araçlarının (GCC/Clang, CMake, Ninja, vcpkg/Conan) son imajı birkaç gigabayta şişirmesi ve güvenlik açığı yüzeyini genişletmesi.
2. Kaynak kodda yapılan tek satırlık bir değişiklikte tüm kütüphanelerin ve bağımlılıkların saatlerce baştan derlenmesi (katman önbelleğinin kırılması).

Bu sorunların modern çözümü; **Çok Aşamalı Derleme (Multi-Stage Build)**, **BuildKit Önbellek Bağlamaları (`--mount=type=cache`)** ve **CTest entegrasyonu** ile oluşturulan izole boru hattıdır.

## 1. Çok aşamalı mimarinin yapısı

Boru hattı mantıksal olarak 5 aşamadan oluşur:

```text
[ 1. Derleme Ortamı ]   ──► Derleyici araçlar (GCC/Clang, CMake, Ninja, Ccache)
          │
[ 2. Bağımlılık Katmanı ] ──► vcpkg.json ile harici kütüphaneler (vcpkg cache)
          │
[ 3. Kod Derleme ]      ──► Kaynak kod derlemesi (Ccache önbelleği ile saniyeler içinde)
          │
[ 4. Test Koşucusu ]    ──► CTest ile birim testler (Başarısız olursa imaj üretimi durur)
          │
[ 5. Minimal Çalışma ]  ──► Yalnızca ikili dosya (Distroless; boyut ölçülmelidir)
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

# APT arşivlerinin docker-clean tarafından silinmesini engelle
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

# APT paketlerini BuildKit önbelleği ile kur
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
RUN git clone --branch 2024.09.30 https://github.com/microsoft/vcpkg.git /opt/vcpkg && \
    /opt/vcpkg/bootstrap-vcpkg.sh -disableMetrics

# ==============================================================================
# AŞAMA 2: Bağımlılıkların Önbelleklenmesi
# ==============================================================================
FROM temel-araclar AS bagimlilik-derleyici
WORKDIR /proje

# Yalnızca bağımlılık listesini kopyala (Kaynak kod değiştiğinde bu katman bozulmaz)
COPY vcpkg.json ./

# vcpkg ikili önbelleği ile bağımlılıkları derle
ARG TARGETARCH
RUN --mount=type=cache,target=/root/.cache/vcpkg \
    case "$TARGETARCH" in amd64) triplet=x64-linux ;; arm64) triplet=arm64-linux ;; *) exit 1 ;; esac && \
    ${VCPKG_ROOT}/vcpkg install --triplet "$triplet"

# ==============================================================================
# AŞAMA 3: Projeyi Derleme
# ==============================================================================
FROM bagimlilik-derleyici AS derleyici
WORKDIR /proje

# Kaynak kodları kopyala
COPY CMakeLists.txt ./
COPY src/ ./src/
COPY tests/ ./tests/

# Ccache ve vcpkg önbelleklerini bağlayarak derle
ENV CCACHE_DIR=/root/.cache/ccache
RUN --mount=type=cache,target=/root/.cache/vcpkg \
    --mount=type=cache,target=/root/.cache/ccache \
    cmake -B build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
        -DVCPKG_INSTALLED_DIR=/proje/vcpkg_installed \
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
COPY --from=test-kosucu /proje/build/bin/uygulama /app/uygulama

USER nonroot:nonroot
ENTRYPOINT ["/app/uygulama"]
```
{: data-filename="Dockerfile"}

Tam build bağlamı `Dockerfile`, `vcpkg.json`, `CMakeLists.txt`, `src/main.cpp` ve `tests/test_main.cpp` dosyalarından oluşur. Preset dosyası gerekmez. Son COPY `test-kosucu` aşamasına bağlıdır; böylece BuildKit çalışma zamanı hedefinde de CTest’i yürütmek zorundadır.

```json
{
  "name": "docker-cpp-ornek",
  "version": "1.0.0",
  "builtin-baseline": "c82f74667287d3dc386bce81e44964370c91a289",
  "dependencies": ["fmt"]
}
```
{: data-filename="vcpkg.json"}

```cpp
#include <fmt/core.h>

int main() {
    fmt::print("Uygulama calisti!\n");
}
```
{: data-filename="src/main.cpp"}

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

int topla(int a, int b) { return a + b; }

int main() {
    const int beklenen = 5;
    if (topla(2, 3) != beklenen) {
        std::cerr << "topla(2, 3): beklenen " << beklenen << ", alinan " << topla(2, 3) << "\n";
        return 1;
    }
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

### Başarısızlık kapısını kanıtlama

Projenin geçici kopyasında `const int beklenen = 5;` satırını `const int beklenen = 6;` yapın. Son çalışma zamanı hedefi dahil aşağıdaki iki derleme sıfırdan farklı çıkmalıdır. Sonra beklentiyi geri alın. Bu açık kontrol `-DNDEBUG` ile de aktiftir.

```bash
docker build --target test-kosucu -t cpp-test-negatif .
docker build --target calisma-zamani -t cpp-runtime-negatif .
```

## 5. İmaj boyutlarının karşılaştırılması

Boyutu seçilen platform ve etiket için ölçün; sabit boyut veya başlangıç süresi garantisi verilmez:

```bash
docker image inspect cpp-uygulama:latest --format '{% raw %}{{.Size}}{% endraw %}'
```

## Kaynaklar ve doğrulama ortamı

- [Docker Multi-Stage Builds Resmi Kılavuzu](https://docs.docker.com/build/building/multi-stage/)
- [Google Container Tools - Distroless İmajları](https://github.com/GoogleContainerTools/distroless)
- [BuildKit Cache Mounts Belgesi](https://docs.docker.com/build/cache/optimize/#use-cache-mounts)

8–9 Kasım 2026: Docker 29.6.2/BuildKit, Debian 12 ARM64, GCC 12.2.0 ve CMake 3.25.1 ile son imaj derlendi ve çalıştırıldı. Derleme komutunda `ccache` ve `-DNDEBUG` görüldü. Kasıtlı yanlış beklenti hem `test-kosucu` hem `calisma-zamani` hedefini exit 1 ile durdurdu. Başarılı derleme performans veya sabit imaj boyutu iddiası oluşturmaz.
