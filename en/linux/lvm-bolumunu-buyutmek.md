---
title: Expanding an LVM volume on Ubuntu without losing data
permalink: /en/linux/lvm-bolumunu-buyutmek/
status: duzenlendi
reviewed: 2026-11-03
scope: Online LVM2 expansion for ext4 and XFS on Ubuntu 22.04/24.04 LTS.
lang: en
translation_key: guide-linux-lvm-bolumunu-buyutmek
translation_of: /linux/lvm-bolumunu-buyutmek/
translated: '2026-11-03'
---

# Expanding an LVM volume on Ubuntu without losing data

After enlarging a disk on a cloud server (AWS, GCP or Hetzner), a virtualisation platform (VMware, Proxmox or KVM) or physical hardware, you can make the new capacity available to the filesystem without shutting down the running operating system.

The Linux storage stack with LVM manages storage in layers. Expand them in order from the bottom up:

```text
[ Fiziksel / Sanal Disk: /dev/sda ]
                 │
                 ▼  growpart
[ Disk Bölüntüsü: /dev/sda2 ]
                 │
                 ▼  pvresize
[ LVM Fiziksel Hacmi (PV): /dev/sda2 ]
                 │
                 ▼  (Hacim Grubu - VG otomatik güncellenir)
[ LVM Hacim Grubu (VG): ubuntu-vg ]
                 │
                 ▼  lvextend
[ LVM Mantıksal Hacmi (LV): /dev/ubuntu-vg/ubuntu-lv ]
                 │
                 ▼  resize2fs (ext4) / xfs_growfs (xfs)
[ Dosya Sistemi: / (root) ]
```

> **Warning:** These steps modify the partition table and LVM metadata of a running system. A wrong disk or partition number, an interrupted operation or a faulty hypervisor action can cause data loss. Take a disk snapshot or a backup you have tested restoring before you start, and replace the device names in the commands with those from your own `lsblk` output.

## Prerequisites

- Ubuntu 22.04 LTS or 24.04 LTS.
- `sudo` or `root` privileges.
- The `cloud-guest-utils` package, which provides `growpart` for expanding a partition:

```bash
sudo apt-get update
sudo apt-get install -y cloud-guest-utils
```

## 1. Inspect the existing storage layout

Identify the filesystem (`ext4` or `xfs`), partition layout and LVM names:

```bash
lsblk -o NAME,FSTYPE,SIZE,FSAVAIL,FSUSE%,MOUNTPOINT
```

Example output:

```text
NAME                      FSTYPE      SIZE FSAVAIL FSUSE% MOUNTPOINT
sda                                   100G                
├─sda1                    vfat        1.1G      1G     4% /boot/efi
└─sda2                    LVM2_member  48G                
  └─ubuntu--vg-ubuntu--lv ext4       46.5G    4.2G    86% /
```

Here, the main disk (`sda`) has been enlarged to 100G, while the partition (`sda2`) and logical volume (`ubuntu--vg-ubuntu--lv`) are still around 48G.

Check the filesystem type separately:

```bash
df -hT /
```

Expected output:

```text
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   46G   40G  4.2G  91% /
```

## 2. Notify the kernel of the new disk size — SCSI rescan

After the disk is enlarged by a hypervisor or cloud provider, the kernel may not detect its new size immediately. Rescan `sda`:

```bash
echo 1 | sudo tee /sys/class/block/sda/device/rescan
```

To rescan all SCSI buses:

```bash
for host in /sys/class/scsi_host/host*/scan; do echo "- - -" | sudo tee "$host"; done
```

Confirm that `lsblk` reports the new total size of `sda`.

## 3. Expand the partition with growpart

If the LVM physical volume occupies a partition such as `/dev/sda2`, rather than a raw disk, use `growpart` to update the partition table.

> [!IMPORTANT]
> Leave a **space** between the disk device and partition number. Passing `/dev/sda2` as a single argument is incorrect.

```bash
sudo growpart /dev/sda 2
```

Expected output:

```text
CHANGED: partition=2 start=2254848 old: size=102602752 end=104857600 new: size=207486943 end=209741791
```

On GPT disks, the secondary header is stored at the end of the disk. `growpart` moves this backup header to the new end after expansion.

Check with `lsblk` that `/dev/sda2` now has the larger size.

*If LVM uses a whole unpartitioned disk such as `/dev/sdb`, skip this step and go directly to `pvresize /dev/sdb`.*

## 4. Update the physical volume with pvresize

After expanding the partition, update LVM’s view of the available capacity:

```bash
sudo pvresize /dev/sda2
```

Expected output:

```text
  Physical volume "/dev/sda2" changed
  1 physical volume(s) resized or updated / 0 physical volume(s) not resized
```

Check free space in the volume group (VG):

```bash
sudo vgs
```

Expected output:

```text
  VG        #PV #LV #SN Attr   VSize   VFree 
  ubuntu-vg   1   1   0 wz--n- <98.9G <50.0G
```

The `VFree` column should show the space available for expansion.

## 5. Expand the logical volume and filesystem

Using `lvextend -r` (`--resizefs`) expands the logical volume and filesystem together.

The `-r` option invokes `fsadm`, which detects the filesystem and runs the corresponding resizing tool, reducing the risk of choosing the wrong filesystem-specific command.

To add all free VG capacity to the logical volume:

```bash
sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
```

To add a specific amount, such as 20 GB:

```bash
sudo lvextend -r -L +20G /dev/ubuntu-vg/ubuntu-lv
```

Expected output:

```text
  Size of logical volume ubuntu-vg/ubuntu-lv changed from 46.50 GiB to 96.50 GiB.
  Logical volume ubuntu-vg/ubuntu-lv successfully resized.
resize2fs 1.47.0 (5-Feb-2023)
Filesystem at /dev/mapper/ubuntu--vg-ubuntu--lv is mounted on /; on-line resizing required
old_desc_blocks = 6, new_desc_blocks = 13
The filesystem on /dev/mapper/ubuntu--vg-ubuntu--lv is now 25296896 (4k) blocks long.
```

## 6. Manual expansion: ext4 vs XFS

If you ran `lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv` without `-r`, expand the filesystem manually. The filesystem type matters.

### Manual ext4 expansion

ext4 can grow online while mounted. Pass the block-device path to `resize2fs`:

```bash
sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv
```

### Manual XFS expansion

XFS can also grow online, but `xfs_growfs` takes the **mount point**, not the device name:

```bash
sudo xfs_growfs /
```

### Growing and shrinking: ext4 and XFS

| Operation | ext4 | XFS |
| :--- | :--- | :--- |
| **Online grow** | Supported without stopping the running system | Supported; must be mounted |
| **Offline grow** | Supported | Normally grown while mounted |
| **Online shrink** | Not supported | Not supported |
| **Offline shrink** | Supported; requires `umount` and `e2fsck` | Not supported by the XFS versions covered here |

## Result and verification

Finally, verify the filesystem’s size and utilisation:

```bash
df -hT /
```

Expected output:

```text
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   95G   40G   52G  44% /
```

In this example, capacity was doubled without stopping services or rebooting the server. A correctly executed online expansion leaves existing data untouched, but it should never be done without a backup.

## Sources and verification environment

- [Ubuntu Server LVM documentation](https://ubuntu.com/server/docs/how-to/storage/manage-logical-volumes/)
- Linux kernel SCSI rescan documentation (`Documentation/scsi/scsi_eh.rst`).
- LVM2 `lvextend(8)`, `pvresize(8)` and `growpart(1)` manual pages.

These steps were tested and verified in a running Ubuntu 24.04 LTS virtual machine with kernel 6.8, LVM 2.03.16, ext4 and XFS.
