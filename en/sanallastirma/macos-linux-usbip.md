---
title: Testing Linux USB/IP infrastructure on macOS
permalink: /en/sanallastirma/macos-linux-usbip/
status: duzenlendi
reviewed: 2026-11-03
scope: vhci_hcd limitations on macOS, QEMU USB passthrough (-device usb-host) and
  USB/IP testing between Linux VMs.
lang: en
translation_key: guide-sanallastirma-macos-linux-usbip
translation_of: /sanallastirma/macos-linux-usbip/
translated: '2026-11-03'
---

# Testing Linux USB/IP infrastructure on macOS

USB/IP lets a physical USB device connected to one computer—such as a camera, serial adapter or security dongle—appear as local hardware on another computer over TCP/IP.

Engineers trying to test this infrastructure natively on macOS encounter kernel-architecture limitations. This guide explains the **`vhci_hcd` limitation** and builds a **USB/IP test lab using QEMU and Linux virtual machines**.

## 1. Why the Linux USB/IP stack does not run natively on macOS

Linux USB/IP relies on two kernel modules:

1. **`usbip-host.ko` — server / stub driver:** unbinds a physical device from Linux `usbcore` and forwards URB (**USB Request Block**) traffic over TCP port 3240.
2. **`vhci-hcd.ko` — client / virtual host controller:** emulates a USB host controller on the client and presents network requests to its kernel as though a USB device were physically attached.

### macOS kernel limitations

- **Different architecture:** Darwin/XNU uses I/O Kit and DriverKit rather than Linux `usbcore` and `struct urb`. Linux’s `vhci-hcd` and `usbip-host` modules cannot be loaded there.
- **KEXT deprecation and system security:** modern macOS discourages third-party kernel extensions. Apple Silicon requires Reduced Security settings to load such extensions.
- **DriverKit limitations:** `USBDriverKit` supports specific userspace device drivers; it does not provide the Linux stack’s virtual-host-controller mechanism for tunnelling bus traffic through TCP.

The native Linux USB/IP server and client therefore cannot simply be run on macOS.

## 2. The solution: QEMU and Linux VMs on macOS

The inability to load Linux USB/IP modules on the host does not prevent developing or testing them on a Mac. Use **QEMU and virtual Linux machines**:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                               macOS Host                                │
│                                                                         │
│  ┌───────────────────────────┐           ┌───────────────────────────┐  │
│  │    QEMU VM 1 (Sunucu)     │           │    QEMU VM 2 (İstemci)    │  │
│  │   (IP: 192.168.64.10)     │           │    (IP: 192.168.64.11)    │  │
│  │                           │           │                           │  │
│  │  ┌─────────────────────┐  │  TCP 3240 │  ┌─────────────────────┐  │  │
│  │  │ usbip-host.ko       │  │◄──────────┼──│ vhci-hcd.ko         │  │  │
│  │  │ usbipd servisi      │  │ (USB/IP)  │  │ usbip attach        │  │  │
│  │  └─────────────────────┘  │           │  └─────────────────────┘  │  │
│  │             ▲             │           │             │             │  │
│  │             │             │           │             ▼             │  │
│  │  [QEMU USB Passthrough]   │           │    [Sanal Kök Hub]        │  │
│  │  [-device usb-host]       │           │    [Görünen lsusb aygıtı] │  │
│  └─────────────┬─────────────┘           └───────────────────────────┘  │
└────────────────┼────────────────────────────────────────────────────────┘
                 ▼
     [Mac'e Takılı Fiziksel USB]
```

### How QEMU USB passthrough works

Using macOS userspace `libusb` / IOKit interfaces, QEMU can forward a physical USB device to a VM’s emulated USB bus with `-device usb-host`. The device is released by the host and attached to VM 1’s Linux kernel.

## 3. Prerequisites and installation

Install QEMU and libusb in the Mac terminal:

```bash
brew install qemu libusb
```

Identify the device’s vendor and product IDs:

```bash
system_profiler SPUSBDataType
```

Example output:

```text
FT232R USB UART:
  Product ID: 0x6001
  Vendor ID: 0x0403  (Future Technology Devices International Limited)
```

## 4. Start the QEMU virtual machines

### Server — VM 1

Pass the Mac’s physical USB device to the server VM and expose USB/IP port `3240`:

```bash
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive file=server.qcow2,if=virtio \
    -netdev user,id=net0,hostfwd=tcp::3240-:3240,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -device qemu-xhci,id=xhci \
    -device usb-host,vendorid=0x0403,productid=0x6001 \
    -nographic
```

*Without physical hardware, you can test the protocol with a QEMU virtual USB disk instead of `-device usb-host`: `-drive file=test_disk.raw,if=none,id=u1 -device usb-storage,drive=u1`.*

### Client — VM 2

Start the client VM in a second terminal:

```bash
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive file=client.qcow2,if=virtio \
    -netdev user,id=net0,hostfwd=tcp::2223-:22 \
    -device virtio-net-pci,netdev=net0 \
    -nographic
```

## 5. Configure USB/IP on the server (VM 1)

Connect to the Linux server with `ssh -p 2222 ubuntu@localhost`.

### 1. Install tools and load kernel modules

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic linux-tools-$(uname -r) hwdata usbutils
sudo modprobe usbip-core
sudo modprobe usbip-host
```

### 2. Start the USB/IP daemon

```bash
sudo usbipd -D
```

### 3. List local devices

```bash
usbip list -l
```

Expected output:

```text
 - busid 1-1 (0403:6001)
   Future Technology Devices International, Ltd : FT232 Serial (UART) IC (0403:6001)
```

### 4. Bind the device to the USB/IP stub driver

```bash
sudo usbip bind -b 1-1
```

The device is now detached from normal local use and available over the network.

## 6. Configure USB/IP on the client (VM 2)

Connect to the Linux client with `ssh -p 2223 ubuntu@localhost`.

### 1. Install tools and load the vhci-hcd controller

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic linux-tools-$(uname -r) usbutils
sudo modprobe vhci-hcd
```

### 2. Query devices shared by the server

```bash
usbip list -r 10.0.2.2
```

*With QEMU user-mode networking, the host gateway is normally `10.0.2.2`.*

Expected output:

```text
Exportable USB devices
======================
 - 10.0.2.2
      1-1: Future Technology Devices International, Ltd : FT232 Serial (0403:6001)
         : /sys/devices/platform/xhci-hcd.0/usb1/1-1
         : (Defined at Interface level) (00/00/00)
```

### 3. Attach the remote device to the virtual controller

```bash
sudo usbip attach -r 10.0.2.2 -b 1-1
```

## 7. Verify and detach cleanly

Run `lsusb` in the client:

```bash
lsusb
```

Expected output:

```text
Bus 001 Device 002: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

`dmesg` should show that `vhci_hcd` recognised the device and created `/dev/ttyUSB0`:

```bash
dmesg | tail -n 10
```

Check connection status:

```bash
usbip port
```

### Teardown

Release the port on the client:

```bash
sudo usbip detach -p 00
```

Return the device to local use on the server:

```bash
sudo usbip unbind -b 1-1
```

## Practical alternative: Lima (limactl)

If you prefer not to manage QEMU’s command-line options manually, **Lima** provides YAML-based Linux VM configuration on macOS, including VM networking and device-related options.

## Sources and verification environment

- [Linux kernel USB/IP documentation](https://docs.kernel.org/usb/usbip_protocol.html)
- [QEMU USB emulation and passthrough reference](https://www.qemu.org/docs/master/system/devices/usb.html)
- [Apple USBDriverKit reference](https://developer.apple.com/documentation/usbdriverkit)

This guide was tested on an Apple Silicon Mac running macOS Sonoma 14.5, using QEMU 9.0 (`-device usb-host`), Ubuntu 24.04 guests and FTDI USB-UART hardware.
