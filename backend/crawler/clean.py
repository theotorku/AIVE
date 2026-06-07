"""HTML noise removal and clean-markdown conversion.

Primary path: trafilatura, which isolates main content and emits markdown,
removing navigation, footers, sidebars, and boilerplate well across varied
templates. Fallback path: a BeautifulSoup strip + markdownify, used when
trafilatura returns nothing usable (rare, but small/odd pages happen).
"""

from __future__ import annotations

import re

import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Structural / chrome elements that are never main content.
_NOISE_TAGS = ["script", "style", "noscript", "template", "svg", "iframe",
               "nav", "header", "footer", "aside", "form"]

# Role / class / id fragments that typically mark site chrome and overlays.
_NOISE_HINTS = [
    "nav", "navbar", "menu", "header", "footer", "sidebar", "breadcrumb",
    "cookie", "consent", "gdpr", "newsletter", "subscribe", "social",
    "share", "modal", "popup", "banner", "skip-link", "back-to-top",
]


def _looks_like_noise(attr_value: str) -> bool:
    value = attr_value.lower()
    return any(hint in value for hint in _NOISE_HINTS)


def _collapse_blank_lines(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _fallback_markdown(html: str) -> str:
    """BeautifulSoup-based stripping when trafilatura yields nothing."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    for el in soup.find_all(True):
        ident = " ".join(
            filter(None, [
                " ".join(el.get("class", []) or []),
                el.get("id", "") or "",
                el.get("role", "") or "",
            ])
        )
        if ident and _looks_like_noise(ident):
            el.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    markdown = md(str(main), heading_style="ATX")
    return _collapse_blank_lines(markdown)


def html_to_markdown(html: str, *, url: str | None = None) -> str:
    """Convert rendered HTML to clean markdown with chrome removed.

    Returns an empty string only if no readable content could be recovered.
    """
    if not html or not html.strip():
        return ""

    extracted = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
        favor_recall=True,
        no_fallback=False,
    )

    if extracted and len(extracted.strip()) >= 80:
        return _collapse_blank_lines(extracted)

    # trafilatura found little/nothing — try the structural fallback.
    fallback = _fallback_markdown(html)
    if len(fallback.strip()) >= len((extracted or "").strip()):
        return fallback
    return _collapse_blank_lines(extracted or "")
