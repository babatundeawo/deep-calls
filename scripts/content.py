"""Essay loading: front matter, Markdown rendering, and derived metadata.

Each file in ``content/`` is one essay. The file name (without ``.md``) is the
URL slug, so ``content/no-other-branch.md`` becomes ``writeups/no-other-branch.html``.
"""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import markdown

WORDS_PER_MINUTE = 200
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


class ContentError(Exception):
    """Raised for problems the owner can fix in a content file."""


@dataclass
class Essay:
    slug: str
    title: str
    category: str
    body_html: str
    subtitle: str = ""
    verse_html: str = ""
    verse_ref_html: str = ""
    featured: int = 0  # 0 = not featured, otherwise display order
    date: str = ""  # YYYY-MM-DD, optional
    excerpt: str = ""
    description: str = ""
    words: int = 0
    minutes: int = 1
    toc: list[tuple[str, str]] = field(default_factory=list)
    search_text: str = ""

    @property
    def url(self) -> str:
        return f"writeups/{self.slug}.html"


def fold(text: str) -> str:
    """Lower-case and strip accents; mirrors ``norm()`` in assets/js/core.js."""
    decomposed = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def parse_front_matter(text: str, source: str) -> tuple[dict[str, str], str]:
    match = FRONT_MATTER.match(text)
    if not match:
        raise ContentError(f"{source}: missing front matter block (--- ... ---) at the top of the file")
    meta: dict[str, str] = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ContentError(f"{source}: front matter line has no colon: {raw!r}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key.strip().lower()] = value
    return meta, text[match.end():]


def _plain(html_fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", html_fragment))).strip()


def _inline(text: str) -> str:
    """Render a short Markdown string to inline HTML (smart quotes, emphasis)."""
    md = markdown.Markdown(extensions=["smarty"])
    out = md.convert(text).strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)


def _trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—- ")
    return cut + "…"


def lead_text(paragraphs: list[str], minimum: int, limit: int) -> str:
    """Join opening paragraphs until there is enough to be a useful summary."""
    out = ""
    for para in paragraphs[:3]:
        out = f"{out} {para}".strip()
        if len(out) >= minimum:
            break
    return _trim(out, limit)


def make_description(paragraphs: list[str], limit: int = 158) -> str:
    """A meta description that ends on a sentence where possible."""
    text = " ".join(paragraphs[:2]).strip()
    if len(text) <= limit:
        return text
    sentences = re.findall(r"[^.!?]+[.!?]+(?:\s|$)", text)
    out = ""
    for sentence in sentences:
        if len(out) + len(sentence) > limit:
            break
        out += sentence
    if len(out) >= 70:
        return out.strip()
    return _trim(text, limit)


def _wrap_references(body: str) -> str:
    """Wrap a trailing "References" section so it can be styled as a footnote block."""
    match = re.search(r'<h2 id="([^"]+)">\s*References\b', body, re.I)
    if not match:
        return body
    head = re.sub(r"<hr\s*/?>\s*$", "", body[: match.start()].rstrip())
    return f'{head}\n<section class="refs" aria-labelledby="{match.group(1)}">\n{body[match.start():]}\n</section>'


def _split_citations(body: str) -> str:
    """Put a quotation's ``— Reference`` line in its own paragraph.

    Markdown joins ``> "quote"`` and ``> — Ref`` into one paragraph. We split
    them so the attribution can be styled separately.
    """
    pattern = re.compile(r"<p>((?:(?!</p>).)*?)\n(— (?:(?!</p>).)*?)</p>", re.S)

    def fix(block: re.Match) -> str:
        return pattern.sub(r'<p>\1</p>\n<p class="cite">\2</p>', block.group(0))

    return re.sub(r"<blockquote>.*?</blockquote>", fix, body, flags=re.S)


def _harden_links(body: str) -> str:
    return re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a rel="noopener noreferrer" href="\1"',
        body,
    )


def load_essay(path: Path) -> Essay:
    source = path.name
    meta, body_md = parse_front_matter(path.read_text(encoding="utf-8"), source)
    for required in ("title", "category"):
        if not meta.get(required):
            raise ContentError(f"{source}: front matter needs a '{required}:' line")

    date = meta.get("date", "")
    if date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ContentError(f"{source}: date must look like 2026-03-14, got {date!r}")

    featured_raw = meta.get("featured", "").lower()
    featured = 0
    if featured_raw in ("true", "yes"):
        featured = 99
    elif featured_raw.isdigit():
        featured = int(featured_raw)

    md = markdown.Markdown(
        extensions=["extra", "smarty", "toc"],
        extension_configs={"toc": {"toc_depth": "2-2", "permalink": False}},
    )
    body = md.convert(body_md)
    toc = [(t["id"], _plain(t["name"])) for t in md.toc_tokens if t["level"] == 2]
    body = _wrap_references(_split_citations(_harden_links(body)))

    # Prose paragraphs outside quotes and reference lists feed the summaries.
    prose_only = re.sub(r"<blockquote>.*?</blockquote>|<section class=\"refs\".*", "", body, flags=re.S)
    paragraphs = [p for p in (_plain(m) for m in re.findall(r"<p>(.*?)</p>", prose_only, re.S)) if len(p) > 25]

    excerpt = meta.get("summary") or lead_text(paragraphs, 110, 230)
    description = meta.get("summary") or make_description(paragraphs)

    words = len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", body)))
    minutes = max(1, round(words / WORDS_PER_MINUTE))

    verse = meta.get("verse", "")
    verse_html = _inline(verse) if verse else ""
    verse_ref_html = _inline(meta.get("verse_ref", "")) if meta.get("verse_ref") else ""

    essay = Essay(
        slug=path.stem,
        title=meta["title"],
        subtitle=meta.get("subtitle", ""),
        category=meta["category"],
        body_html=body,
        verse_html=verse_html,
        verse_ref_html=verse_ref_html,
        featured=featured,
        date=date,
        excerpt=excerpt,
        description=description,
        words=words,
        minutes=minutes,
        toc=toc,
    )
    essay.search_text = fold(
        " ".join([essay.title, essay.subtitle, essay.category, excerpt, _plain(verse_ref_html), _plain(verse_html)])
    )
    return essay


def load_all(content_dir: Path) -> list[Essay]:
    files = sorted(f for f in content_dir.glob("*.md") if f.name.lower() != "readme.md")
    if not files:
        raise ContentError(f"No essays found in {content_dir}")
    essays = [load_essay(f) for f in files]
    slugs = [e.slug for e in essays]
    if len(slugs) != len(set(slugs)):
        raise ContentError("Two essays share the same file name")
    return essays
