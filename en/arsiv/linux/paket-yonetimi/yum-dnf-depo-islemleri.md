---
title: Managing repositories with YUM/DNF
permalink: /en/arsiv/linux/paket-yonetimi/yum-dnf-depo-islemleri/
status: arsiv
reviewed: 2026-11-02
scope: YUM, yum-utils and RHEL 8 repository examples.
archive_reason: Distinguish YUM and DNF versions. Review bulk enable/disable examples
  and wildcard expansion by the shell.
lang: en
translation_key: guide-arsiv-linux-paket-yonetimi-yum-dnf-depo-islemleri
translation_of: /arsiv/linux/paket-yonetimi/yum-dnf-depo-islemleri/
translated: '2026-11-03'
---

# Managing repositories with YUM/DNF

## List repositories

List all available repositories, including disabled ones:

```shell
# yum repolist all
depo id                              depo adı                         durum
rhel-8-for-x86_64-baseos-rpms        Red Hat Enterprise Linux 8 for   etkin
rpmfusion-free-updates               RPM Fusion for EL 8 - Free - U   etkin
rpmfusion-free-updates-testing       RPM Fusion for EL 8 - Free - T   devre dışı
rpmfusion-nonfree-updates            RPM Fusion for EL 8 - Nonfree    etkin
```

## Manage repositories with yum-utils

Install yum-utils:

```shell
# yum install -y yum-utils
```

This provides `yum-config-manager`, which can enable and disable repositories:

```shell
# yum-config-manager --enable <repo-id>
# yum-config-manager --disable <repo-id>
```

### Enable a repository

```shell
# yum-config-manager --enable rpmfusion-free-updates-testing
```

### Disable a repository

```shell
# yum-config-manager --disable rpmfusion-free-updates-testing
```

## Repository selection for a package operation

Use `--enablerepo=<repoid>` during installation, removal or upgrade to enable a repository temporarily for that operation:

```shell
# yum install kernel-ml --enablerepo=elrepo-kernel
```

## Edit repositories manually

Repository definitions are stored in `/etc/yum.repos.d`. An example entry:

```
[rpmfusion-free-updates]
    name=RPM Fusion for EL 8 - Free - Updates
    #baseurl=http://download1.rpmfusion.org/free/el/updates/8/$basearch/
    mirrorlist=http://mirrors.rpmfusion.org/mirrorlist?repo=free-el-updates-released-8&arch=$basearch
    enabled=1
    gpgcheck=1
```

`enabled` is 1 for an enabled repository and 0 for a disabled one.

## Subscription Manager — RHEL only

`subscription-manager` manages subscribed RHEL repositories defined in `redhat.repo`.

### List repositories

```shell
# subscription-manager repos --list
```

### Enable a repository

```shell
# subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
```

### Disable a repository

```shell
# subscription-manager repos --disable=rhel-8-for-x86_64-baseos-rpms
```

## Enable all repositories

```shell
# yum-config-manager --enablerepo=*
```

For RHEL-specific repositories:

```shell
# subscription-manager repos --enable=*
```

## Disable all repositories

```shell
# yum-config-manager --disablerepo=*
```

For RHEL-specific repositories:

```shell
# subscription-manager repos --disable=*
```
