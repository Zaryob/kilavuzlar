---
translation_key: guide-arsiv-linux-paket-yonetimi-yum-dnf-depo-islemleri
lang: tr
title: "YUM/DNF ile depo işlemleri"
permalink: /arsiv/linux/paket-yonetimi/yum-dnf-depo-islemleri/
status: arsiv
reviewed: 2026-11-02
scope: "YUM, yum-utils ve RHEL 8 depo örnekleri."
archive_reason: "YUM ile DNF sürümleri ayrılmalı; topluca depo açma/kapatma örnekleri ve joker karakterlerin kabuk tarafından genişletilmesi gözden geçirilmeli."
redirect_from:
  - "/linux/yum-dnf-ile-depo-islemleri.html"
---

# YUM/DNF ile depo işlemleri

## Depoları Listelemek

Devre dışı bırakılmış depolar dahil, sistem için mevcut tüm depoları listelemek için:


```shell
# yum repolist all
depo id                              depo adı                         durum
rhel-8-for-x86_64-baseos-rpms        Red Hat Enterprise Linux 8 for   etkin
rpmfusion-free-updates               RPM Fusion for EL 8 - Free - U   etkin
rpmfusion-free-updates-testing       RPM Fusion for EL 8 - Free - T   devre dışı
rpmfusion-nonfree-updates            RPM Fusion for EL 8 - Nonfree    etkin
```

## Depolar üzerinde Yum-Utils ile işlem yapmak

Başta yum utils'i kuralım:

```shell
# yum install -y yum-utils
```

Bu bize `yum-config-manager` adında bir komut satırı yapısı sağlamaktadır.
Bunu kullanarak depoları aktifleştirebilir ve deaktive edebiliriz.

```shell
# yum-config-manager --enable <repo-id>
# yum-config-manager --disable <repo-id>
```

### Depoyu aktifleştirmek

```shell
# yum-config-manager --enable rpmfusion-free-updates-testing
```

### Depoyu deaktifleştirmek

```shell
# yum-config-manager --disable rpmfusion-free-updates-testing
```

## Paket bazlı depo işlemleri

Paket kurma kaldırma ve yükseltme işlemlerinde depoları `--enablerepo=<repoid>` komutu ile yönetebiliriz. Bu kısa süreli olarak depoyu aktifleştirecektir.


```shell
# yum install kernel-ml --enablerepo=elrepo-kernel
```

## Depoları Elle Yönetmek

Sisteminize kurulu olan bütün depolar `/etc/yum.repos.d` klasörü altında bulunmaktadır. Burada bulunan dosyalarda depolar şu şekilde görünmektedir.

```
[rpmfusion-free-updates]
    name=RPM Fusion for EL 8 - Free - Updates
    #baseurl=http://download1.rpmfusion.org/free/el/updates/8/$basearch/
    mirrorlist=http://mirrors.rpmfusion.org/mirrorlist?repo=free-el-updates-released-8&arch=$basearch
    enabled=1
    gpgcheck=1
```

buradaki `enabled` parametresi 1 ise açıktı 0 ise kapalıdır.

## Subscription Manager ile yönetmek (sadece RHEL)

`subscription-manager` abonelik yöneticisi, yalnızca `redhat.repo` dosyasındaki depoları etkinleştirmek ve devre dışı bırakmak için kullanılır. RHEL'de bunun bulunmasının sebebi lisans kontrollerini yapmaktır:

### Depoları listelemek

Mevcut depoların bir listesini görmek için:
```shell
# subscription-manager repos --list
```

### Depoları aktifleştirmek

RHEL spesifik bir depoyu aktifleştirmek için:

```shell
# subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
```

### Depoları deaktifleştirmek

RHEL spesifik bir depoyu deaktifleştirmek için:

```shell
# subscription-manager repos --disable=rhel-8-for-x86_64-baseos-rpms
```

## Bütün Depoları Aktifleştirmek

```shell
# yum-config-manager --enablerepo=*
```

RHEL spesifik depolar için

```shell
# subscription-manager repos --enable=*
```

## Bütün Depoları Deaktifleştirmek

```shell
# yum-config-manager --disablerepo=*
```

RHEL spesifik depolar için

```shell
# subscription-manager repos --disable=*
```
