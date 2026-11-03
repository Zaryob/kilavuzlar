---
title: 'CentOS/RHEL: installing VirtualBox 6.1'
permalink: /en/arsiv/linux/sanallastirma/virtualbox-6-1-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: VirtualBox 6.1 and Enterprise Linux-based distributions.
archive_reason: Verify the fixed 6.1 package, repository URL, kernel modules and Secure
  Boot procedure on the intended target version.
lang: en
translation_key: guide-arsiv-linux-sanallastirma-virtualbox-6-1-kurulumu
translation_of: /arsiv/linux/sanallastirma/virtualbox-6-1-kurulumu/
translated: '2026-11-03'
---

# CentOS/RHEL: installing VirtualBox 6.1

VirtualBox is open source virtualisation software developed and published by Oracle. Since Oracle VM VirtualBox 5.2, it requires SSE2 CPU extensions. This setup uses the vboxdrv, vboxnetflt and vboxnetadp kernel modules.

## Add the VirtualBox repository

```shell
$ sudo dnf -y install wget
$ wget https://download.virtualbox.org/virtualbox/rpm/el/virtualbox.repo
$ sudo mv virtualbox.repo /etc/yum.repos.d/
```

## Import the Oracle repository signing key

```shell
wget -q https://www.virtualbox.org/download/oracle_vbox.asc
sudo rpm --import oracle_vbox.asc
```

## Install additional packages

This step requires EPEL:

```shell
sudo dnf -y install binutils kernel-devel kernel-headers libgomp make patch gcc glibc-headers glibc-devel dkms
```

## Install VirtualBox

```shell
sudo dnf install -y VirtualBox-6.1
```

## Final configuration

```shell
sudo usermod -aG vboxusers $USER
sudo /usr/lib/virtualbox/vboxdrv.sh setup
```
