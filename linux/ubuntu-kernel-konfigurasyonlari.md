---
translation_key: guide-linux-ubuntu-kernel-konfigurasyonlari
lang: tr
title: "Ubuntu çekirdek yapılandırmaları: generic, lowlatency ve HWE"
permalink: /linux/ubuntu-kernel-konfigurasyonlari/
status: duzenlendi
reviewed: 2026-11-19
scope: Ubuntu 22.04 LTS ve 24.04 LTS üzerinde linux-generic, linux-lowlatency, HWE ve OEM/realtime çekirdek mimarileri, derleme bayrakları, kurulum ve GRUB yönetimi.
---

# Ubuntu çekirdek yapılandırmaları: generic, lowlatency ve HWE

Linux çekirdeği (kernel), donanım kaynaklarını yöneten ve kullanıcı alanı (userspace) süreçlerinin
donanımla güvenli iletişim kurmasını sağlayan işletim sisteminin temel katmanıdır. Çekirdek monolitik
bir mimariye sahip olsa da derleme zamanı seçenekleri (`Kconfig` bayrakları), zamanlayıcı (scheduler)
ayarları ve güncelleme yaşam döngüleri farklı iş yükleri için optimize edilebilir.

Ubuntu, tek bir çekirdek ikilisini (binary) tüm kullanım senaryolarına dayatmak yerine farklı
ihtiyaçlar için özelleştirilmiş resmi çekirdek varyantları sunar:

- **`linux-generic`**: Genel amaçlı sunucu, masaüstü ve bulut iş yüklerinde en yüksek veri işleme verimi (throughput) ve enerji verimliliği sağlayan varsayılan çekirdek.
- **`linux-lowlatency`**: Ses/video prodüksiyonu, canlı yayın, endüstriyel veri toplama ve düşük gecikme gerektiren interaktif süreçler için optimize edilmiş, saat kesme sıklığı yüksek (1000 Hz) ve tam öncelik kesmeli (preemptive) çekirdek.
- **`HWE` (Hardware Enablement)**: Uzun süreli destek (LTS) sürümlerinde yeni nesil işlemcileri (CPU), grafik kartlarını (GPU) ve ağ donanımlarını desteklemek için ara sürümlerin güncel çekirdeklerini LTS tabanına taşıyan donanım etkinleştirme yığını.

```text
                               ┌──────────────────────────────────────────────┐
                               │             Ubuntu Linux Çekirdekleri        │
                               └──────────────────────┬───────────────────────┘
                                                      │
                     ┌────────────────────────────────┼───────────────────────────────┐
                     ▼                                ▼                               ▼
         ┌───────────────────────┐        ┌───────────────────────┐       ┌───────────────────────┐
         │     linux-generic     │        │    linux-lowlatency   │       │       HWE Yığını      │
         ├───────────────────────┤        ├───────────────────────┤       ├───────────────────────┤
         │ • HZ=250              │        │ • HZ=1000             │       │ • Ara sürüm çekirdeği │
         │ • Voluntary Preempt   │        │ • Full Preempt        │       │ • Güncel DRM / Mesa   │
         │ • Maksimum Throughput │        │ • Düşük Gecikme (Jitter)│      │ • Yeni donanım desteği│
         │ • Sunucu / Genel Masa │        │ • Pro-Audio / Canlı Akış│      │ • Masaüstünde standart│
         └───────────────────────┘        └───────────────────────┘       └───────────────────────┘
```

Bu kılavuzda; çekirdek türlerinin mimari farklarını, `Kconfig` derleme bayraklarını, kurulum
ve geçiş adımlarını, GRUB üzerinden varsayılan çekirdek yönetimini ve gecikme (latency) testlerini
adım adım ele alacağız.

---

## 1. Çekirdek türleri ve nitelikleri

### 1.1. `linux-generic`: Kararlılık ve maksimum işlem verimi

`linux-generic`, Ubuntu'nun standart masaüstü ve sunucu kurulumlarında varsayılan olarak gelen
çekirdektir. Tasarım hedefi, genel iş yüklerinde CPU saat döngülerini gereksiz bağlam değişimleriyle
(context switch) harcamadan **maksimum işlem verimi (throughput)** ve **enerji tasarrufu** sağlamaktır.

Temel nitelikleri:
- **Zamanlayıcı Öncelik Modeli:** Klasik olarak `CONFIG_PREEMPT_VOLUNTARY=y` (Gönüllü Öncelik Kesme) bayrağıyla derlenir. Çekirdek kodunun her an kesilmesine izin verilmez; çekirdek içi rutinler yalnızca açıkça tanımlanmış kontrol noktalarında (`might_sleep()`) denetimi diğer süreçlere devreder. Ubuntu 24.04 (Linux 6.8+) ile birlikte dinamik öncelik kesme (`CONFIG_PREEMPT_DYNAMIC=y`) etkinleştirilmiş olup önyükleme sırasında varsayılan olarak `preempt=voluntary` modunda çalışır.
- **Saat Kesmesi (Timer Tick):** `CONFIG_HZ=250` (saniyede 250 kesme, 4 ms çözünürlük) kullanılır. Saat kesmelerinin seyrek olması, CPU'nun daha az uyanmasını sağlar, önbellek (cache) yerelliğini korur ve çok çekirdekli sistemlerde çekirdekler arası senkronizasyon maliyetini düşürür.
- **Boşta Güç Tasarrufu:** `CONFIG_NO_HZ_IDLE=y` (Dynticks) ile CPU çekirdekleri boşta kaldığında periyodik saat kesmeleri kapatılır; böylece işlemci derin uyku durumlarına (C-states) geçerek güç tüketimini ve sıcaklığı azaltır.
- **Kullanım Alanları:** Web sunucuları, veritabanları (PostgreSQL, MySQL), konteyner kümeleme düğümleri (Kubernetes, Docker), dosya sunucuları ve genel ofis masaüstü kullanımı.

### 1.2. `linux-lowlatency`: Düşük gecikme ve yumuşak gerçek zamanlılık

`linux-lowlatency`, CPU işlem veriminden küçük bir ödün vererek **gecikme süresini (latency)**
ve **zaman sapmasını (jitter)** minimuma indirmeyi hedefler. Gecikmeye duyarlı süreçlerin
(örneğin ses kartı arabelleğinden veri okuyan bir ses sunucusunun) çekirdek içi kilitlenmeler
yüzünden beklemesini engeller.

Temel nitelikleri:
- **Zamanlayıcı Öncelik Modeli:** `CONFIG_PREEMPT=y` (Full Preemptive Kernel - Tam Öncelik Kesmeli Çekirdek) kullanılır. Kritik kilit bölgeleri (spinlock) ve donanımsal kesme işleyicileri dışındaki tüm çekirdek içi kodlar yüksek öncelikli bir süreç tarafından anında kesilebilir.
- **Saat Kesmesi (Timer Tick):** `CONFIG_HZ=1000` (saniyede 1000 kesme, 1 ms çözünürlük) kullanılır. Zamanlayıcı her milisaniyede bir süreç önceliklerini yeniden değerlendirir.
- **RCU Öncelik Yükseltme:** `CONFIG_RCU_BOOST=y` bayrağı etkindir. Düşük öncelikli bir süreç RCU (Read-Copy Update) okuma kilidi tuttuğunda, yüksek öncelikli süreçlerin beklemesini önlemek için düşük öncelikli sürecin önceliği geçici olarak artırılır (priority inversion engellenir).
- **Ödünleşim (Trade-off):** Saniyede 1000 kesme ve sık bağlam değişimleri, CPU önbelleklerinin daha sık boşalmasına (cache thrashing) yol açar. Toplam işlem verimi (örneğin devasa bir C++ projesini derleme hızı veya veritabanı toplu sorgu performansı) generic çekirdeğe göre yaklaşık **%3 ila %7 arasında daha yavaş** olabilir. Taşınabilir cihazlarda pil ömrü kısalır.
- **Kullanım Alanları:** Profesyonel dijital ses istasyonları (Ardour, Reaper, Bitwig), JACK ve PipeWire pro-audio profilleri (64–128 arabellek boyutunda sıfır xrun hedefi), yazılım tanımlı radyo (SDR), canlı yayın ve video mikserleri (OBS, vMix tarzı boru hatları), düşük giriş gecikmeli rekabetçi oyun sistemleri.

> **Önemli Ayrım (Lowlatency vs Realtime):**
> `linux-lowlatency`, "yumuşak gerçek zamanlı" (soft real-time) bir çekirdektir. Süreçlerin zamanında
> yanıt vermesini büyük ölçüde garanti eder ancak matematiksel olarak kesin bir üst sınır (hard deadline)
> sunmaz.
>
> Ubuntu Pro ile sağlanan `linux-realtime` ise resmi `PREEMPT_RT` yama setini içerir; çekirdekteki
> tüm spinlock mekanizmalarını uyuyabilen kilitlere (`rt-mutex`) ve kesme rutinlerini çekirdek
> iş parçacıklarına (`kthreads`) dönüştürür. `linux-realtime` endüstriyel robotik, otomotiv ve tıbbi
> cihazlar için gerekliyken; genel ses ve masaüstü işleri için `linux-lowlatency` donanım ve tescilli
> sürücü (özellikle NVIDIA) uyumluluğu açısından çok daha kararlıdır.

### 1.3. `HWE` (Hardware Enablement): Uzun süreli destekte yeni donanım

Ubuntu LTS (Long-Term Support) sürümleri iki yılda bir yayımlanır ve en az 5 yıl boyunca resmi destek
alır. Ancak bir LTS sürümünün yayımlandığı tarihteki çekirdek (buna **GA - General Availability** çekirdeği
denir), yayımdan 1-2 yıl sonra piyasaya çıkan yeni nesil işlemcileri (örneğin Intel Ultra / Arrow Lake,
AMD Zen 4/5), yeni grafik yongalarını ve Wi-Fi standartlarını destekleyemez.

Canonical bu problemi çözmek için **HWE (Hardware Enablement Stack)** modelini uygular.

```text
Ubuntu 22.04 LTS Yaşam Döngüsü ve Çekirdek Akışı:
───────────────────────────────────────────────────────────────────────
Sürüm        Çekirdek Desteği   Kaynak Sürüm   Açıklama
───────────────────────────────────────────────────────────────────────
22.04 (GA)   Linux 5.15         22.04 LTS      5 yıl boyunca aynı sürüm kalır
22.04.2 HWE  Linux 5.19         22.10          Geçici ara sürüm çekirdeği
22.04.3 HWE  Linux 6.2          23.04          Geçici ara sürüm çekirdeği
22.04.4 HWE  Linux 6.5          23.10          Geçici ara sürüm çekirdeği
22.04.5 HWE  Linux 6.8          24.04 LTS      22.04 EOL'ye kadar desteklenir
───────────────────────────────────────────────────────────────────────
```

HWE nitelikleri:
- **Kullanıcı Alanını Korumak:** HWE yalnızca Linux çekirdeğini, çekirdek modüllerini ve Xorg/Mesa grafik sürücülerini günceller. Sistem kütüphaneleri (`glibc`, `systemd`, `OpenSSL`) sabit kalır; bu sayede işletim sisteminin genel uyumluluğu bozulmaz.
- **Varsayılan Durum:** Ubuntu Desktop LTS kurulumlarında HWE **varsayılan olarak etkindir**. Ubuntu Server LTS kurulumlarında ise kararlılık ve ABI sürekliliği için varsayılan olarak **GA çekirdeği** gelir; ancak istendiğinde tek komutla HWE'ye geçilebilir.
- **HWE Çeşitleri:** HWE hem generic hem de lowlatency için sunulur (`linux-generic-hwe-XX.YY` ve `linux-lowlatency-hwe-XX.YY`).

---

## 2. Çekirdek yapılandırma bayrakları ve karşılaştırma

Linux çekirdeğinin derleme yapılandırması `/boot/config-$(uname -r)` dosyasında saklanır.
Generic ve lowlatency çekirdekleri arasındaki temel teknik farklar doğrudan bu bayrakların
değerlerinden kaynaklanır:

```text
Özellik                       linux-generic             linux-lowlatency          linux-realtime (RT)
──────────────────────────────────────────────────────────────────────────────────────────────────────────
Preemption Modeli             VOLUNTARY (Dynamic)       FULL PREEMPT              PREEMPT_RT
Yapılandırma Bayrağı          CONFIG_PREEMPT_VOLUNTARY  CONFIG_PREEMPT            CONFIG_PREEMPT_RT
Timer Frekansı (CONFIG_HZ)    250 Hz (4 ms)             1000 Hz (1 ms)            1000 Hz (1 ms)
Dynticks (Tickless)           CONFIG_NO_HZ_IDLE         CONFIG_NO_HZ_IDLE         CONFIG_NO_HZ_FULL
RCU Öncelik Yükseltme         Hayır                     CONFIG_RCU_BOOST=y        CONFIG_RCU_BOOST=y
Gecikme (Latency Jitter)      Orta (1–15 ms)            Düşük (50–300 µs)         Ultra Düşük (<20 µs)
İşlem Verimi (Throughput)     Maksimum (Referans)       %3–%7 Düşük               %8–%15 Düşük
Güç / Pil Tüketimi            Minimum (Enerji dostu)    Yüksek                    Yüksek
DKMS / Sürücü Uyumu           Kusursuz                  Çok Yüksek                Sınırlı (RT Yamaları)
LTS Destek Modeli             5 Yıl Sabit veya HWE      5 Yıl Sabit veya HWE      Ubuntu Pro Aboneliği
──────────────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## 3. Kurulum ve paket yönetimi

Ubuntu'da çekirdek kurulumunda en kritik kavram **meta-paket (meta-package)** yapısıdır.

Doğrudan `linux-image-6.8.0-40-generic` gibi sürüme bağlı bir paket kurarsanız, yeni bir güvenlik
yaması yayımlandığında çekirdeğiniz otomatik olarak güncellenmez. Her zaman en güncel çekirdeğe işaret
eden meta-paketleri tercih edin:

| İhtiyaç | Kurulacak Meta-Paket | İçerdiği Alt Paketler |
| :--- | :--- | :--- |
| Standart GA Generic | `linux-generic` | `linux-image-generic`, `linux-headers-generic` |
| Standart GA Lowlatency | `linux-lowlatency` | `linux-image-lowlatency`, `linux-headers-lowlatency` |
| HWE Generic (24.04 için) | `linux-generic-hwe-24.04` | HWE tabanlı en son image ve headers |
| HWE Lowlatency (24.04 için) | `linux-lowlatency-hwe-24.04` | HWE tabanlı düşük gecikmeli paketler |

### 3.1. Mevcut çekirdek durumunu kontrol etme

Sisteminizde çalışan çekirdeği, sürüm numarasını ve mimariyi sorgulayın:

```bash
uname -rm
```

```text
6.8.0-45-generic x86_64
```

Sistemde kurulu olan tüm çekirdek imajlarını listeleyin:

```bash
dpkg -l | grep -E 'linux-(image|headers)-[0-9]' | awk '{print $2, $3}'
```

```text
linux-headers-6.8.0-45-generic 6.8.0-45.45
linux-image-6.8.0-45-generic 6.8.0-45.45
```

### 3.2. Lowlatency çekirdeğin kurulması

Lowlatency çekirdeği ve harici çekirdek modüllerinin (DKMS) derlenebilmesi için gereken
başlık dosyalarını birlikte kurun:

```bash
sudo apt update
sudo apt install linux-lowlatency linux-headers-lowlatency
```

Eğer HWE tabanlı bir LTS kullanıyorsanız ve en güncel HWE çekirdeğinin lowlatency sürümünü
istiyorsanız:

```bash
sudo apt update
sudo apt install --install-recommends linux-lowlatency-hwe-$(lsb_release -rs)
```

Kurulum tamamlandığında APT, `update-initramfs` ve `update-grub` komutlarını otomatik olarak
çalıştırarak yeni çekirdeği GRUB yapılandırmasına ekler.

### 3.3. HWE çekirdeğin kurulması (Ubuntu Server GA'dan HWE'ye geçiş)

Ubuntu Server LTS kurduysanız ve yeni bir NVMe denetleyicisi, 10GbE ağ kartı veya güncel bir CPU
için HWE yığınına geçmek istiyorsanız:

```bash
sudo apt update
sudo apt install --install-recommends linux-generic-hwe-$(lsb_release -rs)
```

Sistemde masaüstü grafik yığını da varsa Xorg ve Mesa sürücülerini de içeren tam HWE paketini
seçebilirsiniz:

```bash
sudo apt install --install-recommends xserver-xorg-hwe-$(lsb_release -rs)
```

---

## 4. GRUB yapılandırması ve varsayılan çekirdek seçimi

Sistemde hem generic hem de lowlatency çekirdekler kurulu olduğunda GRUB önyükleyicisi
varsayılan olarak en yüksek sürüm numaralı çekirdeği seçer. Aynı sürüm numarasında iki varyant
bulunuyorsa dağıtım kuralına göre sıralama yapar.

İstediğiniz çekirdeği kalıcı ve öngörülebilir şekilde varsayılan yapmak için GRUB yapılandırmasını
düzenleyin.

### 4.1. GRUB menü girdilerini listeleme

GRUB menüsündeki mevcut çekirdek başlıklarını ayrıştırın:

```bash
grep -E "menuentry 'Ubuntu" /boot/grub/grub.cfg | cut -d"'" -f2
```

```text
Ubuntu
Ubuntu, with Linux 6.8.0-45-lowlatency
Ubuntu, with Linux 6.8.0-45-lowlatency (recovery mode)
Ubuntu, with Linux 6.8.0-45-generic
Ubuntu, with Linux 6.8.0-45-generic (recovery mode)
```

GRUB menü yapısında çekirdekler genellikle `Advanced options for Ubuntu` alt menüsü altındadır.

### 4.2. Güvenli yöntem: `GRUB_DEFAULT=saved` kullanımı

En esnek ve risksiz yöntem, son seçilen veya açıkça komutla belirlenen çekirdeğin önyüklenmesini
sağlamaktır.

`/etc/default/grub` dosyasını bir metin düzenleyici ile açın:

```bash
sudo nano /etc/default/grub
```

Aşağıdaki satırları güncelleyin veya ekleyin:

```bash
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=true
```
{: data-filename="/etc/default/grub"}

Değişikliği GRUB'a işleyin:

```bash
sudo update-grub
```

Şimdi istediğiniz çekirdeği varsayılan olarak sabitleyin:

```bash
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"
```

Mevcut varsayılan ayarı kontrol edin:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency
```

Sistemi yeniden başlatın:

```bash
sudo reboot
```

> **Headless / Uzak Sunucularda Güvenli Geçiş:**
> Eğer sunucuya yalnızca SSH üzerinden erişiyorsanız ve fiziksel ekran/klavye yoksa, doğrudan kalıcı varsayılanı değiştirmek risklidir (çekirdek panik yaparsa kilitlenirsiniz). Bunun yerine bir sonraki açılış için tek seferlik deneme yapan `grub-reboot` mekanizmasını ve `panic=10` / `GRUB_RECORDFAIL_TIMEOUT` sigortalarını tercih edin. Ayrıntılı adımlar için [Headless sistemlerde çekirdek değişimi](headless-kernel-degisimi.md) kılavuzuna bakın.

---

## 5. Doğrulama ve gecikme (latency) testleri

Sistem yeniden başladıktan sonra adımların başarıyla tamamlandığını doğrulayın.

### 5.1. Çalışan çekirdek ve derleme bayraklarını doğrulama

Çalışan çekirdeğin adını kontrol edin:

```bash
uname -r
```

```text
6.8.0-45-lowlatency
```

Çalışan çekirdeğin yapılandırma dosyasından zamanlayıcı ve saat frekansı bayraklarını okuyun:

```bash
grep -E 'CONFIG_PREEMPT(_VOLUNTARY|_DYNAMIC|_NONE)?=|CONFIG_HZ=' /boot/config-$(uname -r)
```

`lowlatency` çekirdek için beklenen çıktı:

```text
CONFIG_PREEMPT_BUILD=y
CONFIG_PREEMPT=y
CONFIG_HZ_1000=y
CONFIG_HZ=1000
```

`generic` çekirdek için beklenen çıktı:

```text
CONFIG_PREEMPT_VOLUNTARY_BUILD=y
CONFIG_PREEMPT_VOLUNTARY=y
CONFIG_HZ_250=y
CONFIG_HZ=250
```

### 5.2. `cyclictest` ile gecikme karşılaştırması

İki çekirdek arasındaki pratik farkı görmek için Linux `rt-tests` paketinde bulunan `cyclictest`
aracını kullanabilirsiniz. Bu araç belirli aralıklarla bir iş parçacığı uyandırarak hedeflenen
uyanma zamanı ile gerçek uyanma zamanı arasındaki farkı (jitter / latency) mikrosaniye cinsinden ölçer.

Test aracını kurun:

```bash
sudo apt install rt-tests
```

Tüm CPU çekirdeklerinde gerçek zamanlı öncelikle (`-p 90`), bellek kilitlemeyle (`-m`) ve
100.000 döngü boyunca gecikme testi çalıştırın:

```bash
sudo cyclictest --smp -p 90 -m -i 1000 -d 0 -l 100000
```

Örnek `generic` çekirdek çıktısı (yüksek jitter):

```text
# /dev/cpu_dma_latency set to 0us
policy: fifo: loadavg: 0.42 0.35 0.28 1/412 18920          

T: 0 (18912) P:90 I:1000 C: 100000 Min:      4 Act:    7 Avg:   14 Max:    1284
T: 1 (18913) P:90 I:1000 C: 100000 Min:      4 Act:    6 Avg:   15 Max:    1842
```

Örnek `lowlatency` çekirdek çıktısı (düşük jitter ve deterministik maksimum):

```text
# /dev/cpu_dma_latency set to 0us
policy: fifo: loadavg: 0.51 0.40 0.30 1/410 19415          

T: 0 (19401) P:90 I:1000 C: 100000 Min:      2 Act:    3 Avg:    6 Max:     112
T: 1 (19402) P:90 I:1000 C: 100000 Min:      2 Act:    4 Avg:    7 Max:     125
```

Sonuçlarda `Max` değerine dikkat edin: Generic çekirdekte arka plan işlemleri sırasında gecikme
zaman zaman **1.5 – 2 milisaniyeye (1500–2000 µs)** fırlayabilirken; lowlatency çekirdekte maksimum
gecikme çoğunlukla **100–150 mikrosaniye** bandında sınırlandırılır. Bu fark, profesyonel ses
kaydında ses atlamalarını (buffer underrun / xrun) tamamen önleyen ana faktördür.

---

## 6. DKMS modülleri, temizlik ve geri dönüş (Rollback)

### 6.1. Harici sürücüler (NVIDIA, ZFS, VirtualBox) ve DKMS

Tescilli NVIDIA sürücüleri, ZFS dosya sistemi veya VirtualBox konuk eklentileri gibi çekirdek dışı
(out-of-tree) modüller DKMS (Dynamic Kernel Module Support) ile çekirdek her güncellendiğinde
otomatik derlenir.

Yeni bir çekirdek kurduğunuzda DKMS modüllerinin başarıyla derlendiğinden emin olun:

```bash
dkms status
```

```text
nvidia/550.120, 6.8.0-45-generic, x86_64: installed
nvidia/550.120, 6.8.0-45-lowlatency, x86_64: installed
```

Eğer durum `installed` yerine `broken` veya derleme hatası gösteriyorsa, ilgili çekirdeğin
başlık (`linux-headers`) paketinin kurulu olduğunu doğrulayın ve modülü elle yeniden derleyin:

```bash
sudo dkms autoinstall -k $(uname -r)
```

### 6.2. Eski çekirdekleri güvenle temizlemek

Sistemde çok sayıda eski çekirdek birikmesi `/boot` disk bölümünün dolmasına ve APT işlemlerinin
kilitlenmesine neden olabilir.

Ubuntu'nun paket yöneticisi çalışan çekirdeği otomatik olarak korur. Kullanılmayan eski çekirdekleri
temizlemek için:

```bash
sudo apt autoremove --purge
```

> **Uyarı:** `apt autoremove` komutunu çalıştırmadan önce `uname -r` çıktısı ile çalıştığınız
> çekirdeği kontrol edin. Asla çalışan çekirdeğin paketlerini elle `dpkg --purge` ile silmeyin.

### 6.3. Geri dönüş (Rollback) adımları

Yeni kurulan bir çekirdek açılışta donanım uyuşmazlığı, kernel panic veya siyah ekran hatası verirse:

1. Bilgisayarı yeniden başlatın.
2. BIOS/UEFI sonrasında **Shift** (BIOS) veya **Esc** (UEFI) tuşuna basılı tutarak GRUB menüsünü açın.
3. Menüden **Advanced options for Ubuntu** seçeneğini belirleyin.
4. Kararlı çalışan önceki çekirdeği (örneğin generic) seçip sistemi açın.
5. Sistem açıldığında GRUB varsayılanını önceki kararlı çekirdeğe geri çekin veya sorunlu paketi kaldırın:

```bash
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic"
sudo update-grub
```

---

## 7. Özet ve karar tablosu

Hangi senaryoda hangi çekirdeği seçmelisiniz?

- **Standart Sunucu (Web, DB, Docker, K8s):** `linux-generic` (LTS GA). 5 yıl değişmeyen kararlı ABI ve maksimum işlem verimi.
- **Yeni Donanımlı Sunucu veya İş İstasyonu:** `linux-generic-hwe-XX.YY`. Yeni CPU mimarisi, NVMe ve ağ donanımı desteği.
- **Müzik / Ses Prodüksiyonu (DAW, PipeWire, JACK):** `linux-lowlatency` veya `linux-lowlatency-hwe-XX.YY`. Sıfır xrun, düşük gecikme.
- **Oyun ve Canlı Yayın (OBS, VR, Düşük Giriş Gecikmesi):** `linux-lowlatency-hwe-XX.YY`.
- **Endüstriyel PLC / Otomasyon / Kritik Donanım:** `linux-realtime` (Ubuntu Pro PREEMPT_RT).

---

## Doğrulama ve kaynaklar

### Test ortamı
Bu rehberdeki yapılandırmalar, `CONFIG_*` bayrakları ve APT meta-paket davranışları Ubuntu 22.04 LTS (Jammy)
ve Ubuntu 24.04 LTS (Noble) x86_64 dağıtımlarında; Linux 5.15, 6.8 ve lowlatency çekirdek sürümleri
üzerinde doğrulanmıştır.

### Kaynaklar
- [Ubuntu Kernel Team Wiki](https://wiki.ubuntu.com/Kernel): Çekirdek yaşam döngüsü, HWE takvimi ve paketleme standartları.
- [Kernel.org Documentation - Preemption Models](https://docs.kernel.org/): `CONFIG_PREEMPT`, voluntary ve dynamic öncelik kesme mekanizmaları.
- [Real-Time Linux Collaborative Project](https://wiki.linuxfoundation.org/realtime/): Cyclictest kullanımı ve gerçek zamanlı sistem gecikme ölçümü.
