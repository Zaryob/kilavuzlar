---
sort: 6
---

# Debian için depo oluşturma

Bu dokümanda **debian** için depo oluşturma ve depoyu güncelleme konusu
anlatılmıştır.

Gerekli paketlerin kurulması
----------------------------

Aşağıdaki komut ile index almamız için gereken paketi kurabilirsiniz:

``` {.sourceCode .shell}
$ apt-get instal apt-ftparchive
```

Depoyu ağda paylaşmak için web server gerekmektedir.

> **Nginx** veya **Apache** kurmalısınız.

Nginx kurmak için:

``` {.sourceCode .shell}
$ apt install nginx
```

Apache kurmak için:

``` {.sourceCode .shell}
$ apt install apache2
```

Depo ile ilgili temel kavramlar
-------------------------------

Deponun 2 temel dizini bulunmaktadır: **pool** ve **dists**

Deponun bilgilerini **Release** dosyası içinde bulunur.

Deponun temel dizin yapısı şu şekilde özetlenebilir:

``` {.sourceCode .shell}
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

Depoya **pool** ve **dists** dizinleri içinde olmamak şartı ile
istediğiniz dosyaları yerleştirebilirsiniz. (örneğin: index.html)

### Dists

*dists* içerisinde depo indexi depo imzası ve hangi ortama uyumlu
çalıştığına dair bilgiler bulnur.

**dists** dizini içerisinde dağıtım adına göre dizinler bulunur. ve bu
dizinler içerisinde de kısımlara dair dizinler ve **Release** dosyası
bulunur.

Örnek depo **dists** dizin yapısı (imzalanmamış depo):

``` {.sourceCode .shell}
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

*pool* içerisinde de pakekler uygun hiyerarşiye göre dizilmiştir.

**pool** dizininde bulunan paketler genel bir kural olmaması ile
birlikte şu kurallara uygun şekilde dizilmeleri tavsiye edilmektedir:

Alfabetik kural:

1.  Paket isminin ilk harfi ile başlayar dizin içerisinde paket adını
    taşıyan bir dizin olmalı ve paket bu dizinde yer almalı.

    test adındaki bir paket için **pool/t/test/test\_1.0\_amd64.deb**

2.  Paket adının başında lib varsa ve kütüphane dosyası ise ilk harf
    yerine lib kısmından sonraki ilk harf ile beraber alınmalı.

    libncurses paketi için
    **pool/libn/libncurses/libncurses\_6.2-1\_amd64.deb**

Bölümsel kural:

1.  Bölümler belirlenmeli.

    *system*, *util*, *network*, *optional*, *appications* gibi.

2.  Alt bölümler oluşturulabilir.

    bash paketi için **pool/system/shell/bash/bash\_5.0\_amd64.deb**

Küçük depolar için tüm paketleri tek bir dizine yığabilirsiniz.

Alfabetik kurala göre dizilmiş örnek **pool** dizini:

``` {.sourceCode .shell}
pool/
|-- contrib
|-- main
|   `-- f
|       `-- foo
|           `-- foo_1.0_all.deb
`-- non-free

5 directories, 1 file
```

Paketler **paket\_version\_mimari.deb** şeklinde isimlendirilmelidir.

amd64 mimaride ve 1.0 sürümünde olan test adındaki bir paket için
**test\_1.0\_amd64.deb**

### Release

**Release** dosyasında depoya dair bilgiler yer almaktadır. Bu
bilgilerden sonra da dists içerisindeki indexlerin hash değerleri yer
alır. Örneğin:

``` {.sourceCode .shell}
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

İndex alınması
--------------

**pool** dizini içerisine yukarıda anlatılan hiyerarşilere uygun şekilde
paketlerimizi yerleştirmeliyiz. pool içerisinde **main**, **contrib**,
**non-free** adında dizinler olmalıdır. Bu isimler ile **dists** dizini
içerisindeki isimler aynı olmalıdır.

pool içerisindeki paket yerleştirme işlemi bittikten sonra şu komutu
kullanarak index almalıyız:

``` {.sourceCode .shell}
$ apt-ftparchive -a amd64 packages pool/main > dists/stable/main/binary-amd64/Packages
$ gzip -k dists/stable/main/binary-amd64/Packages
$ xz -k dists/stable/main/binary-amd64/Packages
```

İlk komut ile pool/main içerisindeki paketlerin indexlerini dists
içerisindeki main bölümüne yerleştiriyoruz. Bu işlem contrib ve non-free
için benzer şekilde yapılmalıdır. ayrıca eğer i386 veya arm64 veya armhf
için de paketler varsa onlar için de tekrarlamanız gerekmektedir.

İkinci ve üçüncü komut ise aldığımız indexi gzip formatta
sıkıştırmaktadır. Depolarda daha az ağ trafiği yaparak index indirmek
için gzip, bz2 veya xz formatında sıkıtşıtma yapılabilir.

### Release dosyasının yazılması

Release dosyasını elle yazmak hem uğraştırıcıdır. Başlık kısmındaki
değerler değişmeyeceği için onları ayrı bir dosyaya yazıp md5sum
değerlerini de komut kullanarak üstüne ekleyebilirsiniz. *sed* komutu
ile de biçimlendirseniz güzel olur :D

Başlık dosyamızdaki tarihi sonradan güncelleyebilmek için tarih yerine
XdateX yazdık. Başlık dosyası içeriği şu şekilde olamalı:

``` {.sourceCode .YAML}
$ cat baslik
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

Release dosyamızı oluşturmadan önce yardımcı fonksionumuzu tanımlamamız
gerekmektedir. Bashrc içerisine aşağıdaki fonksionu tanımlayalım. (veya
betik yazıyorsanız betik içine) Bu fonksion Release dosyasındaki hash
değerlerinin formatına uygun çıktı üzetebilmemizi sağlar.

``` {.sourceCode .shell}
prepareLine(){
   while read line ; do
       fname=$(echo $line | sed "s/.* //g")
       fhash=$(echo $line | sed "s/ .*//g")
       echo -e "  $fhash\t$(du -bs $fname| sed 's|\./||g')"
   done
```

> }

Başlık ile md5sum birleştirmek için aşağıdakine benzer bir komut dizisi
kullanabilirsiniz:

``` {.sourceCode .shell}
$ cat baslik | sed "s/XdateX/$(date -R)/g" > dists/stable/Release
$ cd dists/stable/
    $ echo "MD5Sum:" >>  Release
$ find . -type f | xargs md5sum | prepareLine >> Release
$ echo "SHA1:" >>  Release
$ find . -type f | xargs sha1sum | prepareLine >> Release
$ echo "SHA256:" >>  Release
$ find . -type f | xargs sha256sum | prepareLine >> Release
$ echo "SHA512:" >>  Release
$ find . -type f | xargs sha512sum | prepareLine  >> Release
```

### Deponun imzalanması

Depoyu eğer imzalamazsak depoyu güncellerken ve depodan paket kurarken
uyarı verirler. Eğer gpg anahtarınız mevcutsa şu komutu
kullanabilirsiniz:

``` {.sourceCode .shell}
$ gpg --clearsign -o InRelease Release
$ gpg -abs -o Release.gpg Release
```

Eğer gpg anahtarınız yoksa oluşturmak için:

``` {.sourceCode .shell}
$ gpg --gen-key
```

Oluşturduğumuz gpg anahtarını listelemek için:

``` {.sourceCode .shell}
$ gpg --list-keys
```

Bu listede gpg anahtarını id değerleri bulunur. Bu değeri kullanarak gpg
anahtarımızı dışarı aktarabiliriz. Aktarılan bu anahtar depoyu kullanmak
isteyen kullanıcılar tarafından anahtar deposuna eklenmelidir.

Elimizdeki gpg anahtarını dışarı aktarmak için:

``` {.sourceCode .shell}
$ gpg --output Release.key --armor --export gpg_id_değeri
```

Deponun ağda paylaşılması
-------------------------

**Apache** veya **nginx** tavsiye etmekle birlikte **busybox httpd** ve
**python3 http.server** kullanılabilir.

Eğer sunucunuz yoksa bir hostingde yada github.io gibi static site
üzerinde de barındırabilirsiniz. (Eğer kullanım şartlarına ihlal durum
oluşturmuyorsa.)

Eğer http(s) yerine ftp kullanmak istiyorsanız **vsftpd** veya **busybox
ftpd** kullanabilirsiniz.

### Deponun kullanıcılar tarafından sisteme eklenmesi

Depomuz tamamlandı ve internet ağının bir parçası haline geldikten sonra
kullanıcılar bu depoyu kullanmak istediklerinde şu adımları
uygulamalılar.

1.  Depoyu imzalayan gpg anahtarını içeri aktarmalılar.

``` {.sourceCode .shell}
$ wget -O - http://depo_sunucusu/depo_konumu/dists/stable/Release.key | apt-key add -
```

2.  /etc/sources.list.d/ dizinine dosya içerisine eklemeliler. (veya
    sources.list dosyasına)

``` {.sourceCode .shell}
$ echo "deb http://depo_sunucusu/depo_konumu stable main contrib non-free" > /etc/apt/sources.list.d/testrepo.list
```

3.  Depoyu güncellemeliler.

``` {.sourceCode .shell}
$ apt-get update
```
