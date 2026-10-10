"""Generated brand imagery: favicons, app icons and social-share cards.

Everything is drawn from code at build time (Pillow), so there are no binary
brand files to maintain. The mark is a "D" with an echo: concentric D shapes,
a nod to "deep calls unto deep" (Psalm 42:7).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(__file__).parent / "fonts"

NAVY = (14, 28, 48)
NAVY_DEEP = (9, 18, 32)
PARCHMENT = (245, 240, 228)
VERMILION = (255, 122, 87)
VERMILION_SOFT = (255, 143, 107)
MUTED = (169, 179, 196)

# Mark geometry in a 48-unit box: (left edge, radius), all centred on (23, 24).
_MARK_CENTRE = (23.0, 24.0)
_MARK_LAYERS = [
    (13.4, 13.6, PARCHMENT),
    (16.6, 10.4, NAVY),
    (19.2, 6.0, VERMILION),
]

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
<rect width="48" height="48" rx="11" fill="#0e1c30"/>
<path d="M13.4 10.4H23a13.6 13.6 0 0 1 0 27.2H13.4z" fill="#f5f0e4"/>
<path d="M16.6 13.6H23a10.4 10.4 0 0 1 0 20.8h-6.4z" fill="#0e1c30"/>
<path d="M19.2 18H23a6 6 0 0 1 0 12h-3.8z" fill="#ff7a57"/>
</svg>
"""


def _draw_mark(draw: ImageDraw.ImageDraw, scale: float, ox: float, oy: float) -> None:
    cx, cy = _MARK_CENTRE
    for left, radius, colour in _MARK_LAYERS:
        draw.rectangle(
            [ox + left * scale, oy + (cy - radius) * scale, ox + cx * scale, oy + (cy + radius) * scale],
            fill=colour,
        )
        draw.pieslice(
            [ox + (cx - radius) * scale, oy + (cy - radius) * scale, ox + (cx + radius) * scale, oy + (cy + radius) * scale],
            -90,
            90,
            fill=colour,
        )


def render_icon(size: int, *, rounded: bool = True, glyph_scale: float = 1.0) -> Image.Image:
    """Square app icon. ``glyph_scale`` < 1 leaves padding (for maskable icons)."""
    ss = 4  # supersample for smooth edges
    big = size * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if rounded:
        draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=big * 11 / 48, fill=NAVY)
    else:
        draw.rectangle([0, 0, big, big], fill=NAVY)
    unit = big / 48 * glyph_scale
    offset = (big - 48 * unit) / 2
    _draw_mark(draw, unit, offset, offset)
    return img.resize((size, size), Image.LANCZOS)


def write_icons(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")
    render_icon(256).save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # iOS and Android apply their own rounding, so fill the whole square.
    render_icon(180, rounded=False, glyph_scale=0.8).convert("RGB").save(out / "apple-touch-icon.png", optimize=True)
    img_dir = out / "assets" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    render_icon(192).save(img_dir / "icon-192.png", optimize=True)
    render_icon(512).save(img_dir / "icon-512.png", optimize=True)
    render_icon(512, rounded=False, glyph_scale=0.62).save(img_dir / "icon-maskable-512.png", optimize=True)


# ---------------------------------------------------------------------------
# Social cards (1200 x 630)
# ---------------------------------------------------------------------------

def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _spaced(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill, tracking: float) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def render_card(title: str, kicker: str, site_name: str, host: str) -> Image.Image:
    w, h = 1200, 630
    base = Image.new("RGB", (w, h), NAVY)
    # Soft vertical gradient
    grad = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        grad.line([(0, y), (w, y)], fill=tuple(int(NAVY[i] * (1 - t) + NAVY_DEEP[i] * t) for i in range(3)))

    # Concentric "echo" rings bleeding off the right edge
    rings = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    cx, cy = 1130, 560
    for n, radius in enumerate(range(120, 900, 95)):
        alpha = max(14, 56 - n * 6)
        rd.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(255, 255, 255, alpha), width=2)
    base = Image.alpha_composite(base.convert("RGBA"), rings)
    draw = ImageDraw.Draw(base)

    left, max_w = 84, 800
    draw.rectangle([left, 84, left + 56, 88], fill=VERMILION)
    _spaced(draw, (left, 108), kicker.upper(), _font("Inter-SemiBold.ttf", 24), VERMILION_SOFT, 3.2)

    # Fit the title: start large, shrink until it sits in at most four lines.
    size = 84
    while True:
        font = _font("Fraunces-SemiBold.ttf", size)
        lines = _wrap(draw, title, font, max_w)
        if (len(lines) <= 4 and len(lines) * size * 1.08 <= 330) or size <= 46:
            break
        size -= 4
    y = 168
    for line in lines[:5]:
        draw.text((left, y), line, font=font, fill=PARCHMENT)
        y += int(size * 1.08)

    # Footer: mark, name and address
    mark = render_icon(64)
    base.alpha_composite(mark, (left, 508))
    draw.text((left + 84, 514), site_name, font=_font("Fraunces-SemiBold.ttf", 34), fill=PARCHMENT)
    draw.text((left + 84, 558), host, font=_font("Inter-Medium.ttf", 20), fill=MUTED)
    return base.convert("RGB")


def write_card(path: Path, title: str, kicker: str, site_name: str, host: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    render_card(title, kicker, site_name, host).save(path, optimize=True)
