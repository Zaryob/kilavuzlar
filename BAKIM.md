---
title: İçerik incelemesi ve bakım planı
permalink: /bakim/
---

# İçerik incelemesi ve bakım planı

İnceleme tarihi: **2 Kasım 2026**. Kapsam: depodaki 15 kılavuz, kategori
sayfaları ve Jekyll yayın yapılandırması.

## Yapılan düzenleme

- 2 Docker kılavuzu ve Vim başvuru belgesi yeniden düzenlendi. Kaynak kontrolü yapıldı; uygulamalı test kapsamı belgelerin kendi doğrulama bölümlerinde belirtilir.
- 9 Linux ve 3 görüntü işleme notu, kapsam ve arşiv gerekçeleriyle saklandı. Arşiv kararı hedef ortamın belirsizliğini ve metindeki eksikleri de kapsar; her satırın geçersiz olduğu anlamına gelmez.
- Boş C/C++, Python ve Raspberry Pi kategori sayfaları kaldırıldı; eski kategori adresleri ana dizine yönlendirildi.
- Dosya adları küçük ASCII harfleri ve kısa çizgiyle standartlaştırıldı. Taşınan belgelerin eski HTML adresleri yönlendirmelerle korundu.
- Arşivdeki Liquid kod blokları standart Markdown'a dönüştürüldü. Debian notundaki blok dışına taşmış fonksiyon parantezi ve model eğitimi notundaki biçimlendirilmemiş komutlar düzeltildi.
- Her belgenin tek bir ana başlığı olması sağlandı; konu dizinlerine açık bağlantılar eklendi.
- Yinelenen `exclude` ayarı birleştirildi, site adresine HTTPS eklendi. Erişilemeyen uzak tema bağımlılığı kaldırıldı; menü ve arşiv notları yerel şablona alındı.

## Önce giderilmesi gereken içerik sorunları

1. **Uzak erişim ve web sunucuları:** VNC belgesinde protokolün kendiliğinden güvenli olduğu söyleniyor ve SSH tüneliyle grafik istemcinin rolleri karışıyor. LAMP/LEMP notları root kimlik doğrulamasını örnek bir parola ile değiştiriyor. LEMP notunda Nginx/PHP-FPM bağlantısı yok; port açmak HTTPS yapılandırması olarak anlatılıyor. Bu belgeler tamamlanmadan arşivden çıkarılmamalı.
2. **Paket ve çekirdek yönetimi:** Debian notunda `apt-get instal apt-ftparchive` komutu, kendi çıktısını hash listesine alan Release üretimi ve eski anahtar ekleme akışı var. YUM/DNF sürümleri ayrılmamış. Çekirdek notunda EPEL ve ELRepo karıştırılıyor; kaldırma rehberinde çalışan çekirdek ve geri dönüş denetimi yok.
3. **Donanım ve sanallaştırma:** AMD notu 2019–2021 dönemine ait; Mesa, amdgpu-pro ve GPU seçimi aynı çözüm gibi sunuluyor. VirtualBox notu 6.1 paketine bağlı. Donanım/dağıtım sürümleri belirlenerek yeniden denenmeli.
4. **Görüntü işleme:** OpenCV notunda sürüm yer tutucuları ile 4.0.0 dizin adları tutarsız; ARM ve genel derleme seçenekleri karışık. Caffe notu Python 2/3.7 ve sabit ABI yollarına bağlı. Model oluşturma rehberinin sözünü ettiği train/test/solver dosyaları depoda bulunmuyor.

## Tekrarlar ve korunmuş varlıklar

LAMP ve LEMP notlarındaki MySQL bölümü aynı içeriği tekrar ediyor. Arşivde iki
notun geçmişi korundu; yenileme sırasında ortak bir veritabanı kurulum belgesine
ayrılmalı ve iki sunucu kılavuzundan oraya bağlantı verilmeli.

`images/docker/` altındaki eski şema ve Docker Desktop ekran görüntüsü yeni
anlatımda kullanılmıyor. Önceden yayımlanmış görsel adreslerini bozmamak için
korundular; eski ekran görüntüsü güncel kurulum adımı sayılmamalı.

## Bundan sonraki bakım

Önce hedef dağıtım ve sürüm seçilmeli. Ardından bir kılavuz sanal makine veya
konteyner içinde baştan sona denenerek yeniden yazılmalı. Başarı denetimi ve
geri dönüş adımları eklenmeli; yalnızca o belge ana dizine taşınmalı.

Yeni içerik ve kontrol komutları için [katkı rehberine](CONTRIBUTING.md) bakın.

## Bu düzenlemenin doğrulaması

- Ruby 3.3, github-pages 232 ve Jekyll 3.10.0 ile katı üst bilgi denetimi açıkken site derlendi.
- Üretilen 54 HTML sayfasındaki 266 yerel bağlantı ve 29 yönlendirme hedefi kontrol edildi. Harici bağlantılar bu otomatik kontrolün kapsamına girmez.
- Ana dizinin görünümü ve arşiv gerekçelerinin sayfa başında gösterilmesi tarayıcıda kontrol edildi.
- 12 arşiv belgesi Git'teki özgün metinleriyle, başlık ve biçim değişiklikleri dışarıda bırakılarak karşılaştırıldı; içerik korunuyor.
- Docker Engine 29.6.2 üzerinde statik C++ örneği Linux/ARM64 için derlenip çalıştırıldı; beklenen çıktı alındı. Çok mimarili örnekte AMD64 ve ARM64 içeren OCI arşivi üretildi; ARM64 çalıştırması `aarch64` döndürdü. Registry'ye gönderim yapılmadı.
- Vim belgesi kaynaklarla karşılaştırıldı; bütün tuşların etkileşimli testi yapılmadı. Arşivdeki kurulum komutları çalıştırılmadı.
