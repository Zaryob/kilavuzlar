---
translation_key: guide-linux-perf-ile-cpu-darbogazi
lang: tr
title: "Linux'ta perf ile CPU darboğazı bulmak"
permalink: /linux/perf-ile-cpu-darbogazi/
status: duzenlendi
reviewed: 2026-11-20
scope: Linux 6.x çekirdeğinde perf aracı ile CPU örnekleme, çağrı grafikleri, donanım sayaçları ve Brendan Gregg Flame Graph analizi.
---

# Linux'ta perf ile CPU darboğazı bulmak

Linux çekirdeğiyle bütünleşik gelen `perf` aracı, donanımsal Performans İzleme Birimi
(PMU) sayaçlarını ve çekirdek izleme noktalarını (tracepoints) kullanarak uygulamalarda
en çok CPU harcayan fonksiyonları nano-saniye hassasiyetinde tespit eder.

Doğru yapılandırılmış bir `perf` profillemesi; döngü darboğazlarını, CPU'yu tüketen sıcak çağrı
yollarını ve fonksiyon maliyetlerini görsel bir **Alev Grafiği (Flame Graph)** üzerinde
görmemizi sağlar. Donanım sayaçlarıyla desteklendiğinde ise önbellek (L1/L3 cache) ıskalamaları
ve bellek bekleme süreleri net biçimde tespit edilebilir.

## 1. Çekirdek izinleri ve sistem ayarları

Linux çekirdeği güvenlik gerekçesiyle kök (`root`) yetkisi olmayan kullanıcıların
performans sayaçlarına erişimini varsayılan olarak kısıtlar.

### `kernel.perf_event_paranoid` ayarı

Bu ayar, kullanıcıların hangi seviyede profilleme yapabileceğini belirler:

- `4`: Ayrıcalıksız kullanıcılar için `perf` kullanımını tümüyle kapatır. Bu seviye ana çekirdekte yoktur; Ubuntu çekirdeği ekler ve Ubuntu 24.04'te varsayılan değerdir.
- `2`: Kullanıcı kendi süreçlerini yalnızca kullanıcı seviyesinde (userspace) profilleyebilir; çekirdek profilleme kapalıdır (ana çekirdeğin varsayılanı).
- `1`: Kullanıcı kendi süreçlerini çekirdek tarafıyla birlikte profilleyebilir. Sistem geneli (`-a`) veya CPU bazlı profilleme hâlâ kapalıdır.
- `0`: Sistem geneli ve CPU bazlı profillemeye de izin verir; ham izleme noktaları kapalı kalır.
- `-1`: Tüm kısıtlamaları kaldırır (ham izleme noktaları dahil).

Bu kılavuzdaki komutlar yalnızca kendi başlattığınız süreci profillediği için `1` yeterlidir. Ayrıcalıksız bir
kullanıcıyla sistem genelinde kayıt (`perf record -a`) için `0` veya daha düşük bir değer ya da `CAP_PERFMON` gerekir.

Geliştirme ortamınızda geçici olarak izin vermek için:

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

Kalıcı hale getirmek için `/etc/sysctl.d/99-perf.conf` dosyasına yazabilirsiniz:

```bash
echo "kernel.perf_event_paranoid = 1" | sudo tee /etc/sysctl.d/99-perf.conf
```

### `kernel.kptr_restrict` ayarı

Eğer `perf report` çıktısında çekirdek sembolleri `[k] 0x00000000` şeklinde gizlenmiş
görünüyorsa çekirdek adres maskelemesini kaldırın:

```bash
sudo sysctl -w kernel.kptr_restrict=0
```

## 2. Derleme parametreleri: Neden Frame Pointer şarttır?

Profilleme yaparken yapılan en büyük hata, kodu optimizasyonsuz (`-O0`) profillemektir.
Optimizasyonsuz kod tamamen farklı bir derleme biçimi sergiler; asıl darboğazları gizler.

Her zaman **RelWithDebInfo** (`-O2` veya `-O3`, `-g`) ile profilleme yapılmalıdır.
Ancak `-O2` düzeyinde derleyiciler çağrı yığınını tutan çerçeve işaretçisini (`%rbp`)
serbest bırakır (`-fomit-frame-pointer`). Bu durum çağrı yığınının kırılmasına yol açar.

Bu nedenle projenizi mutlaka **`-fno-omit-frame-pointer`** ile derleyin:

```bash
g++ -O2 -g -fno-omit-frame-pointer -o hesaplayici main.cpp
```

## 3. Profil kaydı alma (`perf record`)

Uygulamanızı `perf record` ile çalıştırarak CPU kullanım örnekleri toplayın:

```bash
perf record -F 99 -g -- ./hesaplayici
```

### Parametrelerin anlamı:

- `-F 99`: Saniyede çekirdek başına 99 örnek (sample) alır. Neden 100 değil? Linux çekirdek zamanlayıcısı (kernel timer tick) 100, 250 veya 1000 Hz frekansta çalışır. Tam 100 Hz seçildiğinde örnekleme zamanlayıcı vuruşlarıyla rezonansa girerek veriyi yanıltabilir. 99 Hz bu döngüyü kırar.
- `-g`: Çağrı yığınını (call graph) kaydeder.

### Çağrı grafiği yöntemleri (fp vs dwarf vs lbr)

| Yöntem | Bayrak | Ek Yük (Overhead) | Doğruluk ve Sınırlar |
| :--- | :--- | :--- | :--- |
| **Frame Pointer** | `-g` veya `--call-graph fp` | **%1 - %2 (En düşük)** | `-fno-omit-frame-pointer` gerektirir. Üretim ortamında en temiz yöntemdir. |
| **DWARF** | `--call-graph dwarf,8192` | **%15 - %30 (Yüksek)** | Yığın belleğini kopyalar. `perf.data` dosyası gigabaytlarca büyür; ancak çerçeve işaretçisi olmayan kodda çalışır. |
| **LBR (Last Branch Record)** | `--call-graph lbr` | **Donanımsal (~%0)** | `perf` belgesine göre yalnızca Intel işlemcilerde (Haswell ve sonrası) kullanılabilir ve yalnızca kullanıcı seviyesindeki çağrı zincirini verir. Yığın derinliği sınırlıdır; sanal makinelerde genellikle bulunmaz. |

## 4. Raporlama ve analiz (`perf report` ve `perf annotate`)

Kayıt bittiğinde dizinde `perf.data` dosyası oluşur. Bu veriyi terminalde incelemek için:

```bash
perf report --stdio --hierarchy -g graph,0.5,caller
```

Veya etkileşimli TUI arayüzünü açmak için doğrudan:

```bash
perf report
```

### Çıktıdaki kavramlar:

- **Self**: CPU komut işaretçisinin doğrudan o fonksiyonun kendi gövdesi içindeyken harcadığı süre yüzdesidir.
- **Children**: Fonksiyonun kendisi ve çağırdığı tüm alt fonksiyonların toplam CPU süresidir.

### Makine kodu düzeyinde inceleme (`perf annotate`)

En çok CPU tüketen fonksiyonun üzerine gelip `a` tuşuna basarak (veya terminalden `perf annotate <fonksiyon_adi>`) assembly satırlarını açın:

```text
       │    Disassembly of section .text:
       │    00000000000011a0 <KarmasikHesapla>:
  0.03 │        push   %rbp
  1.20 │        mov    %rsp,%rbp
 42.50 │ 11b0:  mov    (%rdi,%rax,4),%edx     <-- Örneklerin %42.5'i bu komutta toplandı
 51.10 │        add    %edx,%ecx              <-- Örneklerin %51.1'i bu komutta (bağımlılık / kayma)
  4.20 │        inc    %rax
  0.97 │        cmp    %rsi,%rax
       │        jne    11b0
```

> **Önemli: Örnek yoğunluğu tek başına önbellek ıskalamasını veya RAM beklemesini kanıtlamaz!**
>
> `perf record -F 99 -g` varsayılan olarak `cycles` (CPU döngüleri) olayını örnekler. `perf annotate` çıktısındaki yüzde, işlemcinin komut işaretçisinin (instruction pointer) o komut üzerindeyken yakalandığı örneklerin oranını gösterir; doğrudan "RAM'den veri bekleniyor" veya "kesinlikle cache miss var" anlamına gelmez.
>
> Modern işlemcilerde (sırasız yürütme / out-of-order execution, derin işlem hatları) bir komut satırında örnek yığılması birkaç farklı nedenden kaynaklanabilir:
> 1. **Döngü vuruşu:** Komutun çok sık çalıştırılması.
> 2. **Veri bağımlılığı gecikmesi (data dependency stall):** Örneğin yukarıdaki `add` komutu (%51.10), bir önceki `mov` komutunun `%edx` yazmacına getireceği veriyi beklerken işlem hattı durakladığı için yüksek örnek alabilir.
> 3. **Kesme kayması (Instruction skid):** PMU sayacı taştığında çekirdek kesmesi (interrupt) üretilene kadar işlemci birkaç komut ilerleyebilir (Intel PEBS veya AMD IBS gibi hassas donanım mekanizmaları kullanılmadıkça).
>
> Bu nedenle `perf annotate` çıktısındaki örnekleme yoğunluğu tek başına önbellek ıskalaması veya RAM beklemesi olarak yorumlanamaz; mutlaka donanım sayaçlarıyla desteklenmelidir.

### Donanım sayaçlarıyla (PMU) bellek darboğazını doğrulama

Bir fonksiyon veya komut satırındaki sıcak noktanın bellek erişimi kaynaklı olduğunu kanıtlamak için Performans İzleme Birimi (PMU) sayaçlarından yararlanılır:

```bash
# 1. Genel CPU döngüsü, komut sayısı ve önbellek ıskalamalarını ölçün:
perf stat -e cycles,instructions,cache-misses,cache-references,L1-dcache-load-misses,LLC-load-misses -- ./hesaplayici
```

Burada incelenecek temel göstergeler:
- **IPC (Instructions Per Cycle):** Eğer IPC değeri düşükse (örneğin < 1.0) ve `cache-misses` ya da `LLC-load-misses` (Son Seviye Önbellek ıskalamaları) yüksekse, CPU'nun komut yürütmek yerine bellek hiyerarşisinden veri beklerken durakladığı (memory stall) kesinleşir.
- **Topdown analizi:** Modern x86 işlemcilerde `perf stat --topdown -- ./hesaplayici` komutu, darboğazın *Backend Bound -> Memory Bound* (Bellek sınırlı) mu yoksa *Core Bound* (Hesaplama sınırlı) mu olduğunu doğrudan sınıflandırır.

Doğrudan önbellek ıskalamalarını profilleyip hangi fonksiyonların buna yol açtığını görmek için:

```bash
# Önbellek ıskalamalarını örnekleyerek kayıt alın:
perf record -e cache-misses -c 1000 -g -- ./hesaplayici
perf report
```

Bellek erişimlerinin gecikmesini ve verinin hangi önbellek kademesinden (L1, L2, LLC veya RAM) geldiğini satır satır analiz etmek için `perf mem`:

```bash
perf mem record -- ./hesaplayici
perf mem report --stdio
```

## 5. Flame Graph (Alev Grafiği) üretimi

Brendan Gregg tarafından geliştirilen Flame Graph araçları, binlerce satırlık metin raporunu
tek bir etkileşimli SVG dosyasına çevirir.

### Araçları indirme

```bash
git clone https://github.com/brendangregg/FlameGraph.git /tmp/FlameGraph
```

### Tek satırda SVG üretimi

```bash
perf script | /tmp/FlameGraph/stackcollapse-perf.pl | /tmp/FlameGraph/flamegraph.pl > flamegraph.svg
```

### Alev Grafiği nasıl okunur?

- **X Ekseni (Genişlik):** Fonksiyonların alfabetik sıralamasıdır. **Zaman akışı değildir!** Bir kutunun genişliği, o çağrı yığınının toplam CPU örnekleri içindeki payını gösterir. Kutu ne kadar genişse CPU o kadar çok oradadır.
- **Y Ekseni (Yükseklik):** Çağrı derinliğidir (stack depth). En altta `main()`, yukarı doğru çıktıkça onun çağırdığı alt fonksiyonlar yer alır.
- **Düz Tepeler (Plateaus):** Üzerinde başka fonksiyon olmayan geniş ve düz kutular, CPU'yu bizzat tüketen fonksiyonlardır (Self Time). Optimizasyon ilk olarak bu fonksiyonlara odaklanmalıdır.
- **Arama:** Tarayıcıda açtığınızda sağ üstteki "Search" butonuna basarak veya `Ctrl+F` ile sembol arayabilirsiniz; eşleşen kutular pembe renkle parlar.

## Kaynaklar ve doğrulama ortamı

- [Brendan Gregg - Linux perf Examples](https://www.brendangregg.com/perf.html)
- [Linux Çekirdeği perf Wiki](https://perfwiki.github.io/main/)
- [FlameGraph Resmi GitHub Deposu](https://github.com/brendangregg/FlameGraph)
- [Linux çekirdek belgesi: `perf_event_paranoid`](https://docs.kernel.org/admin-guide/sysctl/kernel.html#perf-event-paranoid)
- [`perf-record(1)` kılavuz sayfası](https://man7.org/linux/man-pages/man1/perf-record.1.html)

Bu kılavuz, Ubuntu 24.04 LTS (Linux 6.8 x86_64) üzerinde `linux-tools-generic` 6.8.0
ve FlameGraph araç seti ile gerçek bir C++ iş yükü profillenerek test edilmiştir.
