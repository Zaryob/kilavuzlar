---
translation_key: guide-arsiv-linux-donanim-amd-radeon-pro-ayarlari
lang: tr
title: "AMD Radeon Pro ayarları"
permalink: /arsiv/linux/donanim/amd-radeon-pro-ayarlari/
status: arsiv
reviewed: 2026-11-02
scope: "Belgede belirtilen dönem: 2019–2021; Oibaf PPA ve DRI_PRIME."
archive_reason: "Mesa PPA, amdgpu-pro ve hibrit GPU seçimi birbirinden ayrılmalı. Sistem genelindeki DRI_PRIME değişikliği için donanım koşulları belirtilmeli."
redirect_from:
  - "/linux/amd-ekran-karti-ayarlari.html"
---

# AMD Radeon Pro ayarları

AMD Radeon Pro ekran kartlarında amdgpu modülü ile Linux çekirdeğinde standalone destek verilmekte ancak bazı kartlar için amdgpu-pro eklemesi yapılması gerekmektedir ki düzgün bir şekilde kullanabilelim.
Bu kılavuz 2019 ile 2021 arasında bu işi nasıl yaptığımı anlatmaktadır.

## PPA deposunu eklemek

```shell
$ sudo add-apt-repository ppa:oibaf/graphics-drivers
```

## Güncellemeleri işlemek

```shell
$ sudo apt update && sudo apt -y upgrade
```

Bu bize pek çok paketin yükseltileceğini döker. Hepsini yükseltelim

## Son düzenleme

Hala GPU modunda çalışmıyorsa şu komutu işletmeliyiz.

```shell
$ sudo su
# echo 'DRI_PRIME=1' >> /etc/environment
```

Bu satır `DRI_PRIME=1` değişkenini bütün oturumlar için tanımlar.

> **Uyarı:** `/etc/environment` sistem genelidir: bu ayar yalnızca Xorg'u değil, her uygulamayı ikincil GPU'da çalışmaya zorlar. Yalnızca hibrit (iki GPU'lu) sistemlerde anlamlıdır; pil tüketimini artırır ve ikincil GPU kullanılamadığında uygulamalar açılmayabilir. Tek bir uygulama için `DRI_PRIME=1 uygulama` biçiminde çalıştırmak daha güvenlidir. Geri almak için satırı `/etc/environment` dosyasından silin.
