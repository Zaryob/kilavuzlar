---
sort: 2
---

# VIM Tuş Kombinasyonları

## Ekleme moduna geçiş

* **i  (i=insert)**     bulunulan yerde yazma moduna geçer 
* **I  (I=insert)**     satır başına gidip yazma moduna geçer
* **a  (a=append)**     bir sonraki yerden bir karakter sağa kayıp yazma moduna geçer
* **A  (A=append)**     satır sonuna gidip yazma moduna geçer 
* **o**                 aşağıya yeni bir satır ekleyip yazma moduna geçer
* **O**                 yukarıya bir satır ekleyip yazma moduna geçer
* **\<ESC\>**             ekleme modundan çıkar


## Dosya içinde hareket

* **h**               sola bir karakter ilerle
* **l**               sağa bir karakter ilerle
* **j**               aşağı satıra ilerle
* **k**               yukarı satıra ilerle
* *x***h**            x satır yukarı ilerle
* *x***j**            x satır aşağı ilerle
* **H**               imleç sayfa başına git
* *x***H**            imleç sayfa başından x satır aşağıya git
* **L**               imleç sayfa sonuna git
* *x***L**            imleç sayfa sonundan x satır yukarıya git
* **M**               imleç sayfa ortasına git
* **gg**              dosya başına git
* **GG**              dosya sonuna git
* *x***G**            x.satıra git
* **:***x*            x.satıra git
* *\<CTRL\>***e**       dosyayı yukarı doğru kaydır(imlecin yeri değişmez)
* *\<CTRL\>***y**       dosyayı aşağıya doğru kaydır(imlecin yeri değişmez)
* **zt**              bulunulan satırı sayfanın başında gösterir (imlecin yeri değişmez)
* **zb**              bulunulan satırı sayfanın sonuna gösterir(imlecin yeri değişmez)
* **zz**              bulunulan satırı sayfanın ortasına gösterir(imlecin yeri değişmez)
* **%**               parantezin eşini bulur ve imleci oraya götürür
* **“**               imlecin bir önceki konumuna geri döner
* **.**               en son değişikliğin yapıldığı satıra geri döner
* **f***\<harf\>*       satırda,sağa doğru ilk harfin bulunduğu konuma gider
* **F***\<harf\>*       satırda,sola doğru ilk harfin bulunduğu konuma gider
* **ma**              imlecin bulunduğu yeri a noktası olarak işaretle(a..z,A..Z,0..9)(m=mark)
* **a**               a noktasının bulunduğu satıra git
* **‘a**              a noktasına git
* **:marks**          işaretli noktaların listesini gösterir


## Silme, kopyalama ve yapıştırma 

* **x \<DEL\>**         karakteri sil
* **X**               önceki karakteri sil
* **dw**              bir sonraki kelimeye kadar sil(w=word)
* **de**              kelimenin sonuna kadar sil
* **db**              kelimenin başına kadar sil
* **dd**              satırı sil
* **d’a**             a noktasının bulunduğu satırakadar sil
* **‘a**              a noktasına kadar sil
* **d^**              bulunulan yerden,satır başına kadar sil
* **d$**              bulunulan yerden,satır sonuna kadar sil
* **D**               bulunulan yerden,satır sonuna kadar sil
* *x***dd**           x satır sil
* **yl**              harfi kopyala
* **yw**              bir sonraki kelimeye kadar kopyala
* **ye**              kelimenin sonuna kadar kopyala
* **yb**              kelimenin başına kadar kopyala
* **yy**              satırı kopyala
* **y’a**             a noktasına kadar kopyala
* **y^**              bulunulan yerden,satır başına kadar kopyala
* **y$**              bulunulan yerden,satır sonuna kadar kopyala
* **p**               bir sonraki pozisyona yapıştır
* **P**               bir önceki pozisyona yapıştır
* *x***p**            x kere yapıştır


## Dosya veya kabuktan veri alma

* **:r dosya**     dosyanın içeriğini imleçten sonraki satıra yazar
* **:r !komut**    komutun çıktısını imleçten sonraki satıra yazar

## Depo kullanarak kopyalama ve yapıştırma

* **“add**              silinen satırı ‘a’ kodlu depoya koy
* **“ayy**              kopyalanan satırı ‘a’ kodlu depoya koy
* **“ap**               ‘a’ kodlu depodaki veriyi yapıştır
* **:reg a**            ‘a’ kodlu depoda ne olduğunu gösterir (reg=register)
* **:reg abcd**         a, b c, d depolarında ne olduğunu gösterir
* **:reg**              bütün depoları gösterir
* **a..z, A..Z, 0..9**  depo kodu olarak regex'e uygun olan bütün kopyalama ve yapıştırma komutlarını gösterir


## Görsel modda kopyalama ve yapıştırma

* **v**                 görsel moda geç, karakter seçme
* **V**                 görsel moda geç, satır satır seç
* *\<CTRL\>***v**         görsel moda geç, blok seç
* **d**                 seçimi sil
* **c**                 seçimi sil ve yazma moduna geç
* **y**                 seçimi kopyala
* **p**                 seçimi yapıştır


## Arama ve otomatik değiştirme

* **\***                    imlecin üzerinde bulunduğu kelimenin tekrarını sonra doğru arar
* **\#**                    imlecin üzerinde bulunduğu kelimenin tekrarını başa doğru arar
* **/metin**                metini sona doğru ara
* **?metin**                metin başa doğru ara
* **n**                     bir sonrakini bul
* **N**                     bir öncekini bul
* **:s/metin/yeni**         sablona uyan ilk metni, yenisi ile değiştir
* **:s/metin/yeni/g**       satırda,şablona uyan tüm metinleri, yeni ile değiştir 
* **\*:%s/metin/yeni/g\***  dosyada,şablona uyan tüm metinleri, yeni ile değiştir
* **:%s/metin/yeni/gc**     dosyada,şablona uyan metinleri, yeni ile değiştir ama önce onay alır

## Arama şablonunda kullanılan regex komutları

* **^**                        satır başı
* **$**                        satır sonu
* **\[abc\]**                    bu karakterlerden biri…
* **\[^abc\]**                   bu karakterlerden hiçbiri…
* **\.**                       herhangi bir karakter
* **\***  	                   herhangi bir karakter dizisi
* **q/** veya */\<CTRL\>***f**   ileriye doğru yapılmış aramaların listesini verir
* **q?** veya *?\<CTRL\>***f**   geriye doğru yapılmış aramaların listesini verir
* **:set is**                  şablon yazılırken aramaya başla
* **:set hls**                 şablona uyanları belirginleştir
* **:set nohls**               hls modunu kapat
* **:set ic**                  büyük-küçük harf ayırt etmeden arar

## Kesme ve değiştirme işlemleri

* **r\<harf\>**       imlecin bulunduğu harfi sil ve yerine, \<harf\> yaz
* **R**             yazma moduna geç ve eski metnin üstüne yaz
* **cw**            bir sonraki kelimeye kadar olan kısmı sil ve yerine, yazılanları yaz
* **ce**            kelimenin sonuna kadar olan kısmı sil ve yerine, yazılanları yaz
* **cb**            kelimenin başına kadar olan kısmı sil ve yerine, yazılanları yaz
* **c’a**           a noktasının bulunduğu satıra kadar sil ve yerine, yazılanları yaz
* **c`a**           a noktasına kadar sil ve yerine, yazılanları yaz
* **c^**            satırın başına kadar olan kısmı sil ve yerine, yazılanları yaz
* **c$**            satırın sonuna kadar olan kısmı sil ve yerine, yazılanları yaz
* **C**             satırın sonuna kadar olan kısmı sil ve yerine, yazılanları yaz
* *x***cw**         x kelimeyi sil ve yerine, yazılanları yaz


## Geri Alma - İleri Alma

* **u**             yapılan işlemi geri al
* **U**             satırı, imlecin satıra geldiği andaki şekle geri döndür
* *\<CTRL\>***r**     undo işlemini geri al
* *x***u**          son x değişikliği geri al

## Biçimlendirme

* **:set expandtab**
  **:retab**                      tab karakterlerini tab karakterlerini boşluk karakterine çevirir
* **:set noexpandtab**
* **:retab**                      uygun sayıda boşluk karakterini tab karakterine çevirir
* **>>**                          satırı, bir tab aralığı kadar sağa kaydırır
* **<<**                          satırı, bir tab aralığı kadar sola kaydırır
* **>***\<sağ ok tuşu\>*            bulunulan satırı kaydırır
* **>***\<yukarı ok tuşu\>*         bulunulan satır ve bir üst satırı kaydırır
* **>***\<aşağı ok tuşu\>*          bulunulan satır ve bir alt satırı kaydırır
* *x***>>**                       x satırı bir tab aralığı kadar kaydırır
* *x***>** *\<yukarı ok tuşu\>*     bulunulan satır dahil yukarı doğru x satırı sağa kaydırır
* **:set sw=4**                   tab aralığının kaç karakter uzunluğunda olacağını belirtir (sw=shift width)
* **:set tabstop=8**              tab ile kaç karakter gidileceğini belirler
* **:set nu**                     satır numaralarını gösterir (nu=number)
* **:set nonu**                   satır numaralarını gizler (nonu=no number)
* **~**                           imlecin üstünde bulunduğu karakteri büyükse küçük, küçükse büyük yapar
* **:TOhtml**                     metni üretecek HTML kodunu üretir, renklendirmeleri dikkate alır


## Yazma/işlem kolaylaştırıcılar

* *\<CTRL\>***l**                 refresh
* **:setlist/nolist**           görünmeyen karakterleri göstermek veya göstermemek için…
* **ga**                        imlecin altındaki karakterin, karakter kodunu gösterir
* **:as**                       imlecin altındaki karakterin, karakter kodunu gösterir
* *\<CTRL\>***n**                 yazma modundayken kelimeyi, var olan kelimelere bakarak tamamlar 
* *\<CTRL\>***p**                 yazma modundayken kelimeyi, var olan kelimelere bakarak tamamlar
* **\.**                       son yapılan işlemi tekrarlar
* **q:**
* *\<CTRL\>***f**                kullanılmış komutların listesini verir
* **q**
* *\<CTRL\>***f**                ileriye doğru yapılmış aramaların listesini verir
* **q?**
* **?***\<CTRL\>***f**           geriye doğru yapılmış aramaların listesini verir
* *\<CTRL\>***c***\<CTRL\>***c**   komut/arama listesinden çıkmak için
* *\<CTRL\>***x**                imleçin üstünde bulunduğu sayıyı bir azaltır
* *\<CTRL\>***a**                imleçin üstünde bulunduğu sayıyı bir çoğaltır
* **:setfoldmethod=indent**    indent’lere göre blokları belirler (Python kodu için…)
* **zo**                       bloğu açar
* **zO**                       bütün blokları açar
* **zc**                       bloğu kapatır
* **zC**                       bütün blokları kapatır
* **za**                       açıksa, kapalı; kapalıysa, açık hale getirir
* **zj**                       sonraki bloğa geçer
* **zk**                       önceki bloğa geçer
* *\<CTRL\>***xo**               omnifunc tanımlanmış dosya biçimleri için kod tamamlar

## Macrolar 

* **q**                 ilk seferde makro bloğuna gider, bundan sonra girilen ilk harf makronun adı olur, bundan sonra yapılan bütün işlemler makro bloğuna kaydedilir, tekrar q’ye basıldığında makro kaydı sona erer.
* **\@***\<harf\>*         makroyu çalıştırır
* **\“***\<harf\>***p**    makro içeriğini metin olarak sayfaya yazar
* **~/.viminfo**        dosyasından da makro kayıtları görünebilir


## Dosya işlemleri

* **:new** *\<DOSYA\>*    yeni dosya oluştur
* **:S**                dosya tarayıcısını aç. Seçimler için \<ENTER\> kullan
* **:e** *\<DOSYA\>*      var olan bir dosyayı aç
* **:w**                yapılan değişiklikleri kaydet
* **:w** *\<DOSYA\>*      yapılan değişiklikleri ‘dosya’ adı ile kaydet
* **:wq**               yapılan değişiklikleri kaydedip çık
* **:q!**               yapılan değişiklikleri kaydetmeden çık

## Uzak dosya sistemleri

* **:Nread** *scp://kullanici@12.12.12.12/klasor/dosya*      dosyaya scp ile uzaktaki makineden açar.
* **:Nwrite** *scp://kullanici@12.12.12.12/klasor/dosya*     dosyayı scp ile uzaktaki makineye kaydeder.


## Birçok dosya ile aynı anda çalışma

* **:bn**         bir sonraki tampon belleğe geç
* **:bp**         bir önceki tampon belleğe geç
* **:wn**         değişiklikleri kaydet ve bir sonraki tampon belleğe geç
* **:wp**         değişiklikleri kaydet ve bir önceki tampon belleğe geç
* **:bn!**        değişiklikleri kaydetmeden bir sonraki tampon belleğe geç
* **:bx**         x numaralı tampon belleğe geç
* **:bd**         tampon bellegi siler
* **:bd***x*      x numaralı tampon belleği siler
* **:set hidden** bir tampon bellekten diğerine, değişiklikleri kaydetmeden geçmeye izin verir


## Tab’lar ile çalışma

* **:tabedit**                yeni tab oluşturur
* **:tabnew** *\<DOSYA\>*       yeni tab oluşturur ve dosyayı bu tab’da açar
* **:tabc**                   tab’ı kapatır
* **:tabmove**                tab’ı taşı
* **gt**                      sonraki tab’a git
* **gT**                      önceki tab’a git


## Birçok pencere ile aynı anda çalışma

* **:vsp**                    ekranı dikeyde iki pencereye böL
* **:sp**                     ekranı yatayda iki pencereye böl
* *\<CTRL\>***w***\<CTRL\>***w**  diğer pencereye geç
* *\<CTRL\>***w***\<ok tuşu\>*    ok yönündeki pencereye geç
* *\<CTRL\>***w***\<hjkl\>*       yön karakterine göre pencereye geç
* *\<CTRL\>***w** **+**         pencereyi 1 satır uzat
* *\<CTRL\>***w** **–**         pencereyi 1 satır kısalt
* *\<CTRL\>***w** **c**         pencereyi kapat
* **:q**                      pencereyi kapat


## Komut satırı

* **:!komut**    komutu çalıştır
* **:sh**        shell’i çalıştır. Shell’den çıkmak için “exit” komutunu kullan
* **:term**      öntanımlı kabuk ortamını pencere olarak açar.
