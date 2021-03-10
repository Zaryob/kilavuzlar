---
sort: 9
---

# AMD Radeon Pro Ekran Kartlarını Ayarlamak

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