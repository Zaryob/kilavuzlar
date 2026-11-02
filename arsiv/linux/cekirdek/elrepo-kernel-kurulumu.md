---
title: "CentOS/RHEL: ELRepo çekirdeği kurulumu"
permalink: /arsiv/linux/cekirdek/elrepo-kernel-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: "ELRepo EL8 paketi ve kernel-ml/kernel-lt örnekleri."
archive_reason: "EPEL ve ELRepo adları karıştırılmış. Dağıtım uyumu, imza anahtarı, Secure Boot ve geri dönüş adımları doğrulanmalı."
redirect_from:
  - "/linux/centos-rhel_mainline_kernel_kurulumu.html"
---

# CentOS/RHEL: ELRepo çekirdeği kurulumu

CentOS veya RHEL kullananlar bilir ki, bu iki işletim sistemi sürekli en uyumlu ve en optimal sürümleri destekler. Çünkü bu iki işletim sistemi de özellik eklemekten ziyade kararlı kalmayı hedef almaktadır. Ancak benim gibi bazı sürücüleri sebebi son sürün kernel kullanmak isteyen (en azından 5.x sürümleri) kişiler kernel 4.x sürümülerine sahip olan bir işletim sistemini kullanmakta zorluk yaşamakta. İşte bu noktada yardımımıza EPEL depoları ve ElRepo-Kernel koşuyor.

## EPEL Kernel Deposunu aktifleştirmek

Başta GPG anahtarlarını ekleyelim.
```bash
rpm --import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org
```

Şimdi de depoyu ekleyelim.
```
rpm -Uvh https://www.elrepo.org/elrepo-release-8.el8.elrepo.noarch.rpm
```

Ve depo kataloglarını yenileyelim.
```
yum update
```

## Mainline Kerneli Kurmak

Mainline Kernel en son sürüm kerneli ve bunun yamalarını içermekte. Kurmak için:

```bash
yum --enablerepo=elrepo-kernel install kernel-ml -y
```

dememiz yeterli. Eğer ki bu kernele ait header dosyalarına da ihtiyacınız varsa

```bash
yum --enablerepo=elrepo-kernel install kernel-ml kernel-ml-devel -y
```

komutu işinizi görecektir.


## LTS Kernel Kurmak


LTS çekirdeği Kernel topluluğu tarafıdan yamalar ve güvenlik düzenlemeleri ile desteklenen kernel sürümüdür. Kurmak için:

```bash
yum --enablerepo=elrepo-kernel install kernel-lt -y
```

dememiz yeterli. Eğer ki bu kernele ait header dosyalarına da ihtiyacınız varsa

```bash
yum --enablerepo=elrepo-kernel install kernel-lt kernel-lt-devel -y
```

komutu işinizi görecektir.
