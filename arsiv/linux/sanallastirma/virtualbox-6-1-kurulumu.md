---
translation_key: guide-arsiv-linux-sanallastirma-virtualbox-6-1-kurulumu
lang: tr
title: "CentOS/RHEL: VirtualBox 6.1 kurulumu"
permalink: /arsiv/linux/sanallastirma/virtualbox-6-1-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: "VirtualBox 6.1 ve EL tabanlı dağıtımlar."
archive_reason: "Sabit 6.1 paketi, depo adresi, çekirdek modülleri ve Secure Boot adımları hedef sürümde doğrulanmalı."
redirect_from:
  - "/linux/centos-rhel_virtualbox.html"
---

# CentOS/RHEL: VirtualBox 6.1 kurulumu


Virtualbox, Oracle tarafından yayımlanan ve geliştirilen, açık kaynak kodlu bir sanallaştırma programıdır.
Oracle VM VirtualBox 5.2 sürümünden bu yana, SSE2 CPU uzantısı gerekmektedir.  Oracle VM VirtualBox kernel modülleri: vboxdrv, vboxnetflt, ve vboxnetadp bu kurulum ile veraber gelmektedir ve bu modüller sayesinde çalıştırılmaktadır.

## Virtualbox deposunu eklemek

```shell
$ sudo dnf -y install wget
$ wget https://download.virtualbox.org/virtualbox/rpm/el/virtualbox.repo
$ sudo mv virtualbox.repo /etc/yum.repos.d/
```

## Oracle depo imzasını içeri aktarmak

```shell
wget -q https://www.virtualbox.org/download/oracle_vbox.asc
sudo rpm --import oracle_vbox.asc
```

## Ek paketleri kurmak

Bu adım EPEL deposunun eklenmesini gerektirir.

```shell
sudo dnf -y install binutils kernel-devel kernel-headers libgomp make patch gcc glibc-headers glibc-devel dkms
```

## Virtualbox kurulumu


```shell
sudo dnf install -y VirtualBox-6.1
```

## Son ayarlamalar

```shell
sudo usermod -aG vboxusers $USER
sudo /usr/lib/virtualbox/vboxdrv.sh setup
```
