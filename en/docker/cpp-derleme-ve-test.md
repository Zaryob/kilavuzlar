---
title: Building and testing a C++ application in Docker
permalink: /en/docker/cpp-derleme-ve-test/
status: duzenlendi
reviewed: 2026-11-09
scope: Multi-stage Dockerfiles, BuildKit cache mounts, CMake/Ninja, CTest and a Distroless
  runtime.
lang: en
translation_key: guide-docker-cpp-derleme-ve-test
translation_of: /docker/cpp-derleme-ve-test/
translated: '2026-11-09'
---

# Building and testing a C++ application in Docker

The two biggest problems when building C++ projects in Docker containers are:
1. Build tools (GCC/Clang, CMake, Ninja, vcpkg/Conan) can inflate the final image to several gigabytes and increase its attack surface.
2. A single-line source change can invalidate the layer cache and cause libraries and dependencies to be rebuilt from scratch for hours.

A modern solution combines **multi-stage builds**, **BuildKit cache mounts (`--mount=type=cache`)** and **CTest integration** into an isolated pipeline.

## 1. Multi-stage architecture

The pipeline has five logical stages:

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

The complete build context consists of `Dockerfile`, `vcpkg.json`, `CMakeLists.txt`, `src/main.cpp` and `tests/test_main.cpp`. No presets file is needed. The final COPY depends on `test-kosucu`, so BuildKit must execute CTest for the runtime target too.

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

### Proving the failure gate

In a temporary copy of the project, change `const int beklenen = 5;` to `const int beklenen = 6;`. Both builds below must exit nonzero, including the final runtime target. Restore the expectation afterwards. This explicit check remains active with `-DNDEBUG`.

```bash
docker build --target test-kosucu -t cpp-test-negatif .
docker build --target calisma-zamani -t cpp-runtime-negatif .
```

## 5. Comparing image sizes

Measure image size for the chosen platform and tag; no size or startup-time guarantee is implied:

```bash
docker image inspect cpp-uygulama:latest --format '{% raw %}{{.Size}}{% endraw %}'
```

## Sources and verification environment

- [Docker multi-stage builds guide](https://docs.docker.com/build/building/multi-stage/)
- [Google Container Tools — Distroless images](https://github.com/GoogleContainerTools/distroless)
- [BuildKit cache mounts documentation](https://docs.docker.com/build/cache/optimize/#use-cache-mounts)

8–9 November 2026: the final image was built and run with Docker 29.6.2/BuildKit, Debian 12 ARM64, GCC 12.2.0 and CMake 3.25.1. The compile command used `ccache` and `-DNDEBUG`. A deliberately wrong expectation stopped both `test-kosucu` and `calisma-zamani` with exit 1. A successful build does not establish performance or image-size claims.
