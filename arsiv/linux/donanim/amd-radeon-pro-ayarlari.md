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

AMD Radeon Pro ekran kartlarında amdgpu modülü ile Linux çekirdeğinde standlone destek verilmekte ancak bazı kartlar için amdgpu-pro eklemesi yapılması gerekmektedir ki düzgün bir şekilde kullanabilelim.
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
# echo \"DRI_PRIME=1\" >> /etc/environment
```

Bu bizim sistmeimizdeki Xorg'u DRI_PRIME modunda başlatacaktır.
