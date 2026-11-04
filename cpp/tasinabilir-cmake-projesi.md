---
translation_key: guide-cpp-tasinabilir-cmake-projesi
lang: tr
title: "CMake ile taşınabilir C++ projesi oluşturmak"
permalink: /cpp/tasinabilir-cmake-projesi/
status: duzenlendi
reviewed: 2026-11-03
scope: Modern CMake (3.21+) ile target tabanlı mimari, CMakePresets, toolchain ve çoklu platform desteği.
---

# CMake ile taşınabilir C++ projesi oluşturmak

Eski CMake pratiklerinde sıkça kullanılan `include_directories()`, `link_libraries()` veya
`set(CMAKE_CXX_FLAGS "...")` gibi genel (global) komutlar, projeler büyüdükçe kütüphanelerin
birbirinin derleme bayraklarını kirletmesine ve platformlar arası taşınabilirliğin bozulmasına
yol açar.

Modern CMake, nesne yönelimli bir yaklaşımla **Hedefler (Targets)** ve bu hedeflerin
**Kullanım Gereksinimleri (Usage Requirements)** üzerine kuruludur. Bu kılavuzda Linux, macOS
ve Windows üzerinde tutarlı çalışan, `CMakePresets.json` ile yapılandırılan ve farklı
derleyicilere temiz şekilde uyarlanan taşınabilir bir C++ projesinin nasıl kurulacağını ele alacağız.

## 1. Hedef tabanlı (Target-Based) mimari ve görünürlük

Modern CMake'te her kütüphane veya çalıştırılabilir dosya bir hedeftir (`add_library`, `add_executable`).
Bir hedefin bağımlılıkları tanımlanırken üç temel görünürlük düzeyi kullanılır:

- `PRIVATE`: Yalnızca bu hedefin kendi kaynak dosyalarını derlerken gereklidir; bu hedefe bağlanan dış hedeflere aktarılmaz.
- `INTERFACE`: Bu hedefin kendi derlenmesinde kullanılmaz, yalnızca bu hedefe bağlanan tüketicilere aktarılır (örneğin yalnızca başlıklardan oluşan / header-only kütüphaneler).
- `PUBLIC`: Hem hedefin kendisi için gereklidir hem de bu hedefe bağlanan tüm dış hedeflere otomatik olarak devredilir (geçişli bağımlılık).

### Örnek kütüphane ve uygulama ayrımı

Proje dizin yapısı:

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

Kök `CMakeLists.txt` dosyası:

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
{: data-filename="CMakeLists.txt"}

Bu modelde `target_compile_features(hesaplayici PUBLIC cxx_std_20)` yazıldığında, `uygulama`
hedefi `hesaplayici`ya bağlandığı anda C++20 standardını otomatik olarak kazanır.
Elle `-std=c++20` bayrağı eklenmez; CMake bu gereksinimi GCC, Clang veya MSVC için uygun
derleyici parametresine çevirir.

## 2. CMakePresets ile derleme ortamını standartlaştırma

Farklı geliştiricilerin ve CI/CD sistemlerinin komut satırına uzun `-D` parametreleri girmesini
önlemek için CMake 3.19+ sürümünde gelen `CMakePresets.json` kullanılır.

Proje kökünde `CMakePresets.json`:

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
{: data-filename="CMakePresets.json"}

> [!TIP]
> Geliştiricilerin yerel makineye özel yapılandırmaları için `CMakeUserPresets.json` dosyası
> oluşturulabilir. Bu dosya `.gitignore` listesine eklenmeli, sürüm kontrolüne dahil edilmemelidir.

## 3. Toolchain dosyaları ile derleyici ve ortam ayrımı

Derleyici seçimi veya çapraz derleme yaparken değişkenleri komut satırında geçmek yerine
`CMAKE_TOOLCHAIN_FILE` kullanılır. Toolchain dosyası, CMake'in sistem denetimlerini
başlatmadan önce derleyiciyi ve hedef mimariyi temiz şekilde tanımlamasını sağlar.

Örnek Clang araç zinciri (`cmake/toolchains/clang.cmake`):

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
{: data-filename="cmake/toolchains/clang.cmake"}

Presets içine toolchain bağlamak için `configurePresets` alanına `"toolchainFile": "${sourceDir}/cmake/toolchains/clang.cmake"` eklemek yeterlidir.

## 4. Derleme türleri (Build Types) ve yapılandırıcı farkları

CMake'te derleme türleri iki farklı jeneratör modeline göre yönetilir:

### 1. Tekli yapılandırıcılar (Single-Config: Ninja, Unix Makefiles)

Tek bir derleme dizininde tek bir mod barındırır. Yapılandırma anında `CMAKE_BUILD_TYPE` ile belirlenir:

- `Debug`: Hata ayıklama sembolleri (`-g`), optimizasyon kapalı (`-O0`).
- `Release`: Yüksek optimizasyon (`-O3` veya `/O2`), `NDEBUG` makrosu tanımlı.
- `RelWithDebInfo`: Optimizasyonlu derleme (`-O2`) ve hata ayıklama sembolleri (`-g`). Profilleme ve canlı hata analizi için idealdir.
- `MinSizeRel`: Kod boyutunu küçültmeye odaklanan optimizasyon (`-Os` veya `/Os`).

### 2. Çoklu yapılandırıcılar (Multi-Config: Ninja Multi-Config, Visual Studio, Xcode)

Tek bir yapılandırma ile tüm modları derleyebilir. `CMAKE_BUILD_TYPE` yok sayılır. Derleme anında `--config` bayrağı ile hedef seçilir:

```bash
cmake -B build -G "Ninja Multi-Config"
cmake --build build --config Release
cmake --build build --config Debug
```

Kaynak kod veya kütüphane bağlama sırasında derleme türüne göre özel parametre vermek için
üreteç ifadeleri (generator expressions) kullanılır:

```cmake
target_compile_definitions(uygulama PRIVATE
    $<$<CONFIG:Debug>:DEBUG_LOGGING_ENABLED=1>
)
```

## 5. Uygulama ve derleme adımları

Örnek başlık dosyası `include/hesaplayici/topla.hpp`:

```cpp
#pragma once

namespace hesaplayici {
    [[nodiscard]] int topla(int a, int b) noexcept;
}
```
{: data-filename="include/hesaplayici/topla.hpp"}

Örnek gövde dosyası `src/topla.cpp`:

```cpp
#include "hesaplayici/topla.hpp"

namespace hesaplayici {
    int topla(int a, int b) noexcept {
        return a + b;
    }
}
```
{: data-filename="src/topla.cpp"}

Ana program `src/main.cpp`:

```cpp
#include <iostream>
#include "hesaplayici/topla.hpp"

int main() {
    std::cout << "5 + 7 = " << hesaplayici::topla(5, 7) << '\n';
    return 0;
}
```
{: data-filename="src/main.cpp"}

### Projeyi yapılandırma ve derleme

CMakePresets kullanarak projeyi yapılandırın:

```bash
cmake --preset dev-debug
```

Beklenen çıktı:

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

Projeyi derleyin ve çalıştırın:

```bash
cmake --build --preset build-debug
./build/dev-debug/uygulama
```

Beklenen çıktı:

```text
5 + 7 = 12
```

## Kaynaklar ve doğrulama ortamı

- [CMake Resmi Belgesi - Presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html)
- [Craig Scott - Professional CMake: A Practical Guide](https://crascit.com/professional-cmake/)
- [Modern CMake Guidelines](https://cliutils.gitlab.io/modern-cmake/)

Bu kılavuz, macOS Sonoma (ARM64) ve Ubuntu 24.04 (Linux x86_64) ortamlarında CMake 3.28,
Ninja 1.11, Clang 18 ve GCC 14 ile test edilerek doğrulanmıştır.
