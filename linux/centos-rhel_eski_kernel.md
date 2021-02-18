---
sort: 4
---

# CentOS ve RHEL'de Eski Kernel'leri Kaldırma

Bu,  eski çekirdeklerin nasıl silineceği/kaldırılacağı/temizleneceği anlatan hızlı bir kılavuzdur. Burada örnek olarak iki çekirdek kullanıyorum, diğerini daha fazla veya daha az tutmak istiyorsanız, kurulu çekirdek miktarını istediğiniz gibi ayarlayın. Normalde çekirdekleri kaldırmak istemenizin nedeni sınırlı disk alanıdır, örneğin VPS sunucularında ve dizüstü bilgisayarda. Bu çok kolay işlemdir.

## Yüklü Çekirdeklerin Listlenmesi

RHEL'de kurulu çekirdeklerin listesini alalım.
```bash
$ rpm -qa kernel\* |sort -V
kernel-4.18.0-240.10.1.el8_3.x86_64
kernel-4.18.9-200.el8_3.x86_64
kernel-4.18.10-200.el8_3.x86_64
kernel-core-4.18.0-240.10.1.el8_3.x86_64
kernel-core-4.18.9-200.el8_3.x86_64
kernel-core-4.18.10-200.el8_3.x86_64
kernel-devel-4.18.0-240.10.1.el8_3.x86_64
kernel-devel-4.18.9-200.el8_3.x86_64
kernel-devel-4.18.10-200.el8_3.x86_64
kernel-headers-4.18.0-240.10.1.el8_3.x86_64
kernel-modules-4.18.0-240.10.1.el8_3.x86_64
kernel-modules-4.18.9-200.el8_3.x86_64
kernel-modules-4.18.10-200.el8_3.x86_64
kernel-modules-extra-4.18.9-200.el8_3.x86_64
kernel-modules-extra-4.18.10-200.el8_3.x86_64
kernel-tools-4.18.0-240.10.1.el8_3.x86_64
kernel-tools-libs-4.18.0-240.10.1.el8_3.x86_64
```

## Yüklü Çekirdeklerin Silinmesi

### Fedora 28, RHEL/CENTOS 8 sonrası için

```bash
$ dnf remove $(dnf repoquery --installonly --latest-limit=-2 -q)
```

### Fedora 27 ve öncesi, RHEL/CENTOS 6-7 ve öncesi için

``` bash
$ yum install yum-utils
$ package-cleanup --oldkernels --count=2
```

## Çekirdek Sayısını Limitleme

`/etc/yum.conf` veya `/etc/dnf/dnf.conf` için *installonly_limit* ayarlayalım:

```bash
echo "installonly_limit=2" >> /etc/yum.conf
```
