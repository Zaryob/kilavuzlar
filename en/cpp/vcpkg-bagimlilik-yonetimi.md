---
title: Managing C++ dependencies with vcpkg
permalink: /en/cpp/vcpkg-bagimlilik-yonetimi/
status: duzenlendi
reviewed: 2026-11-09
scope: vcpkg manifest mode (vcpkg.json), CMakePresets integration and binary caching.
lang: en
translation_key: guide-cpp-vcpkg-bagimlilik-yonetimi
translation_of: /cpp/vcpkg-bagimlilik-yonetimi/
translated: '2026-11-09'
---

# Managing C++ dependencies with vcpkg

For years, C++ library management relied on operating-system package managers (`apt`, `brew`, `vcpkg install <paket>`) or manually building and copying libraries into `/usr/local`. This “classic mode” can leave developers and CI servers using different library versions, resulting in inconsistent builds.

Modern vcpkg offers **manifest mode**, much like Rust’s `Cargo.toml` or Node.js’s `package.json`. Dependencies are declared in the project-root `vcpkg.json` and downloaded and built automatically when CMake configuration starts.

## 1. Classic mode vs manifest mode

| Feature | Classic mode (`vcpkg install`) | Manifest mode (`vcpkg.json`) |
| :--- | :--- | :--- |
| **Dependency definition** | Commands run by the user | A version-controlled JSON file in the project root |
| **Version pinning** | Difficult; depends on the current vcpkg repository commit | Baseline versions through `builtin-baseline`; selected versions through `overrides` |
| **Installation location** | Global, under the central vcpkg directory | In the project’s `build/vcpkg_installed` directory |
| **Team consistency** | Each developer installs packages manually | Anyone cloning the repository can reproduce the environment with `cmake` |

## 2. Creating a manifest (`vcpkg.json`)

Create `vcpkg.json` in the project root:

```json
{
  "$schema": "https://raw.githubusercontent.com/microsoft/vcpkg-tool/main/docs/vcpkg.schema.json",
  "name": "ornek-vcpkg-uygulamasi",
  "version": "1.0.0",
  "builtin-baseline": "c82f74667287d3dc386bce81e44964370c91a289",
  "dependencies": [
    "fmt",
    "nlohmann-json",
    {
      "name": "cxxopts",
      "version>=": "3.1.1"
    }
  ]
}
```
{: data-filename="vcpkg.json"}

Install the tool at the same upstream tag before continuing (Git, a C++ compiler, CMake and Ninja are prerequisites):

```bash
git clone --branch 2024.09.30 https://github.com/microsoft/vcpkg.git "$HOME/vcpkg-kilavuz"
export VCPKG_ROOT="$HOME/vcpkg-kilavuz"
"$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics
# HEAD: c82f74667287d3dc386bce81e44964370c91a289
```

Do not use `--depth 1`: version constraints and overrides may require historical port trees outside a shallow checkout.

### Meaning of the fields

- `builtin-baseline`: the registry snapshot used for minimum package versions. This example pins the tool checkout and registry to the upstream `2024.09.30` tag. Reproducible binaries additionally require a fixed compiler, SDK, triplet, features and available sources; this field alone does not guarantee future identical builds.
- `dependencies`: the libraries required by the project. You can also specify optional `features` or platform constraints such as `"platform": "!windows"`.

### Pinning versions with `overrides`

Merge an `overrides` block into the main manifest to force a version outside the baseline. This optional fragment is not used in the runnable example; the version output below was obtained without an override:

```json
{
  "overrides": [
    {
      "name": "fmt",
      "version": "10.2.1"
    }
  ]
}
```
{: data-filename="vcpkg.json"}

## 3. CMake integration

vcpkg supplies a toolchain file, `vcpkg.cmake`, that integrates with CMake’s standard `find_package` mechanism.

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.21)
project(VcpkgOrnek LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Bağımlılıkları ara (vcpkg otomatik olarak CONFIG modunda sağlar)
find_package(fmt CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(cxxopts CONFIG REQUIRED)

add_executable(uygulama src/main.cpp)

# Kütüphaneleri bağla
target_link_libraries(uygulama PRIVATE
    fmt::fmt
    nlohmann_json::nlohmann_json
    cxxopts::cxxopts
)
```
{: data-filename="CMakeLists.txt"}

### Connecting the vcpkg toolchain through `CMakePresets.json`

Add the toolchain to `CMakePresets.json` so developers do not have to repeat `-DCMAKE_TOOLCHAIN_FILE=...`:

```json
{
  "version": 3,
  "configurePresets": [
    {
      "name": "vcpkg-temel",
      "hidden": true,
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/${presetName}",
      "cacheVariables": {
        "CMAKE_TOOLCHAIN_FILE": "$env{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake",
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
      }
    },
    {
      "name": "dev-debug",
      "inherits": "vcpkg-temel",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug"
      }
    },
    {
      "name": "dev-release",
      "inherits": "vcpkg-temel",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release"
      }
    }
  ]
}
```
{: data-filename="CMakePresets.json"}

> [!NOTE]
> Make sure `VCPKG_ROOT` is defined in the environment, for example `export VCPKG_ROOT=/opt/vcpkg` or a path such as `$HOME/vcpkg` in your shell profile.

## 4. Private registries and internal packages

The following is a **template**, not part of the runnable example. Do not save it unless you have a real private registry URL, its full 40-character commit and matching packages. Replace every placeholder first:

```json
{
  "default-registry": {
    "kind": "builtin",
    "baseline": "c82f74667287d3dc386bce81e44964370c91a289"
  },
  "registries": [
    {
      "kind": "git",
      "repository": "<PRIVATE_REGISTRY_URL>",
      "baseline": "<40_HEX_COMMIT>",
      "packages": ["sirket-guvenlik", "sirket-protokol"]
    }
  ]
}
```
{: data-filename="vcpkg-configuration.json"}

In this example, `sirket-guvenlik` comes from the private registry, while `fmt` and `nlohmann-json` come from the official registry.

## 5. Binary caching

vcpkg caches compiled packages locally by default. To avoid rebuilding packages for hours on CI/CD servers or in clean builds, configure `VCPKG_BINARY_SOURCES`:

```bash
mkdir -p "$HOME/.cache/vcpkg-kilavuz"
export VCPKG_BINARY_SOURCES="clear;files,$HOME/.cache/vcpkg-kilavuz,readwrite"
```

GitHub Actions uses the same `files` provider with `actions/cache`; the removed `x-gha` provider must not be used. Example steps after checkout and tool installation, on a Linux runner with a fixed toolchain:

{% raw %}
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/vcpkg-kilavuz
    key: vcpkg-${{ runner.os }}-${{ runner.arch }}-gcc12-c82f746-${{ hashFiles('vcpkg.json') }}-${{ github.sha }}
    restore-keys: |
      vcpkg-${{ runner.os }}-${{ runner.arch }}-gcc12-c82f746-${{ hashFiles('vcpkg.json') }}-
- name: Configure and build
  run: |
    export VCPKG_BINARY_SOURCES="clear;files,$HOME/.cache/vcpkg-kilavuz,readwrite"
    cmake --preset dev-debug
    cmake --build build/dev-debug
```
{% endraw %}

For builds using the same package and compiler combination, vcpkg can retrieve the existing binary from the cache within seconds.

## 6. Example application

`src/main.cpp`:

```cpp
#include <cxxopts.hpp>
#include <fmt/core.h>
#include <nlohmann/json.hpp>

int main() {
    cxxopts::Options options("uygulama", "vcpkg manifest example");
    nlohmann::json veri = {
        {"proje", "kilavuzlar"},
        {"mod", "manifest"},
        {"basari", true}
    };

    fmt::print("Uygulama çalıştı!\nJSON Çıktısı: {}\n", veri.dump(2));
    return 0;
}
```
{: data-filename="src/main.cpp"}

### Build process

Configure the project:

```bash
cmake --preset dev-debug
```

Package-version excerpt from the clean `arm64-osx` run (helper ports and timings omitted):

```text
    cxxopts:arm64-osx@3.2.1
    fmt:arm64-osx@11.0.2#1
    nlohmann-json:arm64-osx@3.11.3#1
```

Build and run:

```bash
cmake --build build/dev-debug
./build/dev-debug/uygulama
```

Expected output:

```text
Uygulama çalıştı!
JSON Çıktısı: {
  "basari": true,
  "mod": "manifest",
  "proje": "kilavuzlar"
}
```

## Common problems and solutions

- **`VCPKG_ROOT not found`**: add the vcpkg installation directory to the shell environment with `export VCPKG_ROOT=...`.
- **Triplet mismatch**: use `arm64-osx` for ARM64 macOS, `x64-osx` for x86_64 macOS, and `x64-linux` or `arm64-linux` on Linux. If necessary, add `"VCPKG_TARGET_TRIPLET": "arm64-osx"` to the `vcpkg-temel` preset.
- **Need for a clean install**: if the dependency tree develops an unexpected problem, remove the project’s `build/` and `vcpkg_installed/` directories and configure again.

## Sources and verification environment

- [Microsoft vcpkg documentation — Manifest mode](https://learn.microsoft.com/en-us/vcpkg/consume/manifest-mode)
- [vcpkg binary caching guide](https://learn.microsoft.com/en-us/vcpkg/reference/binarycaching)
- [vcpkg Git registries](https://learn.microsoft.com/en-us/vcpkg/users/registries)

8–9 November 2026: the pinned manifest was installed from sources on macOS 27.2 ARM64 and Debian 12 ARM64 with binary caching disabled; the CMake Debug application was built and run. The `files` provider restored 5/5 packages in a second clean Linux installation. The private registry and Actions service have not been executed.
