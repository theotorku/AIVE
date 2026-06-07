"""Page classification (stage 2).

Assigns each PageDocument one of PAGE_CATEGORIES using deterministic signals
(URL path, title, headings, JSON-LD @type). Classification matters because a
service page is interpreted differently from a blog post downstream.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from backend.app.schema import PageDocument

# Section rules checked BEFORE the service-detail heuristic, so e.g.
# "/blog/why-ac-breaks" is a blog post, not a service page. First match wins.
_SECTION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("contact", ("contact",)),
    ("faq", ("faq", "faqs", "frequently-asked", "questions")),
    ("reviews", ("review", "reviews", "testimonial", "testimonials")),
    ("pricing", ("pricing", "financing", "specials", "coupon", "coupons", "offers", "deals")),
    ("about", ("about", "about-us", "who-we-are", "our-team", "our-story")),
    ("location", ("locations", "location", "service-area", "service-areas", "areas-we-serve", "areas")),
    ("blog", ("blog", "news", "article", "articles", "post", "resources")),
]
_SERVICES_KEYWORDS = ("services", "our-services", "what-we-do")

_SERVICE_DETAIL_HINTS = (
    "repair", "installation", "install", "replacement", "maintenance", "tune-up",
    "ac-", "air-conditioning", "heating", "cooling", "furnace", "heat-pump",
    "plumbing", "drain", "water-heater", "duct", "thermostat",
)


def _path_segments(url: str) -> list[str]:
    return [s for s in urlparse(url).path.strip("/").split("/") if s]


def _json_ld_types(doc: PageDocument) -> set[str]:
    types: set[str] = set()
    for block in doc.metadata.get("json_ld", []):
        t = block.get("@type")
        if isinstance(t, str):
            types.add(t.lower())
        elif isinstance(t, list):
            types.update(str(x).lower() for x in t)
    return types


def classify_page(doc: PageDocument) -> str:
    segments = _path_segments(doc.url)
    path = "/".join(segments).lower()
    title = (doc.title or "").lower()
    heading_blob = " ".join(doc.heading_texts()).lower()
    ld_types = _json_ld_types(doc)

    # Home: empty path.
    if not segments:
        return "home"

    # Strong structured-data signals.
    if "faqpage" in ld_types:
        return "faq"
    if {"blogposting", "article", "newsarticle"} & ld_types:
        return "blog"

    # Section rules win over the service-detail heuristic (e.g. /blog/...).
    for category, keywords in _SECTION_RULES:
        if any(k in path for k in keywords):
            return category

    # Service detail: a deep path under services, or a clear service keyword in
    # the last path segment (e.g. /cooling/ac-repair).
    last = segments[-1].lower() if segments else ""
    if len(segments) >= 2 and ("service" in path or any(h in path for h in _SERVICE_DETAIL_HINTS)):
        return "service_detail"
    if any(h in last for h in _SERVICE_DETAIL_HINTS):
        return "service_detail"

    # Services landing page.
    if any(k in path for k in _SERVICES_KEYWORDS):
        return "services"

    # Fall back to title / heading hints.
    if re.search(r"\bfaq\b|frequently asked", title + " " + heading_blob):
        return "faq"
    if "contact" in title:
        return "contact"
    if "about" in title:
        return "about"
    if "service" in title or "service" in heading_blob:
        return "services"

    return "unknown"


def classify_documents(docs: list[PageDocument]) -> list[PageDocument]:
    for doc in docs:
        doc.category = classify_page(doc)
    return docs
