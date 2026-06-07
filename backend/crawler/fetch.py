"""Page fetching with JS rendering via Playwright (Chromium, headless).

Static-HTML crawlers miss content on most modern HVAC/service sites because
hero copy, service grids, and FAQs are rendered client-side. We therefore
render every page in a real browser, let the network settle, and scroll to
trigger lazy-loaded content before capturing the final HTML.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Browser, TimeoutError as PlaywrightTimeoutError

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ProPlanABI/0.1 (+crawler)"
)


@dataclass
class FetchResult:
    url: str            # final URL after redirects
    status: int | None  # HTTP status of the main response (None if unknown)
    html: str           # fully-rendered HTML
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.html)


def _auto_scroll(page) -> None:
    """Scroll to the bottom in steps so lazy-loaded sections render."""
    try:
        page.evaluate(
            """
            async () => {
              await new Promise((resolve) => {
                let total = 0;
                const step = 400;
                const timer = setInterval(() => {
                  window.scrollBy(0, step);
                  total += step;
                  if (total >= document.body.scrollHeight) {
                    clearInterval(timer);
                    resolve();
                  }
                }, 100);
                // Hard cap so pathological pages can't hang the scroll.
                setTimeout(() => { clearInterval(timer); resolve(); }, 4000);
              });
            }
            """
        )
    except Exception:
        # Scrolling is best-effort; never fail a fetch because of it.
        pass


def fetch_page(
    browser: Browser,
    url: str,
    *,
    timeout_ms: int = 30000,
    user_agent: str = DEFAULT_USER_AGENT,
) -> FetchResult:
    """Render a single URL and return its final HTML.

    Uses a fresh context per page for isolation. Errors are captured on the
    result rather than raised so a single bad page never aborts a crawl.
    """
    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1366, "height": 900},
        ignore_https_errors=True,
        locale="en-US",
    )
    page = context.new_page()
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        # Give client-side rendering a chance to settle; networkidle is best
        # effort because chat widgets / analytics may never go fully idle.
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass
        _auto_scroll(page)
        html = page.content()
        final_url = page.url
        status = response.status if response else None
        return FetchResult(url=final_url, status=status, html=html)
    except PlaywrightTimeoutError:
        return FetchResult(url=url, status=None, html="", error="timeout")
    except Exception as exc:  # noqa: BLE001 - capture any nav failure
        return FetchResult(url=url, status=None, html="", error=f"{type(exc).__name__}: {exc}")
    finally:
        context.close()
