"""Unit tests for noise removal, markdown conversion, and link discovery.

These run offline against fixed HTML so the core logic is verified without a
browser or network. The live browser path is exercised by run_validation.
"""

from backend.crawler.clean import html_to_markdown
from backend.crawler.discover import discover_links

SAMPLE_HTML = """
<html>
  <head><title>Acme HVAC</title><style>.x{color:red}</style></head>
  <body>
    <header><nav><a href="/">Home</a><a href="/services">Services</a></nav></header>
    <main>
      <h1>Acme Heating and Cooling</h1>
      <p>We provide trusted AC repair, furnace installation, and 24/7
      emergency heating service across the metro area. Our certified
      technicians have served local homeowners for over twenty years and
      back every job with a satisfaction guarantee.</p>
      <h2>Our Services</h2>
      <ul><li>AC Repair</li><li>Furnace Installation</li><li>Maintenance</li></ul>
    </main>
    <aside class="newsletter">Subscribe to our newsletter!</aside>
    <footer><p>Copyright 2026 Acme HVAC. Privacy Policy.</p></footer>
    <div class="cookie-banner">We use cookies. Accept?</div>
  </body>
</html>
"""


def test_markdown_keeps_main_content():
    md = html_to_markdown(SAMPLE_HTML, url="https://acme-hvac.example")
    assert "Acme Heating and Cooling" in md
    assert "AC Repair" in md
    assert "Furnace Installation" in md


def test_markdown_strips_chrome_and_noise():
    md = html_to_markdown(SAMPLE_HTML, url="https://acme-hvac.example").lower()
    assert "subscribe to our newsletter" not in md
    assert "we use cookies" not in md
    assert "privacy policy" not in md


def test_empty_html_returns_empty():
    assert html_to_markdown("") == ""
    assert html_to_markdown("   ") == ""


def test_discover_prioritizes_business_pages():
    html = """
    <html><body>
      <a href="/">Home</a>
      <a href="/privacy">Privacy</a>
      <a href="/services">Our Services</a>
      <a href="/faq">FAQ</a>
      <a href="https://facebook.com/acme">Facebook</a>
      <a href="/brochure.pdf">Download Brochure</a>
      <a href="/about-us">About Us</a>
      <a href="mailto:info@acme.com">Email</a>
    </body></html>
    """
    base = "https://acme-hvac.example"
    links = discover_links(base, html, max_pages=5)

    assert links[0].rstrip("/") == base              # homepage always first (canonicalized)
    assert any(l.endswith("/services") for l in links)
    assert any(l.endswith("/faq") for l in links)
    # External, mail, and file links must be excluded.
    assert not any("facebook.com" in l for l in links)
    assert not any(l.endswith(".pdf") for l in links)
    assert not any("mailto" in l for l in links)


def test_discover_respects_max_pages():
    html = "<html><body>" + "".join(
        f'<a href="/page-{i}">Page {i}</a>' for i in range(50)
    ) + "</body></html>"
    links = discover_links("https://acme-hvac.example", html, max_pages=4)
    assert len(links) == 4
