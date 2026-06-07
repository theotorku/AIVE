"""Internal-link discovery.

Given a homepage URL and its rendered HTML, pick a small, high-value set of
same-domain pages to crawl. We prioritise pages that carry business meaning
for downstream ABI work (services, about, contact, FAQ, areas served) and
hard-cap the count so a crawl stays fast and predictable.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup

# Higher score = crawl earlier. Matched against the link path + anchor text.
_PRIORITY_KEYWORDS = {
    "service": 10, "services": 10,
    "about": 8, "about-us": 8,
    "contact": 7, "contact-us": 7,
    "faq": 9, "faqs": 9, "questions": 6,
    "area": 6, "areas": 6, "service-area": 7, "locations": 7, "location": 7,
    "review": 5, "reviews": 5, "testimonial": 5, "testimonials": 5,
    "pricing": 4, "financing": 4, "offers": 5, "specials": 5, "coupons": 4,
    "repair": 6, "installation": 6, "maintenance": 6,
    "ac": 5, "heating": 5, "cooling": 5, "furnace": 5,
}

# Never follow these — file downloads, mail/phone links, admin areas.
_SKIP_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                  ".zip", ".mp4", ".mov", ".doc", ".docx", ".xls", ".xlsx",
                  ".css", ".js", ".ico", ".xml")
_SKIP_PATH_HINTS = ("/wp-admin", "/wp-login", "/cart", "/checkout", "/account",
                    "/privacy", "/terms", "/sitemap")


def _same_registrable_host(a: str, b: str) -> bool:
    """True if two hosts share a domain (ignoring an optional www prefix)."""
    a = a.lower().removeprefix("www.")
    b = b.lower().removeprefix("www.")
    return a == b


def _score_link(path: str, text: str) -> int:
    haystack = f"{path} {text}".lower()
    return sum(weight for kw, weight in _PRIORITY_KEYWORDS.items()
               if kw in haystack)


def discover_links(base_url: str, html: str, *, max_pages: int = 8) -> list[str]:
    """Return an ordered list of same-domain URLs to crawl (incl. base_url).

    The homepage is always first; remaining slots are filled by priority
    score, then by discovery order, deduplicated by URL without fragment.
    """
    base_host = urlparse(base_url).netloc
    soup = BeautifulSoup(html, "lxml")

    seen: set[str] = set()
    ordered: list[str] = []

    base_norm = urldefrag(base_url).url.rstrip("/") or base_url
    seen.add(base_norm)
    ordered.append(base_url)

    candidates: list[tuple[int, int, str]] = []
    for idx, a in enumerate(soup.find_all("a", href=True)):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue

        absolute = urldefrag(urljoin(base_url, href)).url
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if not _same_registrable_host(parsed.netloc, base_host):
            continue

        path = parsed.path.lower()
        if path.endswith(_SKIP_SUFFIXES):
            continue
        if any(hint in path for hint in _SKIP_PATH_HINTS):
            continue

        norm = absolute.rstrip("/") or absolute
        if norm in seen:
            continue
        seen.add(norm)

        score = _score_link(parsed.path, a.get_text(" ", strip=True))
        candidates.append((-score, idx, absolute))

    candidates.sort()  # higher score first (negated), then discovery order
    for _, _, url in candidates:
        if len(ordered) >= max_pages:
            break
        ordered.append(url)

    return ordered
