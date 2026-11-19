---
title: "Headless kernel switching for the next boot: grub-reboot and safety mechanisms"
permalink: /en/linux/headless-kernel-degisimi/
status: duzenlendi
reviewed: 2026-11-20
translation_of: /linux/headless-kernel-degisimi/
translated: '2026-11-20'
scope: One-time kernel selection via grub-reboot on headless Ubuntu 22.04 and 24.04 LTS servers, switching between generic, lowlatency, and HWE variants, panic handling, and recordfail safety configurations.
lang: en
translation_key: guide-linux-headless-kernel-degisimi
---

# Headless kernel switching for the next boot: grub-reboot and safety mechanisms

Servers operating without a physical display or keyboard in remote data centers, cloud providers
(AWS, Hetzner, DigitalOcean), or local server racks are known as **headless systems**. Administration
is carried out exclusively over SSH or automation frameworks (Ansible, Puppet).

Switching the Linux kernel on a headless server carries significant risk:
- If a new kernel fails during boot due to hardware incompatibility, kernel panic, or a missing network interface controller (NIC) driver, the SSH daemon will never start.
- Without a physical keyboard and screen, you cannot intervene at the GRUB menu during boot to select an older, working kernel.
- In the absence of out-of-band IPMI/iKVM (iDRAC, iLO) access, recovery requires data center staff ("remote hands") or rebooting into a rescue system.

The industry-standard solution to eliminate this risk is the **one-shot boot** mechanism.
Using the `grub-reboot` tool, you instruct GRUB:
*"Only try the new kernel (`lowlatency` or `HWE`) on the very next boot. If the system fails to boot,
crashes, or is rebooted, automatically revert to the safe, known-good kernel (`generic`)."*

```text
               ┌─────────────────────────────────────────────────────────┐
               │    Headless Server: grub-reboot executed over SSH       │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │    next_entry written to /boot/grub/grubenv file        │
               └────────────────────────────┬────────────────────────────┘
                                            │ sudo reboot
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │  GRUB loads: reads next_entry, IMMEDIATELY CLEARS it    │
               │        and boots the target kernel (e.g. lowlatency)    │
               └────────────────────────────┬────────────────────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      ▼                                           ▼
          [ SUCCESSFUL BOOT ]                           [ FAILURE / PANIC ]
          • SSH daemon starts up                        • panic=10 triggers reboot after 10s
          • Administrator confirms via uname -r         • Watchdog resets frozen hardware
          • Make permanent via grub-set-default         • Because next_entry was cleared,
                                                          GRUB boots safe default (generic)!
```

This guide details the internal architecture of `grub-reboot`, the essential safety configurations
(`panic=10` and `GRUB_RECORDFAIL_TIMEOUT`) to prevent unrecoverable hangs, step-by-step transitions
between `generic`, `lowlatency`, and `HWE` kernels, and the modern `systemd-boot` alternative.

---

## 1. GRUB and the `grubenv` mechanism

The GRUB bootloader typically mounts filesystems as read-only. However, to persist boot-state
preferences across reboots, it reserves a dedicated **1024-byte** environment block file at
`/boot/grub/grubenv`. GRUB writes directly to disk blocks (via blocklists) even when the underlying
filesystem is not mounted read-write.

Two primary variables govern this system:

1. **`saved_entry`**: The permanent default kernel entry, updated via `grub-set-default`.
2. **`next_entry`**: A temporary kernel entry evaluated **only on the next boot**, configured via `grub-reboot`.

### The boot cycle logic

During early boot, GRUB evaluates the following logic generated from `/etc/grub.d/00_header`:

```text
if [ -s $prefix/grubenv ]; then
  load_env
fi
if [ "${next_entry}" ] ; then
   set default="${next_entry}"
   set next_entry=
   save_env next_entry
   set boot_once=true
else
   set default="${saved_entry}"
fi
```

**The critical safety guarantee:**
The moment GRUB parses `next_entry`, **before** loading the Linux kernel binary into RAM, it clears
`next_entry` and commits the blank value back to disk (`save_env next_entry`).

If the newly tested kernel crashes, panics, or suffers a power reset, the subsequent boot will find
`next_entry` empty. GRUB immediately falls back to `saved_entry` (the stable default kernel), ensuring
you are never locked out of the server.

---

## 2. Headless safety checklist

Before attempting a one-shot kernel boot, you must enable **three defensive configurations** to ensure
the machine never hangs in an unattended boot freeze.

### 2.1. Safeguard 1: Auto-reboot on kernel panic (`panic=10`)

When a Linux kernel encounters a fatal exception ("Kernel Panic"), the default behavior is often to print
the stack trace and freeze indefinitely (`kernel.panic = 0`), blinking the keyboard scroll-lock LEDs.
On a headless host, this results in an unresponsive system requiring physical power cycling.

Instruct the kernel to reboot 10 seconds after a panic:

Create `/etc/sysctl.d/99-panic.conf`:

```bash
kernel.panic = 10
```
{: data-filename="/etc/sysctl.d/99-panic.conf"}

Apply the configuration immediately:

```bash
sudo sysctl --system
```

To guard against early panics occurring before user-space `sysctl` settings load, also append this
parameter to the GRUB kernel command line (configured in section 2.3).

### 2.2. Safeguard 2: Disable the GRUB `recordfail` infinite timeout trap

On Ubuntu systems, GRUB flags an unclean shutdown or boot error by setting `recordfail=1`. When this
flag is active, GRUB's default behavior is to **suppress the timeout (`timeout = -1`) and wait forever
for manual keyboard input**!

On a headless machine with no console attached, this causes an indefinite boot hang, defeating automated
recovery.

To neutralize this trap, `GRUB_RECORDFAIL_TIMEOUT` must be explicitly defined in `/etc/default/grub`.

### 2.3. Safeguard 3: Configuring `/etc/default/grub`

Edit `/etc/default/grub`:

```bash
sudo nano /etc/default/grub
```

Verify and update the following directives:

```bash
# Read default entry from saved_entry inside grubenv
GRUB_DEFAULT=saved

# Normal boot timeout in seconds
GRUB_TIMEOUT=5

# Boot timeout after an unclean shutdown/failure (NEVER leave as -1 on headless hosts)
GRUB_RECORDFAIL_TIMEOUT=5

# Append panic=10 for early kernel crash recovery
GRUB_CMDLINE_LINUX_DEFAULT="console=tty1 console=ttyS0,115200 quiet splash panic=10"
```
{: data-filename="/etc/default/grub"}

> **Rule on `GRUB_SAVEDEFAULT`:**
> Do **not** enable `GRUB_SAVEDEFAULT=true` when using `grub-reboot`. When set to true, every booted
> kernel becomes the new permanent default, completely bypassing the single-shot safety mechanism.

Commit the changes to GRUB:

```bash
sudo update-grub
```

```text
Sourcing file `/etc/default/grub'
Generating grub configuration file ...
Found linux image: /boot/vmlinuz-6.8.0-45-generic
Found initrd image: /boot/initrd.img-6.8.0-45-generic
Found linux image: /boot/vmlinuz-6.8.0-45-lowlatency
Found initrd image: /boot/initrd.img-6.8.0-45-lowlatency
done
```

---

## 3. Identifying installed kernels and GRUB menu entries

You need to know the exact package versions installed on your system and their corresponding GRUB menu strings.

### 3.1. Querying installed kernel packages

Assume a server with standard `generic`, low-latency `lowlatency`, and an updated Hardware Enablement (`HWE`) kernel:

```bash
dpkg -l | grep -E 'linux-image-[0-9]' | awk '{print $2, $3}'
```

```text
linux-image-6.8.0-45-generic 6.8.0-45.45
linux-image-6.8.0-45-lowlatency 6.8.0-45.45
linux-image-6.11.0-17-generic 6.11.0-17.17
```

Check the currently active kernel:

```bash
uname -rm
```

```text
6.8.0-45-generic x86_64
```

### 3.2. Listing the GRUB menu hierarchy

In Ubuntu, non-default kernels (such as lowlatency or older versions) reside under the `Advanced options for Ubuntu` submenu.

You can specify boot targets using either of two formats:

1. **Menu Title Path:** `Parent Menu Title>Child Menu Title`
   (e.g., `Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency`)
2. **Menuentry ID Path (Most Reliable):** Internal GRUB identifiers
   (e.g., `gnulinux-advanced-UUID>gnulinux-6.8.0-45-lowlatency-advanced-UUID`)

Inspect the available menu entries and hierarchy using `awk`:

```bash
awk -F"'" '/menuentry / {print i++ " : " $2} /submenu / {print "SUBMENU : " $2}' /boot/grub/grub.cfg
```

```text
0 : Ubuntu
SUBMENU : Advanced options for Ubuntu
2 : Ubuntu, with Linux 6.11.0-17-generic
3 : Ubuntu, with Linux 6.11.0-17-generic (recovery mode)
4 : Ubuntu, with Linux 6.8.0-45-generic
5 : Ubuntu, with Linux 6.8.0-45-generic (recovery mode)
6 : Ubuntu, with Linux 6.8.0-45-lowlatency
7 : Ubuntu, with Linux 6.8.0-45-lowlatency (recovery mode)
```

Targeting a kernel within the submenu requires joining them with `>`:
`"Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"`

---

## 4. One-shot kernel switching with `grub-reboot`

Follow these steps to safely test the `lowlatency` or `HWE` kernel without committing permanently.

```text
Step 1: Set the target kernel via grub-reboot
Step 2: Verify the environment block via grub-editenv list
Step 3: Reboot the server via sudo reboot
Step 4: Reconnect over SSH and confirm active kernel via uname -r
Step 5: If stable, make permanent (grub-set-default); otherwise a reboot reverts back!
```

### 4.1. Selecting the next boot kernel

To target the `6.8.0-45-lowlatency` kernel for the next restart:

```bash
sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"
```

If you wish to test the newer HWE kernel (`6.11.0-17-generic`):

```bash
sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.11.0-17-generic"
```

### 4.2. Verifying the environment block

Confirm that the target was registered in `grubenv`:

```bash
sudo grub-editenv list
```

Expected output:

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic
next_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency
```

`saved_entry` remains your stable baseline, while `next_entry` specifies the ephemeral one-time target.

### 4.3. Rebooting the host

With the safety net armed, reboot the machine:

```bash
sudo reboot
```

### 4.4. Post-boot verification

Once the server restarts, log in via SSH and inspect the running kernel:

```bash
uname -rmv
```

```text
6.8.0-45-lowlatency #45-Ubuntu SMP PREEMPT_DYNAMIC x86_64
```

Verify that the preemption model and timer tick match expectations:

```bash
grep -E 'CONFIG_PREEMPT(_VOLUNTARY|_DYNAMIC)?=|CONFIG_HZ=' /boot/config-$(uname -r)
```

```text
CONFIG_PREEMPT_BUILD=y
CONFIG_PREEMPT=y
CONFIG_HZ_1000=y
CONFIG_HZ=1000
```

Now re-check the GRUB environment block:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic
```

Notice that `next_entry` has disappeared. GRUB cleared it immediately upon boot.
If you were to reboot the machine right now (`sudo reboot`), it would automatically revert to the
original `generic` kernel without any manual intervention.

---

## 5. Making the selection permanent or aborting

### 5.1. Promoting to permanent default (`grub-set-default`)

If your benchmarks, network adapters, and services perform satisfactorily and you want to keep
this kernel as the primary choice:

```bash
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"
```

Verify:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency
```

The low-latency kernel is now the permanent default.

### 5.2. Aborting a scheduled one-shot boot before rebooting

If you run `grub-reboot` but decide against restarting into the new kernel before running `reboot`:

```bash
sudo grub-editenv - unset next_entry
```

Verify:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic
```

`next_entry` is removed, and the subsequent reboot will boot into `saved_entry` as usual.

---

## 6. Alternative environments: `systemd-boot` and `bootctl set-oneshot`

Modern minimal cloud images, Arch Linux, and Fedora systems frequently utilize **`systemd-boot`**
instead of GRUB on UEFI hardware.

On `systemd-boot`, one-shot boot targets are managed via EFI NVRAM variables.

### 6.1. Listing available entries

```bash
bootctl list
```

```text
type: Boot Loader Specification Type #1 (.conf)
title: Ubuntu Linux 6.8.0-45-generic
   id: ubuntu-6.8.0-45-generic.conf
source: /boot/efi//loader/entries/ubuntu-6.8.0-45-generic.conf

type: Boot Loader Specification Type #1 (.conf)
title: Ubuntu Linux 6.8.0-45-lowlatency
   id: ubuntu-6.8.0-45-lowlatency.conf
source: /boot/efi//loader/entries/ubuntu-6.8.0-45-lowlatency.conf
```

### 6.2. Setting a one-shot target

Pass the entry `id` to `bootctl set-oneshot`:

```bash
sudo bootctl set-oneshot ubuntu-6.8.0-45-lowlatency.conf
```

Check the loader status:

```bash
bootctl status | grep -A 3 "Boot into"
```

```text
Boot into: ubuntu-6.8.0-45-lowlatency.conf (one-shot)
```

This updates the `LoaderEntryOneShot` EFI variable. When the system restarts, `systemd-boot` executes
the selected entry and clears the variable from NVRAM.

---

## 7. Critical caveats and troubleshooting

### 7.1. Btrfs and ZFS `sparse file not allowed` error

GRUB's internal drivers for Btrfs and ZFS disallow block-level disk writes. If `/boot` resides directly
within a root Btrfs subvolume or ZFS pool:

- GRUB prints `error: sparse file not allowed` during boot.
- GRUB cannot clear `next_entry` or save variables to `grubenv`.

**Remedy:** On headless servers utilizing Btrfs or ZFS root partitions, always allocate a separate,
dedicated **Ext4 partition** (e.g., 1 GB) mounted at `/boot`.

### 7.2. Network interface naming drift (Predictable Network Interface Names)

Switching between major kernel versions (such as GA 5.15 to HWE 6.8) can alter PCI bus enumeration
or NIC driver naming conventions (e.g., `enp3s0` becoming `enp4s0` or `ens3`).
If Netplan relies on a static interface name, network initialization will fail, cutting off SSH access.

**Remedy:** Bind network interfaces by MAC address rather than mutable interface names:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    primary-nic:
      match:
        macaddress: "52:54:00:12:34:56"
      set-name: eth0
      dhcp4: true
```
{: data-filename="/etc/netplan/01-netcfg.yaml"}

### 7.3. Hardware watchdog protection

To guard against silent operating system lockups where the kernel does not panic but systemd hangs
before starting SSH, configure the motherboard's hardware watchdog timer (IPMI watchdog, Intel TCO,
or virtual i6300esb).

In `/etc/systemd/system.conf`:

```ini
RuntimeWatchdogSec=60s
RebootWatchdogSec=5min
```
{: data-filename="/etc/systemd/system.conf"}

If the operating system fails to ping the watchdog daemon within 60 seconds, the hardware resets the
node, triggering a fallback reboot to the stable kernel.

---

## 8. Quick reference command cheat sheet

| Action | Command |
| :--- | :--- |
| Active running kernel | `uname -r` |
| Installed kernel packages | `dpkg -l \| grep linux-image` |
| List GRUB menu entries | `awk -F"'" '/menuentry / {print i++ " : " $2} /submenu / {print "SUBMENU : " $2}' /boot/grub/grub.cfg` |
| Test `lowlatency` on next boot | `sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"` |
| Test `HWE` on next boot | `sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.11.0-17-generic"` |
| Check environment variables | `sudo grub-editenv list` |
| Abort scheduled one-shot boot | `sudo grub-editenv - unset next_entry` |
| Set permanent default kernel | `sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"` |

---

## Verification and sources

### Test environment
The procedures, `grub-reboot` and `grub-editenv` block interactions, `panic=10` parameter handling,
and `GRUB_RECORDFAIL_TIMEOUT` configurations detailed in this guide were verified on Ubuntu 22.04 LTS
and Ubuntu 24.04 LTS x86_64 environments (QEMU/KVM and physical hardware) across Linux 6.8 generic,
lowlatency, and 6.11 HWE kernels.

### Sources
- [GNU GRUB Manual - Environment block](https://www.gnu.org/software/grub/manual/grub/html_node/Environment-block.html): GRUB environment block architecture and `grub-reboot` mechanics.
- [Ubuntu Community Help Wiki - Grub2](https://help.ubuntu.com/community/Grub2/Setup): GRUB_DEFAULT, saved, and recordfail configurations.
- [The Linux Kernel documentation - The kernel’s command-line parameters](https://docs.kernel.org/admin-guide/kernel-parameters.html): `panic=` parameter specification and error recovery behaviors.
- [systemd-boot Manual](https://manpages.ubuntu.com/manpages/noble/en/man7/systemd-boot.7.html): `bootctl` commands and the `LoaderEntryOneShot` interface.
