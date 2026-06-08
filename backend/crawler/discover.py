"""Internal-link discovery + crawl planning.

Given a homepage and (optionally) the site's robots.txt and sitemap, build an
ordered, deduplicated plan of same-site pages to crawl — and record *why* every
candidate was kept or dropped so coverage is debuggable.

Sources, in order of authority:
  1. sitemap.xml  — the site's own declaration of its public pages,
  2. on-page nav/footer links (extracted from the rendered, uncleaned HTML),
  3. on-page body links,
  4. links found on pages we crawl (multi-hop, up to max_depth).

Everything is normalized to one canonical host (www vs non-www, trailing slash,
fragments) so the same page isn't crawled twice or counted as missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urldefrag
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

# Higher score = crawl earlier. Matched against the link path + anchor text.
# Generalized beyond HVAC: SaaS/product/service businesses score their key
# pages too (product, pricing, features, solutions, ...).
_PRIORITY_KEYWORDS = {
    "service": 10, "services": 10,
    "product": 10, "products": 10, "platform": 9, "solution": 9, "solutions": 9,
    "pricing": 9, "plans": 7, "features": 7, "how-it-works": 7,
    "about": 8, "about-us": 8, "company": 6, "team": 5,
    "contact": 7, "contact-us": 7, "demo": 7, "get-started": 6, "signup": 5,
    "faq": 9, "faqs": 9, "questions": 6, "docs": 6, "documentation": 6,
    "area": 6, "areas": 6, "service-area": 7, "locations": 7, "location": 7,
    "review": 5, "reviews": 5, "testimonial": 5, "testimonials": 5,
    "case-study": 6, "case-studies": 6, "customers": 5, "use-case": 6,
    "financing": 4, "offers": 5, "specials": 5, "coupons": 4,
    "repair": 6, "installation": 6, "maintenance": 6,
    "ac": 5, "heating": 5, "cooling": 5, "furnace": 5,
    "blog": 3,  # informative but lower priority than core business pages
}

# Never follow these — file downloads, mail/phone links, admin areas.
_SKIP_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                  ".zip", ".mp4", ".mov", ".doc", ".docx", ".xls", ".xlsx",
                  ".css", ".js", ".ico", ".xml", ".json", ".rss")
# Low-ABI-value routes. Kept out of the crawl but recorded with a reason.
_SKIP_PATH_HINTS = ("/wp-admin", "/wp-login", "/cart", "/checkout", "/account",
                    "/login", "/signin", "/privacy", "/terms", "/legal",
                    "/cookie", "/sitemap")


# --- canonical normalization ------------------------------------------------

def _registrable(host: str) -> str:
    """Host without scheme/port and without a leading www."""
    return host.lower().split(":")[0].removeprefix("www.")


def _same_registrable_host(a: str, b: str) -> bool:
    return _registrable(a) == _registrable(b)


def canonical_host(home_final_url: str, html: str | None = None) -> str:
    """The host all URLs should be normalized to.

    Prefers `<link rel=canonical>`'s host (the site's own statement), else the
    homepage's final host after redirects (e.g. non-www -> www).
    """
    host = urlparse(home_final_url).netloc
    if html:
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("link", rel="canonical")
        if link and link.get("href"):
            ch = urlparse(urljoin(home_final_url, link["href"].strip())).netloc
            if ch and _same_registrable_host(ch, host):
                host = ch
    return host


def normalize_url(url: str, host: str) -> str:
    """Canonicalize: force host + https, drop fragment, trim a trailing slash
    (except root). Makes www/non-www, http/https, and #frag the same URL."""
    url = urldefrag(url).url
    p = urlparse(url)
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    query = f"?{p.query}" if p.query else ""
    return f"https://{host.lower()}{path}{query}"


# --- robots.txt + sitemap ---------------------------------------------------

def parse_robots(text: str) -> dict:
    """Parse robots.txt: Disallow rules for `*` (and our agent) + Sitemap URLs."""
    disallow: list[str] = []
    sitemaps: list[str] = []
    applies = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (s.strip() for s in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            applies = value == "*" or "proplanabi" in value.lower()
        elif field == "sitemap" and value:
            sitemaps.append(value)
        elif field == "disallow" and applies and value:
            disallow.append(value)
    return {"disallow": disallow, "sitemaps": sitemaps}


def robots_blocks(path: str, disallow: list[str]) -> bool:
    """True if a path is Disallow-ed (simple prefix match, `*` wildcard)."""
    for rule in disallow:
        prefix = rule.split("*", 1)[0]
        if prefix and path.startswith(prefix):
            return True
        if rule == "/":
            return True
    return False


def parse_sitemap(xml_text: str) -> tuple[list[str], list[str]]:
    """Return (page_locs, child_sitemap_locs) from a sitemap or sitemap index."""
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError:
        return [], []
    tag = root.tag.lower()
    locs = [e.text.strip() for e in root.iter()
            if e.tag.lower().endswith("loc") and e.text and e.text.strip()]
    if tag.endswith("sitemapindex"):
        return [], locs
    return locs, []


# --- on-page link extraction ------------------------------------------------

_NAV_ANCESTORS = ("nav", "header", "footer")


def extract_page_links(base_url: str, html: str, host: str) -> list[tuple[str, str]]:
    """Same-site links from rendered HTML as (normalized_url, source).

    source is "nav" when the anchor sits inside a <nav>/<header>/<footer>, else
    "body". Run on the *uncleaned* HTML so nav/footer links survive.
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(base_url, href)
        p = urlparse(absolute)
        if p.scheme not in ("http", "https"):
            continue
        if not _same_registrable_host(p.netloc, host):
            continue
        norm = normalize_url(absolute, host)
        if norm in seen:
            continue
        seen.add(norm)
        in_nav = any(a.find_parent(t) is not None for t in _NAV_ANCESTORS)
        out.append((norm, "nav" if in_nav else "body"))
    return out


def _score_link(url: str, text: str = "") -> int:
    haystack = f"{urlparse(url).path} {text}".lower()
    return sum(weight for kw, weight in _PRIORITY_KEYWORDS.items()
               if kw in haystack)


def _skip_reason(url: str, host: str, disallow: list[str]) -> str | None:
    p = urlparse(url)
    if not _same_registrable_host(p.netloc, host):
        return "offsite"
    path = p.path.lower()
    if path.endswith(_SKIP_SUFFIXES):
        return "suffix"
    if any(h in path for h in _SKIP_PATH_HINTS):
        return "path-hint"
    if robots_blocks(p.path, disallow):
        return "robots-disallow"
    return None


# --- planning ---------------------------------------------------------------

@dataclass
class Candidate:
    url: str
    source: str   # home | sitemap | nav | body
    depth: int


@dataclass
class DiscoveryPlan:
    canonical_host: str
    crawl: list[Candidate] = field(default_factory=list)        # ordered, capped
    discovered: list[Candidate] = field(default_factory=list)   # all kept (pre-cap)
    skipped: list[dict] = field(default_factory=list)           # {url, reason}
    robots: dict = field(default_factory=dict)
    sitemap_url_count: int = 0


def plan_crawl(
    home_url: str,
    home_html: str,
    *,
    max_pages: int = 12,
    host: str | None = None,
    robots: dict | None = None,
    sitemap_urls: list[str] | None = None,
) -> DiscoveryPlan:
    """Build an ordered crawl plan from the homepage + sitemap, with diagnostics.

    The homepage is always first. Remaining slots are filled by priority score
    (core business pages first), with sitemap and on-page links merged and
    deduped on the canonical host. Multi-hop expansion (depth > 1) is driven by
    the caller as it crawls; this seeds depth 0 (home) and depth 1 candidates.
    """
    host = host or canonical_host(home_url, home_html)
    robots = robots or {"disallow": [], "sitemaps": []}
    disallow = robots.get("disallow", [])
    home_norm = normalize_url(home_url, host)

    plan = DiscoveryPlan(canonical_host=host, robots=robots,
                         sitemap_url_count=len(sitemap_urls or []))
    seen: set[str] = {home_norm}
    plan.crawl.append(Candidate(home_norm, "home", 0))
    plan.discovered.append(Candidate(home_norm, "home", 0))

    # source priority so a page found in both sitemap and nav is labeled "sitemap"
    pool: dict[str, tuple[str, str]] = {}  # norm_url -> (source, anchor_text)

    for loc in sitemap_urls or []:
        # Reject offsite sitemap entries BEFORE normalize_url forces the host on —
        # otherwise https://other.com/foo would be rewritten to the target host
        # and slip past the (post-normalization) offsite check as a bogus page.
        netloc = urlparse(loc).netloc
        if netloc and not _same_registrable_host(netloc, host):
            plan.skipped.append({"url": loc, "reason": "offsite", "source": "sitemap"})
            continue
        norm = normalize_url(loc, host)
        if norm not in pool:
            pool[norm] = ("sitemap", "")
    for norm, source in extract_page_links(home_url, home_html, host):
        if norm not in pool:
            pool[norm] = (source, "")

    scored: list[tuple[int, int, str, str]] = []
    for i, (norm, (source, text)) in enumerate(pool.items()):
        if norm in seen:
            continue
        reason = _skip_reason(norm, host, disallow)
        if reason:
            plan.skipped.append({"url": norm, "reason": reason, "source": source})
            continue
        seen.add(norm)
        plan.discovered.append(Candidate(norm, source, 1))
        # sitemap-listed pages get a small boost (the site says they matter).
        boost = 3 if source == "sitemap" else (2 if source == "nav" else 0)
        scored.append((-(_score_link(norm, text) + boost), i, norm, source))

    scored.sort()
    for _, _, norm, source in scored:
        if len(plan.crawl) >= max_pages:
            plan.skipped.append({"url": norm, "reason": "beyond-max-pages",
                                 "source": source})
            continue
        plan.crawl.append(Candidate(norm, source, 1))
    return plan


def discover_links(base_url: str, html: str, *, max_pages: int = 8) -> list[str]:
    """Backward-compatible homepage-only discovery (no sitemap/robots).

    Returns an ordered list of same-domain URLs to crawl (incl. base_url).
    """
    plan = plan_crawl(base_url, html, max_pages=max_pages)
    return [c.url for c in plan.crawl]
