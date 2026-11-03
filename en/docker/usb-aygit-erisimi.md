---
title: Why USB device access fails in Docker
permalink: /en/docker/usb-aygit-erisimi/
status: duzenlendi
reviewed: 2026-11-03
scope: Docker device mapping, cgroup rules and kernel-module limitations on Linux,
  macOS and Windows (WSL2).
lang: en
translation_key: guide-docker-usb-aygit-erisimi
translation_of: /docker/usb-aygit-erisimi/
translated: '2026-11-03'
---

# Why USB device access fails in Docker

Engineers working on embedded systems, IoT, robotics or hardware development frequently encounter access errors when programming microcontrollers (Arduino, STM32 or ESP32) or USB-to-serial adapters (FTDI, CH340 or CP2102) inside Docker containers.

Three main factors underlie these failures:
1. Operating-system and hypervisor isolation of the USB bus, especially on macOS and Windows.
2. Linux cgroup device controls and container filesystem isolation.
3. The requirement for hardware drivers to be loaded in the host kernel, rather than inside the container.

## 1. Host architecture limitations: Linux vs macOS vs Windows

Docker containers are not virtual machines: they share their host kernel. The consequences differ substantially between operating systems.

### Native Linux Engine

Containers use the host’s Linux kernel directly. Kernel-created device nodes (`/dev/ttyUSB0`, `/dev/bus/usb/...`) can be exposed to a container using filesystem mounts and cgroup permissions.

### Docker Desktop on macOS

macOS uses the XNU (Darwin) kernel. Docker Desktop runs a lightweight **Linux virtual machine** using Apple’s `Virtualization.framework`.

- **Problem:** the macOS hypervisor layer does **not directly pass through** physical USB devices connected to the Mac’s USB-C/Thunderbolt ports to the Linux VM.
- The macOS kernel (IOKit) owns the device. The Linux VM, and therefore the Docker container, cannot see it.
- **Solution:** `docker run --device` alone does not work for a physical macOS device. Serial ports need a network bridge using `socat`, or a **USB/IP** arrangement through a Linux VM.

### Docker Desktop on Windows (WSL2)

Docker Desktop runs in a WSL2 (Windows Subsystem for Linux 2) VM. The Hyper-V architecture does not forward USB devices to WSL2 by default.

- **Solution:** use **`usbipd-win`**. On Windows, `usbipd bind` and `usbipd attach --wsl` attach the USB device to the WSL2 kernel.

## 2. Device mapping and security: `--device` vs `--privileged` vs cgroups

On Linux, accessing a device from a container requires permission at two levels:
1. A node for that device in the container’s `/dev` directory: a character or block device created with `mknod`.
2. Read/write permission for its `major:minor` number in the kernel’s cgroup device filter.

### `--device=/dev/ttyUSB0` — static mapping

At startup, Docker reads the device’s `major:minor` number, creates a node with the same name inside the container and grants access in the cgroup rules.
- **Limitation:** the device must be connected when the container starts.

### The danger of `--privileged` — an antipattern

Many online guides suggest `--privileged` to bypass USB problems. This removes major container-isolation protections:
- Grants `CAP_SYS_ADMIN` and all kernel capabilities.
- Sets the cgroup filter to `a *:* rwm`, granting broad device access.
- Disables AppArmor and Seccomp profiles.

> [!CAUTION]
> Malicious code or a vulnerability in a container running with `--privileged` can gain direct access to host disks (`/dev/sda`), UEFI variables and main memory (`/dev/mem`). Do not use `--privileged` merely to obtain USB access!

### A modern, restricted solution: `--device-cgroup-rule`

Allow selected USB device classes using wildcard rules instead of granting every privilege:

```bash
docker run --rm -it \
  --device-cgroup-rule='c 188:* rmw' \
  --device-cgroup-rule='c 166:* rmw' \
  --device-cgroup-rule='c 189:* rmw' \
  -v /dev:/dev \
  ubuntu:24.04
```

#### Important Linux character-device major numbers

- `188`: USB-to-serial adapters (`/dev/ttyUSB*`).
- `166`: ACM modems and development boards (`/dev/ttyACM*`).
- `189`: raw USB bus devices (`/dev/bus/usb/*/*`, for libusb/hidapi).

## 3. Dynamic USB disconnect/reconnect: the udev hotplug problem

A common surprise is that *the container connects to a device when first started, but loses access after the USB cable is unplugged and reconnected, until the container is restarted.*

### Root cause

1. When a USB device is reconnected, the Linux kernel creates a new node and its device number increases, for example from `/dev/bus/usb/001/004` to `001/005`. For serial ports, the filesystem **inode** is removed and recreated.
2. The container’s `/dev` directory is an isolated `tmpfs` mount. The host `udevd` service creates the new node only in the host’s `/dev`; the container’s mount namespace does not receive it.
3. The old inode mounted through `--device` is now orphaned, causing `No such file or directory` or `Input/output error`.

### Hotplug solution

To support dynamic devices, mount the host device tree as a volume and define the appropriate wildcard cgroup rule:

```bash
docker run --rm -it \
  --device-cgroup-rule='c 188:* rmw' \
  --device-cgroup-rule='c 166:* rmw' \
  -v /dev:/dev \
  my-embedded-app
```

## 4. Missing host kernel drivers

Another misconception is that a hardware driver can be installed inside a container using `apt-get install`.

- Containers do not run their own kernels. Hardware drivers (`.ko` modules) are loaded into the kernel directly.
- `modprobe` or `insmod` cannot normally load modules from inside a container because `CAP_SYS_MODULE` is restricted.
- The driver that recognises the hardware and creates `/dev/ttyUSB0` must be loaded in the **host Linux kernel**.

### Common chips and kernel modules

- **`ch341`**: common Arduino clones and ESP8266 boards (WCH CH340/CH341).
- **`cp210x`**: NodeMCU and ESP32 development boards (Silicon Labs CP2102).
- **`ftdi_sio`**: industrial serial adapters and JTAG programmers.
- **`cdc_acm`**: original Arduino Uno/Mega, Raspberry Pi Pico and USB modems.

### Checking the driver on the host

Watch host kernel messages as you connect the device:

```bash
dmesg | tail -n 20
```

Example of healthy output:

```text
usb 1-1: new full-speed USB device number 5 using xhci_hcd
ch341 1-1:1.0: ch341-uart converter detected
usb 1-1: ch341-uart converter now attached to ttyUSB0
```

If you see only `new USB device found`, without an `attached to tty...` line, the relevant driver module is missing on the host; for example, run `sudo modprobe ch341`.

## Troubleshooting matrix

| Symptom / error | Root cause | Remedy |
| :--- | :--- | :--- |
| Device never appears on macOS | Docker Desktop’s VM does not forward USB | Use USB/IP or a Linux VM bridge. |
| Connection is lost after reconnecting the cable | udev hotplug does not reach the container | Use `-v /dev:/dev` and `--device-cgroup-rule`. |
| `Permission denied` on /dev/ttyUSB0 | Missing dialout group permissions | Use `--group-add dialout` or run the container as root. |
| `lsusb` works but `/dev/ttyUSB0` is absent | Host kernel driver is missing | Load `cp210x` / `ch341` with `modprobe` on the host. |

## Sources and verification environment

- [Linux kernel documentation — Devices and Cgroups](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [usbipd-win repository](https://github.com/dorssel/usbipd-win)
- [Docker Engine device specification](https://docs.docker.com/engine/reference/commandline/run/#device)

This guide was tested and verified on Ubuntu 24.04 (Linux 6.8), macOS Sonoma (Docker Desktop 4.30) and FTDI/CH340 hardware.
