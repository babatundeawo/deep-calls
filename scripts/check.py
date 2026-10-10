#!/usr/bin/env python3
"""Quality checks for the built site in ``dist/``.

Errors (broken internal links, missing titles, anything that would break the
site's Content-Security-Policy) make the check fail. Warnings are printed for
information but never fail the build.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CONFIG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
SITE = urlparse(CONFIG["url"])
BASE_PATH = SITE.path if SITE.path.endswith("/") else SITE.path + "/"


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.h1 = 0
        self.title = ""
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.jsonld: list[str] = []
        self.problems: list[str] = []
        self._in_title = False
        self._in_ld = False
        self._ld_buf = ""
        self._in_inline = False
        self._inline_buf = ""
        self.inline_scripts: list[str] = []
        self.csp = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and a.get("name"):
            self.meta[a["name"]] = a.get("content", "")
        if tag == "meta" and a.get("http-equiv", "").lower() == "content-security-policy":
            self.csp = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        for attr in ("href", "src"):
            if attr in a and tag in ("a", "link", "script", "img", "use"):
                self.links.append(a[attr])
        if tag == "img" and "alt" not in a:
            self.problems.append("<img> without alt text")
        if "style" in a:
            self.problems.append(f"inline style attribute on <{tag}> (blocked by the Content-Security-Policy)")
        for k in a:
            if k.startswith("on"):
                self.problems.append(f"inline event handler {k} on <{tag}> (blocked by the Content-Security-Policy)")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self._ld_buf = ""
        elif tag == "script" and "src" not in a:
            self._in_inline = True
            self._inline_buf = ""
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in a.get("rel", ""):
            self.problems.append("target=_blank link without rel=noopener")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_ld:
            self._in_ld = False
            self.jsonld.append(self._ld_buf)
        if tag == "script" and self._in_inline:
            self._in_inline = False
            self.inline_scripts.append(self._inline_buf)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._ld_buf += data
        if self._in_inline:
            self._inline_buf += data


def resolve(from_file: Path, href: str) -> Path | None:
    """Map an internal link to a file in dist/, or None if it is external."""
    parsed = urlparse(href)
    if parsed.scheme in ("mailto", "tel", "data", "javascript") or parsed.scheme in ("http", "https") and parsed.netloc != SITE.netloc:
        return None
    if parsed.scheme in ("http", "https"):
        target = parsed.path[len(BASE_PATH):] if parsed.path.startswith(BASE_PATH) else parsed.path.lstrip("/")
        base = DIST
    elif href.startswith("#") or not parsed.path:
        return from_file
    elif parsed.path.startswith("/"):
        target = parsed.path[len(BASE_PATH):] if parsed.path.startswith(BASE_PATH) else parsed.path.lstrip("/")
        base = DIST
    else:
        base = from_file.parent
        target = parsed.path
    path = (base / unquote(target)).resolve()
    if path.is_dir():
        path = path / "index.html"
    return path


def main() -> int:
    if not DIST.exists():
        print("dist/ not found. Run scripts/build.py first.", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    pages = sorted(DIST.rglob("*.html"))
    parsed_pages: dict[Path, Page] = {}
    for f in pages:
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        parsed_pages[f.resolve()] = p

    titles: dict[str, Path] = {}
    for f, p in parsed_pages.items():
        rel = f.relative_to(DIST.resolve())
        for problem in sorted(set(p.problems)):
            errors.append(f"{rel}: {problem}")
        if p.h1 != 1:
            errors.append(f"{rel}: expected exactly one <h1>, found {p.h1}")
        title = p.title.strip()
        if not title:
            errors.append(f"{rel}: missing <title>")
        elif title in titles:
            warnings.append(f"{rel}: same <title> as {titles[title].relative_to(DIST.resolve())}")
        titles[title] = f
        desc = p.meta.get("description", "")
        if not desc:
            errors.append(f"{rel}: missing meta description")
        elif len(desc) > 175:
            warnings.append(f"{rel}: meta description is {len(desc)} characters (search results cut it near 160)")
        elif len(desc) < 50:
            warnings.append(f"{rel}: meta description is short ({len(desc)} characters)")
        if rel.name != "404.html" and not p.canonical:
            errors.append(f"{rel}: missing canonical link")
        if not p.csp:
            errors.append(f"{rel}: missing Content-Security-Policy")
        for script in p.inline_scripts:
            digest = "sha256-" + base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
            if digest not in p.csp:
                errors.append(f"{rel}: inline <script> is not allowed by the Content-Security-Policy")
        for blob in p.jsonld:
            try:
                json.loads(blob)
            except json.JSONDecodeError as err:
                errors.append(f"{rel}: invalid JSON-LD ({err})")

        # Internal links and anchors
        for href in p.links:
            if not href or href.startswith("#i-"):
                continue
            target = resolve(f, href)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{rel}: broken link {href}")
                continue
            fragment = urlparse(href).fragment
            if fragment and target.suffix == ".html":
                tp = parsed_pages.get(target)
                if tp and unquote(fragment) not in tp.ids:
                    errors.append(f"{rel}: link {href} points to a missing anchor")

    # Sitemap entries must exist
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    for url in urls:
        target = resolve(DIST / "index.html", url)
        if target is None or not target.exists():
            errors.append(f"sitemap.xml: {url} does not exist in the build")
    if len(urls) != len({u for u in urls}):
        errors.append("sitemap.xml: duplicate URLs")
    essays = list((DIST / "writeups").glob("*.html"))
    if len(urls) != len(essays) + 4:
        warnings.append(f"sitemap lists {len(urls)} URLs for {len(essays)} essays + 4 pages")

    # Social cards exist for every essay
    for f in essays:
        if not (DIST / "assets" / "og" / f"{f.stem}.png").exists():
            errors.append(f"missing social card for {f.name}")

    print(f"Checked {len(pages)} pages.")
    for w in warnings:
        print(f"  warning: {w}")
    for e in errors:
        print(f"  ERROR: {e}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
