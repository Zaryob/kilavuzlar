---
title: AMD Radeon Pro configuration
permalink: /en/arsiv/linux/donanim/amd-radeon-pro-ayarlari/
status: arsiv
reviewed: 2026-11-02
scope: Notes from 2019–2021; Oibaf PPA and DRI_PRIME.
archive_reason: Distinguish the Mesa PPA, amdgpu-pro and hybrid-GPU selection. Specify
  hardware requirements before changing DRI_PRIME system-wide.
lang: en
translation_key: guide-arsiv-linux-donanim-amd-radeon-pro-ayarlari
translation_of: /arsiv/linux/donanim/amd-radeon-pro-ayarlari/
translated: '2026-11-03'
---

# AMD Radeon Pro configuration

The Linux kernel provides AMD Radeon Pro support through the amdgpu module. For some cards, the original notes also used amdgpu-pro components. This guide records the author’s setup from 2019–2021.

## Add the PPA

```shell
$ sudo add-apt-repository ppa:oibaf/graphics-drivers
```

## Apply updates

```shell
$ sudo apt update && sudo apt -y upgrade
```

The output lists packages available for upgrade; the original procedure upgrades them all.

## Final adjustment

If the application still does not use the intended GPU, the notes apply:

```shell
$ sudo su
# echo \"DRI_PRIME=1\" >> /etc/environment
```

This sets DRI_PRIME for the graphical session.
