"""Inline SVG icon set.

Icons are defined once here and emitted into each page as a tiny ``<symbol>``
sprite containing only the icons that page uses. Stroke icons inherit their
stroke from the ``.i`` class; brand glyphs use ``.i--solid`` (filled).
"""

from __future__ import annotations

# name -> (inner SVG markup, solid?)
ICONS: dict[str, tuple[str, bool]] = {
    "search": ('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>', False),
    "menu": ('<path d="M4 7h16M4 12h16M4 17h16"/>', False),
    "close": ('<path d="M6 6l12 12M18 6L6 18"/>', False),
    "arrow-right": ('<path d="M5 12h14M13 6l6 6-6 6"/>', False),
    "arrow-up": ('<path d="M12 19V5M6 11l6-6 6 6"/>', False),
    "chevron-down": ('<path d="M6 9l6 6 6-6"/>', False),
    "clock": ('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>', False),
    "calendar": ('<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>', False),
    "book": ('<path d="M4 19.5A2.5 2.5 0 016.5 17H20V4H6.5A2.5 2.5 0 004 6.5v13z"/><path d="M4 19.5V6.5"/>', False),
    "copy": ('<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 01-1-1V4a1 1 0 011-1h10a1 1 0 011 1v1"/>', False),
    "link": ('<path d="M9 17H7a5 5 0 010-10h2M15 7h2a5 5 0 010 10h-2M8 12h8"/>', False),
    "share": ('<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.5l6.8-3.9M8.6 13.5l6.8 3.9"/>', False),
    "mail": ('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>', False),
    "map-pin": ('<path d="M12 21s-7-6.1-7-11a7 7 0 0114 0c0 4.9-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>', False),
    "sun": ('<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>', False),
    "moon": ('<path d="M20 14.5A8.5 8.5 0 1110 4a6.8 6.8 0 0010 10.5z"/>', False),
    "quill": ('<path d="M20 4c-6 1-11 5-13 13l-3 3M11.5 12.5c3-4 6-6 8.5-8.5"/><path d="M4 20c2-1 4-2 5-4"/>', False),
    "compass": ('<circle cx="12" cy="12" r="9"/><path d="M15 9l-2 6-6 2 2-6z"/>', False),
    "anchor": ('<circle cx="12" cy="5" r="2"/><path d="M12 7v14M5 12H2a10 10 0 0020 0h-3M5 12a7 7 0 007 9M19 12a7 7 0 01-7 9"/>', False),
    "shield": ('<path d="M12 3l7 3v6c0 4.4-3 8.4-7 9-4-.6-7-4.6-7-9V6z"/>', False),
    "scroll": ('<path d="M7 4h11a2 2 0 012 2v13a1 1 0 01-1.7.7L16 18H7a2 2 0 01-2-2V6a2 2 0 012-2z"/><path d="M7 4a2 2 0 00-2 2v13a2 2 0 01-2-2V7a3 3 0 013-3z"/>', False),
    "heart": ('<path d="M20.8 8.6c0 5.4-8.8 10.4-8.8 10.4S3.2 14 3.2 8.6a4.6 4.6 0 018.8-2 4.6 4.6 0 018.8 2z"/>', False),
    "volume": ('<path d="M11 5L6 9H3v6h3l5 4V5z"/><path d="M15.5 8.5a5 5 0 010 7"/><path d="M18.5 6a9 9 0 010 12"/>', False),
    "play": ('<path d="M8 5.5v13l11-6.5z"/>', True),
    "pause": ('<path d="M7 5h4v14H7zM13 5h4v14h-4z"/>', True),
    "stop": ('<rect x="6" y="6" width="12" height="12" rx="1.5"/>', True),
    "empty": ('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/><path d="M8 11h6"/>', False),
    "alert": ('<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.01"/>', False),
    "x": ('<path d="M18.9 2H22l-7.6 8.7L23 22h-7l-5.5-6.8L4.2 22H1l8.1-9.3L1 2h7.2l5 6.3L18.9 2zm-1.2 18h1.7L6.4 4H4.6l13.1 16z"/>', True),
    "whatsapp": ('<path d="M12 2a10 10 0 00-8.6 15L2 22l5.2-1.4A10 10 0 1012 2zm0 18.1a8 8 0 01-4.1-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 1112 20.1zm4.4-6c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1s-.7.8-.9 1c-.2.2-.3.2-.6.1a6.6 6.6 0 01-2-1.2 7.3 7.3 0 01-1.4-1.7c-.1-.2 0-.4.1-.5l.4-.4c.1-.2.2-.3.2-.5.1-.2 0-.4 0-.5s-.6-1.5-.8-2c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.3.3-1 1-1 2.3s1 2.7 1.2 2.9c.1.2 2 3 4.8 4.2a15.6 15.6 0 001.6.6 3.8 3.8 0 001.7.1c.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.2-.3-.2-.6-.3z"/>', True),
    "facebook": ('<path d="M22 12a10 10 0 10-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.4v7A10 10 0 0022 12z"/>', True),
    "github": ('<path d="M12 2a10 10 0 00-3.2 19.5c.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.3-3.4-1.3-.5-1.1-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.7.4-1.1.6-1.3-2.2-.2-4.6-1.1-4.6-5a3.9 3.9 0 011-2.7c-.1-.2-.5-1.3.1-2.8 0 0 .9-.3 2.9 1a10 10 0 015.2 0c2-1.3 2.9-1 2.9-1 .6 1.5.2 2.6.1 2.8a3.9 3.9 0 011 2.7c0 3.9-2.4 4.7-4.6 5 .3.3.6.9.6 1.8v2.7c0 .3.2.6.7.5A10 10 0 0012 2z"/>', True),
}


class IconSet:
    """Tracks which icons a page uses so only those are emitted."""

    def __init__(self) -> None:
        self.used: set[str] = set()

    def need(self, *names: str) -> None:
        for name in names:
            if name not in ICONS:
                raise KeyError(f"Unknown icon: {name}")
            self.used.add(name)

    def __call__(self, name: str, extra: str = "") -> str:
        self.need(name)
        solid = ICONS[name][1]
        classes = "i" + (" i--solid" if solid else "") + (f" {extra}" if extra else "")
        return f'<svg class="{classes}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'

    def sprite(self) -> str:
        symbols = "".join(
            f'<symbol id="i-{name}" viewBox="0 0 24 24">{ICONS[name][0]}</symbol>' for name in sorted(self.used)
        )
        return f'<svg class="sprite" width="0" height="0" aria-hidden="true" focusable="false">{symbols}</svg>'
