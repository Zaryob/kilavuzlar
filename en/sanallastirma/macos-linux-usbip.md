---
title: Testing Linux USB/IP infrastructure on macOS
permalink: /en/sanallastirma/macos-linux-usbip/
status: duzenlendi
reviewed: 2026-11-09
scope: vhci_hcd limitations on macOS, QEMU USB passthrough (-device usb-host) and
  USB/IP testing between Linux VMs.
lang: en
translation_key: guide-sanallastirma-macos-linux-usbip
translation_of: /sanallastirma/macos-linux-usbip/
translated: '2026-11-09'
---

# Testing Linux USB/IP on macOS

Linux USB/IP uses `usbip-host` on the exporting server and `vhci-hcd` on the importing client, over TCP port 3240. These Linux kernel modules do not run on Darwin. This guide uses two Linux VMs; it makes no blanket claim about all third-party macOS USB/IP implementations or DriverKit capabilities.

## 1. Prepare two bootable VMs

Use an Apple Silicon Mac with QEMU/HVF and an Ubuntu 24.04 ARM64 cloud image. The following commands run on macOS in a new lab directory. The image URL is mutable; record its checksum and date for your run.

```bash
brew install qemu libusb
mkdir usbip-lab
cd usbip-lab
curl -fLO https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img
shasum -a 256 noble-server-cloudimg-arm64.img
```

The setup creates independent disk overlays, cloud-init seeds and writable UEFI variable stores. Never share a writable vars file between VMs. Keep the private SSH key local. Run `bash prepare.sh` once:

```bash
set -eu
QEMU_SHARE="$(brew --prefix qemu)/share/qemu"
test -f "$QEMU_SHARE/edk2-aarch64-code.fd"
test -f "$QEMU_SHARE/edk2-arm-vars.fd"
# Run once in a new lab directory; keep each VM's state on subsequent boots.
ssh-keygen -t ed25519 -N "" -f lab_ed25519
for vm in server client; do
    qemu-img create -f qcow2 -F qcow2 \
        -b "$PWD/noble-server-cloudimg-arm64.img" "$vm.qcow2" 12G
    cp "$QEMU_SHARE/edk2-arm-vars.fd" "$vm-vars.fd"
    mkdir "seed-$vm"
    cat > "seed-$vm/meta-data" <<EOF
instance-id: kilavuzlar-$vm
local-hostname: $vm
EOF
    cat > "seed-$vm/user-data" <<EOF
#cloud-config
users:
  - default
ssh_authorized_keys:
  - $(cat lab_ed25519.pub)
ssh_pwauth: false
EOF
    hdiutil makehybrid -o "seed-$vm.iso" -iso -joliet \
        -default-volume-name cidata "seed-$vm"
done
```
{: data-filename="prepare.sh"}

## 2. Start and record both boots

Both VMs have an independent user-mode network, normally with guest address `10.0.2.15`. They are not on a shared LAN. From the client, `10.0.2.2:33240` reaches the host loopback forwarding to the server. The guest server still listens on 3240; host port 33240 avoids a common local conflict. SSH forwarding is bound to host loopback only.

```bash
set -eu
QEMU_SHARE="$(brew --prefix qemu)/share/qemu"
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive if=pflash,format=raw,readonly=on,file="$QEMU_SHARE/edk2-aarch64-code.fd" \
    -drive if=pflash,format=raw,file=server-vars.fd \
    -drive file=server.qcow2,if=virtio,format=qcow2 \
    -drive file=seed-server.iso,if=virtio,format=raw,readonly=on \
    -netdev user,id=net0,hostfwd=tcp:127.0.0.1:33240-:3240,hostfwd=tcp:127.0.0.1:2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -device qemu-xhci,id=xhci \
    -nographic
```
{: data-filename="start-server.sh"}


```bash
set -eu
QEMU_SHARE="$(brew --prefix qemu)/share/qemu"
qemu-system-aarch64 \
    -M virt,highmem=on -accel hvf -cpu host -m 2G -smp 2 \
    -drive if=pflash,format=raw,readonly=on,file="$QEMU_SHARE/edk2-aarch64-code.fd" \
    -drive if=pflash,format=raw,file=client-vars.fd \
    -drive file=client.qcow2,if=virtio,format=qcow2 \
    -drive file=seed-client.iso,if=virtio,format=raw,readonly=on \
    -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2223-:22 \
    -device virtio-net-pci,netdev=net0 \
    -nographic
```
{: data-filename="start-client.sh"}


```bash
bash start-server.sh > server-boot.log 2>&1 &
bash start-client.sh > client-boot.log 2>&1 &
# Wait for cloud-init/SSH to become ready on each VM.
ssh -i ./lab_ed25519 -p 2222 ubuntu@127.0.0.1 'cloud-init status --wait; uname -a; ip -4 addr'
ssh -i ./lab_ed25519 -p 2223 ubuntu@127.0.0.1 'cloud-init status --wait; uname -a; ip -4 addr'
```

Keep `server-boot.log` and `client-boot.log`; a QEMU process starting alone does not prove Ubuntu booted. For software-only USB testing, create a blank raw disk with `qemu-img create -f raw test_disk.raw 64M` and add `-drive file=test_disk.raw,if=none,id=u1,format=raw -device usb-storage,drive=u1` to the server command before boot. This does not validate physical passthrough.

## 3. Physical USB passthrough (hardware required)

Use `system_profiler SPUSBDataType` to identify the real vendor/product IDs. With the server shut down, add the following option to its QEMU command (FTDI example IDs only):

```text
-device usb-host,vendorid=0x0403,productid=0x6001
```

macOS may already own the device through a driver; libusb access, driver release and permissions must be checked with the actual device. Do not treat QEMU accepting the option as a successful USB transfer.

## 4. Export from the server (VM 1)

Run in the server VM. Match the running kernel; some images additionally need `linux-modules-extra-$(uname -r)`. If a matching tools/modules package is unavailable, install a supported generic kernel and reboot first.

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic "linux-tools-$(uname -r)" "linux-modules-extra-$(uname -r)" usbutils
sudo modprobe usbip-host
sudo usbipd -D
usbip list -l
# Replace 1-1 with the actual busid listed above.
sudo usbip bind -b 1-1
```

## 5. Attach from the client (VM 2)

Run in the client VM. Substitute the exported busid; it is not a stable device identifier:

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic "linux-tools-$(uname -r)" "linux-modules-extra-$(uname -r)" usbutils
sudo modprobe vhci-hcd
usbip --tcp-port 33240 list -r 10.0.2.2
sudo usbip --tcp-port 33240 attach -r 10.0.2.2 -b 1-1
# USB enumeration is asynchronous; wait for the expected device to appear.
sudo udevadm settle
lsusb
sudo usbip port
sudo dmesg | tail -n 10
```

A physical FTDI test requires the correct VID:PID on the client, creation of a serial device and an actual serial data-transfer test. `lsusb` alone is not sufficient. For the virtual disk, observe the mass-storage device instead; do not expect `/dev/ttyUSB0`. PCI/xHCI sysfs paths and bus numbers vary.

## 6. Detach and shut down

```bash
# Client: replace 00 with the port shown by sudo usbip port.
sudo usbip detach -p 00
# Server: use the actual exported busid.
sudo usbip unbind -b 1-1
```


```bash
# macOS: shut down each guest cleanly, retaining overlays and vars files.
ssh -i ./lab_ed25519 -p 2223 ubuntu@127.0.0.1 'sudo poweroff'
ssh -i ./lab_ed25519 -p 2222 ubuntu@127.0.0.1 'sudo poweroff'
```

## Sources and verification scope

- [QEMU virt firmware](https://www.qemu.org/docs/master/system/arm/virt.html)
- [QEMU user-mode networking](https://www.qemu.org/docs/master/system/devices/net.html)
- [QEMU USB passthrough](https://www.qemu.org/docs/master/system/devices/usb.html)
- [Linux USB/IP protocol](https://docs.kernel.org/usb/usbip_protocol.html)
- [Ubuntu ARM64 cloud images](https://cloud-images.ubuntu.com/noble/current/)

8–9 November 2026: two Ubuntu ARM64 guests were booted with independent UEFI vars on QEMU 11.1.3/HVF and their network path was checked. A virtual 64 MiB USB disk also passed bind/list/attach, client write/read and detach/unbind. Physical USB passthrough and FTDI data transfer have **not been verified**. Neither this run nor a virtual USB disk establishes physical-hardware acceptance.
