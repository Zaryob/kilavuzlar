---
translation_key: guide-cpp-vcpkg-bagimlilik-yonetimi
lang: tr
title: "vcpkg ile C++ bağımlılıklarını yönetmek"
permalink: /cpp/vcpkg-bagimlilik-yonetimi/
status: duzenlendi
reviewed: 2026-11-09
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
| **Sürüm Kitleme (Pinning)** | Zordur; vcpkg deposunun güncel commit'ine bağlıdır | `builtin-baseline` ile taban sürümler; `overrides` ile seçili sürümler |
| **Kurulum Konumu** | Merkezi vcpkg dizini altında global | Projenin kendi `build/vcpkg_installed` dizininde |
| **Ekip Uyumluluğu** | Her geliştirici paketleri elle kurmak zorundadır | Depoyu klonlayan herkes `cmake` çalıştırdığında aynı ortam kurulur |

## 2. Manifest dosyası oluşturma (`vcpkg.json`)

Proje kök dizininde `vcpkg.json` dosyası oluşturun:

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

Devam etmeden önce aracı aynı upstream etikette kurun (Git, C++ derleyicisi, CMake ve Ninja gerekir):

```bash
git clone --branch 2024.09.30 https://github.com/microsoft/vcpkg.git "$HOME/vcpkg-kilavuz"
export VCPKG_ROOT="$HOME/vcpkg-kilavuz"
"$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics
# HEAD: c82f74667287d3dc386bce81e44964370c91a289
```

`--depth 1` kullanmayın: sürüm kısıtları ve override’lar sığ checkout’ta bulunmayan geçmiş port ağaçlarını gerektirebilir.

### Alanların anlamı:

- `builtin-baseline`: Paketlerin asgari sürümlerinin alındığı kayıt deposu snapshot’ıdır. Örnekte araç checkout’u ve kayıt deposu upstream `2024.09.30` etiketine sabitlenmiştir. Aynı ikilileri üretmek için derleyici, SDK, triplet, özellikler ve kaynak erişimi de sabitlenmelidir; bu alan tek başına yıllar sonra aynı derlemeyi garanti etmez.
- `dependencies`: Projenin ihtiyaç duyduğu kütüphanelerdir. İstenirse opsiyonel özellikler (`features`) veya platform kısıtları (`"platform": "!windows"`) eklenebilir.

### Sürümleri sabitleme (`overrides`)

Baseline dışındaki özel bir sürümü zorlamak istediğinizde ana manifest’e `overrides` bloğu eklenir. Aşağıdaki isteğe bağlı parça çalıştırılan örnekte kullanılmaz; sonraki sürüm çıktıları override olmadan alınmıştır:

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
{: data-filename="CMakePresets.json"}

> [!NOTE]
> Ortamınızda `VCPKG_ROOT` değişkeninin tanımlı olduğundan emin olun (örneğin kabuk
> profilinizde `export VCPKG_ROOT=/opt/vcpkg` veya `$HOME/vcpkg`).

## 4. Özel depolar ve şirket içi paketler (Registries)

Aşağıdaki bir **şablondur**, çalıştırılabilir örneğe dahil değildir. Gerçek özel kayıt deposu URL’si, 40 karakterli commit’i ve paketleri yoksa bu dosyayı kaydetmeyin. Önce bütün yer tutucuları değiştirin:

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

Bu sayede `sirket-guvenlik` paketi özel depodan, `fmt` ve `nlohmann-json` ise resmi depodan çekilir.

## 5. İkili önbellekleme (Binary Caching)

vcpkg, derlediği paketleri varsayılan olarak yerel önbellekte saklar. CI/CD sunucularında
veya temiz derlemelerde paketlerin tekrar tekrar saatlerce derlenmesini önlemek için
`VCPKG_BINARY_SOURCES` ortam değişkeni ayarlanabilir:

```bash
mkdir -p "$HOME/.cache/vcpkg-kilavuz"
export VCPKG_BINARY_SOURCES="clear;files,$HOME/.cache/vcpkg-kilavuz,readwrite"
```

GitHub Actions’ta aynı `files` sağlayıcısını `actions/cache` ile saklayın; kaldırılmış `x-gha` sağlayıcısını kullanmayın. Checkout ve araç kurulumu sonrasında, araç zinciri sabit Linux runner için örnek adımlar:

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

Aynı paketi ve derleyici kombinasyonunu kullanan derlemelerde vcpkg önceden üretilmiş ikiliyi
saniyeler içinde önbellekten çeker.

## 6. Örnek uygulama ve çalıştırma

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

### Derleme süreci

Projeyi yapılandırın:

```bash
cmake --preset dev-debug
```

Temiz `arm64-osx` çalıştırmasından paket sürümleri özeti (yardımcı portlar ve süreler çıkarıldı):

```text
    cxxopts:arm64-osx@3.2.1
    fmt:arm64-osx@11.0.2#1
    nlohmann-json:arm64-osx@3.11.3#1
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
- [vcpkg İkili Önbellekleme Kılavuzu](https://learn.microsoft.com/en-us/vcpkg/reference/binarycaching)
- [vcpkg Git Registries](https://learn.microsoft.com/en-us/vcpkg/users/registries)

8–9 Kasım 2026: sabit manifest macOS 27.2 ARM64 ve Debian 12 ARM64 üzerinde ikili önbellek kapalıyken kaynaklardan kuruldu; CMake Debug uygulaması derlenip çalıştırıldı. `files` sağlayıcısı ikinci temiz Linux kurulumunda 5/5 paketi önbellekten geri yükledi. Özel kayıt deposu ve Actions hizmeti çalıştırılmadı.
