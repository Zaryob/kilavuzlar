---
translation_key: guide-cpp-tracy-ile-profilleme
lang: tr
title: "Tracy ile C++ uygulamasını profillemek"
permalink: /cpp/tracy-ile-profilleme/
status: duzenlendi
reviewed: 2026-11-03
scope: Tracy Profiler (v0.11+) ile C++ enstrümantasyonu, CMake entegrasyonu, frame ve zone analizi.
---

# Tracy ile C++ uygulamasını profillemek

Geleneksel örnekleme (sampling) profilleme araçları (örneğin `perf` veya `gprof`), kodun
hangi fonksiyonlarda zaman geçirdiğini istatistiksel olarak gösterir; ancak belirli bir
karenin (frame) neden geciktiğini, iş parçacıklarının birbirini nasıl beklediğini veya
özel bir fonksiyon bloğunun kaç nanosaniye sürdüğünü gerçek zamanlı izleyemez.

**Tracy Profiler**, modern C ve C++ uygulamaları için geliştirilmiş nanosaniye hassasiyetinde,
çerçeve (frame), bellek ve iş parçacığı odaklı bir **enstrümantasyon (instrumentation)**
profilleyicisidir. İstemci-sunucu (Client-Server) mimarisine sahiptir:

```text
[ C++ Uygulamanız (Client) ]  ─── TCP (Port 8086) ───►  [ tracy-profiler (GUI Server) ]
   (ZoneScoped, FrameMark)                                 (Zaman çizelgesi, FPS, Bellek)
```

## 1. CMake ile Tracy entegrasyonu (FetchContent)

Tracy istemcisi önceden derlenmiş bir kütüphane olarak değil, uygulamanızla birlikte
derlenen kaynak dosyaları halinde sunulur. Modern CMake projelerinde en temiz entegrasyon
`FetchContent` ile sağlanır:

```cmake
cmake_minimum_required(VERSION 3.21)
project(TracyOrnek LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Profilleme anahtarı
option(PROFILING_ENABLED "Tracy Profiler'ı etkinleştir" ON)

if(PROFILING_ENABLED)
    include(FetchContent)
    
    # Yalnızca GUI bağlandığında veri toplayarak bellek tasarrufu yap
    set(TRACY_ENABLE ON CACHE BOOL "" FORCE)
    set(TRACY_ON_DEMAND ON CACHE BOOL "" FORCE)
    
    FetchContent_Declare(
        tracy
        GIT_REPOSITORY https://github.com/wolfpld/tracy.git
        GIT_TAG        v0.11.1
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(tracy)
endif()

add_executable(oyun_motoru src/main.cpp)

# Çağrı yığını unwinding için çerçeve işaretçilerini koru
target_compile_options(oyun_motoru PRIVATE -fno-omit-frame-pointer)

if(PROFILING_ENABLED)
    target_link_libraries(oyun_motoru PRIVATE Tracy::TracyClient)
    target_compile_definitions(oyun_motoru PRIVATE TRACY_ENABLE)
endif()
```

> [!TIP]
> `TRACY_ENABLE` bayrağı tanımlanmadığında tüm Tracy makroları derleme aşamasında
> boş bir koda (`((void)0)`) dönüşür. Arka plan soketi ve bellek izleyiciler tamamen
> koddan çıkarılır; böylece son kullanıcıya dağıtılan Release derlemelerinde **sıfır ek yük** garantilenir.

## 2. Kod içi enstrümantasyon makroları

Kaynak kodunuzda `#include <tracy/Tracy.hpp>` başlığını ekleyerek ölçüm noktalarını belirleyin:

### Bölge (Zone) Ölçümü

- `ZoneScoped`: Fonksiyonun veya kapsam bloğunun (`{ ... }`) başlangıcına konur. RAII prensibiyle bloğun başlangıç ve bitiş zamanını, dosya adını ve satır numarasını otomatik kaydeder.
- `ZoneScopedN("ÖzelAd")`: İsimlendirilmiş bölge tanımlar. Fonksiyon içindeki alt adımları ayırmak için kullanılır.
- `ZoneScopedC(0x00FF88)`: Zaman çizelgesinde kutuyu belirtilen RGB renginde boyar.

```cpp
void DunyayiGuncelle(float deltaZaman) {
    ZoneScoped; // "DunyayiGuncelle" fonksiyonunu profiller
    
    {
        ZoneScopedN("CarpismaTesti");
        FizikCarpismalariniHesapla();
    }

    {
        ZoneScopedNC("YapayZeka", 0xFFAA00); // Turuncu renkli bölge
        YapayZekaKararlariniVer();
    }
}
```

### Kare (Frame) Sınırları

- `FrameMark`: Ana olay veya render döngüsünün en sonuna konur. Tracy bu makroyu gördüğünde bir karenin tamamlandığını anlar ve FPS grafiğinde dikey bir sütun oluşturur.
- `FrameMarkNamed("FizikAdimi")`: Ana render döngüsünden bağımsız çalışan arka plan iş parçacıkları (örneğin 50 Hz çalışan fizik motoru) için kullanılır.

```cpp
while (uygulamaCalisiyor) {
    OlaylariTopla();
    DunyayiGuncelle(dt);
    EkranaCiz();
    
    FrameMark; // Ana karenin bittiğini bildirir
}
```

### Bellek Takibi (Allocation Tracking)

Dinamik bellek tahsislerini izlemek için `TracyAlloc` ve `TracyFree` kullanılır. Uygulama
genelindeki tüm bellek hareketlerini izlemek için global `new`/`delete` operatörleri
aşırı yüklenebilir:

```cpp
#if defined(TRACY_ENABLE)
void* operator new(std::size_t boyut) {
    void* ptr = std::malloc(boyut);
    TracyAlloc(ptr, boyut);
    return ptr;
}

void operator delete(void* ptr) noexcept {
    TracyFree(ptr);
    std::free(ptr);
}
#endif
```

## 3. Tracy Sunucusunu (`tracy-profiler`) çalıştırma

Tracy GUI arayüzünü çalıştırmak için:

- **macOS (Homebrew):** `brew install tracy`
- **Linux:** Tracy deposundaki `profiler/` dizininden derleyebilirsiniz:

```bash
cd tracy/profiler
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/tracy-profiler
```

Uygulamanızı başlattığınızda arayüzün sol üst kısmındaki istemci listesinde görünür.
`Connect` butonuna bastığınız anda veri akışı başlar.

## 4. Frame ve Zone analizi iş akışı

Tracy arayüzü dört ana bölümden oluşur:

### 1. Üst Kare Şeridi (Frame Ribbon)

Arayüzün en üstünde her kare dikey bir çubuk olarak yer alır:
- **Yeşil Çubuklar:** Hedef kare süresinin (örneğin 60 FPS için 16.6 ms) altında kalan akıcı kareler.
- **Kırmızı/Sarı Sıçramalar (Spikes):** Anlık takılmalara (frame drop) yol açan uzun kareler.
- Herhangi bir kırmızı çubuğa tıkladığınızda zaman çizelgesi doğrudan o karenin başladığı ana odaklanır.

### 2. Zaman Çizelgesi ve İş Parçacıkları (Timeline)

Uygulamanızdaki her iş parçacığı yatay bir hat olarak çizilir. `ZoneScoped` ile işaretlediğiniz
bölgeler iç içe geçmiş hiyerarşik kutular halinde akar:
- Fare tekerleği ile yatayda nanosaniye ölçeğine kadar yakınlaşabilirsiniz.
- Sağ tık + sürükleme ile zaman çizelgesinde gezinebilirsiniz.

### 3. İstatistik Tablosu (Zone Statistics)

Arayüzdeki **Statistics** penceresini açarak tüm fonksiyonların kümülatif raporunu inceleyin:
- **Total Time (Toplam Süre):** Uygulama genelinde en çok vaktin nerede harcandığını gösterir.
- **Self Time (Öz Süre):** Fonksiyonun kendi gövdesinde harcanan süredir; alt fonksiyonların çağrı süreleri düşülmüştür. Gerçek algoritma darboğazlarını bulmak için en önemli metriktir.
- **Call Count (Çağrı Sayısı):** Bir karenin içinde gereksiz yere binlerce kez çağrılan mikro fonksiyonları ortaya çıkarır.

### 4. Bellek Grafiği

Tahsis edilen bellek miktarının zamanla sürekli artıp artmadığını (Memory Leak) gösterir.
Serbest bırakılmamış bellek blokları doğrudan kaynak kod satırıyla listelenir.

## Kaynaklar ve doğrulama ortamı

- [Tracy Profiler GitHub Deposu](https://github.com/wolfpld/tracy)
- [Tracy Resmi Kullanım Kılavuzu (PDF)](https://github.com/wolfpld/tracy/releases/latest/download/tracy.pdf)

Bu kılavuz, Ubuntu 24.04 ve macOS Sonoma üzerinde Tracy v0.11.1, CMake 3.28
ve Clang 18 ile test edilmiş ve doğrulanmıştır.
