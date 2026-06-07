"""HTML cleaning + structural parsing (stage 1 helpers).

Separates two concerns the pipeline needs from a rendered page:
  - cleaned main content (chrome removed) -> handed to the markdown converter,
  - structural signals (title, headings, links, metadata, JSON-LD) -> used by
    the classifier and the rule-based extractor.

Noise removal reuses the Goal 01 crawler's tag/heuristic lists so the two
stay consistent.
"""

from __future__ import annotations

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from backend.crawler.clean import _NOISE_HINTS, _NOISE_TAGS, _looks_like_noise
from backend.app.schema import Heading, Link


def parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


def clean_content_soup(html: str) -> BeautifulSoup:
    """Return a soup with site chrome (nav/footer/cookie/etc.) removed."""
    soup = parse(html)
    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    for el in soup.find_all(True):
        # Decomposing a parent above can null out a child still in this list.
        if el.attrs is None:
            continue
        ident = " ".join(filter(None, [
            " ".join(el.get("class", []) or []),
            el.get("id", "") or "",
            el.get("role", "") or "",
        ]))
        if ident and _looks_like_noise(ident):
            el.decompose()
    return soup


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text(" ", strip=True) if h1 else ""


def extract_headings(soup: BeautifulSoup, *, max_headings: int = 60) -> list[Heading]:
    headings: list[Heading] = []
    for level in (1, 2, 3):
        for el in soup.find_all(f"h{level}"):
            text = el.get_text(" ", strip=True)
            if text:
                headings.append(Heading(level=level, text=text))
            if len(headings) >= max_headings:
                return headings
    return headings


def extract_links(soup: BeautifulSoup, base_url: str, *, max_links: int = 200) -> list[Link]:
    links: list[Link] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append(Link(text=a.get_text(" ", strip=True)[:160], href=absolute))
        if len(links) >= max_links:
            break
    return links


def _parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Collect schema.org JSON-LD blocks, flattening @graph containers."""
    blocks: list[dict] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and "@graph" in item and isinstance(item["@graph"], list):
                blocks.extend(g for g in item["@graph"] if isinstance(g, dict))
            elif isinstance(item, dict):
                blocks.append(item)
    return blocks


def extract_metadata(soup: BeautifulSoup) -> dict:
    """Title-independent page metadata used by classification + rules."""
    desc = ""
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        desc = tag["content"].strip()

    og: dict[str, str] = {}
    for meta in soup.find_all("meta", property=True):
        prop = meta.get("property", "")
        if prop.startswith("og:") and meta.get("content"):
            og[prop[3:]] = meta["content"].strip()

    lang = ""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        lang = html_tag["lang"].strip()

    return {
        "description": desc,
        "lang": lang,
        "og": og,
        "json_ld": _parse_json_ld(soup),
    }
