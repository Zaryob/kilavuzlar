---
title: 'CentOS/RHEL: installing an ELRepo kernel'
permalink: /en/arsiv/linux/cekirdek/elrepo-kernel-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: ELRepo EL8 packages and kernel-ml/kernel-lt examples.
archive_reason: The original notes confuse EPEL and ELRepo. Distribution compatibility,
  signing keys, Secure Boot and rollback steps need verification.
lang: en
translation_key: guide-arsiv-linux-cekirdek-elrepo-kernel-kurulumu
translation_of: /arsiv/linux/cekirdek/elrepo-kernel-kurulumu/
translated: '2026-11-03'
---

# CentOS/RHEL: installing an ELRepo kernel

CentOS and RHEL favour stable, compatible versions over adding new features. At the time of these notes, users needing a recent kernel for hardware support, at least a 5.x version, could find a distribution’s 4.x kernel limiting. The original notes turn to the external ELRepo kernel packages for this purpose.

## Enable the kernel repository

First import the GPG key:

```bash
rpm --import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org
```

Add the repository:

```
rpm -Uvh https://www.elrepo.org/elrepo-release-8.el8.elrepo.noarch.rpm
```

Refresh the package metadata:

```
yum update
```

## Install a mainline kernel

The mainline package provides a recent kernel and its patches:

```bash
yum --enablerepo=elrepo-kernel install kernel-ml -y
```

If you also need its header files:

```bash
yum --enablerepo=elrepo-kernel install kernel-ml kernel-ml-devel -y
```

## Install an LTS kernel

An LTS kernel receives long-term patches and security fixes from the kernel community:

```bash
yum --enablerepo=elrepo-kernel install kernel-lt -y
```

To install its header files:

```bash
yum --enablerepo=elrepo-kernel install kernel-lt kernel-lt-devel -y
```
