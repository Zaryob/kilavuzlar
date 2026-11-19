---
translation_key: guide-linux-headless-kernel-degisimi
lang: tr
title: "Headless Linux sistemlerde bir sonraki açılış için çekirdek değişimi: grub-reboot ve güvenlik önlemleri"
permalink: /linux/headless-kernel-degisimi/
status: duzenlendi
reviewed: 2026-11-20
scope: Ubuntu 22.04 LTS ve 24.04 LTS üzerinde SSH erişimli headless sunucularda grub-reboot ile tek seferlik çekirdek seçimi, generic, lowlatency ve HWE varyantları arasında geçiş, panic ve recordfail güvenlik yapılandırmaları.
---

# Headless Linux sistemlerde bir sonraki açılış için çekirdek değişimi: grub-reboot ve güvenlik önlemleri

Uzak veri merkezinde, bulut sağlayıcısında (AWS, Hetzner, DigitalOcean) veya yerel ağdaki bir kabinde
monitörsüz ve klavyesiz çalışan sunuculara **headless sistem** denir. Bu sistemlerin yönetimi tamamen
SSH veya otomasyon araçları (Ansible, Puppet) üzerinden yürütülür.

Headless bir sunucuda Linux çekirdeğini (kernel) değiştirmek yüksek risk taşır:
- Yeni çekirdek donanım uyuşmazlığı, kernel panic veya ağ kartı (NIC) sürücü hatası nedeniyle açılışta kilitlenirse SSH servisi devreye giremez.
- Fiziksel klavye ve ekran olmadığı için açılış esnasında GRUB menüsüne müdahale edip eski çalışan çekirdeği seçemezsiniz.
- Sunucuya IPMI/iKVM (iDRAC, iLO) erişimi yoksa tek kurtuluş veri merkezinden fiziksel müdahale ("remote hands") istemek veya sunucuyu kurtarma (rescue) modunda yeniden başlatmaktır.

Bu riski sıfıra indiren standart yöntem **tek seferlik önyükleme (one-shot boot)** mekanizmasıdır.
`grub-reboot` aracı sayesinde GRUB'a şu talimat verilir:
*"Sadece bir sonraki açılışta yeni çekirdeği (`lowlatency` veya `HWE`) dene. Eğer sistem açılmazsa,
kilitlenirse ya da yeniden başlatılırsa otomatik olarak önceki güvenli çekirdeğe (`generic`) geri dön."*

```text
               ┌─────────────────────────────────────────────────────────┐
               │   Headless Sunucu: SSH üzerinden grub-reboot emri verilir│
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │    /boot/grub/grubenv dosyasına next_entry yazılır      │
               └────────────────────────────┬────────────────────────────┘
                                            │ sudo reboot
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │ GRUB açılır: next_entry'yi okur, HEMEN SİLER ve kaydeder│
               │         Yeni çekirdeği (örn. lowlatency) yükler         │
               └────────────────────────────┬────────────────────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      ▼                                           ▼
          [ BAŞARILI AÇILIŞ ]                           [ BAŞARISIZ / PANIC ]
          • SSH servisi ayağa kalkar                    • panic=10 ile 10 sn sonra reboot
          • Admin uname -r ile onaylar                  • Watchdog sistemi yeniden başlatır
          • grub-set-default ile kalıcı yapılır         • next_entry silinmiş olduğundan
                                                          GRUB güvenli çekirdeğe (generic) döner!
```

Bu kılavuzda; `grub-reboot` mekanizmasının mimarisini, sunucunun kilitlenmesini önleyen kritik
güvenlik sigortalarını (`panic=10` ve `GRUB_RECORDFAIL_TIMEOUT`), `generic`, `lowlatency` ve `HWE`
çekirdekleri arasında adım adım geçişi ve `systemd-boot` alternatifini ele alacağız.

---

## 1. GRUB ve `grubenv` mekanizmasının iç yüzü

GRUB önyükleyicisi, dosya sistemlerini genellikle salt okunur (read-only) bağlar. Ancak önyükleme
tercihlerini saklayabilmek için `/boot/grub/grubenv` adında tam **1024 baytlık** özel bir ortam
dosyası kullanır. GRUB, bu dosyaya doğrudan disk blokları (blocklist) üzerinden güvenli bir şekilde
yazabilir.

Sistemde iki kritik GRUB değişkeni bulunur:

1. **`saved_entry`**: Sistemin kalıcı varsayılan çekirdeğidir. `grub-set-default` komutuyla ayarlanır.
2. **`next_entry`**: Yalnızca **bir sonraki açılışta** çalıştırılacak geçici çekirdek girdisidir. `grub-reboot` komutuyla ayarlanır.

### Açılış döngüsü nasıl işler?

Sistem açılırken GRUB yapılandırmasındaki (`/etc/grub.d/00_header`) şu mantık devreye girer:

```text
if [ -s $prefix/grubenv ]; then
  load_env
fi
if [ "${next_entry}" ] ; then
   set default="${next_entry}"
   set next_entry=
   save_env next_entry
   set boot_once=true
else
   set default="${saved_entry}"
fi
```

**Bu mantığın sağladığı hayati güvenlik şudur:**
GRUB, `next_entry` değişkenini okuduğu anda, henüz Linux çekirdeğini belleğe yüklemeden **önce**
`next_entry`'yi bellekten temizler ve diske kaydeder (`save_env next_entry`).

Yeni çekirdek yüklendiğinde bir felaket yaşanırsa (örneğin kernel panic veya elektrik kesintisi),
bir sonraki yeniden başlatmada `next_entry` boş olacağı için GRUB otomatik olarak `saved_entry`'de
kayıtlı olan eski kararlı çekirdeği başlatır. Böylece sunucu erişilemez duruma düşmez.

---

## 2. Kilitlenmeye karşı güvenlik ağı (Headless Safety Checklist)

Bir sonraki açılışta yeni çekirdeği denemeden önce, sunucunuzun acil durumlarda kilitlenip
kalmasını engelleyen **üç güvenlik sigortasını** yapılandırmanız şarttır.

### 2.1. Sigorta 1: Kernel panic anında otomatik yeniden başlatma (`panic=10`)

Bir Linux çekirdeği donanım veya sürücü hatası nedeniyle "Kernel Panic" durumuna düştüğünde,
varsayılan çekirdek davranışı ekrana hata basıp sonsuza kadar beklemektir (`kernel.panic = 0`).
Headless sunucuda bu durum sunucunun tamamen donması anlamına gelir.

Çekirdeğe panik anında 10 saniye bekledikten sonra donanımı yeniden başlatmasını söyleyin:

`/etc/sysctl.d/99-panic.conf` dosyasını oluşturun:

```bash
kernel.panic = 10
```
{: data-filename="/etc/sysctl.d/99-panic.conf"}

Ayarları etkinleştirin:

```bash
sudo sysctl --system
```

Çekirdeğin henüz kullanıcı alanına (`sysctl`) ulaşamadan paniklemesi ihtimaline karşı bu parametreyi
GRUB çekirdek satırına da ekleyin (bölüm 2.3'te yapılacaktır).

### 2.2. Sigorta 2: GRUB `recordfail` sonsuz bekleme tuzağını kapatma

Ubuntu'da GRUB, bir açılışın başarısız olduğunu veya sistemin düzgün kapatılmadığını algılarsa
`recordfail=1` bayrağı koyar. Bu bayrak etkinleştiğinde GRUB'ın varsayılan davranışı,
**zaman aşımını iptal etmek (`timeout = -1`) ve kullanıcının klavyeden bir tuşa basmasını sonsuza kadar beklemektir!**

Monitörsüz bir sunucuda bu davranış tam bir felakettir; çekirdek panik yapıp makineyi yeniden
başlatsa bile GRUB menüsünde sonsuza dek asılı kalır.

Bu tuzağı engellemek için `/etc/default/grub` dosyasında `GRUB_RECORDFAIL_TIMEOUT` tanımlanmalıdır.

### 2.3. Sigorta 3: `/etc/default/grub` dosyasını yapılandırma

`/etc/default/grub` dosyasını düzenleyin:

```bash
sudo nano /etc/default/grub
```

Aşağıdaki satırları kontrol edin ve güncelleyin:

```bash
# GRUB varsayılanını grubenv içerisindeki saved_entry'den al
GRUB_DEFAULT=saved

# Normal açılışta menü bekleme süresi (saniye)
GRUB_TIMEOUT=5

# Başarısız açılış (recordfail) durumunda bekleme süresi (ASLA -1 olmamalı)
GRUB_RECORDFAIL_TIMEOUT=5

# Çekirdek komut satırına panic=10 ekle (erken çekirdek çökmelerinde 10 sn sonra reset)
GRUB_CMDLINE_LINUX_DEFAULT="console=tty1 console=ttyS0,115200 quiet splash panic=10"
```
{: data-filename="/etc/default/grub"}

> **Önemli Kural (`GRUB_SAVEDEFAULT`):**
> `grub-reboot` kullanırken dosyanıza `GRUB_SAVEDEFAULT=true` satırını **eklemeyin**. Eğer bu satır
> eklenirse, açılan her çekirdek otomatik olarak kalıcı varsayılan yapılır; bu da `grub-reboot`'un
> tek seferlik güvenlik korumasını boşa çıkarır.

Değişiklikleri GRUB yapılandırma dosyasına yazın:

```bash
sudo update-grub
```

```text
Sourcing file `/etc/default/grub'
Generating grub configuration file ...
Found linux image: /boot/vmlinuz-6.8.0-45-generic
Found initrd image: /boot/initrd.img-6.8.0-45-generic
Found linux image: /boot/vmlinuz-6.8.0-45-lowlatency
Found initrd image: /boot/initrd.img-6.8.0-45-lowlatency
done
```

---

## 3. Sistemdeki çekirdeklerin ve GRUB menü girdilerinin tespiti

Sunucunuzda kurulu olan çekirdek paketlerini ve bunların GRUB içerisindeki tam adlarını bilmeniz gerekir.

### 3.1. Kurulu çekirdek paketlerini sorgulama

Örnek senaryomuzda sistemimizde hem standart `generic`, hem gecikmeye duyarlı `lowlatency`, hem de
daha güncel bir donanım etkinleştirme (`HWE`) çekirdeği kurulu olsun:

```bash
dpkg -l | grep -E 'linux-image-[0-9]' | awk '{print $2, $3}'
```

```text
linux-image-6.8.0-45-generic 6.8.0-45.45
linux-image-6.8.0-45-lowlatency 6.8.0-45.45
linux-image-6.11.0-17-generic 6.11.0-17.17
```

Şu an çalışan çekirdeği öğrenelim:

```bash
uname -rm
```

```text
6.8.0-45-generic x86_64
```

### 3.2. GRUB menü hiyerarşisini listeleme

Ubuntu'da en son kurulan çekirdek dışındaki alternatif çekirdekler (lowlatency veya eski generic sürümler)
genellikle `Advanced options for Ubuntu` alt menüsünün altına yerleştirilir.

GRUB'a hedef belirtirken iki farklı sözdizimi kullanılabilir:

1. **Menü Başlığı Yolu (Title Path):** `Üst Menü Başlığı>Alt Menü Başlığı`
   (örneğin: `Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency`)
2. **Menü Kimliği Yolu (Menuentry ID - En Güvenli):** GRUB'ın dahili kimlikleri
   (örneğin: `gnulinux-advanced-UUID>gnulinux-6.8.0-45-lowlatency-advanced-UUID`)

Sistemdeki menü başlıklarını ve hiyerarşiyi listeleyen şu komutu çalıştırın:

```bash
awk -F"'" '/menuentry / {print i++ " : " $2} /submenu / {print "SUBMENU : " $2}' /boot/grub/grub.cfg
```

```text
0 : Ubuntu
SUBMENU : Advanced options for Ubuntu
2 : Ubuntu, with Linux 6.11.0-17-generic
3 : Ubuntu, with Linux 6.11.0-17-generic (recovery mode)
4 : Ubuntu, with Linux 6.8.0-45-generic
5 : Ubuntu, with Linux 6.8.0-45-generic (recovery mode)
6 : Ubuntu, with Linux 6.8.0-45-lowlatency
7 : Ubuntu, with Linux 6.8.0-45-lowlatency (recovery mode)
```

Alt menüdeki bir çekirdeği seçmek için `>` ayracını kullanırız. Örneğin:
`"Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"`

---

## 4. `grub-reboot` ile tek seferlik çekirdek değişimi

Şimdi adım adım çalışan standart `generic` çekirdekten `lowlatency` veya `HWE` çekirdeğine
güvenli geçiş yapalım.

```text
Adım 1: Hedef çekirdeği grub-reboot ile ayarla
Adım 2: grub-editenv list ile ortam dosyasını doğrula
Adım 3: sudo reboot ile sunucuyu yeniden başlat
Adım 4: SSH ile bağlan ve uname -r ile çalışan çekirdeği onayla
Adım 5: Memnunsan kalıcı yap (grub-set-default); değilsen bir sonraki reboot eski çekirdeğe döner!
```

### 4.1. Bir sonraki açılış çekirdeğini belirleme

Hedefimiz `6.8.0-45-lowlatency` çekirdeği olsun:

```bash
sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"
```

Eğer HWE çekirdeğini (`6.11.0-17-generic`) denemek isteseydiniz komut şu şekilde olurdu:

```bash
sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.11.0-17-generic"
```

### 4.2. Ortam değişkenini doğrulama

Komutun diske doğru yazıldığını kontrol edin:

```bash
sudo grub-editenv list
```

Beklenen çıktı:

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic
next_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency
```

Burada `saved_entry` kalıcı varsayılanımızı, `next_entry` ise yalnızca bir sonraki açılışta
çalıştırılacak geçici çekirdeğimizi gösterir.

### 4.3. Sunucuyu yeniden başlatma

Her şey hazır olduğuna göre sunucuyu yeniden başlatın:

```bash
sudo reboot
```

### 4.4. Yeni çekirdeğin doğrulama adımları

Sunucu yeniden başladığında SSH ile tekrar bağlanın ve çalışan çekirdeği kontrol edin:

```bash
uname -rmv
```

```text
6.8.0-45-lowlatency #45-Ubuntu SMP PREEMPT_DYNAMIC x86_64
```

Zamanlayıcı ve preemption modunu doğrulayın:

```bash
grep -E 'CONFIG_PREEMPT(_VOLUNTARY|_DYNAMIC)?=|CONFIG_HZ=' /boot/config-$(uname -r)
```

```text
CONFIG_PREEMPT_BUILD=y
CONFIG_PREEMPT=y
CONFIG_HZ_1000=y
CONFIG_HZ=1000
```

Tebrikler; sunucu başarılı bir şekilde `lowlatency` çekirdeği ile açılmıştır.

Tekrar `grub-editenv list` komutunu çalıştırırsanız `next_entry` alanının GRUB tarafından
otomatik olarak temizlendiğini görürsünüz:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic
```

Bu durum; sunucuyu bu aşamada tekrar yeniden başlatırsanız (`sudo reboot`), hiçbir ek işlem
yapmanıza gerek kalmadan otomatik olarak önceki `generic` çekirdeğe geri döneceğini kanıtlar!

---

## 5. Değişikliği kalıcı yapma veya vazgeçme (Rollback)

### 5.1. Değişikliği kalıcı yapmak (`grub-set-default`)

Yeni çekirdeğin performansından, ağ sürücülerinden ve kararlılığından memnun kaldıysanız ve
sunucunun bundan sonraki tüm açılışlarda bu çekirdekle başlamasını istiyorsanız:

```bash
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"
```

Kontrol edin:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency
```

Artık `lowlatency` çekirdeği kalıcı varsayılan olmuştur.

### 5.2. Yeniden başlatmadan önce tek seferlik seçimi iptal etme

Eğer `grub-reboot` komutunu verdikten sonra henüz sunucuyu yeniden başlatmadıysanız ve
fikrinizi değiştirip işlemi iptal etmek isterseniz:

```bash
sudo grub-editenv - unset next_entry
```

Kontrol edin:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic
```

`next_entry` silindiği için bir sonraki açılış standart `saved_entry` ile gerçekleşecektir.

---

## 6. Alternatif ortam: `systemd-boot` ve `bootctl set-oneshot`

Bazı modern minimal bulut imajlarında, Arch Linux ve Fedora sunucularda GRUB yerine UEFI yerel
önyükleyicisi olan **`systemd-boot`** kullanılır.

`systemd-boot` kullanan sistemlerde tek seferlik çekirdek değişimi EFI değişkenleri üzerinden
çok daha zarif bir şekilde yürütülür.

### 6.1. Mevcut girdileri listeleme

```bash
bootctl list
```

```text
type: Boot Loader Specification Type #1 (.conf)
title: Ubuntu Linux 6.8.0-45-generic
   id: ubuntu-6.8.0-45-generic.conf
source: /boot/efi//loader/entries/ubuntu-6.8.0-45-generic.conf

type: Boot Loader Specification Type #1 (.conf)
title: Ubuntu Linux 6.8.0-45-lowlatency
   id: ubuntu-6.8.0-45-lowlatency.conf
source: /boot/efi//loader/entries/ubuntu-6.8.0-45-lowlatency.conf
```

### 6.2. Tek seferlik açılış hedefi belirleme

`bootctl set-oneshot` komutuna ilgili girdinin `id` değerini verin:

```bash
sudo bootctl set-oneshot ubuntu-6.8.0-45-lowlatency.conf
```

Durumu kontrol edin:

```bash
bootctl status | grep -A 3 "Boot into"
```

```text
Boot into: ubuntu-6.8.0-45-lowlatency.conf (one-shot)
```

Bu ayar UEFI NVRAM üzerindeki `LoaderEntryOneShot` değişkenine yazılır. Sistem yeniden başladığında
`systemd-boot` bu girdiyi başlatır ve EFI değişkenini sıfırlar.

---

## 7. Kritik tuzaklar ve sorun giderme

### 7.1. Btrfs ve ZFS dosya sistemlerinde `sparse file not allowed` hatası

GRUB'ın Btrfs ve ZFS dosya sistemi sürücülerinde disk bloklarına yazma kısıtlaması bulunur.
Eğer `/boot` dizini ayrı bir Ext4 bölümü yerine doğrudan Btrfs/ZFS kök dizini içindeyse:

- Açılışta `error: sparse file not allowed` hatası alınabilir.
- GRUB açılış esnasında `next_entry` değişkenini silemez veya `save_env` başarısız olur.

**Çözüm:** Headless sunucularda `grubenv` mekanizmasını güvenle kullanabilmek için `/boot` dizinini
her zaman ayrı bir küçük (örn. 1 GB) **Ext4** bölümü olarak konumlandırın.

### 7.2. Ağ arayüzü isimlerinin değişmesi (Predictable Network Interface Names)

Farklı bir çekirdeğe (özellikle GA'dan yeni bir HWE çekirdeğine) geçildiğinde PCI veri yolu
numaralandırması veya ağ kartı sürücüsü değişebilir.
Örneğin çekirdek 5.15'te `enp3s0` olan ağ kartı, çekirdek 6.8'de `enp4s0` veya `ens3` haline gelebilir.

Eğer `/etc/netplan/` yapılandırmanız sabit arayüz adına bağlıysa ağ ayağa kalkmaz ve SSH bağlantısı kesilir.

**Önlem:** Netplan yapılandırmasında arayüzü adı yerine MAC adresi ile eşleştirin:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    primary-nic:
      match:
        macaddress: "52:54:00:12:34:56"
      set-name: eth0
      dhcp4: true
```
{: data-filename="/etc/netplan/01-netcfg.yaml"}

### 7.3. Donanımsal Watchdog (İleri Düzey Koruma)

Çekirdek panik yapmasa bile kullanıcı alanında bir deadlock yüzünden SSH servisi başlamazsa,
sistem kilitlenmiş kalabilir. Modern sunucularda anakart üzerinde bulunan donanımsal Watchdog
(IPMI watchdog, Intel TCO veya sanal ortamlarda i6300esb) hayat kurtarır.

Systemd donanım watchdog desteğini etkinleştirmek için `/etc/systemd/system.conf` dosyasında
şu ayarı yapın:

```ini
RuntimeWatchdogSec=60s
RebootWatchdogSec=5min
```
{: data-filename="/etc/systemd/system.conf"}

Eğer işletim sistemi 60 saniye boyunca watchdog aygıtına "hayattayım" sinyali (ping) gönderemezse,
anakart sunucuya donanımsal reset atar; sunucu yeniden başlar ve `next_entry` silinmiş olduğu için
güvenli çekirdeğe döner.

---

## 8. Hızlı başvuru komut kartı

| İşlem | Komut |
| :--- | :--- |
| Mevcut çalışan çekirdek | `uname -r` |
| Kurulu çekirdek paketleri | `dpkg -l \| grep linux-image` |
| GRUB menü girdilerini listeleme | `awk -F"'" '/menuentry / {print i++ " : " $2} /submenu / {print "SUBMENU : " $2}' /boot/grub/grub.cfg` |
| Sonraki açılışta `lowlatency` dene | `sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"` |
| Sonraki açılışta `HWE` dene | `sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.11.0-17-generic"` |
| Ortam değişkenlerini kontrol et | `sudo grub-editenv list` |
| Tek seferlik seçimi iptal et | `sudo grub-editenv - unset next_entry` |
| Çekirdeği kalıcı varsayılan yap | `sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"` |

---

## Doğrulama ve kaynaklar

### Test ortamı
Bu kılavuzdaki adımlar, `grub-reboot` ve `grub-editenv` ortam bloğu davranışları, `panic=10` çekirdek
parametresi ve `GRUB_RECORDFAIL_TIMEOUT` mekanizması Ubuntu 22.04 LTS ve Ubuntu 24.04 LTS x86_64
ortamlarında (QEMU/KVM ve fiziksel test sunucusu) Linux 6.8 generic, lowlatency ve 6.11 HWE çekirdekleri
üzerinde test edilerek doğrulanmıştır.

### Kaynaklar
- [GNU GRUB Manual - Environment block](https://www.gnu.org/software/grub/manual/grub/html_node/Environment-block.html): GRUB ortam bloğu mimarisi ve `grub-reboot` çalışma mantığı.
- [Ubuntu Community Help Wiki - Grub2](https://help.ubuntu.com/community/Grub2/Setup): GRUB_DEFAULT, saved ve recordfail yapılandırmaları.
- [The Linux Kernel documentation - The kernel’s command-line parameters](https://docs.kernel.org/admin-guide/kernel-parameters.html): `panic=` parametresi ve hata kurtarma davranışları.
- [systemd-boot Manual](https://manpages.ubuntu.com/manpages/noble/en/man7/systemd-boot.7.html): `bootctl` ve `LoaderEntryOneShot` arayüzü.
