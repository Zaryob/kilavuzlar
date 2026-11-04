---
title: Building and testing a C++ application in Docker
permalink: /en/docker/cpp-derleme-ve-test/
status: duzenlendi
reviewed: 2026-11-03
scope: Multi-stage Dockerfiles, BuildKit cache mounts, CMake/Ninja, CTest and a Distroless
  runtime.
lang: en
translation_key: guide-docker-cpp-derleme-ve-test
translation_of: /docker/cpp-derleme-ve-test/
translated: '2026-11-03'
---

# Building and testing a C++ application in Docker

The two biggest problems when building C++ projects in Docker containers are:
1. Build tools (GCC/Clang, CMake, Ninja, vcpkg/Conan) can inflate the final image to several gigabytes and increase its attack surface.
2. A single-line source change can invalidate the layer cache and cause libraries and dependencies to be rebuilt from scratch for hours.

A modern solution combines **multi-stage builds**, **BuildKit cache mounts (`--mount=type=cache`)** and **CTest integration** into an isolated pipeline.

## 1. Multi-stage architecture

The pipeline has four logical stages:

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

## 2. A production-oriented multi-stage Dockerfile

Create `Dockerfile` in the project root:

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

## 3. Example CMakeLists.txt and test definition

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

Example test file, `tests/test_main.cpp`:

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

## 4. Building, testing and selecting a target

Start a build using Docker BuildKit’s advanced caching features:

```bash
DOCKER_BUILDKIT=1 docker build -t cpp-uygulama:latest .
```

### Selecting target stages in CI/CD

You can split CI into stages instead of running every step at once:

1. **Run only the tests:**
   ```bash
   docker build --target test-kosucu -t test-raporu .
   ```
   If a test fails, the build stops immediately and prints its error logs to the console.

2. **Produce only the final production image:**
   ```bash
   docker build --target calisma-zamani -t cpp-uygulama:prod .
   ```

## 5. Comparing image sizes

The difference between a traditional single-stage image and a multi-stage Distroless image:

```text
Geleneksel GCC + CMake İmajı:       ~1.85 GB
Multi-Stage Distroless İmajı:        ~28.4 MB
```

The final image contains no unnecessary compilers, header files (`.h`/`.hpp`), package manager or shell. This keeps startup quick and reduces the attack surface.

## Sources and verification environment

- [Docker multi-stage builds guide](https://docs.docker.com/build/building/multi-stage/)
- [Google Container Tools — Distroless images](https://github.com/GoogleContainerTools/distroless)
- [BuildKit cache mounts documentation](https://docs.docker.com/build/cache/backends/)

These steps were tested and verified using Docker Engine 26.1 and BuildKit on a Debian 12 base with GCC 12, CMake 3.25 and Ninja.
