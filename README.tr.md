# Kılavuzlar

[English](README.md) · **Türkçe**

Süleyman Poyraz'ın yazılım geliştirme ve sistem yönetimi notları. Türkçe özgün metinler ve
İngilizce çevirileriyle bir Jekyll sitesi olarak yayımlanır.

[Siteyi açın](https://zaryob.github.io/kilavuzlar/) · [İngilizce sürüm](https://zaryob.github.io/kilavuzlar/en/)

## Depoda neler var

- `docker/`, `linux/`, `cpp/`, `emacs/`, `sanallastirma/`, `vim/` — kılavuzlar; her konu ayrı klasörde.
- `arsiv/` — özgün içerikleri korunan eski Linux ve görüntü işleme notları. Her birinin
  başında kapsamı ve yeniden kullanılmadan önce tamamlanması gerekenler yazılıdır.
- `en/` — Türkçe klasörlerle aynı düzende İngilizce çeviriler.
- `index.md` — sitenin Türkçe ana sayfası (`/`); İngilizce ana sayfa `en/README.md` dosyasıdır (`/en/`).
- Konu klasörlerindeki `README.md` — o klasörün sitedeki dizin sayfası.
- `_layouts/`, `_includes/`, `_data/`, `assets/` — site düzeni ve ortak konsol teması.
- `scripts/` — Jekyll sarmalayıcısı ve bağlantı denetimi.

Bu dosya ve `README.md` depoyu anlatır; sitede yayımlanmaz.

## Önizleme ve denetimler

Python 3, Ruby 3.3 veya üstü ve Bundler gerekir. Deponun kök dizininden çalıştırın:

```sh
python3 scripts/jekyll.py install
python3 scripts/jekyll.py serve
```

Önizleme <http://localhost:4000/kilavuzlar/> adresinde açılır. Yayımlamadan önce:

```sh
python3 scripts/jekyll.py build --strict_front_matter
python3 scripts/check_site.py _site --baseurl /kilavuzlar
npx --yes pagefind@1.6.0 --site _site
```

GitHub Actions aynı derlemeyi, bağlantı denetimini ve Pagefind indekslemesini her push ve
pull request için çalıştırır; `main` dalını GitHub Pages'e yayımlar.

## Katkı

Kılavuz ekleme ve bakım kuralları [CONTRIBUTING.md](CONTRIBUTING.md) dosyasında, son içerik
incelemesinin bulguları [BAKIM.md](BAKIM.md) dosyasındadır.

`assets/console/` altındaki dosyalar ve ortak include'lar
[console-theme](https://github.com/Zaryob/console-theme) deposundan gelir; değişiklikleri
orada yapın.

## Lisans

Kılavuzlar ve arşiv notları [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.tr) ile lisanslıdır ([LICENSE-CONTENT](LICENSE-CONTENT), [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt)). Sitenin kaynak kodu GPL-3.0-or-later ile lisanslıdır ([LICENSE](LICENSE)). Üçüncü taraf malzeme kendi lisansını korur.
