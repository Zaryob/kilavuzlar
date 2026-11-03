---
translation_key: guide-cpp-gcc-clang-gecis-problemleri
lang: tr
title: "GCC'den Clang'e geçerken karşılaşılan problemler"
permalink: /cpp/gcc-clang-gecis-problemleri/
status: duzenlendi
reviewed: 2026-11-03
scope: C++17/C++20/C++23 projelerinin GCC'den LLVM/Clang derleyicisine taşınması, ABI, linker ve standart kütüphane farkları.
---

# GCC'den Clang'e geçerken karşılaşılan problemler

Yıllarca GCC ile derlenmiş büyük bir C++ kod tabanını LLVM/Clang'e taşımak; daha hızlı
derleme süreleri, gelişmiş statik analiz (`clang-tidy`), modern bağlayıcı (`lld`) ve üstün
hata ayıklama sembolleri vaat eder. Ancak pratikte "GCC ile uyarısız derlenen kod Clang ile
de derlenir" varsayımı yanlıştır.

Clang, ISO C++ standartlarına ve iki aşamalı şablon çözümlemesine (two-phase lookup) GCC'den
çok daha katı yaklaşır. Ayrıca bağlayıcı (linker), standart kütüphane (`libstdc++` vs `libc++`)
ve ABI uyumluluğunda kritik tuzaklar barındırır.

## 1. Standart kütüphane tuzakları: `libstdc++` vs `libc++`

Linux üzerinde Clang varsayılan olarak sistemdeki GNU `libstdc++` kütüphanesini kullanır.
macOS üzerinde ise Apple Clang yalnızca LLVM'in `libc++` kütüphanesini tanır.

### Geçişli başlık dosyası kirliliği (Transitive Header Inclusions)

GCC'nin `libstdc++` başlıkları (örneğin `<vector>` veya `<iostream>`), tarihsel olarak
birçok standart başlığı kendi içinde dolaylı (geçişli) olarak dahil eder. Geliştiriciler
farkında olmadan `<cstdint>`, `<utility>` veya `<limits>` eklemeden `uint32_t`, `std::pair`
veya `std::numeric_limits` kullanabilir.

LLVM'in `libc++` kütüphanesi ise başlık bağımsızlığına çok sıkı uyar. Bu kod Clang ile
derlendiğinde anında şu hatalar alınır:

```text
error: 'uint32_t' does not name a type; did you mean 'u_int32_t'?
error: no member named 'pair' in namespace 'std'
```

**Çözüm:** Eksik olan `#include <cstdint>`, `#include <utility>` veya `#include <limits>`
satırlarını doğrudan ilgili kaynak veya başlık dosyasına ekleyin.

### Karışık nesne bağlama ve ABI uyuşmazlığı

Bir kütüphaneyi GCC (`libstdc++`) ile, uygulamanın kendisini ise Clang + `libc++` ile
derleyip birbirine bağlayamazsınız:

- `libc++`, C++ sembollerini `std::__1::` satır içi (inline) ad alanında manglerken, `libstdc++` ise `std::__cxx11::` ad alanını kullanır.
- `std::string` veya `std::vector` bellek yerleşimi (memory layout) iki kütüphane arasında tamamen farklıdır.

Bu iki dünyayı aynı süreçte karıştırmak tanımsız davranışlara (Undefined Behavior),
çökmelere ve linker hatalarına yol açar.

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

`lld`, GNU `ld`ye göre ODR (One Definition Rule) ihlallerine ve çift sembol tanımlarına
çok daha az tolerans gösterir.

### LTO (Link Time Optimization) Bayt Kodu Uyumsuzluğu

GCC ve Clang, LTO için tamamen farklı ara temsil (IR) formatları üretir:

- GCC `-flto`: ELF bölümlerinde **GIMPLE** bayt kodu oluşturur.
- Clang `-flto`: ELF bölümlerinde **LLVM Bitcode** (`.llvmbc`) oluşturur.

> [!WARNING]
> GCC ile LTO kullanılarak derlenmiş bir statik kütüphane (`.a`), Clang LTO ile
> derlenen bir projeye bağlanamaz. `lld` bağlayıcısı GIMPLE kodunu çözümleyemez. LTO
> kullanılacaksa tüm bağımlılıklar aynı derleyici ailesiyle derlenmelidir.

## 3. Clang'in katı dil kuralları ve şablon denetimleri

### İki Aşamalı Şablon Araması (Two-Phase Template Lookup)

GCC, şablon türetilmiş sınıflarda taban sınıf üyelerinin aranmasını uzun yıllar boyunca
örnekleme (instantiation) anına kadar gevşek bırakmıştır. Clang ise C++ standardını katı
şekilde uygular:

```cpp
template <typename T>
struct Taban {
    void calis();
};

template <typename T>
struct Turemis : Taban<T> {
    void baslat() {
        calis(); // GCC derleyebilir; Clang HATA verir!
    }
};
```

Clang hata mesajı:

```text
error: use of undeclared identifier 'calis'
note: must qualify identifier to find this declaration in dependent base class
```

**Neden:** `Taban<T>`, `T` parametresine bağlı bir tiptir (dependent base). Derleyici
ayrıştırma (parsing) aşamasında `calis` fonksiyonunun taban sınıfta olduğunu varsayamaz.

**Çözüm:** Çağrıyı `this->calis();` veya `Taban<T>::calis();` olarak niteleyin.

### Örtük Kopyalama Kurucusunun Silinmesi (Deleted Copy Constructor)

C++11 standardına göre (madde §12.8), bir sınıfta kullanıcı tanımlı bir **taşıma kurucusu
(move constructor)** veya **taşıma atama operatörü** varsa, derleyici artık örtük bir
kopyalama kurucusu (copy constructor) üretmez (`= delete` kabul edilir).

GCC geriye dönük uyumluluk için bu durumlarda yalnızca uyarı verirken, Clang doğrudan
derleme hatası üretir:

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
> İki farklı OpenMP çalışma zamanı CPU çekirdeklerini paylaşmaya çalışırken derhal kilitlenmelere
> (deadlock) veya bellek ihlallerine (SIGSEGV) neden olur.

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
- [C++ Standard Core Language Defect Reports - Two-phase Lookup](https://www.open-std.org/jtc1/sc22/wg21/)

Bu belgedeki senaryolar, Ubuntu 24.04 üzerinde GCC 14.2 ve Clang 18.1 derleyicileri
ile test edilerek doğrulanmıştır.
