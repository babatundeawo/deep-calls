#!/usr/bin/env python3
"""Build the Deep Calls website into ``dist/``.

Run by GitHub Actions on every push (see .github/workflows/deploy.yml). It reads
the essays in ``content/``, the design files in ``assets/`` and the settings in
``site.config.json``, and writes a complete static site.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import images  # noqa: E402
import templates as t  # noqa: E402
from content import WARNINGS, ContentError, load_all  # noqa: E402

try:  # Optional: smaller files when the minifiers are installed.
    from rcssmin import cssmin
    from rjsmin import jsmin
except ImportError:  # pragma: no cover
    cssmin = jsmin = None

DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
JS_FILES = ["core", "shelf", "home", "library", "article", "listen", "contact"]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_assets() -> str:
    """Concatenate CSS, minify JS, copy fonts. Returns a short content hash for cache-busting."""
    css = "\n".join(p.read_text(encoding="utf-8") for p in sorted((ASSETS / "css").glob("*.css")))
    css = cssmin(css) if cssmin else css
    write(DIST / "assets" / "css" / "site.css", css)

    digest = hashlib.sha1(css.encode())
    for name in JS_FILES:
        source = (ASSETS / "js" / f"{name}.js").read_text(encoding="utf-8")
        out = jsmin(source) if jsmin else source
        write(DIST / "assets" / "js" / f"{name}.js", out)
        digest.update(out.encode())

    shutil.copytree(ASSETS / "fonts", DIST / "assets" / "fonts")
    return digest.hexdigest()[:8]


def report_content(essays: list) -> None:
    """Say clearly which essays were published and which were skipped (and why).

    On GitHub this shows as yellow warnings on the run and a summary on its page.
    """
    for name, message in WARNINGS:
        print(f"::warning file={name},title=Essay skipped::{message}")
        print(f"SKIPPED {name}: {message}", file=sys.stderr)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    lines = [f"### Deep Calls build\n", f"Published **{len(essays)}** essays.\n"]
    if WARNINGS:
        lines.append(f"**{len(WARNINGS)} file(s) were skipped** (the rest still published). Fix and commit to include them:\n")
        lines += [f"- `{name}`: {message}" for name, message in WARNINGS]
    with open(summary, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    config = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    try:
        essays = load_all(ROOT / "content", config)
    except ContentError as err:
        print(f"\nContent problem: {err}\n", file=sys.stderr)
        return 1
    report_content(essays)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    version = build_assets()
    site = t.Site(config, essays, version)

    # Pages
    write(DIST / "index.html", t.build_home(site))
    write(DIST / "library.html", t.build_library(site))
    write(DIST / "about.html", t.build_about(site))
    write(DIST / "contact.html", t.build_contact(site))
    write(DIST / "404.html", t.build_404(site))
    for essay in site.essays:
        write(DIST / essay.url, t.build_essay(site, essay))

    # Search index (loaded on demand by the Ctrl/Cmd+K palette)
    index = [
        {"t": e.title, "u": e.url, "c": e.category, "s": e.subtitle, "e": e.excerpt, "v": t.plain(e.verse_ref_html), "m": e.minutes, "f": 1 if e.featured else 0}
        for e in site.essays
    ]
    write(DIST / "assets" / "search.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))

    # SEO and app files
    urls = [(site.url, "")] + [(site.abs(p), "") for p in ("library.html", "about.html", "contact.html")]
    urls += [(site.abs(e.url), e.date) for e in site.essays]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        sitemap.append(f"  <url><loc>{t.esc(loc)}</loc>{f'<lastmod>{lastmod}</lastmod>' if lastmod else ''}</url>")
    sitemap.append("</urlset>")
    write(DIST / "sitemap.xml", "\n".join(sitemap) + "\n")
    write(DIST / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {site.abs('sitemap.xml')}\n")

    manifest = {
        "name": f"{site.name}: {site.tagline}",
        "short_name": site.name,
        "description": site.tagline,
        "id": site.base_path,
        "start_url": site.base_path,
        "scope": site.base_path,
        "display": "standalone",
        "background_color": "#f6f4ee",
        "theme_color": "#0a2a2e",
        "icons": [
            {"src": "assets/img/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "assets/img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            {"src": "favicon.svg", "sizes": "any", "type": "image/svg+xml"},
        ],
    }
    write(DIST / "site.webmanifest", json.dumps(manifest, indent=2) + "\n")

    # Brand imagery: icons and social cards
    images.write_icons(DIST)
    images.write_card(DIST / "assets" / "og" / "default.png", "Faith that survives the hard questions.", "A library of long form essays", site.name, site.host)
    for essay in site.essays:
        images.write_card(DIST / "assets" / "og" / f"{essay.slug}.png", essay.title, essay.category, site.name, site.host)

    print(f"Built {len(site.essays)} essays and 5 pages into {DIST.relative_to(ROOT)}/ (assets v{version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
