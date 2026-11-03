---
title: Creating a Debian repository
permalink: /en/arsiv/linux/paket-yonetimi/debian-deposu-olusturma/
status: arsiv
reviewed: 2026-11-02
scope: A Debian 10.5 example using apt-ftparchive and apt-key.
archive_reason: Rework the package-install command, Release-file self-hashing and
  key distribution. Prepare a repeatable example using signed-by.
lang: en
translation_key: guide-arsiv-linux-paket-yonetimi-debian-deposu-olusturma
translation_of: /arsiv/linux/paket-yonetimi/debian-deposu-olusturma/
translated: '2026-11-03'
---

# Creating a Debian repository

This document describes creating and updating a **Debian** package repository.

## Install the required packages

The original command for installing the indexing tool is retained below; its typo is identified in the archive warning:

```bash
apt-get instal apt-ftparchive
```

A web server is required to share the repository over the network.

> Install **Nginx** or **Apache**.

For Nginx:

```bash
apt install nginx
```

For Apache:

```bash
apt install apache2
```

## Repository concepts

A repository has two main directories: **pool** and **dists**. The **Release** file contains repository metadata.

Basic directory structure:

```bash
repository/
|-- dists
|   `-- stable
|       |-- Release
|       |-- contrib
|       |-- main
|       `-- non-free
`-- pool
    |-- contrib
    |-- main
    `-- non-free
```

You may place other files, such as index.html, outside **pool** and **dists**.

### Dists

*dists* contains package indexes, signatures and information about supported environments. It has a directory for each distribution, containing component subdirectories and **Release**.

Example **dists** structure for an unsigned repository:

```bash
dists/
`-- stable
    |-- Release
    |-- contrib
    |   |-- binary-amd64
    |   |   |-- Packages
    |   |   `-- Packages.gz
    |   `-- binary-i386
    |       |-- Packages
    |       `-- Packages.gz
    |-- main
    |   |-- binary-amd64
    |   |   |-- Packages
    |   |   `-- Packages.gz
    |   `-- binary-i386
    |       |-- Packages
    |       `-- Packages.gz
    `-- non-free
        |-- binary-amd64
        |   |-- Packages
        |   `-- Packages.gz
        `-- binary-i386
            |-- Packages
            `-- Packages.gz

10 directories, 13 files
```

### Pool

*pool* stores packages in a hierarchy. Although no single layout is mandatory, these conventions are useful.

Alphabetical layout:

1. Create a directory based on the package’s first letter, then a package-named directory. For a package called test: **pool/t/test/test\_1.0\_amd64.deb**.
2. For library names beginning with lib, use lib plus the next letter. For libncurses: **pool/libn/libncurses/libncurses\_6.2-1\_amd64.deb**.

Category layout:

1. Define categories such as *system*, *util*, *network*, *optional* and *appications*.
2. Add subcategories if needed, for example **pool/system/shell/bash/bash\_5.0\_amd64.deb**.

A small repository can keep all packages in one directory.

Example alphabetically arranged **pool**:

```bash
pool/
|-- contrib
|-- main
|   `-- f
|       `-- foo
|           `-- foo_1.0_all.deb
`-- non-free

5 directories, 1 file
```

Package filenames follow **package\_version\_architecture.deb**. A package named test, version 1.0 for amd64, is **test\_1.0\_amd64.deb**.

### Release

**Release** contains repository metadata followed by hashes of the indexes under dists:

```bash
Origin: Debian
Label: Debian
Suite: stable
Version: 10.5
Codename: stable
Changelogs: https://sulincix.github.io
Date: Sat, 01 Aug 2020 11:04:59 UTC
Acquire-By-Hash: yes
Architectures: amd64 i386
Components: main contrib non-free
Description: Test repository
MD5Sum:
  09055bc807e6edb1d39b9478c3e979e6  2472    Release.key
  a4acada35cf263239778004cc3a3052c  659 Release.gpg
  6b41b0a0be8cc937b40b431f74f2321f  4427    InRelease
  b15aade8df5dac635bb851713d5b30c0  396 Release
  8fcbf476f836a406733f7468d9be00fa  2280    main/binary-amd64/Packages
  17393ff93c41644879ba128ffb0b22d3  1348    main/binary-amd64/Packages.xz
  bb3d363cfd9263fce932c1cc12c18e68  1286    main/binary-amd64/Packages.gz
  089b664e3c4e3222cefff76098e9b8a7  1156    main/binary-i386/Packages
  aad80a1b6699ca9f538107937506ef70  820 main/binary-i386/Packages.xz
  af2c952ea91ad4d89f6259f2a3ac397d  747 main/binary-i386/Packages.gz
SHA1:
  bf969834bcf3fe37435317fec8ae6375f5cbfcab  2472    Release.key
  be23df080f41ca983de08838452a6e2c77a31836  659 Release.gpg
  e5a3ee28bae50959ee62a73270b9162f59884437  4427    InRelease
  e7247091579e00f62a96a6b6d6957b1a2715732b  1035    Release
  0276cc6bd45abaed900a2dfdafe7b01dde21b89b  2280    main/binary-amd64/Packages
  f9ff41da670bf4836367cd170dfc5086bb80cb69  1348    main/binary-amd64/Packages.xz
  4ce6b6deaa2722bb9256e89dc8bbb28bb653847b  1286    main/binary-amd64/Packages.gz
  dab4a82db5aaa3e50fb2e9d4584fadd0d79c9ac8  1156    main/binary-i386/Packages
  751dd84b265115e52ab482c9249b5d7205fa3e1b  820 main/binary-i386/Packages.xz
  9620d2eda8c4fc29f4130b0bbf603a0a35df8563  747 main/binary-i386/Packages.gz
SHA256:
  8ec32aa00483111e9552c03262a1704d6e44e42f4451265b66b2a0fe920a69f8  2472    Release.key
  60af76151b979d0c0eb0ae859e33cc1f6f1be0c09cb201a81e303d536df796cf  659 Release.gpg
  f7f32eba3c9fa2fe69832bbb12c0fb446c723f6fbe64ae992260702310981d68  4427    InRelease
  254fefc722399f2316a3bf5d245939e99506e0589220f0d1549b7aa97c40089b  1805    Release
  52f805226b147e0e68c5b659f0efd42a4ab27033b6a13e6aac9b6a04ba808891  2280    main/binary-amd64/Packages
  55f622e5bb9e2fe7f9eae38488a3b7034b48e61774915ac88ed1b871c4f752a3  1348    main/binary-amd64/Packages.xz
  1576654604e7a85dc84862e234a23d89af7d020d048491b31baed92f6a066f58  1286    main/binary-amd64/Packages.gz
  afb0bf00963b462ce942381563c14e02e124c7767df08f62117d3f42be02f083  1156    main/binary-i386/Packages
  b4a0d98a479cd9812ff79f15d9ee41edc13967c87f6800ed257f9fdc2f0eacb0  820 main/binary-i386/Packages.xz
  b2bca5e3c273f4b5a9df7bc8206a411c23dbdf5db329e4e969bcb38274b16feb  747 main/binary-i386/Packages.gz
SHA512:
  b3c7b2ca8c88639558b8f9d880e559d4ae6cca7f66f61d6db6f29c48b2e3bfbb0cc39f3ef9feccb4dfad616410c38a60f774e52df2ee0ee8f4ecf1420e662ef3  2472    Release.key
  a679b02b193493c00a679d18e830447f60169a5689e3ae9678ee65ac925fdc4de44a3e1099da34889dca5ef01fa29befb3f493881a88e08bb1d21432d125c93f  659 Release.gpg
  290ef238a374930f2cf08572e1a2cc024ef7184a00bd8c85f63ceb876952b008edfb5fea0dcafc2247b31cef72914609e1d51a943378571599c801ed24db56a2  4427    InRelease
  16686a082d2b4f183ff5ddaa87328c7b0ba6788fa9e0f85cc66d70c8f9862e22acf235957acd36bb7ea3f77579ced07d54ae553c33d179c3b9f3913276575ee8  2935    Release
  591da357d487637d1b6b40286aaef08c599ee8f4f9894bdc1763e1102c68c37a3f57516cdb2d1267c71103adc0ec13e2ecf39c3014a10e9f905caa4c3f29af55  2280    main/binary-amd64/Packages
  f6bff31b379fd4aa99b960b15275f5db113c049587761d1f10dc8de33be831f360b1f4dd00223f206b57cbbec008e1aebf2b2c4fdb8a3b5aefbfa4f1c3810d33  1348    main/binary-amd64/Packages.xz
  69bc3bee91d222eeff12e479a44aeb7d22fc8aa71c597aeb3c4f9a42b6c737fcfb4422084dd6e1387540bc0b56e9cacfeb7818e1d09063624dba54170ffa5fab  1286    main/binary-amd64/Packages.gz
  d54bcb50ab9409e3480dc002c520d240a02804ba648b9a581d524e1ae161f33a8d31e2bd4e0528db07c34ef2b0e4c53b7286ebc38fb319ff47be18be9db67db0  1156    main/binary-i386/Packages
  ff4ee4f90b1ecd861d1adedaa6f0d77684c188add447e81f5131ce8e77ede3f4c99762c6e22c7804f11694b57d160ab46f44075a3ff8305fe285bc43f68700d0  820 main/binary-i386/Packages.xz
  07524f649a0ffc66192af4925b750d22ce3fc446eb0d890b473713615fde4b2174214e94bdcdac97b5281e2386c5efaf7a8aa139a03f69c10b6d181e99d81c8a  747 main/binary-i386/Packages.gz
```

## Generate indexes

Place packages in **pool** using the chosen layout. The example uses **main**, **contrib** and **non-free**, matching the component names under **dists**.

After placing the packages, generate indexes:

```bash
apt-ftparchive -a amd64 packages pool/main > dists/stable/main/binary-amd64/Packages
gzip -k dists/stable/main/binary-amd64/Packages
xz -k dists/stable/main/binary-amd64/Packages
```

The first command indexes pool/main into the main component under dists. Repeat for contrib and non-free, and for any additional architectures such as i386, arm64 or armhf.

The remaining commands compress the index with gzip. Repositories can also use bz2 or xz to reduce download traffic.

### Write the Release file

Rather than writing Release manually each time, keep its fixed header in a separate file and append hash output. The original example also uses *sed* for formatting.

The header uses XdateX as a placeholder for a date updated later:

```bash
cat baslik
    Origin: Debian
    Label: Debian
    Suite: stable
    Version: 10.5
    Codename: stable
    Changelogs: https://sulincix.github.io
    Date: XdateX
    Acquire-By-Hash: yes
    Architectures: amd64 i386
    Components: main contrib non-free
    Description: Test repository
```

Define the helper function in Bashrc, or in a script. It formats hash output for Release:

```bash
prepareLine(){
   while read line ; do
       fname=$(echo $line | sed "s/.* //g")
       fhash=$(echo $line | sed "s/ .*//g")
       echo -e "  $fhash\t$(du -bs $fname| sed 's|\./||g')"
   done
}
```

Combine the header and hashes with a command sequence such as:

```bash
cat baslik | sed "s/XdateX/$(date -R)/g" > dists/stable/Release
cd dists/stable/
echo "MD5Sum:" >>  Release
find . -type f | xargs md5sum | prepareLine >> Release
echo "SHA1:" >>  Release
find . -type f | xargs sha1sum | prepareLine >> Release
echo "SHA256:" >>  Release
find . -type f | xargs sha256sum | prepareLine >> Release
echo "SHA512:" >>  Release
find . -type f | xargs sha512sum | prepareLine  >> Release
```

### Sign the repository

Without a repository signature, clients warn during updates and installation. If you already have a GPG key:

```bash
gpg --clearsign -o InRelease Release
gpg -abs -o Release.gpg Release
```

To create a key:

```bash
gpg --gen-key
```

List the keys:

```bash
gpg --list-keys
```

The list contains key IDs. Use the relevant ID to export the public key for users of the repository:

```bash
gpg --output Release.key --armor --export gpg_id_değeri
```

## Share the repository

**Apache** or **Nginx** are suggested; **busybox httpd** and **python3 http.server** are alternatives.

You can also use hosting or a static service such as github.io, provided that its terms permit this use. For FTP instead of HTTP(S), the original notes suggest **vsftpd** or **busybox ftpd**.

### Add the repository on a client

Once the repository is available online, the original client procedure is:

1. Import the GPG key used to sign the repository:

```bash
wget -O - http://depo_sunucusu/depo_konumu/dists/stable/Release.key | apt-key add -
```

2. Add the source definition to a file under /etc/sources.list.d/, or to sources.list, as shown in the historical example:

```bash
echo "deb http://depo_sunucusu/depo_konumu stable main contrib non-free" > /etc/apt/sources.list.d/testrepo.list
```

3. Update repository metadata:

```bash
apt-get update
```
