---
title: Creating a portable C++ project with CMake
permalink: /en/cpp/tasinabilir-cmake-projesi/
status: duzenlendi
reviewed: 2026-11-03
scope: Target-based architecture, CMakePresets, toolchains and cross-platform support
  using modern CMake (3.21+).
lang: en
translation_key: guide-cpp-tasinabilir-cmake-projesi
translation_of: /cpp/tasinabilir-cmake-projesi/
translated: '2026-11-03'
---

# Creating a portable C++ project with CMake

Global commands commonly used in older CMake projects, such as `include_directories()`, `link_libraries()` and `set(CMAKE_CXX_FLAGS "...")`, can cause libraries to pollute one another’s build flags and undermine portability as a project grows.

Modern CMake takes an object-oriented approach built around **targets** and their **usage requirements**. This guide sets up a portable C++ project that works consistently on Linux, macOS and Windows, uses `CMakePresets.json` and adapts cleanly to different compilers.

## 1. Target-based architecture and visibility

Every library or executable is a target (`add_library`, `add_executable`). Dependencies have three basic visibility levels:

- `PRIVATE`: needed only when compiling this target’s own source files; not propagated to consumers that link to it.
- `INTERFACE`: not used to compile the target itself; propagated only to its consumers, as with header-only libraries.
- `PUBLIC`: required by the target itself and automatically propagated to consumers as a transitive dependency.

### Separating a library from an application

Project directory structure:

```text
tasinabilir-cpp/
├── CMakeLists.txt
├── CMakePresets.json
├── include/
│   └── hesaplayici/
│       └── topla.hpp
├── src/
│   ├── topla.cpp
│   └── main.cpp
```

Root `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.21)
project(TasinabilirCpp VERSION 1.0.0 LANGUAGES CXX)

# Clangd ve dil sunucuları için derleme veritabanını dışa aktar
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 1. Kütüphane hedefi
add_library(hesaplayici STATIC
    src/topla.cpp
)

# Kütüphane genelinde C++ standardı belirleme
target_compile_features(hesaplayici PUBLIC cxx_std_20)

# Başlık dizini kuralı: Kendi derlemesinde ve tüketiciye aktarımda
target_include_directories(hesaplayici
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# 2. Çalıştırılabilir ikili hedefi
add_executable(uygulama
    src/main.cpp
)

# Kütüphaneyi uygulamaya bağla (C++ standardı ve başlık yolu otomatik devralınır)
target_link_libraries(uygulama PRIVATE hesaplayici)

# Derleyiciye özgü uyarı bayrakları (Taşınabilir koşullu ekleme)
if (MSVC)
    target_compile_options(uygulama PRIVATE /W4 /WX)
else()
    target_compile_options(uygulama PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
```

With `target_compile_features(hesaplayici PUBLIC cxx_std_20)`, the `uygulama` target automatically acquires the C++20 requirement when it links to `hesaplayici`. There is no need to add `-std=c++20` manually: CMake translates the requirement into the correct GCC, Clang or MSVC option.

## 2. Standardising the build environment with CMakePresets

`CMakePresets.json`, introduced in CMake 3.19+, avoids long lists of `-D` arguments for individual developers and CI/CD systems.

Create `CMakePresets.json` in the project root:

```json
{
  "version": 3,
  "cmakeMinimumRequired": {
    "major": 3,
    "minor": 21,
    "patch": 0
  },
  "configurePresets": [
    {
      "name": "temel",
      "hidden": true,
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/${presetName}",
      "cacheVariables": {
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
      }
    },
    {
      "name": "dev-debug",
      "displayName": "Geliştirme (Debug)",
      "inherits": "temel",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug"
      }
    },
    {
      "name": "dev-release",
      "displayName": "Dağıtım (Release)",
      "inherits": "temel",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release"
      }
    }
  ],
  "buildPresets": [
    {
      "name": "build-debug",
      "configurePreset": "dev-debug"
    },
    {
      "name": "build-release",
      "configurePreset": "dev-release"
    }
  ]
}
```

> [!TIP]
> Developers can put machine-specific configuration in `CMakeUserPresets.json`. Add this file to `.gitignore` rather than committing it.

## 3. Separating the compiler and environment with toolchain files

Use `CMAKE_TOOLCHAIN_FILE` instead of passing compiler-selection or cross-compilation variables on the command line. A toolchain file defines the compiler and target architecture before CMake begins its system checks.

Example Clang toolchain, `cmake/toolchains/clang.cmake`:

```cmake
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

# macOS ve Linux üzerinde modern lld bağlayıcısını tercih et (varsa)
find_program(LLD_EXECUTABLE ld.lld)
if(LLD_EXECUTABLE)
    set(CMAKE_EXE_LINKER_FLAGS_INIT "-fuse-ld=lld")
    set(CMAKE_SHARED_LINKER_FLAGS_INIT "-fuse-ld=lld")
endif()
```

To connect the toolchain to a preset, add `"toolchainFile": "${sourceDir}/cmake/toolchains/clang.cmake"` under `configurePresets`.

## 4. Build types and generator differences

CMake manages build types using two generator models.

### 1. Single-config generators: Ninja and Unix Makefiles

One build directory holds one configuration, selected at configure time using `CMAKE_BUILD_TYPE`:

- `Debug`: debugging symbols (`-g`) with optimisation disabled (`-O0`).
- `Release`: high optimisation (`-O3` or `/O2`) with `NDEBUG` defined.
- `RelWithDebInfo`: optimisation (`-O2`) and debugging symbols (`-g`), useful for profiling and investigating production failures.
- `MinSizeRel`: optimisation focused on code size (`-Os` or `/Os`).

### 2. Multi-config generators: Ninja Multi-Config, Visual Studio and Xcode

One configured build tree supports all configurations. `CMAKE_BUILD_TYPE` is ignored; select the configuration at build time with `--config`:

```bash
cmake -B build -G "Ninja Multi-Config"
cmake --build build --config Release
cmake --build build --config Debug
```

Use generator expressions to apply configuration-specific compilation or linking options:

```cmake
target_compile_definitions(uygulama PRIVATE
    $<$<CONFIG:Debug>:DEBUG_LOGGING_ENABLED=1>
)
```

## 5. Application and build steps

Example header, `include/hesaplayici/topla.hpp`:

```cpp
#pragma once

namespace hesaplayici {
    [[nodiscard]] int topla(int a, int b) noexcept;
}
```

Implementation file, `src/topla.cpp`:

```cpp
#include "hesaplayici/topla.hpp"

namespace hesaplayici {
    int topla(int a, int b) noexcept {
        return a + b;
    }
}
```

Main program, `src/main.cpp`:

```cpp
#include <iostream>
#include "hesaplayici/topla.hpp"

int main() {
    std::cout << "5 + 7 = " << hesaplayici::topla(5, 7) << '\n';
    return 0;
}
```

### Configure and build the project

Configure using CMakePresets:

```bash
cmake --preset dev-debug
```

Expected output:

```text
-- The CXX compiler identification is AppleClang 17.0.0.17000013
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring done
-- Generating done
-- Build files have been written to: .../tasinabilir-cpp/build/dev-debug
```

Build and run:

```bash
cmake --build --preset build-debug
./build/dev-debug/uygulama
```

Expected output:

```text
5 + 7 = 12
```

## Sources and verification environment

- [CMake documentation — Presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html)
- [Craig Scott — Professional CMake: A Practical Guide](https://crascit.com/professional-cmake/)
- [Modern CMake Guidelines](https://cliutils.gitlab.io/modern-cmake/)

This guide was tested and verified on macOS Sonoma (ARM64) and Ubuntu 24.04 (Linux x86_64) with CMake 3.28, Ninja 1.11, Clang 18 and GCC 14.
