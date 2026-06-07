"""Crawl orchestration that emits rich PageDocuments (stage 1).

Reuses the Goal 01 Playwright fetcher and link-discovery, then layers on the
structural parsing the pipeline needs (title, headings, links, metadata,
JSON-LD) alongside the cleaned markdown.
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright

from backend.crawler.discover import discover_links
from backend.crawler.fetch import fetch_page
from backend.app.schema import PageDocument
from backend.app.services import cleaner, markdown_converter


def _build_document(url: str, html: str) -> PageDocument:
    raw_soup = cleaner.parse(html)
    content_soup = cleaner.clean_content_soup(html)
    markdown = markdown_converter.to_markdown(html, url=url)
    return PageDocument(
        url=url,
        title=cleaner.extract_title(raw_soup),
        markdown=markdown,
        headings=cleaner.extract_headings(content_soup),
        links=cleaner.extract_links(raw_soup, url),
        metadata=cleaner.extract_metadata(raw_soup),
    )


def crawl_documents(
    start_url: str,
    *,
    max_pages: int = 6,
    timeout_ms: int = 30000,
) -> list[PageDocument]:
    """Crawl a site and return one PageDocument per successfully fetched page."""
    docs: list[PageDocument] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            home = fetch_page(browser, start_url, timeout_ms=timeout_ms)
            if not home.ok:
                return docs
            docs.append(_build_document(home.url, home.html))

            urls = discover_links(home.url, home.html, max_pages=max_pages)
            for url in urls:
                if url == home.url:
                    continue
                fetched = fetch_page(browser, url, timeout_ms=timeout_ms)
                if fetched.ok:
                    docs.append(_build_document(fetched.url, fetched.html))
        finally:
            browser.close()
    return docs
