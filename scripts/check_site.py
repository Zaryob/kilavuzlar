#!/usr/bin/env python3
"""Check links and redirect targets in a built Jekyll site (stdlib only)."""

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.targets = set()
        self.links = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.targets.add(attrs["id"])
        if tag == "a" and "name" in attrs:
            self.targets.add(attrs["name"])
        key = "src" if tag in {"img", "script"} else "href"
        if tag in {"a", "link", "img", "script"} and attrs.get(key):
            self.links.append(attrs[key])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    parser.add_argument("--baseurl", default="/kilavuzlar")
    args = parser.parse_args()
    root = args.site.resolve()
    prefix = args.baseurl.rstrip("/")
    pages = {p.resolve(): Page(p.read_text()) for p in root.rglob("*.html")}
    errors = []
    if not (root / "index.html").is_file():
        errors.append("Site kökünde index.html bulunamadı; önce Jekyll derlemesini çalıştırın.")

    def locate(path):
        path = unquote(path)
        if prefix and path != prefix and not path.startswith(prefix + "/"):
            return None
        relative = path[len(prefix):].lstrip("/")
        target = (root / relative).resolve()
        if root not in target.parents and target != root:
            return None
        return target / "index.html" if target.is_dir() else target

    def check(link, origin, source):
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc:
            return
        absolute = urlsplit(urljoin(origin, link))
        target = locate(absolute.path)
        if target is None or not target.is_file():
            errors.append(f"{source}: hedef bulunamadı: {link}")
        elif absolute.fragment and target in pages:
            fragment = unquote(absolute.fragment)
            if fragment not in pages[target].targets:
                errors.append(f"{source}: sayfa içi hedef bulunamadı: {link}")

    count = 0
    for path, page in pages.items():
        relative = path.relative_to(root).as_posix()
        origin = prefix + "/" + relative
        if origin.endswith("/index.html"):
            origin = origin[:-len("index.html")]
        for link in page.links:
            check(link, origin, relative)
            parsed = urlsplit(link)
            if not parsed.scheme and not parsed.netloc:
                count += 1

    redirects = root / "redirects.json"
    aliases = json.loads(redirects.read_text()) if redirects.is_file() else {}
    site_host = None
    # Canonical links establish this site's origin, so off-site redirects fail.
    index = pages.get((root / "index.html").resolve())
    if index:
        site_host = next((urlsplit(link).netloc for link in index.links
                          if urlsplit(link).scheme in {"http", "https"}), None)
    for source, destination in aliases.items():
        alias = locate(prefix + source)
        if alias not in pages:
            errors.append(f"Yönlendirme sayfası bulunamadı: {source}")
        parsed = urlsplit(destination)
        if parsed.netloc and parsed.netloc != site_host:
            errors.append(f"Site dışına yönlendirme: {source} → {destination}")
        check(parsed.path, prefix + "/", source)

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"OK: {len(pages)} HTML sayfası, {count} yerel bağlantı, {len(aliases)} yönlendirme.")


if __name__ == "__main__":
    main()
