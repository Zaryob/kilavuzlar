---
title: Content review and maintenance plan
permalink: /en/bakim/
lang: en
translation_key: guide-BAKIM
translation_of: /bakim/
translated: '2026-11-03'
---

# Content review and maintenance plan

Recorded review date: **2 November 2026**. Scope: the repository’s then-current 15 guides, category pages and Jekyll publishing configuration.

## Changes made

- Reorganised two Docker guides and the Vim reference. Sources were reviewed; each document states its practical test coverage.
- Retained nine Linux and three image-processing notes with scope and archive reasons. Archiving reflects uncertain environments and omissions; it does not mean every line is invalid.
- Removed empty C/C++, Python and Raspberry Pi categories and redirected their old URLs to the main index.
- Standardised filenames to lowercase ASCII and hyphens, preserving old HTML URLs through redirects.
- Converted archived Liquid code blocks to standard Markdown. Fixed a misplaced function brace in the Debian notes and unfenced commands in the model-training notes.
- Ensured each document has one main heading and explicit links to topic indexes.
- Merged duplicate `exclude` settings, changed the site URL to HTTPS and removed an unreachable remote-theme dependency. Navigation and archive notices now use local templates.

## Content issues to resolve first

1. **Remote access and web servers:** the VNC text incorrectly describes the protocol as inherently secure and confuses the SSH tunnel with the graphical client. LAMP/LEMP examples change root authentication using a sample password. LEMP omits Nginx/PHP-FPM integration and presents opening a port as HTTPS setup. Keep these documents archived until completed.
2. **Packages and kernels:** the Debian example contains `apt-get instal apt-ftparchive`, a Release-generation procedure that hashes its own output, and an outdated key-installation flow. YUM/DNF versions are not distinguished. Kernel notes confuse EPEL and ELRepo; removal instructions lack checks for the running kernel and rollback.
3. **Hardware and virtualisation:** AMD notes cover 2019–2021 and conflate Mesa, amdgpu-pro and GPU selection. The VirtualBox note is tied to version 6.1. Retest against specified hardware/distribution versions.
4. **Image processing:** OpenCV placeholders conflict with 4.0.0 paths, and ARM/general build flags are mixed. Caffe depends on Python 2/3.7 and fixed ABI paths. Referenced train/test/solver files are absent from the model-training guide.

## Duplication and retained assets

The LAMP and LEMP MySQL sections repeat the same content. Both histories are preserved; a future rewrite should extract a shared database-installation guide and link both server documents to it.

The historical diagram and Docker Desktop screenshot under `images/docker/` are unused by the rewritten instructions. They remain to preserve published image URLs; the old screenshot is not a current installation step.

## Future maintenance

Choose the target distribution and version first. Rewrite one guide by testing it end to end in a VM or container, add success checks and rollback steps, then promote only that document into the main collection.

See the [contribution guide](CONTRIBUTING.md) for content rules and checking commands.

## Verification of the recorded revision

- Built with Ruby 3.3, github-pages 232 and Jekyll 3.10.0, with strict front-matter validation.
- Checked 266 local links and 29 redirect targets across the then-generated 54 HTML pages. External links were outside this automated check.
- Inspected the main index and archive notices in a browser.
- Compared 12 archived documents with their Git originals, ignoring heading/format changes; their content was retained.
- Built and ran the static C++ example for Linux/ARM64 on Docker Engine 29.6.2, obtaining the expected output. The multi-architecture example produced an OCI archive with AMD64 and ARM64; the ARM64 run returned `aarch64`. No registry push was performed.
- Reviewed the Vim reference against sources without testing every key interactively. Archived installation commands were not executed.
