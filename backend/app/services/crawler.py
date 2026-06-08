"""Crawl orchestration that emits rich PageDocuments + coverage diagnostics.

Builds a crawl plan from the site's robots.txt and sitemap.xml plus on-page
links (extracted from the rendered, uncleaned HTML), normalizes everything to one
canonical host, crawls breadth-first up to max_pages/max_depth, and records why
every URL was discovered, skipped, or crawled — so coverage is auditable and a
shallow crawl is detectable before extraction/scoring.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from playwright.sync_api import sync_playwright

from backend.crawler.discover import (
    Candidate, canonical_host, extract_page_links, normalize_url, parse_robots,
    parse_sitemap, plan_crawl, _skip_reason)
from backend.crawler.fetch import fetch_page, DEFAULT_USER_AGENT
from backend.app.schema import PageDocument
from backend.app.services import cleaner, markdown_converter

# Below this many crawled pages relative to what the site advertises, the report
# should warn that it may be incomplete.
_MIN_PAGES = 3


@dataclass
class CrawlBundle:
    documents: list[PageDocument] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)


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


def _http_get(browser, url: str, *, timeout_ms: int = 15000) -> tuple[int | None, str]:
    """Fetch a text resource (robots.txt / sitemap.xml) via the browser stack."""
    ctx = browser.new_context(user_agent=DEFAULT_USER_AGENT, ignore_https_errors=True)
    try:
        resp = ctx.request.get(url, timeout=timeout_ms)
        return resp.status, resp.text()
    except Exception:  # noqa: BLE001
        return None, ""
    finally:
        ctx.close()


def _gather_sitemap_urls(browser, host: str, robots: dict, *,
                         max_sitemaps: int = 10) -> list[str]:
    """Fetch declared sitemaps (+ /sitemap.xml fallback), recursing indexes once."""
    queue = list(robots.get("sitemaps") or [])
    if not queue:
        queue = [f"https://{host}/sitemap.xml"]
    seen: set[str] = set()
    pages: list[str] = []
    fetched = 0
    while queue and fetched < max_sitemaps:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        fetched += 1
        status, body = _http_get(browser, sm)
        if status != 200 or not body.strip().startswith("<"):
            continue
        locs, children = parse_sitemap(body)
        pages.extend(locs)
        queue.extend(c for c in children if c not in seen)
    # de-dupe, preserve order
    out, seen_p = [], set()
    for u in pages:
        if u not in seen_p:
            seen_p.add(u)
            out.append(u)
    return out


def crawl_documents(
    start_url: str,
    *,
    max_pages: int = 12,
    max_depth: int = 2,
    timeout_ms: int = 30000,
) -> CrawlBundle:
    """Crawl a site and return PageDocuments plus a crawl_coverage report.

    Coverage captures discovered_urls, skipped_urls (with reason), crawled_urls
    (with depth + link_source), the canonical host, robots/sitemap facts, the
    final page count, and a low-coverage warning.
    """
    bundle = CrawlBundle()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            home = fetch_page(browser, start_url, timeout_ms=timeout_ms)
            if not home.ok:
                bundle.coverage = {
                    "start_url": start_url, "final_url": home.url,
                    "error": home.error or "empty homepage",
                    "final_page_count": 0, "low_coverage": True,
                    "warning": "Low Crawl Coverage Warning: This report may be "
                               "incomplete because only 0 pages were crawled.",
                    "discovered_urls": [], "skipped_urls": [], "crawled_urls": [],
                }
                return bundle

            host = canonical_host(home.url, home.html)
            r_status, r_body = _http_get(browser, f"https://{host}/robots.txt")
            robots = parse_robots(r_body) if r_status == 200 else {"disallow": [], "sitemaps": []}
            robots["fetched"] = r_status == 200
            sitemap_urls = _gather_sitemap_urls(browser, host, robots)

            plan = plan_crawl(home.url, home.html, max_pages=max_pages, host=host,
                              robots=robots, sitemap_urls=sitemap_urls)

            # Breadth-first crawl. Sitemap/home/nav links seed depth 0-1; pages we
            # crawl can surface deeper links (up to max_depth) when capacity remains.
            docs: list[PageDocument] = []
            crawled: list[dict] = []
            discovered = {c.url: c for c in plan.discovered}
            visited: set[str] = set()
            queued: set[str] = {c.url for c in plan.crawl}
            rejected: set[str] = {s["url"] for s in plan.skipped}
            frontier: deque[Candidate] = deque(plan.crawl)

            while frontier and len(docs) < max_pages:
                cand = frontier.popleft()
                if cand.url in visited:
                    continue
                visited.add(cand.url)

                fetched = home if cand.source == "home" else fetch_page(
                    browser, cand.url, timeout_ms=timeout_ms)
                if not fetched.ok:
                    crawled.append({"url": cand.url, "depth": cand.depth,
                                    "link_source": cand.source, "ok": False,
                                    "error": fetched.error or "fetch failed"})
                    continue

                doc = _build_document(fetched.url, fetched.html)
                docs.append(doc)
                crawled.append({"url": cand.url, "depth": cand.depth,
                                "link_source": cand.source, "ok": True,
                                "markdown_chars": len(doc.markdown)})

                # Multi-hop expansion only when we still have capacity to use it.
                if cand.depth < max_depth and len(docs) + len(frontier) < max_pages:
                    for norm, source in extract_page_links(fetched.url, fetched.html, host):
                        if norm in visited or norm in queued or norm in rejected:
                            continue
                        reason = _skip_reason(norm, host, robots.get("disallow", []))
                        if reason:
                            rejected.add(norm)
                            plan.skipped.append({"url": norm, "reason": reason,
                                                 "source": source})
                            continue
                        queued.add(norm)
                        child = Candidate(norm, source, cand.depth + 1)
                        discovered.setdefault(norm, child)
                        frontier.append(child)

            meaningful = len(discovered)
            final = len(docs)
            low = final < meaningful or final < _MIN_PAGES
            warning = (
                f"Low Crawl Coverage Warning: This report may be incomplete "
                f"because only {final} pages were crawled."
                + (f" The site appears to have at least {meaningful} public pages."
                   if meaningful > final else "")
            ) if low else None

            bundle.documents = docs
            bundle.coverage = {
                "start_url": start_url,
                "final_url": home.url,
                "canonical_host": host,
                "robots": {"fetched": robots.get("fetched", False),
                           "disallow": robots.get("disallow", []),
                           "sitemaps": robots.get("sitemaps", [])},
                "sitemap_url_count": len(sitemap_urls),
                "max_pages": max_pages, "max_depth": max_depth,
                "discovered_urls": [{"url": c.url, "link_source": c.source,
                                     "depth": c.depth} for c in discovered.values()],
                "skipped_urls": plan.skipped,
                "crawled_urls": crawled,
                "final_page_count": final,
                "meaningful_pages_found": meaningful,
                "low_coverage": low,
                "warning": warning,
            }
        finally:
            browser.close()
    return bundle
