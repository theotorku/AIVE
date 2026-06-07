"""ProPlan ABI — Goal 01 crawler package.

Crawl a website (JS-rendered), strip navigation/footer noise, and export
clean, readable markdown. Scope is intentionally limited to crawling +
markdown conversion (no extraction, scoring, or dashboard).
"""

from .crawl import crawl_site, CrawlResult, PageResult

__all__ = ["crawl_site", "CrawlResult", "PageResult"]
