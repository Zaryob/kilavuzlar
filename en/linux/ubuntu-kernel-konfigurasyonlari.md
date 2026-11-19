---
title: "Ubuntu kernel configurations: generic, lowlatency and HWE"
permalink: /en/linux/ubuntu-kernel-konfigurasyonlari/
status: duzenlendi
reviewed: 2026-11-19
scope: Architectures, build flags, installation, and GRUB management for linux-generic, linux-lowlatency, HWE, and OEM/realtime kernels on Ubuntu 22.04 LTS and 24.04 LTS.
lang: en
translation_key: guide-linux-ubuntu-kernel-konfigurasyonlari
translation_of: /linux/ubuntu-kernel-konfigurasyonlari/
translated: '2026-11-19'
---

# Ubuntu kernel configurations: generic, lowlatency and HWE

The Linux kernel is the fundamental layer of the operating system that manages hardware
resources and enables user-space processes to safely communicate with physical devices.
Although the kernel has a monolithic architecture, build-time configuration options
(`Kconfig` flags), scheduler parameters, and release life cycles can be tailored for
distinct workloads.

Rather than forcing a single kernel binary onto all use cases, Ubuntu provides official,
purpose-built kernel variants:

- **`linux-generic`**: The default kernel designed for general server, desktop, and cloud workloads, providing the highest throughput and power efficiency.
- **`linux-lowlatency`**: Optimized for audio/video production, live streaming, industrial data acquisition, and latency-sensitive interactive tasks, featuring a higher timer frequency (1000 Hz) and full preemption.
- **`HWE` (Hardware Enablement)**: A hardware enablement stack that backports newer kernels and graphics stacks from interim Ubuntu releases to Long-Term Support (LTS) versions, supporting modern CPUs, GPUs, and network hardware.

```text
                               ┌──────────────────────────────────────────────┐
                               │             Ubuntu Linux Kernels             │
                               └──────────────────────┬───────────────────────┘
                                                      │
                     ┌────────────────────────────────┼───────────────────────────────┐
                     ▼                                ▼                               ▼
         ┌───────────────────────┐        ┌───────────────────────┐       ┌───────────────────────┐
         │     linux-generic     │        │    linux-lowlatency   │       │       HWE Stack       │
         ├───────────────────────┤        ├───────────────────────┤       ├───────────────────────┤
         │ • HZ=250              │        │ • HZ=1000             │       │ • Interim release pkg │
         │ • Voluntary Preempt   │        │ • Full Preempt        │       │ • Updated DRM / Mesa  │
         │ • Maximum Throughput  │        │ • Low Latency/Jitter  │       │ • Modern HW support   │
         │ • Server / Standard   │        │ • Pro-Audio / Streams │       │ • Default on Desktop  │
         └───────────────────────┘        └───────────────────────┘       └───────────────────────┘
```

In this guide, we explore the architectural differences, `Kconfig` flags, installation
steps, default kernel selection in GRUB, and latency benchmarking with `cyclictest`.

---

## 1. Kernel flavors and characteristics

### 1.1. `linux-generic`: Stability and maximum throughput

`linux-generic` is the default kernel installed on standard Ubuntu Desktop and Server systems.
Its design goal is to maximize **computational and I/O throughput** while minimizing context
switches and power consumption.

Key attributes:
- **Preemption Model:** Classically compiled with `CONFIG_PREEMPT_VOLUNTARY=y` (Voluntary Preemption). Arbitrary kernel execution cannot be interrupted; code only yields at explicitly defined checkpoints (`might_sleep()`). In Ubuntu 24.04 (Linux 6.8+), dynamic preemption (`CONFIG_PREEMPT_DYNAMIC=y`) is enabled, booting by default in `preempt=voluntary` mode.
- **Timer Frequency:** Uses `CONFIG_HZ=250` (250 timer interrupts per second, 4 ms resolution). Infrequent timer ticks reduce CPU wakeups, preserve CPU cache locality, and lower inter-core synchronization overhead on multi-core systems.
- **Idle Power Efficiency:** `CONFIG_NO_HZ_IDLE=y` (Dynticks) turns off periodic timer interrupts on idle cores, allowing modern CPUs to enter deep sleep states (C-states) to reduce heat and power consumption.
- **Typical Use Cases:** Web servers, databases (PostgreSQL, MySQL), container hosts (Kubernetes, Docker), storage nodes, and general office desktop usage.

### 1.2. `linux-lowlatency`: Low latency and soft real-time responsiveness

`linux-lowlatency` trades a small amount of raw throughput to minimize **latency** and
**timing jitter**. It ensures latency-critical processes (such as an audio server feeding
a sound card ring buffer) do not block on long-running in-kernel routines.

Key attributes:
- **Preemption Model:** Uses `CONFIG_PREEMPT=y` (Full Preemptive Kernel). Except for critical spinlock sections and hardware interrupt handlers, almost all in-kernel execution can be preempted immediately by higher-priority tasks.
- **Timer Frequency:** Uses `CONFIG_HZ=1000` (1000 timer interrupts per second, 1 ms resolution). The scheduler re-evaluates process priorities every millisecond.
- **RCU Priority Boosting:** Enables `CONFIG_RCU_BOOST=y`. When a low-priority task holds an RCU read-side lock that a high-priority task is waiting on, the kernel boosts the low-priority task's priority to prevent priority inversion.
- **Trade-offs:** Frequent timer interrupts and more context switches increase cache thrashing. Batch computing workloads (such as compiling a large C++ code base or running massive database aggregations) can run **3% to 7% slower** compared to `linux-generic`. Battery consumption on laptops is also higher.
- **Typical Use Cases:** Digital audio workstations (Ardour, Reaper, Bitwig), JACK and PipeWire pro-audio setups (buffer sizes of 64–128 frames with zero xruns), software-defined radio (SDR), live video streaming and vision mixers (OBS Studio), and competitive gaming requiring minimal input latency.

> **Important Distinction (Lowlatency vs Realtime):**
> `linux-lowlatency` is a "soft real-time" kernel. It prioritizes responsiveness and eliminates
> most jitter, but cannot provide a deterministic, mathematically guaranteed worst-case latency bound.
>
> Ubuntu Pro provides `linux-realtime`, which incorporates the official `PREEMPT_RT` patch set.
> It converts spinlocks into sleepable mutexes (`rt-mutex`) and forces interrupt handlers into
> kernel threads (`kthreads`). While `linux-realtime` is essential for industrial robotics and
> medical devices, `linux-lowlatency` is much more stable and compatible with third-party proprietary
> hardware drivers (such as NVIDIA GPUs).

### 1.3. `HWE` (Hardware Enablement): Modern hardware on LTS releases

Ubuntu LTS releases arrive every two years and receive five years of standard maintenance.
However, the initial **GA (General Availability)** kernel (e.g., Linux 5.15 on 22.04 or Linux 6.8
on 24.04) does not support processors, GPUs, or wireless chipsets released in subsequent years.

Canonical solves this through the **HWE (Hardware Enablement Stack)**:

```text
Ubuntu 22.04 LTS Lifecycle and Kernel Progression:
───────────────────────────────────────────────────────────────────────
Release      Kernel Shipped     Source Release  Description
───────────────────────────────────────────────────────────────────────
22.04 (GA)   Linux 5.15         22.04 LTS       Remains supported for 5 years
22.04.2 HWE  Linux 5.19         22.10           Interim kernel backport
22.04.3 HWE  Linux 6.2          23.04           Interim kernel backport
22.04.4 HWE  Linux 6.5          23.10           Interim kernel backport
22.04.5 HWE  Linux 6.8          24.04 LTS       Supported until 22.04 EOL
───────────────────────────────────────────────────────────────────────
```

HWE characteristics:
- **Userspace Isolation:** HWE only updates the kernel, kernel modules, and the Xorg/Mesa graphics stack. Core userspace libraries (`glibc`, `systemd`, `OpenSSL`) remain untouched, preserving application compatibility.
- **Default Behavior:** Ubuntu Desktop LTS installs ship with HWE **enabled by default**. Ubuntu Server LTS defaults to the **GA kernel** for strict stability and long-term ABI consistency, though administrators can switch to HWE with a single command.
- **Variants:** HWE packages exist for both generic and lowlatency flavors (`linux-generic-hwe-XX.YY` and `linux-lowlatency-hwe-XX.YY`).

---

## 2. Kernel configuration flags and comparison

Linux kernel build configurations are stored in `/boot/config-$(uname -r)`.
The differences between flavors stem directly from these compile-time flags:

```text
Feature                       linux-generic             linux-lowlatency          linux-realtime (RT)
──────────────────────────────────────────────────────────────────────────────────────────────────────────
Preemption Model              VOLUNTARY (Dynamic)       FULL PREEMPT              PREEMPT_RT
Configuration Flag            CONFIG_PREEMPT_VOLUNTARY  CONFIG_PREEMPT            CONFIG_PREEMPT_RT
Timer Frequency (CONFIG_HZ)   250 Hz (4 ms)             1000 Hz (1 ms)            1000 Hz (1 ms)
Dynticks (Tickless)           CONFIG_NO_HZ_IDLE         CONFIG_NO_HZ_IDLE         CONFIG_NO_HZ_FULL
RCU Priority Boosting         No                        CONFIG_RCU_BOOST=y        CONFIG_RCU_BOOST=y
Latency Jitter                Moderate (1–15 ms)        Low (50–300 µs)           Ultra-low (<20 µs)
Throughput                    Maximum (Baseline)        3–7% Lower                8–15% Lower
Power / Battery Consumption   Minimum (Efficient)       Higher                    Higher
DKMS / Driver Compatibility   Flawless                  Very High                 Limited (RT Patches)
LTS Support Model             5-Year Fixed or HWE       5-Year Fixed or HWE       Ubuntu Pro Subscription
──────────────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## 3. Installation and package management

When managing kernels in Ubuntu, always rely on **meta-packages**.

Installing a concrete kernel package directly (e.g. `linux-image-6.8.0-45-generic`) will leave
your system without future security updates when a point release arrives. Meta-packages ensure
ongoing automated updates:

| Requirement | Meta-Package | Included Components |
| :--- | :--- | :--- |
| Standard GA Generic | `linux-generic` | `linux-image-generic`, `linux-headers-generic` |
| Standard GA Lowlatency | `linux-lowlatency` | `linux-image-lowlatency`, `linux-headers-lowlatency` |
| HWE Generic (for 24.04) | `linux-generic-hwe-24.04` | Latest HWE image and headers |
| HWE Lowlatency (for 24.04) | `linux-lowlatency-hwe-24.04` | Latest HWE lowlatency packages |

### 3.1. Checking your current kernel

Check the active running kernel release and architecture:

```bash
uname -rm
```

```text
6.8.0-45-generic x86_64
```

List installed kernel packages on your system:

```bash
dpkg -l | grep -E 'linux-(image|headers)-[0-9]' | awk '{print $2, $3}'
```

```text
linux-headers-6.8.0-45-generic 6.8.0-45.45
linux-image-6.8.0-45-generic 6.8.0-45.45
```

### 3.2. Installing the lowlatency kernel

Install the lowlatency kernel along with its development headers (required to compile DKMS modules):

```bash
sudo apt update
sudo apt install linux-lowlatency linux-headers-lowlatency
```

If you are running an LTS system with HWE and want the latest lowlatency HWE kernel:

```bash
sudo apt update
sudo apt install --install-recommends linux-lowlatency-hwe-$(lsb_release -rs)
```

Upon package installation, APT automatically invokes `update-initramfs` and `update-grub`
to register the new kernel in the boot menu.

### 3.3. Installing the HWE kernel on Ubuntu Server

To upgrade an Ubuntu Server LTS running the GA kernel to the newer HWE stack for updated
storage controllers, NICs, or processors:

```bash
sudo apt update
sudo apt install --install-recommends linux-generic-hwe-$(lsb_release -rs)
```

If the system also runs graphical applications, install the full graphical HWE stack:

```bash
sudo apt install --install-recommends xserver-xorg-hwe-$(lsb_release -rs)
```

---

## 4. GRUB configuration and default kernel selection

When multiple kernels are installed, GRUB defaults to the highest version number.
When both generic and lowlatency exist with identical version numbers, the bootloader
follows distribution priority rules.

To explicitly and reliably select your preferred kernel, configure `/etc/default/grub`.

### 4.1. Inspecting GRUB menu entries

Extract the list of kernel menu titles from the GRUB configuration:

```bash
grep -E "menuentry 'Ubuntu" /boot/grub/grub.cfg | cut -d"'" -f2
```

```text
Ubuntu
Ubuntu, with Linux 6.8.0-45-lowlatency
Ubuntu, with Linux 6.8.0-45-lowlatency (recovery mode)
Ubuntu, with Linux 6.8.0-45-generic
Ubuntu, with Linux 6.8.0-45-generic (recovery mode)
```

In standard GRUB layouts, specific kernels reside under the `Advanced options for Ubuntu` submenu.

### 4.2. Recommended method: Using `GRUB_DEFAULT=saved`

The most resilient method is to allow saving and explicitly setting the default kernel via tools.

Edit `/etc/default/grub`:

```bash
sudo nano /etc/default/grub
```

Set the following parameters:

```bash
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=true
```
{: data-filename="/etc/default/grub"}

Regenerate the GRUB configuration:

```bash
sudo update-grub
```

Now select your target kernel permanently:

```bash
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency"
```

Verify the active saved entry:

```bash
sudo grub-editenv list
```

```text
saved_entry=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-lowlatency
```

Reboot the machine:

```bash
sudo reboot
```

> **Safe Switching on Headless / Remote Servers:**
> If you administer a remote server over SSH without physical display access, switching the permanent default immediately is dangerous (a kernel panic locks you out). Instead, use `grub-reboot` to test the new kernel on the next boot alongside `panic=10` and `GRUB_RECORDFAIL_TIMEOUT` safeguards. See the [Headless kernel switching](headless-kernel-degisimi.md) guide for full instructions.

---

## 5. Verification and latency testing

After rebooting, verify that the expected kernel is active and evaluate its performance.

### 5.1. Inspecting active kernel flags

Verify the running kernel release string:

```bash
uname -r
```

```text
6.8.0-45-lowlatency
```

Read scheduler and timer flags from the active kernel's configuration file:

```bash
grep -E 'CONFIG_PREEMPT(_VOLUNTARY|_DYNAMIC|_NONE)?=|CONFIG_HZ=' /boot/config-$(uname -r)
```

Expected output on `lowlatency`:

```text
CONFIG_PREEMPT_BUILD=y
CONFIG_PREEMPT=y
CONFIG_HZ_1000=y
CONFIG_HZ=1000
```

Expected output on `generic`:

```text
CONFIG_PREEMPT_VOLUNTARY_BUILD=y
CONFIG_PREEMPT_VOLUNTARY=y
CONFIG_HZ_250=y
CONFIG_HZ=250
```

### 5.2. Latency benchmarking with `cyclictest`

The `cyclictest` utility from the `rt-tests` suite measures the difference between when a thread
is scheduled to wake up and when it actually executes (latency/jitter).

Install the benchmark tool:

```bash
sudo apt install rt-tests
```

Run a 100,000-cycle test across all CPU cores with real-time priority (`-p 90`) and memory locking (`-m`):

```bash
sudo cyclictest --smp -p 90 -m -i 1000 -d 0 -l 100000
```

Representative output on `generic` under desktop activity (higher jitter and latency spikes):

```text
# /dev/cpu_dma_latency set to 0us
policy: fifo: loadavg: 0.42 0.35 0.28 1/412 18920          

T: 0 (18912) P:90 I:1000 C: 100000 Min:      4 Act:    7 Avg:   14 Max:    1284
T: 1 (18913) P:90 I:1000 C: 100000 Min:      4 Act:    6 Avg:   15 Max:    1842
```

Representative output on `lowlatency` (predictable upper bound):

```text
# /dev/cpu_dma_latency set to 0us
policy: fifo: loadavg: 0.51 0.40 0.30 1/410 19415          

T: 0 (19401) P:90 I:1000 C: 100000 Min:      2 Act:    3 Avg:    6 Max:     112
T: 1 (19402) P:90 I:1000 C: 100000 Min:      2 Act:    4 Avg:    7 Max:     125
```

Notice the `Max` metric: generic kernels occasionally experience latency spikes up to
**1.5–2 ms (1500–2000 µs)** during I/O bursts, whereas the lowlatency kernel stays tightly
bounded around **100–150 µs**. This predictability prevents buffer underruns (xruns) in
pro-audio recording.

---

## 6. DKMS modules, maintenance, and rollback

### 6.1. Third-party drivers (NVIDIA, ZFS, VirtualBox) and DKMS

Proprietary drivers and out-of-tree file systems rely on DKMS (Dynamic Kernel Module Support)
to build modules whenever a new kernel is installed.

Verify that all DKMS modules compiled cleanly for the new kernel:

```bash
dkms status
```

```text
nvidia/550.120, 6.8.0-45-generic, x86_64: installed
nvidia/550.120, 6.8.0-45-lowlatency, x86_64: installed
```

If a module status shows `broken` or missing, verify that `linux-headers-lowlatency` is
installed and trigger a rebuild:

```bash
sudo dkms autoinstall -k $(uname -r)
```

### 6.2. Safely pruning old kernels

Accumulating multiple kernel versions consumes disk space and can cause `/boot` partition
exhaustion.

Use APT to prune unused kernels while automatically protecting the running kernel:

```bash
sudo apt autoremove --purge
```

> **Warning:** Check `uname -r` before purging. Never manually force-remove active kernel
> packages using raw `dpkg --purge` operations.

### 6.3. Recovery and rollback steps

If a newly installed kernel fails to boot or triggers a kernel panic:

1. Reboot the system.
2. Hold **Shift** (BIOS) or **Esc** (UEFI) during boot to reveal the GRUB menu.
3. Navigate to **Advanced options for Ubuntu**.
4. Choose the previously working kernel (e.g. generic) to boot.
5. Once in the desktop or shell, reset GRUB's default entry back to the stable kernel:

```bash
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-45-generic"
sudo update-grub
```

---

## 7. Decision summary

- **Standard Servers (Web, Database, Docker, Kubernetes):** `linux-generic` (LTS GA). Five years of stable ABI and maximum computational throughput.
- **Modern Hardware Servers or Workstations:** `linux-generic-hwe-XX.YY`. Support for newer CPU architectures, NVMe controllers, and high-speed NICs.
- **Audio & Music Production (DAW, PipeWire, JACK):** `linux-lowlatency` or `linux-lowlatency-hwe-XX.YY`. Zero xruns, minimal buffer latency.
- **Gaming & Live Streaming (OBS, VR, Low Input Lag):** `linux-lowlatency-hwe-XX.YY`.
- **Industrial Automation / Robotics / Safety-Critical Systems:** `linux-realtime` (Ubuntu Pro PREEMPT_RT).

---

## Verification and references

### Test environment
The configuration parameters, `CONFIG_*` build flags, and APT meta-package behaviors in this guide
were verified on Ubuntu 22.04 LTS (Jammy) and Ubuntu 24.04 LTS (Noble) x86_64 environments across
Linux 5.15, 6.8, and lowlatency kernel builds.

### References
- [Ubuntu Kernel Team Wiki](https://wiki.ubuntu.com/Kernel): Kernel lifecycle, HWE cadence, and packaging guidelines.
- [Kernel.org Documentation - Preemption Models](https://docs.kernel.org/): `CONFIG_PREEMPT`, voluntary, and dynamic preemption mechanics.
- [Real-Time Linux Collaborative Project](https://wiki.linuxfoundation.org/realtime/): Cyclictest benchmark guidelines and deterministic latency analysis.
