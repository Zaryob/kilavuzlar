---
translation_key: guide-linux-lvm-bolumunu-buyutmek
lang: tr
title: "Ubuntu'da LVM bölümünü veri kaybetmeden büyütmek"
permalink: /linux/lvm-bolumunu-buyutmek/
status: duzenlendi
reviewed: 2026-11-03
scope: Ubuntu 22.04/24.04 LTS üzerinde ext4 ve XFS dosya sistemleri için LVM2 çevrimiçi genişletme.
---

# Ubuntu'da LVM bölümünü veri kaybetmeden büyütmek

Bulut sunucularında (AWS, GCP, Hetzner), sanallaştırma platformlarında (VMware, Proxmox, KVM)
veya fiziksel sunucularda disk boyutu artırıldığında, bu alanı çalışan işletim sistemini
kapatmadan (zero downtime) dosya sistemine dahil etmek mümkündür.

LVM (Logical Volume Manager, Mantıksal Hacim Yöneticisi) kullanan Linux depolama yığını, depolamayı katmanlar halinde yönetir. Alanı güvenle
büyütmek için bu katmanları aşağıdan yukarıya doğru sırayla genişletmek gerekir:

```text
[ Fiziksel / Sanal Disk: /dev/sda ]
                 │
                 ▼  growpart
[ Disk Bölüntüsü: /dev/sda2 ]
                 │
                 ▼  pvresize
[ LVM Fiziksel Hacmi (PV): /dev/sda2 ]
                 │
                 ▼  (Hacim Grubu - VG otomatik güncellenir)
[ LVM Hacim Grubu (VG): ubuntu-vg ]
                 │
                 ▼  lvextend
[ LVM Mantıksal Hacmi (LV): /dev/ubuntu-vg/ubuntu-lv ]
                 │
                 ▼  resize2fs (ext4) / xfs_growfs (xfs)
[ Dosya Sistemi: / (root) ]
```

> **Uyarı:** Bu adımlar çalışan sistemin bölüm tablosunu ve LVM üstverisini değiştirir. Yanlış disk ya da
> bölüm numarası, yarıda kesilen bir işlem veya hatalı bir hipervizör işlemi veri kaybına yol
> açabilir. Başlamadan önce diskin anlık görüntüsünü (snapshot) ya da geri yüklenebildiğini
> sınadığınız bir yedeğini alın; komutlardaki aygıt adlarını kendi `lsblk` çıktınıza göre yazın.

## Ön koşullar

- Ubuntu 22.04 LTS veya 24.04 LTS kurulu bir sistem.
- `sudo` veya `root` yetkileri.
- Disk tablosunu genişletmek için `cloud-guest-utils` paketi (içinde `growpart` bulunur):

```bash
sudo apt-get update
sudo apt-get install -y cloud-guest-utils
```

## 1. Mevcut depolama düzenini inceleme

Öncelikle dosya sisteminizin türünü (`ext4` veya `xfs`), disk bölümleme yapısını ve LVM
adlarını tespit edin:

```bash
lsblk -o NAME,FSTYPE,SIZE,FSAVAIL,FSUSE%,MOUNTPOINT
```

Beklenen çıktı örneği:

```text
NAME                      FSTYPE      SIZE FSAVAIL FSUSE% MOUNTPOINT
sda                                   100G                
├─sda1                    vfat        1.1G      1G     4% /boot/efi
└─sda2                    LVM2_member  48G                
  └─ubuntu--vg-ubuntu--lv ext4       46.5G    4.2G    86% /
```

Burada görüldüğü gibi ana disk (`sda`) 100G boyutuna çıkarılmış, ancak bölüntü (`sda2`)
ve mantıksal hacim (`ubuntu--vg-ubuntu--lv`) halen yaklaşık 48G seviyesindedir.

Dosya sistemi türünü ayrıca doğrulamak için:

```bash
df -hT /
```

Beklenen çıktı:

```text
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   46G   40G  4.2G  91% /
```

## 2. Çekirdeğe yeni disk boyutunu bildirme (SCSI Rescan)

Hipervizör veya bulut sağlayıcısı tarafında disk boyutu büyütüldüğünde çekirdek yeni boyutu
anında fark etmeyebilir. `sda` diski için yeniden tarama sinyali gönderin:

```bash
echo 1 | sudo tee /sys/class/block/sda/device/rescan
```

Tüm SCSI veri yollarını topluca taratmak isterseniz:

```bash
for host in /sys/class/scsi_host/host*/scan; do echo "- - -" | sudo tee "$host"; done
```

`lsblk` çıktısında `sda` diskinin toplam boyutunun güncellendiğini doğrulayın.

## 3. Disk bölüntüsünü genişletme (growpart)

LVM fiziksel hacmi doğrudan ham disk yerine bir bölüntü üzerindeyse (`/dev/sda2`),
bölüntü tablosunu güncellemek için `growpart` kullanılır.

> [!IMPORTANT]
> `growpart` komutunda disk aygıtı ile bölüntü numarası arasında **boşluk** bırakılmalıdır.
> `/dev/sda2` şeklinde tek parametre verilirse hata alınır.

```bash
sudo growpart /dev/sda 2
```

Beklenen çıktı:

```text
CHANGED: partition=2 start=2254848 old: size=102602752 end=104857600 new: size=207486943 end=209741791
```

GPT disklerde ikincil (yedek) başlık diskin en son sektörlerinde yer alır. Disk büyütüldüğünde
`growpart` bu GPT yedek başlığını otomatik olarak diskin yeni sonuna taşır.

`lsblk` ile kontrol ettiğinizde `/dev/sda2` bölüntüsünün yeni boyuta ulaştığını görebilirsiniz.

*(Not: Eğer LVM'i bölüntüsüz ham disk `/dev/sdb` üzerinde kullanıyorsanız bu adımı atlayıp
doğrudan `pvresize /dev/sdb` adımına geçebilirsiniz.)*

## 4. Fiziksel Hacmi (PV) güncelleme (pvresize)

Bölüntü büyüdükten sonra LVM meta verilerini bilgilendirmek gerekir:

```bash
sudo pvresize /dev/sda2
```

Beklenen çıktı:

```text
  Physical volume "/dev/sda2" changed
  1 physical volume(s) resized or updated / 0 physical volume(s) not resized
```

Hacim grubundaki (VG) boş alanı teyit edin:

```bash
sudo vgs
```

Beklenen çıktı:

```text
  VG        #PV #LV #SN Attr   VSize   VFree 
  ubuntu-vg   1   1   0 wz--n- <98.9G <50.0G
```

`VFree` sütununda genişletilmeye hazır boş alan görünmelidir.

## 5. Mantıksal Hacim ve dosya sistemini genişletme

En güvenli ve önerilen yöntem, Mantıksal Hacim ile dosya sistemini tek bir işlemde
`lvextend -r` (`--resizefs`) bayrağıyla büyütmektir.

`-r` bayrağı arka planda `fsadm` aracını çalıştırır; dosya sisteminin `ext4` mü yoksa `xfs` mi
olduğunu otomatik algılayarak doğru komutu tetikler ve parametre hatası riskini ortadan kaldırır.

VG'deki tüm boş alanı mantıksal hacme eklemek için:

```bash
sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
```

Eğer tüm boş alan yerine belirli bir miktar (örneğin 20 GB) eklemek isterseniz:

```bash
sudo lvextend -r -L +20G /dev/ubuntu-vg/ubuntu-lv
```

Beklenen çıktı:

```text
  Size of logical volume ubuntu-vg/ubuntu-lv changed from 46.50 GiB to 96.50 GiB.
  Logical volume ubuntu-vg/ubuntu-lv successfully resized.
resize2fs 1.47.0 (5-Feb-2023)
Filesystem at /dev/mapper/ubuntu--vg-ubuntu--lv is mounted on /; on-line resizing required
old_desc_blocks = 6, new_desc_blocks = 13
The filesystem on /dev/mapper/ubuntu--vg-ubuntu--lv is now 25296896 (4k) blocks long.
```

## 6. Manuel genişletme ve dosya sistemi farkları (ext4 vs XFS)

Eğer `-r` bayrağını unutup yalnızca `lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv`
çalıştırdıysanız, dosya sistemini manuel olarak genişletmeniz gerekir.
Burada dosya sistemi türüne göre kritik farklar vardır:

### ext4 için manuel genişletme

ext4 dosya sistemi çevrimiçi (sistem bağlı ve çalışırken) genişletilebilir.
`resize2fs` komutuna hedef blok aygıtının yolu verilir:

```bash
sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv
```

### XFS için manuel genişletme

XFS dosya sistemi de çevrimiçi genişletilebilir, ancak ext4'ten farklı olarak
`xfs_growfs` komutuna aygıt adı değil, **bağlama noktası** verilir:

```bash
sudo xfs_growfs /
```

### ext4 ve XFS genişletme/küçültme sınırları

| Yetenek | ext4 | XFS |
| :--- | :--- | :--- |
| **Çevrimiçi Büyütme (Online Grow)** | Desteklenir (sistem çalışırken kesintisiz) | Desteklenir (bağlı olmak zorundadır) |
| **Çevrimdışı Büyütme (Offline Grow)** | Desteklenir | Yaygın değildir (bağlıyken genişletilir) |
| **Çevrimiçi Küçültme (Online Shrink)** | Desteklenmez | Desteklenmez |
| **Çevrimdışı Küçültme (Offline Shrink)** | Desteklenir (`umount` ve `e2fsck` şarttır) | **Asla desteklenmez** (XFS mimari gereği küçülemez) |

## Sonuç ve doğrulama

Son olarak dosya sisteminin güncel boyutunu ve kullanım durumunu doğrulayın:

```bash
df -hT /
```

Beklenen çıktı:

```text
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   95G   40G   52G  44% /
```

Bu örnekte hiçbir hizmet durdurulmadan ve sunucu yeniden başlatılmadan kullanılabilir alan
iki katına çıkarılmıştır. Çevrimiçi genişletme doğru uygulandığında mevcut veriye dokunmaz;
yine de yedeksiz yapılmamalıdır.

## Kaynaklar ve doğrulama ortamı

- [Ubuntu Server LVM Belgeleri](https://ubuntu.com/server/docs/how-to/storage/manage-logical-volumes/)
- Linux Çekirdeği SCSI Yeniden Tarama Kılavuzu (`Documentation/scsi/scsi_eh.rst`)
- LVM2 `lvextend(8)`, `pvresize(8)` ve `growpart(1)` kılavuz sayfaları

Bu kılavuzdaki adımlar, Ubuntu 24.04 LTS (Kernel 6.8, LVM 2.03.16, ext4 ve XFS)
üzerinde çalışan canlı bir sanal makinede test edilmiş ve doğrulanmıştır.
