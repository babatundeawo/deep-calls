"""HTML templates for every page type.

Pages are plain f-strings: no template engine to learn or break. All text that
comes from content files is escaped with ``esc`` unless it is already trusted
HTML produced by the Markdown renderer.

Security note: pages are served from GitHub Pages, which cannot send custom
HTTP headers, so a Content-Security-Policy is delivered via a <meta> tag. No
inline scripts or inline style attributes are used (except the one tiny theme
script, which is allowed by hash), so the policy can stay strict.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import re
from urllib.parse import quote, urlparse

from content import Essay
from icons import IconSet

# Runs before first paint: sets the theme (no flash) and marks the page as JS-enabled.
THEME_INIT = (
    "(function(){var d=document.documentElement;d.className=d.className.replace('no-js','js');"
    "try{var t=localStorage.getItem('deepcalls-theme');"
    "if(t!=='light'&&t!=='dark'){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}"
    "d.setAttribute('data-theme',t)}catch(e){d.setAttribute('data-theme','light')}})();"
)
THEME_INIT_HASH = "sha256-" + base64.b64encode(hashlib.sha256(THEME_INIT.encode()).digest()).decode()

CSP = "; ".join(
    [
        "default-src 'self'",
        f"script-src 'self' '{THEME_INIT_HASH}'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self' mailto:",
        "manifest-src 'self'",
    ]
)

FONTS_PRELOAD = ["fraunces-latin.woff2", "literata-latin.woff2"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def plain(html_fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", html_fragment))).strip()


def ld_json(data: dict) -> str:
    """JSON-LD safe to embed inside a <script> element."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


class Site:
    """Everything a template needs to know about the whole site."""

    def __init__(self, config: dict, essays: list[Essay], version: str) -> None:
        self.cfg = config
        self.name: str = config["name"]
        self.tagline: str = config["tagline"]
        self.url: str = config["url"].rstrip("/") + "/"
        self.base_path: str = urlparse(self.url).path  # "/deep-calls/" or "/" for a custom domain
        self.host: str = urlparse(self.url).netloc + (self.base_path.rstrip("/") or "")
        self.version = version
        self.has_dates = any(e.date for e in essays)

        # Library order: featured first (by their number), then A-Z by title.
        self.essays = sorted(essays, key=lambda e: (e.featured == 0, e.featured, e.title.lower()))
        self.by_slug = {e.slug: e for e in self.essays}
        self.featured = [e for e in self.essays if e.featured]

        listed = list(config.get("categories", []))
        found = sorted({e.category for e in essays} - set(listed))
        self.categories = [c for c in listed if any(e.category == c for e in essays)] + found
        self.hue = {name: (i % 8) + 1 for i, name in enumerate(listed + found)}
        self.cat_count = {c: sum(1 for e in essays if e.category == c) for c in self.categories}
        self.total_words = sum(e.words for e in essays)
        self.total_minutes = sum(e.minutes for e in essays)

    # ---- URLs ----
    def abs(self, path: str = "") -> str:
        return self.url + path

    def cat_href(self, rp: str, category: str) -> str:
        return f"{rp}library.html?cat={quote(category)}"


# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------

MARK = (
    '<svg class="brand__mark" viewBox="0 0 48 48" aria-hidden="true" focusable="false">'
    '<rect class="mark-bg" width="48" height="48" rx="11"/>'
    '<path class="mark-ring" d="M13.4 10.4H23a13.6 13.6 0 0 1 0 27.2H13.4z"/>'
    '<path class="mark-gap" d="M16.6 13.6H23a10.4 10.4 0 0 1 0 20.8h-6.4z"/>'
    '<path class="mark-core" d="M19.2 18H23a6 6 0 0 1 0 12h-3.8z"/></svg>'
)

NAV = [
    ("home", "Home", "index.html"),
    ("library", "Library", "library.html"),
    ("about", "About", "about.html"),
    ("contact", "Contact", "contact.html"),
]


def brand(site: Site, rp: str) -> str:
    return f'<a class="brand" href="{rp}index.html" aria-label="{esc(site.name)}, home">{MARK}<span class="brand__name">{esc(site.name)}</span></a>'


def header(site: Site, rp: str, current: str | None, icon: IconSet) -> str:
    links = "".join(
        f'<li><a class="nav__link" href="{rp}{href}"{" aria-current=\"page\"" if key == current else ""}>{label}</a></li>'
        for key, label, href in NAV
    )
    return f"""<header class="site-header" data-scrolled="false">
  <div class="container nav">
    {brand(site, rp)}
    <nav aria-label="Primary">
      <ul class="nav__links">{links}</ul>
    </nav>
    <div class="nav__actions">
      <a class="search-trigger" href="{rp}library.html" data-search-open aria-keyshortcuts="Control+K Meta+K">{icon('search')}<span class="search-trigger__label">Search</span><kbd data-kbd-hint aria-hidden="true">Ctrl K</kbd></a>
      <button type="button" class="icon-btn theme-toggle" data-theme-toggle data-js-only aria-label="Dark mode" aria-pressed="false">{icon('sun', 'i-sun')}{icon('moon', 'i-moon')}</button>
    </div>
  </div>
</header>"""


TABS = [
    ("home", "Home", "index.html", "home"),
    ("library", "Library", "library.html", "book"),
    ("saved", "Saved", "library.html?saved=1", "bookmark"),
    ("about", "About", "about.html", "compass"),
]


def tabbar(rp: str, current: str | None, icon: IconSet) -> str:
    """Bottom tab bar for small screens. Plain links, so it works without JS."""
    items = []
    for key, label, href, ico in TABS:
        badge = '<span class="tabbar__badge" data-saved-count hidden>0</span>' if key == "saved" else ""
        cur = ' aria-current="page"' if key == current else ""
        items.append(f'<a class="tabbar__link" href="{rp}{href}"{cur}>{icon(ico)}<span>{label}</span>{badge}</a>')
    return f'<nav class="tabbar" aria-label="Quick navigation">{"".join(items)}</nav>'


def footer(site: Site, rp: str, icon: IconSet) -> str:
    cats = "".join(
        f'<li><a href="{site.cat_href(rp, c)}">{esc(c)}</a></li>' for c in site.categories
    )
    email = esc(site.cfg["email"])
    return f"""<footer class="site-footer on-ink">
  <div class="container">
    <div class="footer__grid">
      <div class="footer__brand">
        {brand(site, rp)}
        <p>Essays on scripture, doubt, and the God who is never in a hurry. Written for the curious, the sceptical, and the tired.</p>
      </div>
      <nav aria-label="Footer">
        <h2 class="footer__title">Explore</h2>
        <ul class="footer__list">
          <li><a href="{rp}index.html">Home</a></li>
          <li><a href="{rp}library.html">Full library</a></li>
          <li><a href="{rp}about.html">About this project</a></li>
          <li><a href="{rp}contact.html">Contact</a></li>
        </ul>
      </nav>
      <div>
        <h2 class="footer__title">Themes</h2>
        <ul class="footer__list">{cats}</ul>
      </div>
    </div>
    <div class="footer__base">
      <span>&copy; <span data-year>{_year()}</span> {esc(site.name)}. Soli Deo Gloria.</span>
      <span><a href="{esc(site.cfg['github'])}" rel="noopener noreferrer">GitHub</a> &middot; <a href="mailto:{email}">{email}</a></span>
    </div>
  </div>
</footer>"""


def _year() -> int:
    import datetime

    return datetime.date.today().year


def head(
    site: Site,
    *,
    title: str,
    description: str,
    path: str,
    rp: str,
    icon_set: IconSet,
    og_image: str,
    og_alt: str,
    og_type: str = "website",
    noindex: bool = False,
    schema: list[dict] | None = None,
    extra_scripts: list[str] | None = None,
) -> str:
    canonical = site.abs(path)
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large"
    full_title = title if title == site.name else f"{title} | {site.name}"
    if title == site.name:
        full_title = f"{site.name} | {site.tagline}"
    og_url = site.abs(og_image)
    preloads = "\n".join(
        f'<link rel="preload" href="{rp}assets/fonts/{f}" as="font" type="font/woff2" crossorigin>' for f in FONTS_PRELOAD
    )
    schema_tags = "\n".join(f'<script type="application/ld+json">{ld_json(s)}</script>' for s in (schema or []))
    canonical_tag = "" if noindex else f'<link rel="canonical" href="{esc(canonical)}">'
    og_url_tag = "" if noindex else f'<meta property="og:url" content="{esc(canonical)}">'
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="{robots}">
{canonical_tag}
<meta http-equiv="Content-Security-Policy" content="{esc(CSP)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f6f4ee" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#061a1c" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(site.name)}">
<meta property="og:locale" content="{esc(site.cfg['locale'])}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
{og_url_tag}
<meta property="og:image" content="{esc(og_url)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(full_title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_url)}">
<link rel="icon" href="{rp}favicon.ico" sizes="48x48">
<link rel="icon" href="{rp}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{rp}apple-touch-icon.png">
<link rel="manifest" href="{rp}site.webmanifest">
{preloads}
<link rel="stylesheet" href="{rp}assets/css/site.css?v={site.version}">
<script>{THEME_INIT}</script>
{schema_tags}"""


def page(
    site: Site,
    *,
    title: str,
    description: str,
    path: str,
    rp: str,
    current: str | None,
    body: str,
    icon: IconSet,
    scripts: list[str] | None = None,
    og_image: str = "assets/og/default.png",
    og_alt: str | None = None,
    og_type: str = "website",
    noindex: bool = False,
    schema: list[dict] | None = None,
    root_attr: str | None = None,
    body_class: str = "",
) -> str:
    """Wrap a page body in the shared document shell."""
    icon.need("search", "arrow-up", "sun", "moon", "home", "book", "bookmark", "compass")
    header_html = header(site, rp, current, icon)
    footer_html = footer(site, rp, icon)
    script_tags = "\n".join(
        f'<script src="{rp}assets/js/{name}.js?v={site.version}" defer></script>' for name in ["core", "shelf", *(scripts or [])]
    )
    head_html = head(
        site,
        title=title,
        description=description,
        path=path,
        rp=rp,
        icon_set=icon,
        og_image=og_image,
        og_alt=og_alt or f"{site.name}: {site.tagline}",
        og_type=og_type,
        noindex=noindex,
        schema=schema,
    )
    body_html = f"""<a class="skip-link" href="#main">Skip to content</a>
{header_html}
<main id="main" tabindex="-1">
{body}
</main>
{footer_html}
{tabbar(rp, current, icon)}
<button type="button" class="to-top" data-to-top data-show="false" aria-label="Back to top">{icon('arrow-up')}</button>
<div class="toast" data-toast role="status" aria-live="polite"></div>
{icon.sprite()}
{script_tags}"""
    return f"""<!doctype html>
<html lang="{esc(site.cfg['language'])}" class="no-js" data-root="{esc(root_attr if root_attr is not None else rp)}">
<head>
{head_html}
</head>
<body{f' class="{body_class}"' if body_class else ''}>
{body_html}
</body>
</html>
"""


def breadcrumb(items: list[tuple[str, str | None]]) -> str:
    lis = []
    for label, href in items:
        if href:
            lis.append(f'<li><a href="{href}">{esc(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{esc(label)}</li>')
    return f'<nav class="breadcrumb" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'


def essay_card(site: Site, e: Essay, rp: str, icon: IconSet, *, variant: str = "", reveal: bool = True, data: bool = False, level: int = 3) -> str:
    cls = "card" + (f" card--{variant}" if variant else "")
    extra = ""
    if data:
        extra = (
            f' data-essay data-cat="{esc(e.category)}" data-hay="{esc(e.search_text)}"'
            f' data-title="{esc(e.title)}" data-min="{e.minutes}" data-featured="{1 if e.featured else 0}"'
            f' data-date="{esc(e.date)}"'
        )
    art = ""
    if variant == "feature":
        circles = "".join(f'<circle cx="260" cy="0" r="{r}"/>' for r in range(50, 400, 55))
        art = f'<div class="card__art" aria-hidden="true"><svg viewBox="0 0 260 260">{circles}</svg></div>'
    return f"""<a class="{cls}" href="{rp}{e.url}" data-slug="{esc(e.slug)}" data-hue="{site.hue[e.category]}"{' data-reveal' if reveal else ''}{extra}>
  {art}<span class="tag">{esc(e.category)}</span>
  <h{level} class="card__title">{esc(e.title)}</h{level}>
  <p class="card__excerpt">{esc(e.excerpt)}</p>
  <div class="card__foot"><span>{e.minutes} min read</span><span class="card__go">Read {icon('arrow-right')}</span></div>
</a>"""


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

def build_home(site: Site) -> str:
    icon = IconSet()
    rp = ""
    icon.need("arrow-right", "pause", "play", "quill", "compass", "anchor")

    verses = [e for e in site.featured if e.verse_html and e.verse_ref_html][:6]
    slides = "".join(
        f"""<figure class="verse" data-active="{'true' if i == 0 else 'false'}">
          <blockquote class="verse__text">{e.verse_html}</blockquote>
          <figcaption class="verse__cite">{e.verse_ref_html}<br><a class="verse__link" href="{e.url}">From &ldquo;{esc(e.title)}&rdquo;</a></figcaption>
        </figure>"""
        for i, e in enumerate(verses)
    )
    dots = "".join(
        f'<button type="button" class="verse-panel__dot" data-verse-dot data-js-only aria-label="Show verse {i + 1}" aria-current="{"true" if i == 0 else "false"}"></button>'
        for i in range(len(verses))
    )

    big, *rest = site.featured[:6]
    cards = essay_card(site, big, rp, icon, variant="feature") + "".join(essay_card(site, e, rp, icon) for e in rest)

    themes = "".join(
        f"""<li class="theme-row"><a href="{site.cat_href(rp, c)}" data-hue="{site.hue[c]}" data-reveal>
          <span class="theme-row__dot" aria-hidden="true"></span><span class="theme-row__name">{esc(c)}</span>
          <span class="theme-row__count">{site.cat_count[c]} {'essay' if site.cat_count[c] == 1 else 'essays'}</span>{icon('arrow-right')}</a></li>"""
        for c in site.categories
    )

    n = len(site.essays)
    body = f"""
<section class="hero">
  <div class="container hero__grid">
    <div>
      <p class="eyebrow">A library of long form essays</p>
      <h1>Faith that survives <em>the hard questions.</em></h1>
      <p class="hero__lede">{esc(site.tagline)} Essays on scripture, doubt, culture, and the God who draws in curves. They are written to be read slowly, argued with, and returned to.</p>
      <div class="hero__actions">
        <a class="btn" href="library.html">Browse the library {icon('arrow-right', 'i--arrow')}</a>
        <a class="btn btn--outline" href="about.html">What this is</a>
      </div>
    </div>
    <aside class="verse-panel on-ink" data-verses aria-label="Scripture from the essays">
      <svg class="verse-panel__echo" viewBox="0 0 600 600" aria-hidden="true" focusable="false">{"".join(f'<circle cx="300" cy="300" r="{r}"/>' for r in range(40, 300, 38))}</svg>
      <p class="verse-panel__label">Scripture, from the essays</p>
      <div class="verse-panel__slides" data-verse-live aria-live="off">{slides}</div>
      <div class="verse-panel__controls">
        <div class="verse-panel__dots">{dots}</div>
        <button type="button" class="icon-btn verse-panel__pause" data-verse-pause data-js-only aria-label="Pause verse rotation" aria-pressed="false">{icon('pause', 'i-pause')}{icon('play', 'i-play')}</button>
      </div>
    </aside>
  </div>
</section>

<div class="container">
  <div class="stats" aria-label="The library at a glance">
    <div class="stat"><span class="stat__num">{n}</span><span class="stat__label">Essays</span></div>
    <div class="stat"><span class="stat__num">{site.total_words:,}</span><span class="stat__label">Words written</span></div>
    <div class="stat"><span class="stat__num">{site.total_minutes}</span><span class="stat__label">Minutes of reading</span></div>
    <div class="stat"><span class="stat__num">{len(site.categories)}</span><span class="stat__label">Themes</span></div>
  </div>
</div>

<div class="container" data-continue hidden></div>

<section class="section" id="start">
  <div class="container">
    <div class="section-head" data-reveal>
      <h2>Start here</h2>
      <p>A handful of essays to begin with. The full, searchable library of {n} essays across {len(site.categories)} themes lives on its own page.</p>
    </div>
    <div class="bento">{cards}</div>
    <p class="actions actions--center"><a class="btn btn--outline" href="library.html">Browse all {n} essays {icon('arrow-right', 'i--arrow')}</a></p>
  </div>
</section>

<section class="section" id="themes">
  <div class="container">
    <div class="section-head" data-reveal>
      <h2>Browse by theme</h2>
    </div>
    <ul class="themes">{themes}</ul>
  </div>
</section>

<section class="statement on-ink" id="why">
  <div class="container statement__grid">
    <div data-reveal>
      <p class="eyebrow">Why this exists</p>
      <h2>Not a sermon. Not a comment-section reply. <em>A real answer, slowly built.</em></h2>
    </div>
    <div data-reveal>
      <p>Most writing about faith online is built for a scroll: a quote card, a hot take, a clip stripped of its argument. Deep Calls is the opposite bet: essays long enough to actually make a case, quiet enough to sit with, honest enough to name the hard parts of the question before offering an answer.</p>
      <p>Every piece here starts with a real question someone actually asked, whether at a vigil, in a comment section or over a meal after service, and tries to answer it the way it deserves: with scripture, with history, with logic, and without pretending the question was easy.</p>
      <ul class="principles">
        <li><span><strong>Written to be argued with.</strong> Every essay engages the strongest version of the counter-argument, not a strawman.</span></li>
        <li><span><strong>Scripture first.</strong> Claims are traced back to the text, not just asserted from the pulpit.</span></li>
        <li><span><strong>Built for the long haul.</strong> No clickbait and no countdown timers, just essays meant to be read twice.</span></li>
      </ul>
      <a class="btn btn--on-ink" href="about.html">Read the full story {icon('arrow-right', 'i--arrow')}</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="cta" data-reveal>
      <div>
        <h2>Have a question that deserves an essay?</h2>
        <p>Every essay here started as a real question from a real person. If you have one, send it, and it might become the next writeup.</p>
      </div>
      <a class="btn" href="contact.html">Get in touch {icon('arrow-right', 'i--arrow')}</a>
    </div>
  </div>
</section>
"""
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site.name,
            "description": site.tagline,
            "url": site.url,
            "inLanguage": site.cfg["language"],
            "potentialAction": {
                "@type": "SearchAction",
                "target": {"@type": "EntryPoint", "urlTemplate": f"{site.url}library.html?q={{search_term_string}}"},
                "query-input": "required name=search_term_string",
            },
        }
    ]
    return page(
        site,
        title=site.name,
        description=f"{site.tagline} {len(site.essays)} essays on scripture, doubt and culture, written to be read slowly and argued with.",
        path="",
        rp=rp,
        current="home",
        body=body,
        icon=icon,
        scripts=["home"],
        schema=schema,
    )


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------

def build_library(site: Site) -> str:
    icon = IconSet()
    rp = ""
    icon.need("search", "empty", "arrow-right", "shuffle")
    n = len(site.essays)
    chips = '<button type="button" class="chip" data-chip="" aria-pressed="true">All essays</button><button type="button" class="chip chip--saved" data-chip-saved aria-pressed="false">Saved <span class="chip__count" data-saved-count>0</span></button>' + "".join(
        f'<button type="button" class="chip" data-chip="{esc(c)}" data-hue="{site.hue[c]}" aria-pressed="false">{esc(c)} <span class="chip__count">{site.cat_count[c]}</span></button>'
        for c in site.categories
    )
    sort_options = [("featured", "Featured first")]
    if site.has_dates:
        sort_options.append(("newest", "Newest first"))
    sort_options += [("az", "Title, A to Z"), ("quick", "Quickest read"), ("long", "Longest read")]
    options = "".join(f'<option value="{v}">{l}</option>' for v, l in sort_options)
    cards = "".join(essay_card(site, e, rp, icon, reveal=False, data=True, level=2) for e in site.essays)

    body = f"""
<div class="container page-hero">
  {breadcrumb([("Home", "index.html"), ("Library", None)])}
  <p class="eyebrow">The full archive</p>
  <h1>Every essay, in one place.</h1>
  <p class="page-hero__lede">Search by title or theme, or filter by category. New writeups are added here as they&rsquo;re written.</p>
  <p class="page-hero__actions" data-js-only><button type="button" class="btn btn--outline btn--sm" data-surprise>{icon('shuffle')}Surprise me</button></p>
</div>

<section class="container">
  <div class="toolbar" role="search" aria-label="Filter essays">
    <div class="toolbar__row">
      <div class="search-field">
        {icon('search')}
        <label class="sr-only" for="q">Search essays</label>
        <input class="control" id="q" type="search" data-q data-js-only placeholder="Search essays: try &ldquo;hell&rdquo;, &ldquo;Esther&rdquo;, &ldquo;Islam&rdquo;" autocomplete="off">
      </div>
      <label class="sort" data-js-only>Sort <select class="control" data-sort>{options}</select></label>
    </div>
    <div class="chips" role="group" aria-label="Filter by theme" data-js-only>{chips}</div>
  </div>
  <p class="result-count" data-count role="status" aria-live="polite">{n} essays</p>
  <div class="grid" data-grid>{cards}</div>
  <div class="empty" data-empty data-show="false">
    {icon('empty')}
    <h2>Nothing matches that yet</h2>
    <p data-empty-text>Try a different word, or clear the filters to see everything.</p>
    <button type="button" class="btn btn--outline btn--sm" data-clear>Clear filters</button>
  </div>
</section>
"""
    return page(
        site,
        title="Library",
        description=f"Browse all {n} Deep Calls essays. Search by title or theme, or filter by category.",
        path="library.html",
        rp=rp,
        current="library",
        body=body,
        icon=icon,
        scripts=["library"],
        schema=[
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": f"{site.name} library",
                "url": site.abs("library.html"),
                "hasPart": [{"@type": "Article", "name": e.title, "url": site.abs(e.url)} for e in site.essays],
            }
        ],
    )


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------

def build_about(site: Site) -> str:
    icon = IconSet()
    rp = ""
    icon.need("quill", "compass", "anchor", "shield", "scroll", "heart", "arrow-right")
    n = len(site.essays)
    values = [
        ("quill", "Argued with, not around", "Every essay engages the strongest version of the counter-argument, not a strawman built to lose."),
        ("compass", "Scripture first", "Claims are traced back to the text itself, not just asserted from the pulpit or assumed as background."),
        ("anchor", "Built for the long haul", "No clickbait, no countdown timers, no manufactured outrage. Essays meant to be read twice."),
        ("shield", "Honest about doubt", "The hard parts of a question get named plainly before an answer is offered, not buried under certainty."),
        ("scroll", "Long form on purpose", "Some things can’t be said in a caption. These essays take the space the question actually needs."),
        ("heart", "Written for real people", "Every essay starts from an actual question someone asked, not a hypothetical and not a strawman."),
    ]
    value_html = "".join(
        f'<div class="value" data-reveal>{icon(i)}<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for i, t, d in values
    )
    steps = [
        ("A real question", "Every essay starts with something someone actually asked, in a comment section, at a vigil or over a meal after church."),
        ("Scripture and sources", "The text is read slowly, cross-referenced, and checked against history and theology, and, where the topic touches current events, against current reporting."),
        ("The strongest counter-case", "Before an answer is written, the best version of the opposing view gets a fair hearing. Weak arguments don’t get the final word."),
        ("A slow draft", "Long form and unhurried, written to be read twice and not skimmed once."),
    ]
    step_html = "".join(f"<li data-reveal><h3>{esc(t)}</h3><p>{esc(d)}</p></li>" for t, d in steps)

    body = f"""
<div class="container page-hero">
  {breadcrumb([("Home", "index.html"), ("About", None)])}
  <p class="eyebrow">Why this exists</p>
  <h1>Not a sermon. Not a comment-section reply.</h1>
  <p class="page-hero__lede">A real answer, slowly built, for the curious, the sceptical and the tired.</p>
</div>

<section class="container--narrow">
  <div class="prose-lg">
    <p>Most writing about faith online is built for a scroll: a quote card, a hot take, a clip stripped of its argument. Deep Calls is the opposite bet: essays long enough to actually make a case, quiet enough to sit with, honest enough to name the hard parts of the question before offering an answer.</p>
    <p>Every piece here starts with a real question someone actually asked, whether at a vigil, in a comment section or over a meal after service, and tries to answer it the way it deserves: with scripture, with history, with logic, and without pretending the question was easy.</p>
  </div>
</section>

<div class="container">
  <div class="stats stats--spaced" aria-label="The library at a glance">
    <div class="stat"><span class="stat__num">{n}</span><span class="stat__label">Essays</span></div>
    <div class="stat"><span class="stat__num">{site.total_words:,}</span><span class="stat__label">Words written</span></div>
    <div class="stat"><span class="stat__num">{site.total_minutes}</span><span class="stat__label">Minutes of reading</span></div>
    <div class="stat"><span class="stat__num">{len(site.categories)}</span><span class="stat__label">Themes</span></div>
  </div>
  <h2 class="sr-only">What guides every essay</h2>
  <div class="values">{value_html}</div>
</div>

<section class="container--narrow">
  <h2 class="eyebrow">How a writeup gets made</h2>
  <ol class="steps">{step_html}</ol>
  <div class="actions actions--center">
    <a class="btn" href="library.html">Start reading {icon('arrow-right', 'i--arrow')}</a>
    <a class="btn btn--outline" href="contact.html">Get in touch</a>
  </div>
</section>
"""
    return page(
        site,
        title="About",
        description="Why Deep Calls exists, how each essay gets written, and what it means to take a hard question seriously.",
        path="about.html",
        rp=rp,
        current="about",
        body=body,
        icon=icon,
    )


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

def build_contact(site: Site) -> str:
    icon = IconSet()
    rp = ""
    icon.need("mail", "github", "clock", "map-pin", "arrow-right", "alert", "copy")
    email = esc(site.cfg["email"])
    body = f"""
<div class="container page-hero">
  {breadcrumb([("Home", "index.html"), ("Contact", None)])}
  <p class="eyebrow">Get in touch</p>
  <h1>Ask a question. Suggest a topic. Point out a mistake.</h1>
  <p class="page-hero__lede">Every essay here started as a real question from a real person. If you have one, send it, and it might become the next writeup.</p>
</div>

<section class="container contact-grid">
  <div>
    <form data-contact-form data-to="{email}" action="mailto:{email}" method="post" enctype="text/plain" novalidate>
      <div class="field-row">
        <div class="field">
          <label for="name">Your name</label>
          <input class="control" id="name" name="name" type="text" autocomplete="name" required aria-describedby="name-err">
          <span class="field__error" id="name-err" role="alert"></span>
        </div>
        <div class="field">
          <label for="email">Your email</label>
          <input class="control" id="email" name="email" type="email" autocomplete="email" required aria-describedby="email-err">
          <span class="field__error" id="email-err" role="alert"></span>
        </div>
      </div>
      <div class="field">
        <label for="topic">What&rsquo;s this about</label>
        <select class="control" id="topic" name="topic">
          <option>A question about an essay</option>
          <option>A topic suggestion</option>
          <option>A correction or factual note</option>
          <option>Something else</option>
        </select>
      </div>
      <div class="field">
        <label for="message">Your message</label>
        <textarea class="control" id="message" name="message" required aria-describedby="message-err"></textarea>
        <span class="field__error" id="message-err" role="alert"></span>
      </div>
      <button type="submit" class="btn">Send message {icon('arrow-right', 'i--arrow')}</button>
      <p class="form-note">This opens your email app with the message pre-filled. Deep Calls is a static site with no server, so nothing is stored here.</p>
    </form>
    <div class="sent" data-sent tabindex="-1" data-show="false">
      <div class="notice notice--info"><p><strong>Your email app should be opening.</strong> If nothing happened, you can send it another way.</p></div>
      <div class="sent__actions">
        <a class="btn btn--outline btn--sm" data-mailto href="mailto:{email}">Open in email app</a>
        <button type="button" class="btn btn--outline btn--sm" data-copy-message>{icon('copy')} Copy message</button>
      </div>
    </div>
  </div>

  <aside class="contact-card">
    <h2>Other ways to reach out</h2>
    <p>Prefer email directly, or want to browse first? Here&rsquo;s where things live.</p>
    <ul class="contact-list">
      <li>{icon('mail')}<span><a href="mailto:{email}">{email}</a><small>General questions and corrections</small></span></li>
      <li>{icon('github')}<span><a href="{esc(site.cfg['github'])}" rel="noopener noreferrer">{esc(site.cfg['github'].replace('https://', ''))}</a><small>Code, other projects, and issues</small></span></li>
      <li>{icon('clock')}<span><strong>Usually within a few days</strong><small>This is a one-person project, written in the margins of a week</small></span></li>
      <li>{icon('map-pin')}<span><strong>Written from Nigeria</strong><small>For readers everywhere asking the same hard questions</small></span></li>
    </ul>
  </aside>
</section>
"""
    return page(
        site,
        title="Contact",
        description="Send a question, a correction, or a topic suggestion to Deep Calls.",
        path="contact.html",
        rp=rp,
        current="contact",
        body=body,
        icon=icon,
        scripts=["contact"],
    )


# ---------------------------------------------------------------------------
# 404
# ---------------------------------------------------------------------------

def build_404(site: Site) -> str:
    icon = IconSet()
    rp = site.base_path  # absolute, because this page is served from any missing URL
    icon.need("arrow-right", "search")
    body = f"""
<div class="container lost">
  <span class="lost__code" aria-hidden="true">404</span>
  <h1>Lost the plot.</h1>
  <p>This page doesn&rsquo;t exist, or it wandered off somewhere in the archive. Let&rsquo;s get you back on solid ground.</p>
  <div class="actions actions--center">
    <a class="btn" href="{rp}library.html">Back to the library {icon('arrow-right', 'i--arrow')}</a>
    <a class="btn btn--outline" href="{rp}index.html">Go home</a>
  </div>
</div>
"""
    return page(
        site,
        title="Page not found",
        description="This page wandered off. Let’s get you back to the library.",
        path="404.html",
        rp=rp,
        current=None,
        body=body,
        icon=icon,
        noindex=True,
    )


# ---------------------------------------------------------------------------
# Essay
# ---------------------------------------------------------------------------

def related(site: Site, e: Essay, count: int = 3) -> list[Essay]:
    """Other essays from the same theme first (wrapping around A-Z), then the rest."""
    same = [x for x in site.essays if x.category == e.category and x.slug != e.slug]
    same.sort(key=lambda x: x.title.lower())
    # Start after the current title so each essay points to a different neighbour.
    after = [x for x in same if x.title.lower() > e.title.lower()] + [x for x in same if x.title.lower() <= e.title.lower()]
    others = [x for x in site.essays if x.category != e.category]
    start = site.essays.index(e)
    others = others[start % max(1, len(others)):] + others[: start % max(1, len(others))]
    return (after + others)[:count]


def build_essay(site: Site, e: Essay) -> str:
    icon = IconSet()
    rp = "../"
    icon.need("clock", "chevron-down", "share", "link", "whatsapp", "copy", "arrow-right", "calendar", "bookmark", "type", "arrow-left")
    url = site.abs(e.url)
    enc_url, enc_title = quote(url, safe=""), quote(e.title, safe="")

    toc = ""
    if len(e.toc) >= 3:
        items = "".join(f'<li><a href="#{esc(i)}">{esc(t)}</a></li>' for i, t in e.toc)
        toc = f"""<nav aria-label="In this essay"><details class="toc" data-toc open>
        <summary>In this essay {icon('chevron-down')}</summary><ol>{items}</ol></details></nav>"""

    sub = f'<p class="essay-head__sub">{esc(e.subtitle)}</p>' if e.subtitle else ""
    date_li = ""
    if e.date:
        date_li = f'<li>{icon("calendar")}<time datetime="{e.date}">{_fmt_date(e.date)}</time></li>'
    epigraph = ""
    if e.verse_html:
        cite = f"<figcaption><cite>{e.verse_ref_html}</cite></figcaption>" if e.verse_ref_html else ""
        epigraph = f'<figure class="epigraph"><blockquote><p>&ldquo;{e.verse_html}&rdquo;</p></blockquote>{cite}</figure>'

    more_cards = "".join(essay_card(site, x, rp, icon) for x in related(site, e))
    desc = e.description

    body = f"""
<div class="progress" aria-hidden="true"><span class="progress__bar" data-progress></span></div>
<article data-essay-page data-slug="{esc(e.slug)}" data-title="{esc(e.title)}">
<div class="container essay-head">
  <a class="back" href="{rp}library.html">{icon('arrow-left')}Library</a>
  <a class="tag" href="{site.cat_href(rp, e.category)}" data-hue="{site.hue[e.category]}">{esc(e.category)}</a>
  <h1>{esc(e.title)}</h1>
  {sub}
  <ul class="essay-meta">
    <li>{icon('clock')}{e.minutes} min read</li>
    {date_li}
  </ul>
  {epigraph}
  <div class="essay-tools">
    <div class="essay-tools__row">
      <button type="button" class="btn btn--outline btn--sm save-btn" data-save="{esc(e.slug)}" data-js-only aria-pressed="false">{icon('bookmark')}<span data-save-label>Save for later</span></button>
      <div class="textsize" data-textsize data-js-only role="group" aria-label="Text size">
        <button type="button" class="icon-btn" data-textsize-step="-1" aria-label="Smaller text"><span aria-hidden="true">A</span></button>
        <button type="button" class="icon-btn" data-textsize-step="1" aria-label="Larger text"><span aria-hidden="true" class="textsize__big">A</span></button>
      </div>
    </div>
  </div>
</div>

<div class="container essay-layout">
  {toc}
  <div>
    <div class="prose" data-prose>
{e.body_html}
    </div>
    <div class="essay-end">
      <div class="share">
        <span class="share__label">Share this essay</span>
        <button type="button" class="icon-btn" data-share-native data-tip="Share" aria-label="Share">{icon('share')}</button>
        <button type="button" class="icon-btn" data-copy-link data-tip="Copy link" aria-label="Copy link">{icon('link')}</button>
        <a class="icon-btn" data-tip="Share on WhatsApp" aria-label="Share on WhatsApp (opens in a new tab)" target="_blank" rel="noopener noreferrer" href="https://wa.me/?text={enc_title}%20{enc_url}">{icon('whatsapp')}</a>
      </div>
    </div>
  </div>
</div>
</article>

<section class="container more" aria-labelledby="more-h">
  <div class="more__head"><h2 id="more-h">Keep reading</h2><a class="link" href="{rp}library.html">Full library</a></div>
  <div class="grid">{more_cards}</div>
</section>
"""
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": e.title,
        "description": desc,
        "wordCount": e.words,
        "articleSection": e.category,
        "inLanguage": site.cfg["language"],
        "url": url,
        "mainEntityOfPage": url,
        "image": site.abs(f"assets/og/{e.slug}.png"),
        "publisher": {"@type": "Organization", "name": site.name, "url": site.url},
    }
    if e.date:
        article["datePublished"] = e.date
    if site.cfg.get("author"):
        article["author"] = {"@type": "Person", "name": site.cfg["author"]}
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": site.url},
            {"@type": "ListItem", "position": 2, "name": "Library", "item": site.abs("library.html")},
            {"@type": "ListItem", "position": 3, "name": e.title, "item": url},
        ],
    }
    icon.need("copy")
    return page(
        site,
        title=e.title,
        description=desc,
        path=e.url,
        rp=rp,
        current="library",
        body=body,
        icon=icon,
        scripts=["article"],
        og_image=f"assets/og/{e.slug}.png",
        og_alt=f"{e.title}, an essay on {site.name}",
        og_type="article",
        schema=[article, crumbs],
    )


def _fmt_date(iso: str) -> str:
    import datetime

    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"
