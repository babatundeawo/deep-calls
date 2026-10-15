"""Essay loading: front matter, Markdown rendering, and derived metadata.

Each file in ``content/`` is one essay. The file name (without ``.md``) is the
URL slug, so ``content/no-other-branch.md`` becomes ``writeups/no-other-branch.html``.

Drop-in publishing: an essay needs nothing but its text. A front matter block is
optional. Without one, the title is taken from the first ``# Heading`` and the
category is worked out from the wording (see ``category_keywords`` in
``site.config.json``). One broken file never stops the others from publishing: it
is skipped with a clear warning (set ``DEEP_CALLS_STRICT=1`` to make it fatal).
"""

from __future__ import annotations

import html
import os
import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import markdown

WORDS_PER_MINUTE = 200
FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)
FIRST_HEADING = re.compile(r"\A\s*#[ \t]+(.+?)[ \t]*#*[ \t]*(?:\n|\Z)")
LEADING_RULES = re.compile(r"\A\s*(?:(?:\*{3,}|-{3,}|_{3,})[ \t]*(?:\n|\Z))+")
WARNINGS: list[tuple[str, str]] = []  # (file name, message) collected while loading


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


def read_text_any(path: Path) -> str:
    """Read a file saved as UTF-8 (with or without BOM) or as UTF-16 (Windows Notepad "Unicode")."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def strip_unsafe_html(body: str) -> str:
    """Remove inline styles, event handlers and scripts that the site's security policy blocks."""
    body = re.sub(r"<script\b.*?</script>", "", body, flags=re.S | re.I)
    body = re.sub(r"\s(?:style|on[a-z]+)=(\"[^\"]*\"|\'[^\']*\')", "", body, flags=re.I)
    return body


def normalize_text(text: str) -> str:
    """Make files from any editor look the same: no BOM, Unix line endings."""
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").lstrip()


def parse_front_matter(text: str, source: str) -> tuple[dict[str, str], str]:
    """Split off the optional ``--- ... ---`` block. No block means no settings."""
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")) or raw[:1] in " \t":
            continue  # blank, comment, list item or continuation line: not a setting
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key.strip().lower()] = value
    return meta, text[match.end():]


def take_heading(body: str) -> tuple[str, str]:
    """Remove a leading ``# Title`` (and any ``***`` rule after it); return (title, rest)."""
    match = FIRST_HEADING.match(body)
    if not match:
        return "", body
    title = re.sub(r"[*`]", "", match.group(1)).strip()
    rest = LEADING_RULES.sub("", body[match.end():])
    return title, rest.lstrip("\n")


def demote_h1(body: str) -> str:
    """A page has exactly one <h1> (the title), so any further ``# Heading`` becomes ``##``."""
    out, fenced = [], False
    for line in body.split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and re.match(r"#[ \t]+\S", line):
            line = "#" + line
        out.append(line)
    return "\n".join(out)


def slugify(stem: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", fold(stem)).strip("-")


def infer_category(title: str, body_md: str, config: dict) -> str:
    """Pick the best-fitting category from keyword lists; fall back to the default."""
    default = config.get("default_category") or (config.get("categories") or ["Essays"])[0]
    title_l, body_l = title.lower(), body_md.lower()
    best, best_score = default, 2  # needs a clear signal (score 3+) to beat the default
    for category, words in (config.get("category_keywords") or {}).items():
        score = sum(5 * title_l.count(w.lower()) + body_l.count(w.lower()) for w in words)
        if score > best_score:
            best, best_score = category, score
    return best


def added_date(path: Path) -> str:
    """The day the file first entered the repository (needs full git history), else ''."""
    path = path.resolve()
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%cs", "--", str(path)],
            cwd=path.parent, capture_output=True, text=True, timeout=20, check=False,
        ).stdout.split()
        return out[-1] if out else ""
    except (OSError, subprocess.SubprocessError):
        return ""


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


def load_essay(path: Path, config: dict | None = None, used_slugs: set[str] | None = None) -> Essay:
    config = config or {}
    source = path.name
    meta, body_md = parse_front_matter(normalize_text(read_text_any(path)), source)

    heading, body_md = take_heading(body_md)
    meta["title"] = meta.get("title") or heading or path.stem.replace("_", "-").replace("-", " ").strip().title()
    body_md = demote_h1(body_md)
    if not body_md.strip():
        raise ContentError(f"{source}: the file has no essay text")
    if not meta.get("category"):
        meta["category"] = infer_category(meta["title"], body_md, config)
    if not meta.get("date") and config.get("auto_date", True):
        meta["date"] = added_date(path)

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
    body = strip_unsafe_html(md.convert(body_md))
    toc = [(t["id"], _plain(t["name"])) for t in md.toc_tokens if t["level"] == 2]
    body = _wrap_references(_split_citations(_harden_links(body)))

    # Prose paragraphs outside quotes and reference lists feed the summaries.
    prose_only = re.sub(r"<blockquote>.*?</blockquote>|<section class=\"refs\".*", "", body, flags=re.S)
    paragraphs = [p for p in (_plain(m) for m in re.findall(r"<p>(.*?)</p>", prose_only, re.S)) if len(p) > 25]

    excerpt = meta.get("summary") or lead_text(paragraphs, 110, 230) or meta["title"]
    description = meta.get("summary") or make_description(paragraphs) or f"{meta['title']}: an essay from {config.get('name', 'Deep Calls')}."

    words = len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", body)))
    minutes = max(1, round(words / WORDS_PER_MINUTE))

    verse = meta.get("verse", "")
    verse_html = _inline(verse) if verse else ""
    verse_ref_html = _inline(meta.get("verse_ref", "")) if meta.get("verse_ref") else ""

    slug = base = slugify(path.stem) or "essay"
    n = 2
    while used_slugs is not None and slug in used_slugs:
        slug, n = f"{base}-{n}", n + 1
    if used_slugs is not None:
        used_slugs.add(slug)

    essay = Essay(
        slug=slug,
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


def load_all(content_dir: Path, config: dict | None = None) -> list[Essay]:
    """Load every essay. A file that cannot be read is skipped and reported, not fatal."""
    strict = os.environ.get("DEEP_CALLS_STRICT") == "1"
    files = sorted(
        f for f in content_dir.rglob("*.md")
        if f.name.lower() != "readme.md" and not f.name.startswith(("_", "."))
    )
    essays: list[Essay] = []
    used: set[str] = set()
    WARNINGS.clear()
    for f in files:
        try:
            essays.append(load_essay(f, config, used))
        except (ContentError, UnicodeDecodeError, OSError) as err:
            if strict:
                raise ContentError(str(err)) from err
            WARNINGS.append((f.relative_to(content_dir.parent).as_posix(), str(err).removeprefix(f"{f.name}: ")))
    if not essays:
        raise ContentError(f"No publishable essays found in {content_dir}")
    return essays
