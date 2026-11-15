# Kılavuzlar

**English** · [Türkçe](README.tr.md)

Süleyman Poyraz's notes on software development and system administration, published as a
Jekyll site with Turkish originals and English translations.

[Read the site](https://zaryob.github.io/kilavuzlar/) · [English edition](https://zaryob.github.io/kilavuzlar/en/)

## What is in the repository

- `docker/`, `linux/`, `cpp/`, `emacs/`, `sanallastirma/`, `vim/` — the guides, one folder per topic.
- `arsiv/` — older Linux and image-processing notes, kept with their original content. Each
  one states its scope and what must be completed before it is reused.
- `en/` — English translations, mirroring the Turkish folders.
- `index.md` — the Turkish home page of the site (`/`); `en/README.md` is the English one (`/en/`).
- `README.md` inside each topic folder — that folder's index page on the site.
- `_layouts/`, `_includes/`, `_data/`, `assets/` — the site layout and the shared console theme.
- `scripts/` — the Jekyll wrapper and the link check.

This file and `README.tr.md` describe the repository and are not published on the site.

## Preview and checks

You need Python 3, Ruby 3.3 or newer, and Bundler. From the repository root:

```sh
python3 scripts/jekyll.py install
python3 scripts/jekyll.py serve
```

The preview is at <http://localhost:4000/kilavuzlar/>. Before publishing:

```sh
python3 scripts/jekyll.py build --strict_front_matter
python3 scripts/check_site.py _site --baseurl /kilavuzlar
npx --yes pagefind@1.6.0 --site _site
```

GitHub Actions runs the same build, link check and Pagefind indexing on every push and pull
request, and publishes `main` to GitHub Pages.

## Contributing

The rules for adding and maintaining guides are in [CONTRIBUTING.md](CONTRIBUTING.md)
([English](en/CONTRIBUTING.md)); the findings of the latest content review are in
[BAKIM.md](BAKIM.md) ([English](en/BAKIM.md)).

The files under `assets/console/` and the shared includes come from the
[console-theme](https://github.com/Zaryob/console-theme) repository; change them there.

## License

Guides and archive notes are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) ([LICENSE-CONTENT](LICENSE-CONTENT), [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt)). The site's source code is licensed under GPL-3.0-or-later ([LICENSE](LICENSE)). Third-party material keeps its own licence.
