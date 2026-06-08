"""Offline tests for crawl planning + coverage (no network).

Covers robots/sitemap parsing, canonical normalization, on-page link source
tagging, skip reasons, and the priority/cap behaviour of plan_crawl.
"""

from backend.crawler.discover import (
    canonical_host, normalize_url, parse_robots, parse_sitemap, robots_blocks,
    extract_page_links, plan_crawl)


# ---- robots.txt ------------------------------------------------------------

def test_parse_robots_disallow_and_sitemaps():
    txt = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /admin\n"
        "Sitemap: https://www.x.com/sitemap.xml\n"
    )
    r = parse_robots(txt)
    assert "/api/" in r["disallow"] and "/admin" in r["disallow"]
    assert r["sitemaps"] == ["https://www.x.com/sitemap.xml"]


def test_parse_robots_only_applies_relevant_user_agent():
    txt = "User-agent: BadBot\nDisallow: /\n\nUser-agent: *\nDisallow: /api/\n"
    r = parse_robots(txt)
    assert r["disallow"] == ["/api/"]  # the Disallow: / under BadBot is ignored


def test_robots_blocks_prefix_and_wildcard():
    assert robots_blocks("/api/x", ["/api/"]) is True
    assert robots_blocks("/blog", ["/api/"]) is False
    assert robots_blocks("/p/123", ["/p/*"]) is True


# ---- sitemap ---------------------------------------------------------------

def test_parse_sitemap_urlset():
    xml = ("<urlset><url><loc>https://x.com/</loc></url>"
           "<url><loc>https://x.com/about</loc></url></urlset>")
    locs, children = parse_sitemap(xml)
    assert locs == ["https://x.com/", "https://x.com/about"]
    assert children == []


def test_parse_sitemap_index_returns_children():
    xml = ("<sitemapindex><sitemap><loc>https://x.com/sm1.xml</loc></sitemap>"
           "<sitemap><loc>https://x.com/sm2.xml</loc></sitemap></sitemapindex>")
    locs, children = parse_sitemap(xml)
    assert locs == []
    assert children == ["https://x.com/sm1.xml", "https://x.com/sm2.xml"]


# ---- canonical normalization ----------------------------------------------

def test_canonical_host_prefers_canonical_link():
    html = '<html><head><link rel="canonical" href="https://www.x.com/"></head></html>'
    assert canonical_host("https://x.com/", html) == "www.x.com"


def test_normalize_url_collapses_www_slash_fragment():
    a = normalize_url("https://x.com/about/#team", "www.x.com")
    b = normalize_url("http://www.x.com/about", "www.x.com")
    assert a == b == "https://www.x.com/about"
    assert normalize_url("https://x.com/", "www.x.com") == "https://www.x.com/"


# ---- on-page link extraction ----------------------------------------------

def test_extract_page_links_tags_nav_vs_body():
    html = """
    <html><body>
      <nav><a href="/about">About</a></nav>
      <main><a href="/products/scopeai">ScopeAI</a>
            <a href="https://twitter.com/x">Twitter</a></main>
    </body></html>"""
    links = extract_page_links("https://www.x.com/", html, "www.x.com")
    by_url = {u: s for u, s in links}
    assert by_url["https://www.x.com/about"] == "nav"
    assert by_url["https://www.x.com/products/scopeai"] == "body"
    assert all("twitter.com" not in u for u, _ in links)  # offsite dropped


# ---- planning --------------------------------------------------------------

def test_plan_crawl_merges_sitemap_and_prioritizes():
    html = '<html><body><a href="/blog">Blog</a></body></html>'
    plan = plan_crawl(
        "https://www.x.com/", html, max_pages=4, host="www.x.com",
        robots={"disallow": ["/api/"], "sitemaps": []},
        sitemap_urls=["https://www.x.com/products/scopeai",
                      "https://www.x.com/about", "https://www.x.com/api/secret",
                      "https://www.x.com/privacy"])
    urls = [c.url for c in plan.crawl]
    assert urls[0] == "https://www.x.com/"          # home first
    # product + about (sitemap, high priority) beat blog; capped at 4.
    assert "https://www.x.com/products/scopeai" in urls
    assert "https://www.x.com/about" in urls
    assert len(urls) == 4
    # robots-disallowed + privacy are skipped with reasons.
    reasons = {s["url"]: s["reason"] for s in plan.skipped}
    assert reasons.get("https://www.x.com/api/secret") == "robots-disallow"
    assert reasons.get("https://www.x.com/privacy") == "path-hint"


def test_plan_crawl_rejects_offsite_sitemap_loc():
    # An offsite sitemap entry must be rejected as 'offsite', not rewritten onto
    # the target host and crawled as a bogus page.
    plan = plan_crawl(
        "https://www.x.com/", "<html></html>", max_pages=8, host="www.x.com",
        robots={"disallow": [], "sitemaps": []},
        sitemap_urls=["https://www.x.com/about", "https://other.com/foo"])
    urls = [c.url for c in plan.crawl]
    assert "https://www.x.com/about" in urls
    assert "https://www.x.com/foo" not in urls          # not rewritten + crawled
    assert all("other.com" not in u for u in urls)
    reasons = {s["url"]: s["reason"] for s in plan.skipped}
    assert reasons.get("https://other.com/foo") == "offsite"


def test_plan_crawl_respects_max_pages_and_records_overflow():
    html = "<html><body>" + "".join(
        f'<a href="/s/{i}">S{i}</a>' for i in range(20)) + "</body></html>"
    plan = plan_crawl("https://www.x.com/", html, max_pages=5, host="www.x.com")
    assert len(plan.crawl) == 5
    assert any(s["reason"] == "beyond-max-pages" for s in plan.skipped)
