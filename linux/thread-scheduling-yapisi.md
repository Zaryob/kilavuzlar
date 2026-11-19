---
translation_key: guide-linux-thread-scheduling-yapisi
lang: tr
title: "Linux thread scheduling (iş parçacığı çizelgeleme) yapısı"
permalink: /linux/thread-scheduling-yapisi/
status: duzenlendi
reviewed: 2026-11-19
scope: Linux çekirdeğinde iş parçacığı (thread) temsili, çizelgeleme sınıfları (CFS, EEVDF, Real-Time, Deadline), vruntime mekanizması, bağlam değişimi ve SMP yük dengeleme.
---

# Linux thread scheduling (iş parçacığı çizelgeleme) yapısı

Linux çekirdeği, çoklu görev (multitasking) yürütürken donanım kaynaklarını süreçler (process) ve
iş parçacıkları (thread) arasında paylaştırır. Ancak Linux'un tasarımında geleneksel işletim
sistemlerinden radikal bir fark bulunur: **Çekirdek seviyesinde bağımsız bir "thread" veri yapısı yoktur.**

Gerek tek bir işlem parçası gerekse yüzlerce alt iş parçacığı başlatan devasa bir sunucu uygulaması
olsun, Linux çekirdeği için her yürütme birimi bir `task_struct` nesnesidir. Çizelgeleyici (scheduler),
bu görevleri CPU çekirdeklerine dağıtırken adillik, yanıt süresi (latency) ve işlem hacmi (throughput)
arasındaki hassas dengeyi kurar.

Bu kılavuz; Linux 6.x çekirdeklerinde iş parçacıklarının nasıl temsil edildiğini, modüler çizelgeleme
sınıflarını (`sched_class`), CFS ve Linux 6.6 ile gelen EEVDF algoritmalarını, bağlam değişiminin
(context switch) donanım seviyesindeki maliyetini ve SMP çok çekirdek mimarisindeki yük dengeleme
prensiplerini şemalarla açıklar.

---

## 1. Linux çekirdeğinde iş parçacığı modeli (1:1 NPTL ve `task_struct`)

Geleneksel POSIX standartlarında süreç (adres uzayı sahibi) ile iş parçacığı (yürütme akışı) kavramsal
olarak kesin çizgilerle ayrılır. Linux ise **1:1 İş Parçacığı Modeli** (NPTL - Native POSIX Thread Library)
kullanır; yani kullanıcı uzayındaki her bir `pthread`, çekirdekte tam olarak bir adet `task_struct`
ile eşleşir.

### `clone()` sistem çağrısı ve kaynak paylaşımı

Linux'ta bir süreç oluşturulurken [`fork(2)`](https://zaryob.github.io/syscall/tr/call/fork/), iş parçacığı oluşturulurken ise [`clone(2)`](https://zaryob.github.io/syscall/tr/call/clone/) (veya daha modern [`clone3(2)`](https://zaryob.github.io/syscall/tr/call/clone3/)) sistem çağrısı
kullanılır. Aslında `fork()` ve [`vfork(2)`](https://zaryob.github.io/syscall/tr/call/vfork/) da çekirdeğin içindeki genel `kernel_clone()` fonksiyonuna
yapılan birer çağrıdır; aralarındaki tek fark `clone_flags` parametreleridir:

- `CLONE_VM`: Bellek adres uzayı paylaşılır (`mm_struct`).
- `CLONE_FS`: Dosya sistemi kök ve çalışma dizini bilgileri paylaşılır (`fs_struct`).
- `CLONE_FILES`: Açık dosya tanımlayıcıları (file descriptors) tablosu paylaşılır (`files_struct`).
- `CLONE_SIGHAND`: Sinyal işleyicileri paylaşılır.
- `CLONE_THREAD`: Görev, çağıran sürecin iş parçacığı grubuna (Thread Group) dahil edilir.

```text
+-----------------------------------------------------------------------------------+
|                        SÜREÇ VE İŞ PARÇACIĞI MİMARİSİ                             |
+-----------------------------------------------------------------------------------+

     Kullanıcı Uzayı (Userspace)
     +-------------------------------------------------------------------------+
     | Süreç (PID: 4100)                                                       |
     |                                                                         |
     |  +--------------------+   +--------------------+   +-----------------+  |
     |  | Ana Thread (TID 1) |   | İşçi Thread (TID 2)|   | G/Ç Thread (TID)|  |
     |  | Kullanıcı Yığını   |   | Kullanıcı Yığını   |   | Kullanıcı Yığını|  |
     |  +---------+----------+   +---------+----------+   +--------+--------+  |
     +------------|------------------------|-----------------------|-----------+
                  | clone(CLONE_VM|...)    |                       |
     Çekirdek     |                        |                       |
     (Kernel)     v                        v                       v
     +------------------------+  +--------------------+  +--------------------+
     | task_struct (Lider)    |  | task_struct        |  | task_struct        |
     |  pid: 4100 (TID)       |  |  pid: 4101 (TID)   |  |  pid: 4102 (TID)   |
     |  tgid: 4100 (PID)      |  |  tgid: 4100 (PID)  |  |  tgid: 4100 (PID)  |
     |  se: sched_entity      |  |  se: sched_entity  |  |  se: sched_entity  |
     |  thread_info / stack   |  |  thread_info/stack |  |  thread_info/stack |
     +-----------+------------+  +---------+----------+  +---------+----------+
                 |                         |                       |
                 +------------+------------+-----------------------+
                              |
                              +---> mm_struct     ──► [Ortak Sayfa Tabloları / Bellek]
                              +---> files_struct  ──► [Ortak Açık Dosya Tanımlayıcıları]
                              +---> signal_struct ──► [Ortak Sinyal Eylemleri]
```

### PID, TID ve TGID karmaşası

Kullanıcı uzayı ile çekirdek uzayı arasında terim farkı bulunur:

| Kavram | Kullanıcı Uzayı (POSIX API) | Çekirdek İçi (`task_struct`) | Açıklama |
| :--- | :--- | :--- | :--- |
| **Süreç Kimliği** | [`getpid(2)`](https://zaryob.github.io/syscall/tr/call/getpid/) | `p->tgid` (Thread Group ID) | Grubun ana sürecinin (liderinin) kimliğidir. |
| **İş Parçacığı Kimliği** | [`gettid(2)`](https://zaryob.github.io/syscall/tr/call/gettid/) / `pthread_self()` | `p->pid` (Process ID) | Çekirdeğin her bir `task_struct` nesnesine verdiği benzersiz tekil kimliktir. |

Çizelgeleyici, bir görevi CPU'ya atarken `tgid` ile ilgilenmez; doğrudan `task_struct` içindeki
`sched_entity` yapısını kuyruğa sokar.

---

## 2. Çizelgeleyici sınıfları ve öncelik hiyerarşisi (`sched_class`)

Linux çekirdeği nesne yönelimli benzeri bir fonksiyon tablosu (`struct sched_class`) yapısıyla
modüler bir çizelgeleyici kullanır. Her çizelgeleme sınıfı, görevlerin kuyruğa alınması (`enqueue_task`),
çıkarılması (`dequeue_task`) ve sıradaki görevin seçilmesi (`pick_next_task`) için kendi kurallarını belirler.

Bir CPU üzerinde yeni bir iş parçacığı seçileceğinde (`pick_next_task()`), çekirdek sınıfları
en katı öncelikten en düşüğe doğru sırayla tarar.

```text
+-----------------------------------------------------------------------------------+
|               ÇİZELGELEME SINIFLARI VE ÖNCELİK HİYERARŞİSİ                        |
+-----------------------------------------------------------------------------------+

   Öncelik     Çizelgeleme Sınıfı     Politika (Policy)          Kullanım Alanı
  ===================================================================================
     0         stop_sched_class       (Özel Çekirdek)          CPU Hotplug, RCU, Migration
     |
     v         dl_sched_class         SCHED_DEADLINE           Sert Gerçek Zamanlı (EDF/CBS)
               ----------------------------------------------------------------------
     1-99      rt_sched_class         SCHED_FIFO, SCHED_RR     Yumuşak Gerçek Zamanlı (Ses, Motor)
               ----------------------------------------------------------------------
    100-139    fair_sched_class       SCHED_NORMAL (OTHER)     Standart Kullanıcı Süreçleri
    (Nice                             SCHED_BATCH              Toplu İşler (Arka Plan)
    -20..+19)                         SCHED_IDLE               Düşük Öncelikli Görevler
               ----------------------------------------------------------------------
    140        idle_sched_class       SCHED_IDLE (swapper)     İş Yokken CPU'yu Uyutan Görev
```

### 1. `stop_sched_class`
En yüksek öncelikli sınıftır. Normal kullanıcı veya çekirdek süreçleri bu sınıfa atanamaz.
Bir çekirdeği kapatırken (CPU hotplug) veya çekirdek kilitlenmelerinde diğer tüm görevleri anında
durdurmak (`stop_machine`) amacıyla kullanılır.

### 2. `dl_sched_class` (`SCHED_DEADLINE`)
Son teslim tarihi tabanlı (Earliest Deadline First - EDF) ve Sabit Bant Genişliği Sunucusu
(Constant Bandwidth Server - CBS) mimarisini kullanır. Bir görevin üç parametresi vardır:
- **Runtime**: Periyot başına ihtiyaç duyulan CPU süresi.
- **Deadline**: Görevin bitmesi gereken azami süre.
- **Period**: Görevin tekrarlanma sıklığı.

Eğer sistem `Runtime / Period` oranına göre CPU kapasitesini aşmayacağını garanti edebiliyorsa
(Admission Control), bu sınıftaki iş parçacıkları RT ve CFS görevlerinin önüne geçerek kesin
zamanlamayla yürütülür.

### 3. `rt_sched_class` (`SCHED_FIFO`, `SCHED_RR`)
POSIX gerçek zamanlı iş parçacıklarını yönetir. 1 ile 99 arasında statik öncelik alır:
- `SCHED_FIFO` (First-In, First-Out): Önceliği eşit veya daha yüksek başka bir görev gelmedikçe,
  I/O beklemesine girmedikçe veya kendisi CPU'yu bırakmadıkça ([`sched_yield(2)`](https://zaryob.github.io/syscall/tr/call/sched_yield/)) kesintisiz çalışır.
- `SCHED_RR` (Round-Robin): `SCHED_FIFO` ile aynıdır, ancak eşit öncelikteki görevler arasında
  zaman dilimi (timeslice - genellikle 100 ms) esasına göre döner.

> [!WARNING]
> Bir `SCHED_FIFO` görevi sonsuz döngüye girerse çekirdeğin geri kalanının (ve masaüstünün)
> donmasına yol açabilir. Çekirdek bunu önlemek için varsayılan olarak her 1 saniyede 50 milisaniyeyi
> gerçek zamanlı olmayan görevlere ayırır (`/proc/sys/kernel/sched_rt_runtime_us = 950000`).

### 4. `fair_sched_class` (`SCHED_NORMAL` / `SCHED_OTHER`)
Sistemdeki görevlerin %99'unun çalıştığı ana sınıftır. Nice değerleri (-20 ile +19) bu sınıfta geçerlidir.
Linux 2.6.23'ten Linux 6.5'e kadar **CFS** (Completely Fair Scheduler), Linux 6.6 sonrasında ise
**EEVDF** (Earliest Eligible Virtual Deadline First) algoritmasını kullanır.

### 5. `idle_sched_class`
Kuyrukta çalışacak hiçbir görev kalmadığında devreye girer. Her CPU çekirdeği için çekirdek başlangıcında
oluşturulan `swapper/X` (PID 0) iş parçacığıdır. CPU'yu enerji tasarrufu durumlarına (C-states, `hlt` / `mwait`) sokar.

---

## 3. Çekirdek veri yapıları: Per-CPU Runqueue (`struct rq`)

Modern çok çekirdekli sistemlerde küresel tek bir çalışma kuyruğu kullanmak felaketle sonuçlanır:
Her çekirdek bir görev almak için aynı küresel kilide (spinlock) başvurur ve aşırı kilit çekişmesi
(lock contention) nedeniyle performans çöker.

Bu yüzden Linux çekirdeğinde her mantıksal CPU çekirdeğinin kendisine ait bağımsız bir
**`struct rq` (Runqueue)** nesnesi vardır.

```text
+-----------------------------------------------------------------------------------+
|                        PER-CPU RUNQUEUE (struct rq)                               |
+-----------------------------------------------------------------------------------+

     CPU 0                                              CPU 1
  +---------------------------------------+          +---------------------------+
  | struct rq                             |          | struct rq                 |
  |  raw_spinlock_t lock                  |          |  ...                      |
  |  struct task_struct *curr ──► (Çalışan)|          |                           |
  |                                       |          |                           |
  |  +---------------------------------+  |          |                           |
  |  | dl_rq (SCHED_DEADLINE)          |  |          |                           |
  |  |   rb_root_cached (Deadline EDF) |  |          |                           |
  |  +---------------------------------+  |          |                           |
  |                                       |          |                           |
  |  +---------------------------------+  |          |                           |
  |  | rt_rq (SCHED_FIFO / SCHED_RR)   |  |          |                           |
  |  |   prio_array (100 öncelik)      |  |          |                           |
  |  |   [0..99] bitmap + kuyruklar    |  |          |                           |
  |  +---------------------------------+  |          |                           |
  |                                       |          |                           |
  |  +---------------------------------+  |          |                           |
  |  | cfs_rq (SCHED_NORMAL / EEVDF)   |  |          |                           |
  |  |   rb_root_cached (Kırmızı-Siyah)|  |          |                           |
  |  |   min_vruntime = 14205820 ns    |  |          |                           |
  |  +---------------------------------+  |          |                           |
  +---------------------------------------+          +---------------------------+
```

### Alt kuyrukların mimarisi

1. **`dl_rq`**: Görevleri son teslim tarihlerine göre sıralayan kırmızı-siyah ağaçtır.
2. **`rt_rq`**: 100 seviyeli bir dizi (`struct rt_prio_array`) ve bir bit haritasıdır (bitmap).
   Çekirdek, `sched_find_first_bit()` komutuyla donanımsal bit tarama komutlarını (`bsfl`/`clz`)
   kullanarak $O(1)$ sürede en yüksek öncelikli RT kuyruğunu anında bulur.
3. **`cfs_rq`**: Normal görevleri sanal çalışma sürelerine (`vruntime`) veya EEVDF uygunluk
   kriterlerine göre kırmızı-siyah ağaçta tutar.

---

## 4. Adil çizelgeleme mantığı: CFS'ten EEVDF'ye Sanal Çalışma Süresi

Standart görevler (`fair_sched_class`) için temel ilke, CPU zamanını görevlerin ağırlıklarına
(nice değerlerine) orantılı olarak kusursuz biçimde paylaştırmaktır.

### Nice değerleri ve ağırlık tablosu

Linux'ta nice aralığı `-20` (en yüksek öncelik) ile `+19` (en düşük öncelik) arasındadır.
Varsayılan değer `0`dır. Çekirdek, bu değerleri doğrudan birer çarpan tablosuna
(`sched_prio_to_weight`) dönüştürür:

```c
const int sched_prio_to_weight[40] = {
    /* -20 */ 88761, 71755, 56483, ...
    /*   0 */ 1024,
    /* +19 */ 15
};
```

Nice değerindeki her 1 puanlık artış veya azalış, görevin aldığı CPU ağırlığında yaklaşık **%10**
oranında bir değişime karşılık gelir. Örneğin Nice -5 olan bir görev, Nice 0 olan bir göreve kıyasla
yaklaşık 3 kat daha fazla CPU zamanı hakkı elde eder.

### Sanal Çalışma Süresi (`vruntime`) hesabı

Bir iş parçacığı fiziksel CPU üzerinde $\Delta \text{exec}$ kadar gerçek süre harcadığında,
çekirdek onun sanal çalışma süresini (`vruntime`) şu formülle artırır:

$$\text{vruntime}_{\text{yeni}} = \text{vruntime}_{\text{eski}} + \Delta \text{exec} \times \left( \frac{\text{NICE\_0\_LOAD}}{\text{ağırlık}} \right)$$

- **Nice 0 Görevi (Ağırlık = 1024)**: Çarpan $1024 / 1024 = 1.0$ olur. Fiziksel saat ne kadar ilerlerse `vruntime` da birebir o kadar artar.
- **Düşük Öncelikli Görev (Nice +10, Ağırlık = 110)**: Çarpan $1024 / 110 \approx 9.3$ olur. Görev 1 ms çalışsa bile sanal saati 9.3 ms ilerler; hızla ağacın sağına kayar ve sırasını kaybeder.
- **Yüksek Öncelikli Görev (Nice -5, Ağırlık = 3121)**: Çarpan $1024 / 3121 \approx 0.32$ olur. Fiziksel olarak 3 ms çalışsa bile sanal saati yalnızca 1 ms ilerler; ağacın solunda kalarak CPU'yu daha sık alır.

### Kırmızı-Siyah Ağaç (Red-Black Tree) organizasyonu

Görevler `vruntime` değerlerine göre dengeli bir ikili arama ağacında (Red-Black Tree) tutulur:

```text
+-----------------------------------------------------------------------------------+
|               KIRMIZI-SİYAH AĞAÇ VE SANAL SÜRE (vruntime) DÜZENİ                  |
+-----------------------------------------------------------------------------------+

                           [ Düğüm B ]
                         vruntime = 120 ms
                           /           \
                          /             \
               [ Düğüm A ]               [ Düğüm C ]
             vruntime = 95 ms          vruntime = 160 ms
               /
              /
     [ rb_leftmost ]
     vruntime = 80 ms  <-- ÇİZELGELEYİCİ BİR SONRAKİ İŞ OLARAK BUNU SEÇER (O(1))
     (En az çalışmış,
      en çok hak sahibi)
```

Çekirdek ağacın en solundaki elemanı her zaman önbellekte tutar (`rb_leftmost`). Bu sayede
sıradaki iş parçacığını seçmek $O(1)$ sürede tamamlanır. Ağaçtan çıkarma ve ekleme ise $O(\log N)$
karmaşıklıktadır.

### Linux 6.6 ile Gelen Büyük Değişim: CFS'ten EEVDF'ye

CFS 15 yıl boyunca çok başarılı olsa da önemli bir kusuru vardı: **Gecikme (latency) kontrolü.**
CFS yalnızca adil süre garantisi veriyordu; interaktif bir iş parçacığının (örneğin fare hareketi,
ses paketi veya veri tabanı soket yanıtı) ne kadar sürede uyanıp CPU alacağını garanti edemiyordu.
Bunu çözmek için kullanılan sezgisel yamalar (`sched_latency`, `min_granularity`) karmaşık ve kırılgandı.

Linux 6.6 çekirdeği ile Peter Zijlstra tarafından geliştirilen **EEVDF (Earliest Eligible Virtual Deadline First)**
algoritmasına geçildi.

```text
+-----------------------------------------------------------------------------------+
|                           EEVDF ÇALIŞMA MEKANİZMASI                               |
+-----------------------------------------------------------------------------------+

   1. Uygunluk (Eligibility) Koşulu:
      Lag_i = V (Ortalama Sanal Zaman) - vruntime_i
      * Eğer Lag_i >= 0 ise (yani görev hakkından az çalışmışsa): UYGUN (ELIGIBLE)
      * Eğer Lag_i < 0 ise (görev hakkından fazla çalışmışsa): UYGUN DEĞİL

   2. Sanal Teslim Süresi (Virtual Deadline):
      d_i = vruntime_i + (İstenen Zaman Dilimi q_i / Ağırlık w_i)

   3. Seçim Kuralı:
      Çizelgeleyici, sadece UYGUN (Lag >= 0) olan adaylar arasından
      en küçük d_i değerine sahip olanı çalıştırır!
```

EEVDF sayesinde, küçük zaman dilimlerine ihtiyaç duyan interaktif veya gecikmeye duyarlı iş
parçacıkları küçük $q_i$ talep ederek erken bir teslim süresi ($d_i$) alır ve uzun süren hesaplama
görevlerinin önüne hemen geçebilir.

---

## 5. Bağlam değişimi (Context Switching) anatomisi

Çizelgeleyici bir sonraki `task_struct` nesnesini seçtikten sonra, CPU'yu eski iş parçacığından alıp
yeni iş parçacığına devretmelidir. Bu operasyon `context_switch()` fonksiyonu ile gerçekleştirilir.

```text
+-----------------------------------------------------------------------------------+
|                          BAĞLAM DEĞİŞİMİ AKIŞ ŞEMASI                              |
+-----------------------------------------------------------------------------------+

                       [ __schedule() Tetiklendi ]
                                    |
                                    v
                         [ pick_next_task() ]
                                    |
                                    v
                        [ context_switch(prev, next) ]
                                    |
        +---------------------------+---------------------------+
        |                                                       |
        v                                                       v
  1. Bellek Bağlamı Değişimi                              2. İşlemci Yazmaç Değişimi
     (switch_mm_irqs_off)                                    (switch_to)
        |                                                       |
  +-----+------------------------------+                  +-----+----------------------+
  | prev->mm == next->mm ?             |                  | %rsp (Yığın Göstericisi)   |
  |                                    |                  | %rip (Komut Göstericisi)   |
  | [EVET] -> AYNI SÜRECİN THREAD'LERİ |                  | Genel Yazmaçlar (%rbx..)   |
  |   * CR3 değiştirilmez!             |                  | FS_BASE / GS_BASE (TLS)    |
  |   * TLB boşaltılmaz!               |                  | FPU/AVX (XSAVE/XRSTOR)     |
  |   * ÇOK HIZLI GEÇİŞ                |                  +----------------------------+
  |                                    |                                |
  | [HAYIR] -> FARKLI SÜREÇLER         |                                v
  |   * CR3 güncellenir (Sayfa Tablosu)|                    [ Yeni Görev Yürütülür ]
  |   * TLB temizlenir (veya PCID)     |
  +------------------------------------+
```

### 1. Bellek bağlamı değişimi (`switch_mm_irqs_off`)

Eğer çalışan önceki görev ile sıradaki görev aynı sürecin iki farklı iş parçacığı ise
(`prev->mm == next->mm`), adres uzayları birebir aynıdır:
- Bellek sayfa tabloları (x86_64 mimarisinde `CR3` denetim yazmacı) **kesinlikle değiştirilmez**.
- İşlemcinin Sanal Adres Önbelleği (TLB - Translation Lookaside Buffer) **geçerliliğini korur**.

İşte iş parçacığı (thread) kullanmanın süreç (process) değiştirmeye göre sağladığı devasa performans
avantajının fiziksel nedeni budur. Süreç değişiminde `CR3` yazılır, TLB önbelleği ıskalamaları
(cache miss) tavan yapar ve bellek gecikmesi katlanır.

### 2. İşlemci ve yazmaç değişimi (`switch_to`)

İşlemcinin donanım yazmaçları bir görevden diğerine aktarılır:
1. Donanımsal çağrı yığını göstericisi (`%rsp`) ve komut işaretçisi (`%rip`) değiştirilir.
2. Çağrılanın korumakla yükümlü olduğu genel yazmaçlar (`%rbx`, `%rbp`, `%r12` - `%r15`) yığına yazılır ve okunur.
3. Thread-Local Storage işaretçileri (`FS_BASE` / `GS_BASE`) yeni iş parçacığına güncellenir.
4. FPU ve vektör yazmaçları (SSE, AVX-512) modern çekirdeklerde `XSAVE` ve `XRSTOR` komutlarıyla
   güvenli ve optimize şekilde korunur.

### Gönüllü (Voluntary) ve Zorunlu (Involuntary) geçişler

- **Gönüllü Geçiş (Voluntary Context Switch)**: İş parçacığı bir disk okuması, ağ soketi, `sleep()`
  veya bir `pthread_mutex_lock()` beklediğinde kendiliğinden CPU'yu bırakır.
- **Zorunlu Geçiş (Involuntary / Preemptive Context Switch)**: Zamanlayıcı kesmesi (`scheduler_tick`)
  geldiğinde veya daha yüksek öncelikli bir görev uyandığında, çekirdek mevcut görevin bayraklarına
  `TIF_NEED_RESCHED` işaretini koyar. Çekirdek uzayından kullanıcı uzayına dönülürken görev zorla
  CPU'dan indirilir.

---

## 6. Çok çekirdekli sistemlerde (SMP / NUMA) yük dengeleme

Tek bir çekirdeğin kuyruğu boş kalırken diğerinin kuyruğunda 50 iş parçacığı birikirse sistem verimsizleşir.
Linux, **Çizelgeleme Etki Alanları (Scheduling Domains)** hiyerarşisi üzerinden yük dengelemesi yapar.

```text
+-----------------------------------------------------------------------------------+
|               NUMA VE ÇİZELGELEME ETKİ ALANI (sched_domain) MİMARİSİ              |
+-----------------------------------------------------------------------------------+

  NUMA Düğümü 0 (Bellek Bankası 0)            NUMA Düğümü 1 (Bellek Bankası 1)
  +---------------------------------------+   +---------------------------------------+
  | Soket 0                               |   | Soket 1                               |
  |  Paylaşımlı L3 Önbellek (LLC Domain)  |   |  Paylaşımlı L3 Önbellek (LLC Domain)  |
  |                                       |   |                                       |
  |  Çekirdek 0 (MC)     Çekirdek 1 (MC)  |   |  Çekirdek 2 (MC)     Çekirdek 3 (MC)  |
  |  +----------------+  +--------------+ |   |  +----------------+  +--------------+ |
  |  | SMT 0  | SMT 1 |  | SMT 2 | SMT 3| |   |  | SMT 4  | SMT 5 |  | SMT 6 | SMT 7| |
  |  | CPU 0  | CPU 1 |  | CPU 2 | CPU 3| |   |  | CPU 4  | CPU 5 |  | CPU 6 | CPU 7| |
  |  +--------+-------+  +-------+------+ |   |  +--------+-------+  +-------+------+ |
  +---------------------------------------+   +---------------------------------------+
        \                                                    /
         \====== Hızlı QPI / UPI / Infinity Fabric Interconnect =====/
```

### Dengeleme Hiyerarşisi ve Maliyet

Yük dengeleme en ucuz seviyeden en pahalıya doğru denenir:
1. **SMT Seviyesi (Hyper-Threading)**: CPU 0 ile CPU 1 aynı fiziksel çekirdeğin L1/L2 önbelleğini paylaşır. Görev taşımak neredeyse bedavadır.
2. **MC Seviyesi (Multi-Core)**: Aynı çip üzerindeki çekirdekler L3 önbelleği (LLC) paylaşır. Önbellek ısınma kaybı düşüktür.
3. **NUMA Seviyesi**: Görevi Soket 0'dan Soket 1'e taşımak, iş parçacığının kendi belleğine uzaktan (interconnect üzerinden) erişmesine neden olur ve ciddi bellek gecikmesi yaratır. Bu yüzden NUMA seviyesinde göç ancak dengesizlik çok belirgin olduğunda yapılır.

### Çekirdek İzolasyonu ve Çekirdek Çizelgelemesi (Core Scheduling)

- **CPU Afinitesi (`taskset` / [`sched_setaffinity(2)`](https://zaryob.github.io/syscall/tr/call/sched_setaffinity/))**: Bir iş parçacığını belirli çekirdeklere kilitleyerek L1/L2 önbellek ısınmasını (cache warmth) korur; mevcut maske [`sched_getaffinity(2)`](https://zaryob.github.io/syscall/tr/call/sched_getaffinity/) ile okunabilir.
- **Core Scheduling ([`prctl(2)`](https://zaryob.github.io/syscall/tr/call/prctl/))**: Linux 5.14 ile gelen `PR_SCHED_CORE` özelliği; aynı fiziksel çekirdeğin SMT kardeşlerinde yalnızca birbiriyle güven ilişkisi olan iş parçacıklarının eşzamanlı çalışmasını sağlar. Bu sayede Spectre ve MDS gibi donanımsal yan kanal saldırıları önlenir.

---

## 7. Uygulamalı izleme, analiz ve öncelik yönetimi

İş parçacıklarının çizelgeleme davranışlarını doğrudan sistem üzerinde inceleyebileceğiniz pratik komutlar:

### İş parçacıklarını ve çekirdek atamalarını listeleme

Sistemdeki iş parçacıklarını, hangi CPU çekirdeğinde çalıştıklarını ve önceliklerini görmek için:

```bash
ps -eo pid,tid,class,rtprio,ni,pri,psr,comm -L | grep -v "TS   -"
```

Parametrelerin anlamı:
- `tid`: İş parçacığı kimliği (Thread ID).
- `class`: Çizelgeleme sınıfı (`TS` = Normal/Fair, `FF` = FIFO, `RR` = Round-Robin, `DL` = Deadline).
- `rtprio`: Gerçek zamanlı öncelik (1-99).
- `ni`: Nice değeri (-20 ile +19).
- `psr`: İş parçacığının o anda atandığı işlemci çekirdeği (Processor core).

Canlı olarak iş parçacığı bazında izlemek için:

```bash
top -H
```

### Gönüllü ve zorunlu bağlam değişimlerini (Context Switch) ölçme

Bir sürecin veya iş parçacığının ne sıklıkla bağlam değişimine uğradığını görmek:

```bash
pidstat -w -t -p <PID> 1
```

Örnek çıktı:

```text
14:22:01      UID      TGID       TID   cswch/s nvcswch/s  Command
14:22:02     1000      4520         -      2.00    148.00  hesaplayici
14:22:02     1000         -      4520      1.00     50.00  |__hesaplayici
14:22:02     1000         -      4521      1.00     98.00  |__worker_1
```

- `cswch/s` (Voluntary): Gönüllü bağlam değişimi. Yüksekse iş parçacığı kilit (mutex), I/O veya soket bekliyor demektir.
- `nvcswch/s` (Non-voluntary): Zorunlu bağlam değişimi. Yüksekse iş parçacığı CPU sınırına takılıyor ve zamanlayıcı tarafından zorla kesiliyor demektir.

### Çekirdek çizelgeleme istatistiklerini doğrudan `/proc` üzerinden okuma

Belirli bir iş parçacığının sanal çalışma süresi (`vruntime`) ve bekleme istatistikleri `/proc` altında tutulur:

```bash
cat /proc/<PID>/task/<TID>/sched
```

Örnek çıktı kesiti:

```text
worker_1 (4521, #threads: 2)
-------------------------------------------------------------------
se.exec_start                                :       1425890.124502
se.vruntime                                  :         15420.892014
se.sum_exec_runtime                          :          1250.410293
se.nr_migrations                             :                    4
nr_switches                                  :                  340
nr_voluntary_switches                        :                   12
nr_involuntary_switches                      :                  328
```

### Öncelik değiştirme: `chrt` ve `renice`

`chrt` aracı, çekirdeğin [`sched_setscheduler(2)`](https://zaryob.github.io/syscall/tr/call/sched_setscheduler/) ve [`sched_setattr(2)`](https://zaryob.github.io/syscall/tr/call/sched_setattr/) sistem çağrıları üzerinden çalışır; sorgulama için ise [`sched_getscheduler(2)`](https://zaryob.github.io/syscall/tr/call/sched_getscheduler/) ve [`sched_getattr(2)`](https://zaryob.github.io/syscall/tr/call/sched_getattr/) kullanılır.

Çalışan bir iş parçacığını `SCHED_FIFO` sınıfına 50 öncelikle geçirmek:

```bash
sudo chrt -f -p 50 <TID>
```

Çizelgeleme sınıfını sorgulamak:

```bash
chrt -p <TID>
```

Örnek çıktı:

```text
pid 4521's current scheduling policy: SCHED_FIFO
pid 4521's current scheduling priority: 50
```

### Çizelgeleme gecikmelerini `perf sched` ile ölçme

Bir iş parçacığı çalışmaya hazır hale geldiği (wake-up) an ile CPU'ya fiilen alındığı an arasındaki
gecikmeyi (scheduling latency) tespit etmek:

```bash
sudo perf sched record -- sleep 2
sudo perf sched latency
```

Örnek analiz raporu:

```text
 -----------------------------------------------------------------------------------------------------------------
  Task                  |   Runtime ms  | Switches | Avg delay ms | Max delay ms | Max delay start     | Max delay at       |
 -----------------------------------------------------------------------------------------------------------------
  worker_1:4521         |   1820.450 ms |      450 |     0.012 ms |     0.185 ms |   142589.102345 s   |   142589.102530 s  |
  kworker/u16:2:120     |     12.100 ms |       45 |     0.004 ms |     0.021 ms |   142588.940120 s   |   142588.940141 s  |
 -----------------------------------------------------------------------------------------------------------------
```

Bu rapordaki `Avg delay ms` ve `Max delay ms`, iş parçacığının çalışmaya hazır olduğu halde CPU
boşalana kadar ne kadar süre kuyrukta bekletildiğini gösterir. Gerçek zamanlı sistem optimizasyonunda
bu değerin asgariye indirilmesi hedeflenir.

---

## Kaynaklar ve doğrulama ortamı

- [Linux Çekirdek Belgesi: CFS Scheduler](https://docs.kernel.org/scheduler/sched-design-CFS.html)
- [Linux Çekirdek Belgesi: Deadline Task Scheduling](https://docs.kernel.org/scheduler/sched-deadline.html)
- [Peter Zijlstra: EEVDF Scheduler Patchset (Linux Kernel Archives)](https://lore.kernel.org/lkml/20230531124603.650795323@infradead.org/)
- [Robert Love: Linux Kernel Development (3rd Edition) - Chapter 4: Process Scheduling](https://www.oreilly.com/library/view/linux-kernel-development/9780768696974/)
- [`sched(7)` kılavuz sayfası](https://man7.org/linux/man-pages/man7/sched.7.html)

### İlgili sistem çağrıları (Linux Sistem Çağrısı Referansı)

- [`clone(2)`](https://zaryob.github.io/syscall/tr/call/clone/): Yeni iş parçacığı veya alt süreç oluşturma.
- [`clone3(2)`](https://zaryob.github.io/syscall/tr/call/clone3/): Genişletilebilir bayrak yapısıyla modern `clone` arayüzü.
- [`fork(2)`](https://zaryob.github.io/syscall/tr/call/fork/) ve [`vfork(2)`](https://zaryob.github.io/syscall/tr/call/vfork/): Süreç çatallama çağrıları.
- [`getpid(2)`](https://zaryob.github.io/syscall/tr/call/getpid/) ve [`gettid(2)`](https://zaryob.github.io/syscall/tr/call/gettid/): Süreç ve iş parçacığı kimliklerini sorgulama.
- [`sched_yield(2)`](https://zaryob.github.io/syscall/tr/call/sched_yield/): CPU'yu gönüllü olarak bırakma.
- [`sched_setaffinity(2)`](https://zaryob.github.io/syscall/tr/call/sched_setaffinity/) ve [`sched_getaffinity(2)`](https://zaryob.github.io/syscall/tr/call/sched_getaffinity/): CPU çekirdek afinitesini belirleme ve sorgulama.
- [`sched_setscheduler(2)`](https://zaryob.github.io/syscall/tr/call/sched_setscheduler/) ve [`sched_getscheduler(2)`](https://zaryob.github.io/syscall/tr/call/sched_getscheduler/): Çizelgeleme sınıfı ve öncelik atama.
- [`sched_setattr(2)`](https://zaryob.github.io/syscall/tr/call/sched_setattr/) ve [`sched_getattr(2)`](https://zaryob.github.io/syscall/tr/call/sched_getattr/): SCHED_DEADLINE parametreleri ve EEVDF dilim süreleri yönetimi.
- [`prctl(2)`](https://zaryob.github.io/syscall/tr/call/prctl/): `PR_SCHED_CORE` ile çekirdek izolasyonu ve güvenlik yapılandırması.

Bu kılavuzdaki kavramlar ve komutlar, Ubuntu 24.04 LTS (Linux 6.8.0-48 x86_64) ve Debian 12
(Linux 6.6+ çekirdek) üzerinde `util-linux`, `procps` ve `linux-tools-generic` araçları ile
test edilerek doğrulanmıştır.
