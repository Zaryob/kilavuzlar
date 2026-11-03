---
title: Profiling a C++ application with Tracy
permalink: /en/cpp/tracy-ile-profilleme/
status: duzenlendi
reviewed: 2026-11-03
scope: C++ instrumentation, CMake integration and frame/zone analysis using Tracy
  Profiler (v0.11+).
lang: en
translation_key: guide-cpp-tracy-ile-profilleme
translation_of: /cpp/tracy-ile-profilleme/
translated: '2026-11-03'
---

# Profiling a C++ application with Tracy

Traditional sampling profilers such as `perf` and `gprof` show statistically which functions consume time. Instrumentation offers another view: investigating a particular delayed frame, thread waits and the duration of an individual function scope.

**Tracy Profiler** is a nanosecond-resolution **instrumentation profiler** for modern C and C++ applications, focused on frames, memory and threads. It uses a client–server architecture:

```text
[ C++ Uygulamanız (Client) ]  ─── TCP (Port 8086) ───►  [ tracy-profiler (GUI Server) ]
   (ZoneScoped, FrameMark)                                 (Zaman çizelgesi, FPS, Bellek)
```

## 1. Integrating Tracy with CMake (FetchContent)

The Tracy client is distributed as source built with your application rather than as a precompiled library. In a modern CMake project, `FetchContent` provides a convenient integration:

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
> Without `TRACY_ENABLE`, Tracy macros compile to no-ops (`((void)0)`). Background sockets and allocation tracking are removed, eliminating instrumentation overhead in Release builds distributed to users.

## 2. Instrumentation macros

Include `#include <tracy/Tracy.hpp>` and mark measurement points in your source.

### Zones

- `ZoneScoped`: place at the start of a function or scope (`{ ... }`). Using RAII, it automatically records start/end times, the filename and line number.
- `ZoneScopedN("ÖzelAd")`: names a zone to distinguish substeps within a function.
- `ZoneScopedC(0x00FF88)`: colours the timeline box with the specified RGB value.

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

### Frame boundaries

- `FrameMark`: place at the end of the main event or rendering loop. It marks completion of a frame and adds a column to the FPS chart.
- `FrameMarkNamed("FizikAdimi")`: marks independently running background frames, such as a 50 Hz physics simulation.

```cpp
while (uygulamaCalisiyor) {
    OlaylariTopla();
    DunyayiGuncelle(dt);
    EkranaCiz();
    
    FrameMark; // Ana karenin bittiğini bildirir
}
```

### Allocation tracking

Use `TracyAlloc` and `TracyFree` to track dynamic allocations. To track allocations throughout the application, you can overload global `new` and `delete`:

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

## 3. Running the Tracy server (`tracy-profiler`)

To run the graphical profiler:

- **macOS (Homebrew):** `brew install tracy`
- **Linux:** build from the repository’s `profiler/` directory:

```bash
cd tracy/profiler
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/tracy-profiler
```

Start your application; it should appear in the client list at the upper left. Click `Connect` to begin streaming data.

## 4. Frame and zone analysis workflow

The Tracy interface has four main areas.

### 1. Frame ribbon

Each frame appears as a vertical bar at the top:
- **Green bars:** frames below the target duration, such as 16.6 ms for 60 FPS.
- **Red/yellow spikes:** long frames that cause visible stuttering or dropped frames.
- Clicking a red bar focuses the timeline on the start of that frame.

### 2. Timeline and threads

Each application thread is drawn as a horizontal track. Regions marked with `ZoneScoped` appear as nested boxes:
- Zoom with the mouse wheel, down to nanosecond scales.
- Right-click and drag to navigate the timeline.

### 3. Zone statistics

Open **Statistics** to inspect aggregate function measurements:
- **Total Time:** where the application spends the most time overall.
- **Self Time:** time spent in a function’s own body, excluding child calls; particularly useful for finding algorithmic bottlenecks.
- **Call Count:** reveals tiny functions called unnecessarily thousands of times per frame.

### 4. Memory graph

Shows whether allocated memory grows continuously over time, suggesting a memory leak. Unfreed allocations are listed with their source locations.

## Sources and verification environment

- [Tracy Profiler repository](https://github.com/wolfpld/tracy)
- [Tracy user manual (PDF)](https://github.com/wolfpld/tracy/releases/latest/download/tracy.pdf)

This guide was tested and verified on Ubuntu 24.04 and macOS Sonoma using Tracy v0.11.1, CMake 3.28 and Clang 18.
