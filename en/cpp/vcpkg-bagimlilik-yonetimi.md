---
title: Managing C++ dependencies with vcpkg
permalink: /en/cpp/vcpkg-bagimlilik-yonetimi/
status: duzenlendi
reviewed: 2026-11-03
scope: vcpkg manifest mode (vcpkg.json), CMakePresets integration and binary caching.
lang: en
translation_key: guide-cpp-vcpkg-bagimlilik-yonetimi
translation_of: /cpp/vcpkg-bagimlilik-yonetimi/
translated: '2026-11-03'
---

# Managing C++ dependencies with vcpkg

For years, C++ library management relied on operating-system package managers (`apt`, `brew`, `vcpkg install <paket>`) or manually building and copying libraries into `/usr/local`. This “classic mode” can leave developers and CI servers using different library versions, resulting in inconsistent builds.

Modern vcpkg offers **manifest mode**, much like Rust’s `Cargo.toml` or Node.js’s `package.json`. Dependencies are declared in the project-root `vcpkg.json` and downloaded and built automatically when CMake configuration starts.

## 1. Classic mode vs manifest mode

| Feature | Classic mode (`vcpkg install`) | Manifest mode (`vcpkg.json`) |
| :--- | :--- | :--- |
| **Dependency definition** | Commands run by the user | A version-controlled JSON file in the project root |
| **Version pinning** | Difficult; depends on the current vcpkg repository commit | Explicit versions through `builtin-baseline` and `overrides` |
| **Installation location** | Global, under the central vcpkg directory | In the project’s `build/vcpkg_installed` directory |
| **Team consistency** | Each developer installs packages manually | Anyone cloning the repository can reproduce the environment with `cmake` |

## 2. Creating a manifest (`vcpkg.json`)

Create `vcpkg.json` in the project root:

```json
{
  "$schema": "https://raw.githubusercontent.com/microsoft/vcpkg-tool/main/docs/vcpkg.schema.json",
  "name": "ornek-vcpkg-uygulamasi",
  "version": "1.0.0",
  "builtin-baseline": "5040e32d43717de55ff672a11540d99042b5c54d",
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

### Meaning of the fields

- `builtin-baseline`: the hash of the vcpkg Git commit used to resolve packages. It lets later builds, even years afterwards, use the same versions. Obtain the current baseline hash by running `git rev-parse HEAD` in the vcpkg repository.
- `dependencies`: the libraries required by the project. You can also specify optional `features` or platform constraints such as `"platform": "!windows"`.

### Pinning versions with `overrides`

Add an `overrides` block to require a specific version outside the baseline:

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

add_executable(uygulama src/main.cpp)

# Kütüphaneleri bağla
target_link_libraries(uygulama PRIVATE
    fmt::fmt
    nlohmann_json::nlohmann_json
)
```

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

> [!NOTE]
> Make sure `VCPKG_ROOT` is defined in the environment, for example `export VCPKG_ROOT=/opt/vcpkg` or a path such as `$HOME/vcpkg` in your shell profile.

## 4. Private registries and internal packages

To use packages from private Git repositories alongside open source libraries, add `vcpkg-configuration.json` to the project root:

```json
{
  "default-registry": {
    "kind": "builtin",
    "baseline": "5040e32d43717de55ff672a11540d99042b5c54d"
  },
  "registries": [
    {
      "kind": "git",
      "repository": "https://github.com/sirketim/vcpkg-ozel-depo",
      "baseline": "a1b2c3d4e5f6...",
      "packages": ["sirket-guvenlik", "sirket-protokol"]
    }
  ]
}
```

In this example, `sirket-guvenlik` comes from the private registry, while `fmt` and `nlohmann-json` come from the official registry.

## 5. Binary caching

vcpkg caches compiled packages locally by default. To avoid rebuilding packages for hours on CI/CD servers or in clean builds, configure `VCPKG_BINARY_SOURCES`:

```bash
# Yerel dosya sistemi önbelleği:
export VCPKG_BINARY_SOURCES="clear;files,/opt/vcpkg-cache,readwrite"

# GitHub Actions ortamında:
export VCPKG_BINARY_SOURCES="clear;gha,readwrite"
```

For builds using the same package and compiler combination, vcpkg can retrieve the existing binary from the cache within seconds.

## 6. Example application

`src/main.cpp`:

```cpp
#include <iostream>
#include <fmt/core.h>
#include <nlohmann/json.hpp>

int main() {
    nlohmann::json veri = {
        {"proje", "kilavuzlar"},
        {"mod", "manifest"},
        {"basari", true}
    };

    fmt::print("Uygulama çalıştı!\nJSON Çıktısı: {}\n", veri.dump(2));
    return 0;
}
```

### Build process

Configure the project:

```bash
cmake --preset dev-debug
```

Expected output:

```text
-- Running vcpkg install
Detecting compiler hash for triplet x64-linux...
The following packages will be built and installed:
    fmt:x64-linux -> 10.2.1
    nlohmann-json:x64-linux -> 3.11.3
Restored 2 package(s) from /home/kullanici/.cache/vcpkg/archives in 12 ms.
-- Running vcpkg install - done
-- Found fmt: .../build/dev-debug/vcpkg_installed/x64-linux/share/fmt/fmt-config.cmake
-- Found nlohmann_json: .../build/dev-debug/vcpkg_installed/x64-linux/share/nlohmann_json/nlohmann_jsonConfig.cmake
-- Configuring done
-- Generating done
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
- [vcpkg binary caching guide](https://learn.microsoft.com/en-us/vcpkg/users/binarycaching)
- [vcpkg Git registries](https://learn.microsoft.com/en-us/vcpkg/users/registries)

This guide was tested on Ubuntu 24.04 (Linux x86_64) and macOS Sonoma (ARM64), using vcpkg 2024-09, CMake 3.28 and Ninja 1.11.
