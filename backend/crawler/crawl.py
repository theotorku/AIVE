"""Crawl orchestration: URL in, clean markdown files out.

Pipeline per site:
  1. Render the homepage (Playwright, JS-aware).
  2. Discover a small, high-value set of internal pages.
  3. Render each page, strip chrome, convert to markdown.
  4. Write one markdown file per page plus a combined site markdown.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from .clean import html_to_markdown
from .discover import discover_links
from .fetch import fetch_page


@dataclass
class PageResult:
    url: str
    status: int | None
    markdown_chars: int
    output_file: str | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.markdown_chars > 0


@dataclass
class CrawlResult:
    start_url: str
    domain: str
    pages: list[PageResult] = field(default_factory=list)
    output_dir: str | None = None

    @property
    def pages_crawled(self) -> int:
        return len(self.pages)

    @property
    def pages_ok(self) -> int:
        return sum(1 for p in self.pages if p.ok)

    @property
    def total_markdown_chars(self) -> int:
        return sum(p.markdown_chars for p in self.pages)

    @property
    def has_critical_error(self) -> bool:
        """A site fails validation if no page produced readable markdown."""
        return self.pages_ok == 0


def _normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _domain_slug(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return re.sub(r"[^a-z0-9.-]", "_", host) or "site"


def _page_slug(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return slug[:80] or "page"


def crawl_site(
    start_url: str,
    *,
    output_root: str | Path = "output",
    max_pages: int = 8,
    timeout_ms: int = 30000,
) -> CrawlResult:
    """Crawl one website and export clean markdown. Never raises per-page."""
    start_url = _normalize_url(start_url)
    domain = _domain_slug(start_url)
    out_dir = Path(output_root) / domain
    out_dir.mkdir(parents=True, exist_ok=True)

    result = CrawlResult(start_url=start_url, domain=domain, output_dir=str(out_dir))
    combined: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            home = fetch_page(browser, start_url, timeout_ms=timeout_ms)
            if not home.ok:
                result.pages.append(PageResult(
                    url=start_url, status=home.status, markdown_chars=0,
                    output_file=None, error=home.error or "empty homepage",
                ))
                return result

            urls = discover_links(home.url, home.html, max_pages=max_pages)
            # Reuse the already-rendered homepage HTML instead of refetching.
            prefetched = {home.url: home}

            for url in urls:
                fetched = prefetched.get(url) or fetch_page(
                    browser, url, timeout_ms=timeout_ms
                )
                if not fetched.ok:
                    result.pages.append(PageResult(
                        url=url, status=fetched.status, markdown_chars=0,
                        output_file=None, error=fetched.error or "fetch failed",
                    ))
                    continue

                markdown = html_to_markdown(fetched.html, url=fetched.url)
                if not markdown.strip():
                    result.pages.append(PageResult(
                        url=fetched.url, status=fetched.status, markdown_chars=0,
                        output_file=None, error="no readable content",
                    ))
                    continue

                file_path = out_dir / f"{_page_slug(fetched.url)}.md"
                header = f"<!-- source: {fetched.url} -->\n\n"
                file_path.write_text(header + markdown, encoding="utf-8")
                combined.append(f"# Source: {fetched.url}\n\n{markdown}")

                result.pages.append(PageResult(
                    url=fetched.url, status=fetched.status,
                    markdown_chars=len(markdown), output_file=str(file_path),
                ))
        finally:
            browser.close()

    if combined:
        (out_dir / "_site.md").write_text(
            "\n\n---\n\n".join(combined), encoding="utf-8"
        )
    (out_dir / "_crawl.json").write_text(
        json.dumps(asdict(result), indent=2), encoding="utf-8"
    )
    return result
