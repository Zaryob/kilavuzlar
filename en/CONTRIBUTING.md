---
title: Contribution and maintenance rules
permalink: /en/katki/
lang: en
translation_key: guide-CONTRIBUTING
translation_of: /katki/
translated: '2026-11-03'
---

# Contribution and maintenance rules

## New guides

- Place the document in its topic directory. Add a linked `README.md` for a new directory.
- Use lowercase ASCII letters and hyphens in filenames. Preserve Turkish characters in Turkish titles and prose.
- Use one main heading (`#`) per document, with `##` and `###` sections.
- Put commands in fenced blocks with a language identifier. Do not prefix copyable commands with `$` or `#`; show output separately in a `text` block.
- State the purpose, operating-system/version scope, prerequisites, steps, expected results and sources.
- Distinguish source review from an environment in which the commands were actually run. Do not label untested instructions as current or working.

Example front matter, retained in the source language:

```yaml
---
title: Belgenin başlığı
permalink: /konu/belge-adi/
status: duzenlendi
reviewed: 2026-11-02
scope: Hedef işletim sistemi, sürüm ve araçlar.
---
```

## Updating and archiving

When moving a document, add its previous HTML URL to `redirect_from`. Use actual `.md` files for internal links; Jekyll converts them to page permalinks when publishing.

Place notes with unclear currency or environment under the appropriate `arsiv/` topic. Fill in `status: arsiv`, `scope` and `archive_reason`. Complete missing steps and verify the target environment before promoting a document out of the archive. Archive original notes instead of deleting them, and link new treatments to the historical material.

## Local preview and checks

In an environment with Ruby and Bundler, using Ruby 3.3 in the recorded review:

```bash
bundle install
bundle exec jekyll serve
```

Preview: [localhost:4000/kilavuzlar/](http://localhost:4000/kilavuzlar/).

Before publishing:

```bash
bundle exec jekyll build --strict_front_matter
python3 scripts/check_site.py _site --baseurl /kilavuzlar
npx --yes pagefind@1.6.0 --site _site
```

The checker verifies local pages, images, styles, anchors and redirect targets. External-site currency and the actual operation of guide commands must be checked separately.

Specify the language in code blocks. If the snippet represents an example file, add a filename directly below the closing fence, like `{: data-filename="Dockerfile"}`.

## Language editions

Keep the Turkish source in its topic directory and its English counterpart under
`en/` with the same file structure. Give both the same `translation_key`, with
`lang: tr` and `lang: en` respectively. Prefix the English permalink with `/en`;
original URLs and redirects stay in the Turkish source. Preserve code samples
byte for byte in both editions. Record the translation date in `translated`;
translation alone does not change `reviewed` or establish new verification.
Translate the scope and archive-reason fields too. Check links in both languages
when updating a document.
