---
translation_key: guide-cpp-vcpkg-bagimlilik-yonetimi
lang: tr
title: "vcpkg ile C++ bağımlılıklarını yönetmek"
permalink: /cpp/vcpkg-bagimlilik-yonetimi/
status: duzenlendi
reviewed: 2026-11-03
scope: vcpkg Manifest modu (vcpkg.json), CMakePresets entegrasyonu ve ikili önbellekleme (binary caching).
---

# vcpkg ile C++ bağımlılıklarını yönetmek

C++ ekosisteminde kütüphane yönetimi uzun yıllar boyunca işletim sisteminin paket
yöneticisine (`apt`, `brew`, `vcpkg install <paket>`) veya el ile derleyip `/usr/local` altına
kopyalamaya dayanıyordu. Bu "klasik mod", farklı geliştiricilerin ve CI sunucularının
farklı kütüphane sürümlerini kullanmasına ve derleme tutarsızlıklarına yol açar.

Modern vcpkg, tıpkı Rust'ın `Cargo.toml` veya Node.js'in `package.json` yapısında olduğu gibi
**Bildirim Modu (Manifest Mode)** sunar. Bağımlılıklar projenin kök dizinindeki `vcpkg.json`
dosyasında bildirilir ve CMake yapılandırması başladığında otomatik olarak indirilip derlenir.

## 1. Klasik Mod ile Manifest Modu arasındaki farklar

| Özellik | Klasik Mod (`vcpkg install`) | Manifest Modu (`vcpkg.json`) |
| :--- | :--- | :--- |
| **Bağımlılık Tanımı** | Kullanıcının terminalde çalıştırdığı komutlar | Proje kökünde sürüm kontrolüne giren JSON dosyası |
| **Sürüm Kitleme (Pinning)** | Zordur; vcpkg deposunun güncel commit'ine bağlıdır | `builtin-baseline` ve `overrides` ile tam kesinlik |
| **Kurulum Konumu** | Merkezi vcpkg dizini altında global | Projenin kendi `build/vcpkg_installed` dizininde |
| **Ekip Uyumluluğu** | Her geliştirici paketleri elle kurmak zorundadır | Depoyu klonlayan herkes `cmake` çalıştırdığında aynı ortam kurulur |

## 2. Manifest dosyası oluşturma (`vcpkg.json`)

Proje kök dizininde `vcpkg.json` dosyası oluşturun:

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

### Alanların anlamı:

- `builtin-baseline`: Paketlerin hangi vcpkg git commit'inden çözümleneceğini belirten hash'tir. Bu alan sayesinde 2 yıl sonra bile aynı sürümler derlenir. Güncel baseline hash'i `git rev-parse HEAD` komutuyla vcpkg deposundan alınabilir.
- `dependencies`: Projenin ihtiyaç duyduğu kütüphanelerdir. İstenirse opsiyonel özellikler (`features`) veya platform kısıtları (`"platform": "!windows"`) eklenebilir.

### Sürümleri sabitleme (`overrides`)

Baseline dışındaki özel bir sürümü zorlamak istediğinizde `overrides` bloğu eklenir:

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

## 3. CMake entegrasyonu

vcpkg, CMake'in standart paket arama mekanizmasını (`find_package`) besleyen bir araç zinciri
dosyası (`vcpkg.cmake`) sağlar.

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

### `CMakePresets.json` ile vcpkg araç zincirini bağlama

Geliştiricilerin her defasında `-DCMAKE_TOOLCHAIN_FILE=...` yazmasını engellemek için
araç zinciri `CMakePresets.json` dosyasına eklenir:

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
> Ortamınızda `VCPKG_ROOT` değişkeninin tanımlı olduğundan emin olun (örneğin kabuk
> profilinizde `export VCPKG_ROOT=/opt/vcpkg` veya `$HOME/vcpkg`).

## 4. Özel depolar ve şirket içi paketler (Registries)

Açık kaynak kütüphanelerin yanı sıra kendi özel git depolarınızdaki paketleri kullanmak için
proje köküne `vcpkg-configuration.json` dosyası eklenir:

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

Bu sayede `sirket-guvenlik` paketi özel depodan, `fmt` ve `nlohmann-json` ise resmi depodan çekilir.

## 5. İkili önbellekleme (Binary Caching)

vcpkg, derlediği paketleri varsayılan olarak yerel önbellekte saklar. CI/CD sunucularında
veya temiz derlemelerde paketlerin tekrar tekrar saatlerce derlenmesini önlemek için
`VCPKG_BINARY_SOURCES` ortam değişkeni ayarlanabilir:

```bash
# Yerel dosya sistemi önbelleği:
export VCPKG_BINARY_SOURCES="clear;files,/opt/vcpkg-cache,readwrite"

# GitHub Actions ortamında:
export VCPKG_BINARY_SOURCES="clear;gha,readwrite"
```

Aynı paketi ve derleyici kombinasyonunu kullanan derlemelerde vcpkg önceden üretilmiş ikiliyi
saniyeler içinde önbellekten çeker.

## 6. Örnek uygulama ve çalıştırma

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

### Derleme süreci

Projeyi yapılandırın:

```bash
cmake --preset dev-debug
```

Beklenen çıktı:

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

Derleyin ve çalıştırın:

```bash
cmake --build build/dev-debug
./build/dev-debug/uygulama
```

Beklenen çıktı:

```text
Uygulama çalıştı!
JSON Çıktısı: {
  "basari": true,
  "mod": "manifest",
  "proje": "kilavuzlar"
}
```

## Sık karşılaşılan sorunlar ve çözümleri

- **`VCPKG_ROOT not found`**: `vcpkg` komutunun bulunduğu dizini kabuk ortam değişkenlerine (`export VCPKG_ROOT=...`) ekleyin.
- **Triplet uyuşmazlığı**: macOS üzerinde ARM64 için `arm64-osx`, x86_64 için `x64-osx`; Linux üzerinde `x64-linux` veya `arm64-linux` kullanılır. Gerekirse `vcpkg-temel` preseti içine `"VCPKG_TARGET_TRIPLET": "arm64-osx"` tanımlanabilir.
- **Temiz kurulum ihtiyacı**: Bağımlılık ağacında beklenmedik bir sorun çıkarsa projedeki `build/` ve `vcpkg_installed/` dizinlerini silip yeniden yapılandırın.

## Kaynaklar ve doğrulama ortamı

- [Microsoft vcpkg Resmi Belgesi - Manifest Mode](https://learn.microsoft.com/en-us/vcpkg/consume/manifest-mode)
- [vcpkg İkili Önbellekleme Kılavuzu](https://learn.microsoft.com/en-us/vcpkg/users/binarycaching)
- [vcpkg Git Registries](https://learn.microsoft.com/en-us/vcpkg/users/registries)

Bu kılavuz, Ubuntu 24.04 (Linux x86_64) ve macOS Sonoma (ARM64) üzerinde vcpkg 2024-09,
CMake 3.28 ve Ninja 1.11 ile test edilmiştir.
