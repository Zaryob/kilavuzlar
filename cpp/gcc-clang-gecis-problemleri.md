---
translation_key: guide-cpp-gcc-clang-gecis-problemleri
lang: tr
title: "GCC'den Clang'e geçerken karşılaşılan problemler"
permalink: /cpp/gcc-clang-gecis-problemleri/
status: duzenlendi
reviewed: 2026-11-09
scope: C++17/C++20/C++23 projelerinin GCC'den LLVM/Clang derleyicisine taşınması, ABI, linker ve standart kütüphane farkları.
---

# GCC'den Clang'e geçerken karşılaşılan problemler

Yıllarca GCC ile derlenmiş büyük bir C++ kod tabanını LLVM/Clang'e taşımak; daha hızlı
derleme süreleri, gelişmiş statik analiz (`clang-tidy`), modern bağlayıcı (`lld`) ve üstün
hata ayıklama sembolleri vaat eder. Ancak pratikte "GCC ile uyarısız derlenen kod Clang ile
de derlenir" varsayımı yanlıştır.

Her iki derleyici de iki aşamalı şablon aramasını uygular; bu, genel bir “GCC kabul eder, Clang reddeder” ayrımı değildir. Bağlayıcı, standart kütüphane (`libstdc++` ve `libc++`) ve ABI farklarını ayrı değerlendirmek gerekir.

## 1. Standart kütüphane tuzakları: `libstdc++` vs `libc++`

Linux üzerinde Clang varsayılan olarak sistemdeki GNU `libstdc++` kütüphanesini kullanır.
macOS üzerinde Apple Clang varsayılan olarak LLVM `libc++` kullanır.

### Geçişli başlık dosyası kirliliği (Transitive Header Inclusions)

GCC'nin `libstdc++` başlıkları (örneğin `<vector>` veya `<iostream>`), tarihsel olarak
birçok standart başlığı kendi içinde dolaylı (geçişli) olarak dahil eder. Geliştiriciler
farkında olmadan `<cstdint>`, `<utility>` veya `<limits>` eklemeden `uint32_t`, `std::pair`
veya `std::numeric_limits` kullanabilir.

Geçişli include’lar kütüphane ve sürüme göre değişir; derleyiciler arasında garantili fark değildir. Kesin bir eksik başlık örneği için hiç include olmadan `std::uint32_t value = 0;` derleyin. Clang şu hatayı verir:

```text
error: use of undeclared identifier 'std'
```

**Çözüm:** Eksik olan `#include <cstdint>`, `#include <utility>` veya `#include <limits>`
satırlarını doğrudan ilgili kaynak veya başlık dosyasına ekleyin.

### Karışık nesne bağlama ve ABI uyuşmazlığı

GCC (`libstdc++`) ile derlenmiş kütüphane ile Clang + `libc++` kullanan uygulama arasında STL nesneleri taşıyan bir C++ arayüzü doğrudan uyumlu kabul edilmemelidir:

- `libc++`, C++ sembollerini `std::__1::` satır içi (inline) ad alanında manglerken, `libstdc++` ise `std::__cxx11::` ad alanını kullanır.
- `std::string` veya `std::vector` bellek yerleşimi (memory layout) iki kütüphane arasında tamamen farklıdır.

C++ kütüphane nesnelerini bu sınırdan geçirmek tanımsız davranış, çökme veya linker hatası doğurabilir. Ayrı sahiplik kurallarıyla tasarlanmış bir C ABI sınırı farklıdır.

### `libstdc++` Çift ABI Sorunu (`_GLIBCXX_USE_CXX11_ABI`)

GCC 5 ile birlikte C++11 uyumlu yeni bir `std::string` ABI'ı (SSO - Short String Optimization)
tanıtıldı. Eski sistemlerde derlenmiş üçüncü taraf ticari kütüphaneler halen eski COW (Copy-On-Write)
string modelini (`_GLIBCXX_USE_CXX11_ABI=0`) kullanıyor olabilir.

Clang ile bu kütüphanelere bağlanırken bağlayıcı şu hatayı verir:

```text
undefined reference to `Fonksiyon(std::__cxx11::basic_string<char, ...>)'
```

Eğer üçüncü taraf kütüphaneyi yeniden derleme şansınız yoksa Clang derleme bayraklarına
geçici olarak `-D_GLIBCXX_USE_CXX11_ABI=0` eklenmelidir.

## 2. Bağlayıcı (Linker) ve LTO uyumsuzlukları

### Bağlayıcı seçimi: `ld.bfd` vs `lld`

GCC varsayılan olarak GNU `ld` (`ld.bfd`) veya `gold` kullanır. Clang ile çalışırken
en yüksek hız avantajını elde etmek için LLVM'in bağlayıcısı `lld` tercih edilir:

```bash
clang++ -fuse-ld=lld main.o -o uygulama
```

Her iki bağlayıcı da normalde çift güçlü sembol tanımını reddeder. Pek çok ODR ihlalinin teşhisi zorunlu değildir; `lld` seçimi bir ODR doğruluk denetimi değildir.

### LTO (Link Time Optimization) Bayt Kodu Uyumsuzluğu

GCC ve Clang, LTO için tamamen farklı ara temsil (IR) formatları üretir:

- GCC `-flto`: ELF bölümlerinde **GIMPLE** bayt kodu oluşturur.
- Clang `-flto`: Nesne dosyası olarak **LLVM bitcode** üretir. `-fembed-bitcode` ile ELF içine gömülen bitcode ayrı bir akıştır.

> [!WARNING]
> GCC ile LTO kullanılarak derlenmiş bir statik kütüphane (`.a`), Clang LTO ile
> derlenen bir projeye bağlanamaz. `lld` bağlayıcısı GIMPLE kodunu çözümleyemez. LTO
> kullanılacaksa tüm bağımlılıklar aynı derleyici ailesiyle derlenmelidir.

## 3. Taşınabilir dil kuralları ve şablon denetimleri

### İki Aşamalı Şablon Araması (Two-Phase Template Lookup)

GCC iki aşamalı aramayı 3.4’ten beri uygular. Her iki derleyici de normal standart modunda aşağıdaki niteliksiz bağımlı taban çağrısını reddeder. GCC `-fpermissive` bazı hataları uyarıya çevirebilir; taşınabilir bir çözüm değildir:

```cpp
template <typename T>
struct Taban {
    void calis();
};

template <typename T>
struct Turemis : Taban<T> {
    void baslat() {
        calis(); // Both GCC and Clang reject this call.
    }
};
```

Clang hata mesajı:

```text
error: use of undeclared identifier 'calis'
```

**Neden:** `Taban<T>`, `T` parametresine bağlı bir tiptir (dependent base). Derleyici
ayrıştırma (parsing) aşamasında `calis` fonksiyonunun taban sınıfta olduğunu varsayamaz.

**Çözüm:** Çağrıyı `this->calis();` veya `Taban<T>::calis();` olarak niteleyin.

### Örtük Kopyalama Kurucusunun Silinmesi (Deleted Copy Constructor)

C++11 standardına göre (madde §12.8), bir sınıfta kullanıcı tanımlı bir **taşıma kurucusu
(move constructor)** veya **taşıma atama operatörü** varsa, derleyici artık örtük bir
kopyalama kurucusu (copy constructor) üretmez (`= delete` kabul edilir).

Bu durumda kopyalama girişimini hem GCC hem Clang reddeder. Örneğin aşağıdaki tam programı derleyin:

```cpp
struct Baglanti {
    Baglanti() = default;
    Baglanti(Baglanti&&) = default;
};
int main() {
    Baglanti a;
    Baglanti b(a); // Both GCC and Clang reject copying.
}
```

```text
error: call to implicitly-deleted copy constructor of 'Baglanti'
```

**Çözüm:** Sınıfa açıkça `= default` veya özel kopyalama mantığı tanımlayın:

```cpp
Baglanti(const Baglanti&) = default;
Baglanti& operator=(const Baglanti&) = default;
```

### Değişken Uzunluklu Diziler (VLA - Variable Length Arrays)

GCC, C99 standardında bulunan VLA (`int dizi[n];`) yapısını C++ kodunda da bir GNU eklentisi
olarak kabul eder. Ancak VLA standart C++'ta yer almaz.

Clang, sınıflar veya karmaşık nesneler içeren VLA yapılarını reddeder ve `-Wvla` uyarıları üretir.
Güvenli ve taşınabilir çözüm `std::vector<int> dizi(n);` veya dinamik bellek kullanmaktır.

## 4. OpenMP ve Dinamik Çalışma Zamanı Çakışmaları

GCC, OpenMP iş parçacığı havuzu için GNU `libgomp` kütüphanesini kullanır.
Clang ise LLVM'in `libomp` kütüphanesini kullanır:

```bash
# Ubuntu üzerinde Clang OpenMP desteği:
sudo apt-get install -y libomp-dev
clang++ -fopenmp main.cpp -o uygulama
```

> [!CAUTION]
> Aynı süreç içerisinde hem `libgomp` hem de `libomp` kütüphanelerinin yüklenmesine
> (örneğin biri paylaşımlı kütüphaneden, diğeri ana uygulamadan) asla izin vermeyin.
> Birlikte yüklenmeleri kaynak çekişmesi, kilitlenme veya çalışma zamanı hatası riski taşır; her durumda derhal çökme garantisi yoktur.

## 5. Taşıma Kontrol Listesi (Migration Checklist)

| İnceleme Alanı | Kontrol Edilecek Husus | Önerilen Düzeltme |
| :--- | :--- | :--- |
| **Başlıklar** | Eksik `<cstdint>`, `<utility>` içermeleri | İlgili başlıkları doğrudan ekleyin |
| **Şablonlar** | Bağımlı taban sınıf çağrıları | `this->fonksiyon()` nitelemesi kullanın |
| **Bağlayıcı** | LTO nesne uyumu | Tüm nesneleri Clang ile derleyin (`-fuse-ld=lld`) |
| **Uyarılar** | `-Werror` altındaki Clang uyarıları | `-Wno-unknown-warning-option` ile derleyiciye özgü bayrakları ayırın |
| **OpenMP** | `libgomp` / `libomp` karışımı | Yalnızca tek bir OpenMP çalışma zamanı bağlayın |

## Kaynaklar ve doğrulama ortamı

- [LLVM Clang Compiler User's Manual](https://clang.llvm.org/docs/UsersManual.html)
- [GCC to Clang Migration Guide - Chromium Project](https://chromium.googlesource.com/chromium/src/+/main/docs/clang.md)
- [C++ Standard Core Language Defect Reports - Two-phase Lookup](https://gcc.gnu.org/onlinedocs/gcc/Name-lookup.html)

8–9 Kasım 2026: eksik başlık, bağımlı taban, silinen kopyalama ve VLA örnekleri Debian 12 ARM64 üzerinde GCC 12 ve Clang 14 ile, düzeltilmiş varyantları da dahil derlendi. Bu kontrol bütün ABI, OpenMP ve bağlayıcı birleşimlerinin doğrulanması değildir.
