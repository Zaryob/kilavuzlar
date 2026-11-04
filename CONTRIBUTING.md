---
translation_key: guide-CONTRIBUTING
lang: tr
title: Katkı ve bakım kuralları
permalink: /katki/
---

# Katkı ve bakım kuralları

## Yeni kılavuz

- Belgeyi konu klasörüne koyun; yeni klasör için bağlantılı bir `README.md` ekleyin.
- Dosya adında küçük ASCII harfleri ve kısa çizgi kullanın. Başlık ve metinde Türkçe karakterleri koruyun.
- Bir belgede tek ana başlık (`#`) kullanın. Bölümleri `##` ve `###` ile ayırın.
- Komutları dil belirtilmiş üç ters tırnaklı bloklara yazın. Kopyalanacak komutların başına `$` veya `#` istemi eklemeyin; çıktıyı ayrı `text` bloğunda gösterin.
- Blok bir örnek dosyanın içeriğini gösteriyorsa kapanış çitinin hemen altına `{: data-filename="Dockerfile"}` gibi bir dosya adı ekleyin.
- Amaç, işletim sistemi ve sürüm, ön koşullar, uygulama adımları, beklenen sonuç ve kaynakları belirtin.
- Kaynak kontrolü ile komutların gerçekten çalıştırıldığı test ortamını ayrı yazın. Test edilmemiş bir belgeyi güncel veya çalışır diye etiketlemeyin.

Örnek üst bilgi:

```yaml
---
title: Belgenin başlığı
permalink: /konu/belge-adi/
status: duzenlendi
reviewed: 2026-11-02
scope: Hedef işletim sistemi, sürüm ve araçlar.
---
```

## Güncelleme ve arşivleme

Eski bir belgeyi taşırken önceki HTML adresini `redirect_from` listesine ekleyin.
Dahili bağlantılarda gerçek `.md` dosyasını kullanın; Jekyll yayın sırasında
bağlantıyı sayfanın kalıcı adresine çevirir.

Güncelliği veya çalışma ortamı belirsiz notu `arsiv/` altında ilgili konuya koyun.
`status: arsiv`, `scope` ve `archive_reason` alanlarını doldurun. Arşivden çıkarmadan
önce eksik adımları tamamlayıp hedef ortamda doğrulayın. Özgün notları silmek
yerine arşivleyin; aynı konunun yeni anlatımında eski notla ilişki kurun.

## Yerel önizleme ve kontrol

Python 3, Ruby 3.3 veya üstü ve Bundler gerekir. Deponun kök dizininden çalıştırın:

```bash
python3 scripts/jekyll.py install
python3 scripts/jekyll.py serve
```

Önizleme: [localhost:4000/kilavuzlar/](http://localhost:4000/kilavuzlar/).

Yayımlamadan önce:

```bash
python3 scripts/jekyll.py build --strict_front_matter
python3 scripts/check_site.py _site --baseurl /kilavuzlar
npx --yes pagefind@1.6.0 --site _site
```

Kontrol betiği yerel sayfa, görsel, stil, sayfa içi bağlantı ve yönlendirme
hedeflerini denetler. Harici sitelerin güncelliği ve kılavuz komutlarının
çalışması ayrıca kontrol edilmelidir.

GitHub Actions siteyi derler, arama indeksini üretir ve `main` derlemelerini
GitHub Pages'e yayımlar. Yerelde blog ve kılavuz indekslerini birlikte denemek
için ana sitenin `scripts/preview_suite.py` betiğini kullanın.

## Dil sürümleri

Türkçe kaynak dosyayı konu klasöründe, İngilizce karşılığını aynı dosya yapısıyla
`en/` altında tutun. İkisine aynı `translation_key`, kendi dilleri için `lang: tr`
ve `lang: en` ekleyin. İngilizce kalıcı adresin başına `/en` gelir; özgün adres ve
yönlendirmeler Türkçe dosyada kalır. Kod örneklerini iki sürümde de birebir koruyun.
Çeviri tarihini `translated` ile belirtin; yalnızca çeviri yapıldığı için `reviewed`
tarihini veya belgenin doğrulama iddiasını değiştirmeyin. Kapsam ve arşiv gerekçesi
alanlarını da çevirin. Değişiklik yaparken iki dilin bağlantılarını birlikte denetleyin.
