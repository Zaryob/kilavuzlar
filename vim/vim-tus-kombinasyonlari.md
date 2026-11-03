---
translation_key: guide-vim-vim-tus-kombinasyonlari
lang: tr
title: Vim tuş kombinasyonları
permalink: /vim/vim-tus-kombinasyonlari/
status: duzenlendi
reviewed: 2026-11-02
scope: Eklentisiz Vim; varsayılan tuş eşlemeleri.
redirect_from:
  - /vim/vim-tus-kombinasyonlari.html
---

# Vim tuş kombinasyonları

Aksi belirtilmedikçe komutlar normal modda kullanılır. `Esc` normal moda döner.
`Ctrl+w h`, Ctrl ile w'ye birlikte, ardından h'ye basmak anlamına gelir.
`{n}` sayı, `{harf}` ise sizin seçeceğiniz harf için yer tutucudur.

## Yazma ve seçim

- `i` / `a`: imleçten önce / sonra ekleme moduna geçer.
- `I` / `A`: ilk boşluk olmayan karakterde / satır sonunda ekleme moduna geçer.
- `o` / `O`: alta / üste yeni satır açar ve ekleme moduna geçer.
- `v` / `V` / `Ctrl+v`: karakter / satır / blok seçer.
- `Esc`: ekleme veya seçim modundan çıkar.

## Hareket

- `h`, `j`, `k`, `l`: sola, aşağı, yukarı, sağa gider.
- `{n}j` / `{n}k`: n satır aşağı / yukarı gider.
- `w` / `b` / `e`: sonraki kelimenin başına / önceki kelimenin başına / kelime sonuna gider.
- `0` / `^` / `$`: satır başına / ilk boşluk olmayan karaktere / satır sonuna gider.
- `gg` / `G`: dosya başına / sonuna gider.
- `{n}G` veya `:{n}`: n numaralı satıra gider.
- `H` / `M` / `L`: ekranın üst / orta / alt satırına gider.
- `{n}H` / `{n}L`: ekranın üstünden / altından n'inci satıra gider.
- `f{harf}` / `F{harf}`: satırda sağdaki / soldaki eşleşmeye gider.
- `%`: eşleşen paranteze gider.
- `Ctrl+e` / `Ctrl+y`: görünümü aşağı / yukarı kaydırır.
- `zt` / `zz` / `zb`: imlecin satırını ekranın üstüne / ortasına / altına alır.

## İşaretler ve geri dönüş

- `ma`: bulunduğunuz konumu `a` işareti olarak kaydeder.
- `'a`: işaretin satırındaki ilk boşluk olmayan karaktere gider.
- `` `a ``: işaretin tam konumuna gider.
- `''`: önceki atlama konumunun satırına döner.
- `` `. ``: son değişikliğin konumuna gider.
- `:marks`: işaretleri listeler.

## Silme, kopyalama ve değiştirme

- `x` / `X`: imlecin altındaki / önceki karakteri siler.
- `dw` / `de` / `db`: sonraki kelime başına / kelime sonuna / önceki kelime başına kadar siler.
- `dd` / `{n}dd`: bir / n satır siler.
- `d^` / `d$` veya `D`: ilk boşluk olmayan karaktere / satır sonuna kadar siler.
- `d'a`: işaretin satırına kadar, sınır satırları dahil siler.
- `yy` / `yw` / `ye` / `yb`: satırı / kelime başına / sonuna / önceki başına kadar kopyalar.
- `yl` / `y^` / `y$`: karakteri / satırın ilk boşluk olmayan karakterine / sonuna kadar kopyalar.
- `y'a`: işaretin satırına kadar, sınır satırları dahil kopyalar.
- `p` / `P`: kopyalanan veya silinen metni sonra / önce yapıştırır.
- `{n}p`: n kez yapıştırır.
- `r{harf}`: tek karakteri değiştirir.
- `R`: üzerine yazma moduna geçer.
- `cw` / `ce` / `cb`: kelime hareketiyle belirlenen kısmı değiştirir.
- `cc` / `C`: satırı / satır sonuna kadar olan kısmı değiştirir.
- Seçim modunda `d` / `c` / `y`: seçimi siler / değiştirir / kopyalar.

## Geri alma ve tekrar

- `u`: son değişikliği geri alır.
- `Ctrl+r`: geri alınan değişikliği yeniden uygular.
- `.`: son değişikliği tekrarlar.
- `Ctrl+a` / `Ctrl+x`: imleçteki veya sonrasındaki sayıyı artırır / azaltır.

## Yazmaçlar ve makrolar

- `"ayy` / `"add`: satırı `a` yazmacına kopyalar / siler.
- `"ap`: `a` yazmacını yapıştırır.
- `:registers` veya `:reg a`: yazmaçları veya `a` yazmacını gösterir.
- `qa`: `a` yazmacına makro kaydını başlatır; normal modda `q` kaydı bitirir.
- `@a` / `{n}@a`: makroyu bir / n kez çalıştırır.
- `@@`: son çalıştırılan makroyu tekrarlar.

## Arama ve değiştirme

- `/metin` / `?metin`: ileri / geri arar; Enter ile aramayı başlatır.
- `n` / `N`: arama yönünde / ters yönde sonraki eşleşmeye gider.
- `*` / `#`: imleçteki kelimeyi ileri / geri arar.
- `:s/eski/yeni/`: satırdaki ilk eşleşmeyi değiştirir.
- `:s/eski/yeni/g`: satırdaki bütün eşleşmeleri değiştirir.
- `:%s/eski/yeni/gc`: dosyadaki eşleşmeleri tek tek onay alarak değiştirir.
- `q/` / `q?` / `q:`: ileri arama / geri arama / komut geçmişini açar; `:q` kapatır.
- `:set incsearch`: yazarken eşleşmeyi gösterir.
- `:set hlsearch` / `:nohlsearch`: eşleşmeleri vurgular / mevcut vurguyu temizler.
- `:set ignorecase`: büyük-küçük harf farkını yok sayar.

Varsayılan arama deseninde `^` satır başını, `$` sonunu, `.` bir karakteri,
`[abc]` kümedeki bir karakteri, `[^abc]` küme dışındaki bir karakteri belirtir.
`*` önceki öğeyi sıfır veya daha çok kez tekrarlar; herhangi bir dizi için `.*`
kullanılır. Desen davranışı `:set magic?` seçeneğine bağlıdır.

## Girinti, görünüm ve tamamlama

- `>>` / `<<`: satırı sağa / sola kaydırır.
- `{n}>>`: n satırı sağa kaydırır.
- `:set shiftwidth=4` / `:set tabstop=8`: girinti genişliğini / sekme duraklarını ayarlar.
- `:set number` / `:set nonumber`: satır numaralarını açar / kapatır.
- `:set list` / `:set nolist`: görünmeyen karakterleri gösterir / gizler.
- `~`: karakterin büyük-küçük harfini değiştirir.
- `ga` veya `:ascii`: karakter kodunu gösterir.
- `Ctrl+l`: ekranı yeniden çizer.
- Ekleme modunda `Ctrl+n` / `Ctrl+p`: sonraki / önceki kelime tamamlama adayını seçer.
- Ekleme modunda `Ctrl+x Ctrl+o`: tanımlı `omnifunc` ile tamamlar.
- `:TOhtml`: ilgili çalışma zamanı eklentisi varsa renklendirilmiş HTML üretir.

## Katlama

- `:set foldmethod=indent`: girintiye göre katlar.
- `zo` / `zc` / `za`: katı açar / kapatır / durumunu değiştirir.
- `zO` / `zC`: imleçteki katı ve alt katlarını açar / kapatır.
- `zR` / `zM`: bütün katları açar / kapatır.
- `zj` / `zk`: sonraki / önceki kata gider.

## Dosya ve kabuk işlemleri

- `:edit dosya`: dosyayı açar.
- `:new dosya`: yeni pencerede dosya açar.
- `:w` / `:w dosya`: kaydeder / belirtilen dosyaya yazar.
- `:wq` / `:q` / `:q!`: kaydedip kapatır / kapatır / değişiklikleri bırakarak kapatır.
- `:r dosya`: dosya içeriğini mevcut satırdan sonra ekler.
- `:r !komut`: komut çıktısını mevcut satırdan sonra ekler.
- `:!komut` / `:shell`: kabuk komutu / geçici kabuk çalıştırır.
- `:terminal`: terminal desteği olan Vim'de terminal açar.
- `:Explore`: netrw varsa dosya tarayıcısını açar.
- `:Nread scp://kullanici@sunucu/yol/dosya`: netrw ve SSH ile uzak dosyayı okur.
- `:Nwrite scp://kullanici@sunucu/yol/dosya`: netrw ve SSH ile uzak dosyaya yazar.

## Tamponlar, sekmeler ve pencereler

Tampon dosyanın bellekteki içeriği, pencere bu içeriğin görünümü, sekme ise
pencere düzenidir.

- `:ls`: tamponları listeler.
- `:bnext` / `:bprevious` / `:buffer {n}`: sonraki / önceki / numaralı tampona geçer.
- `:bdelete` veya `:bdelete {n}`: tamponu listeden kaldırır; kaydedilmemiş değişiklikte uyarır.
- `:set hidden`: değiştirilmiş tamponu kaydetmeden arka planda tutabilmeyi sağlar.
- `:tabnew dosya`: yeni sekmede dosya açar.
- `gt` / `gT` / `:tabclose`: sonraki sekmeye / önceki sekmeye gider / sekmeyi kapatır.
- `:tabmove {n}`: sekmeyi n'inci sekmenin arkasına taşır; 0 başa taşır.
- `:vsplit` / `:split`: dikey / yatay böler.
- `Ctrl+w w` veya `Ctrl+w h/j/k/l`: diğer pencereye / belirtilen yöne geçer.
- `Ctrl+w +` / `Ctrl+w -`: pencere yüksekliğini artırır / azaltır.
- `Ctrl+w c`: pencereyi kapatır.

## Kaynaklar ve doğrulama

Belgedeki hatalı hareket, işaret, tekrar ve tampon komutları Vim'in kendi
[hareket](https://vimhelp.org/motion.txt.html),
[hızlı başvuru](https://vimhelp.org/quickref.txt.html),
[tekrar](https://vimhelp.org/repeat.txt.html) ve
[pencere](https://vimhelp.org/windows.txt.html) belgeleriyle karşılaştırılarak düzeltildi.
Yerel tuş eşlemeleri ve derleme seçenekleri davranışı değiştirebilir; ayrıntılar
Vim içinde `:help` ile görülebilir.
