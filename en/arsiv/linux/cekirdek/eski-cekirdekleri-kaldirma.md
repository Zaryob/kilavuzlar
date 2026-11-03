---
title: 'CentOS/RHEL: removing old kernels'
permalink: /en/arsiv/linux/cekirdek/eski-cekirdekleri-kaldirma/
status: arsiv
reviewed: 2026-11-02
scope: Examples for Fedora 27/28 and RHEL/CentOS 6–8.
archive_reason: Verify preservation of the running kernel, a fallback kernel and the
  package-removal behaviour appropriate to the target distribution.
lang: en
translation_key: guide-arsiv-linux-cekirdek-eski-cekirdekleri-kaldirma
translation_of: /arsiv/linux/cekirdek/eski-cekirdekleri-kaldirma/
translated: '2026-11-03'
---

# CentOS/RHEL: removing old kernels

These are short historical notes on removing old kernels to reclaim limited disk space, for example on VPS instances and laptops. The example keeps two kernels; adjust the count if you intend to retain more or fewer.

## List installed kernels

List the installed RHEL kernel packages:

```bash
$ rpm -qa kernel\* |sort -V
kernel-4.18.0-240.10.1.el8_3.x86_64
kernel-4.18.9-200.el8_3.x86_64
kernel-4.18.10-200.el8_3.x86_64
kernel-core-4.18.0-240.10.1.el8_3.x86_64
kernel-core-4.18.9-200.el8_3.x86_64
kernel-core-4.18.10-200.el8_3.x86_64
kernel-devel-4.18.0-240.10.1.el8_3.x86_64
kernel-devel-4.18.9-200.el8_3.x86_64
kernel-devel-4.18.10-200.el8_3.x86_64
kernel-headers-4.18.0-240.10.1.el8_3.x86_64
kernel-modules-4.18.0-240.10.1.el8_3.x86_64
kernel-modules-4.18.9-200.el8_3.x86_64
kernel-modules-4.18.10-200.el8_3.x86_64
kernel-modules-extra-4.18.9-200.el8_3.x86_64
kernel-modules-extra-4.18.10-200.el8_3.x86_64
kernel-tools-4.18.0-240.10.1.el8_3.x86_64
kernel-tools-libs-4.18.0-240.10.1.el8_3.x86_64
```

## Remove installed kernels

### Fedora 28 and later; RHEL/CentOS 8 and later

```bash
$ dnf remove $(dnf repoquery --installonly --latest-limit=-2 -q)
```

### Fedora 27 and earlier; RHEL/CentOS 6–7 and earlier

``` bash
$ yum install yum-utils
$ package-cleanup --oldkernels --count=2
```

## Limit the number of retained kernels

Set *installonly_limit* in `/etc/yum.conf` or `/etc/dnf/dnf.conf`:

```bash
echo "installonly_limit=2" >> /etc/yum.conf
```
