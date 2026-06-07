# Decisions

Architecture and product decisions, newest first.

## 2026-06-06 — Goal 01 crawler stack

- **JS rendering with Playwright (Chromium, headless).** Most HVAC/service
  sites render hero copy, service grids, and FAQs client-side. Static fetch
  misses them. Trade-off: slower per page; mitigated with a network-settle cap
  and bounded auto-scroll.
- **trafilatura for extraction → markdown, BeautifulSoup+markdownify fallback.**
  trafilatura isolates main content and strips chrome well across varied
  templates and emits markdown directly. The structural fallback covers the
  rare pages where it returns too little.
- **Bounded, prioritized internal-link discovery (default 6–8 pages).** Crawl
  the homepage plus the highest-value same-domain pages (services, about,
  contact, FAQ, areas served) instead of the whole site. Keeps Goal 01 fast
  and focused; full-site crawling is out of scope.
- **Per-site failures are non-fatal.** A page or site that fails is recorded,
  not raised, so a batch run completes and reports rather than aborting.
- **Code lives under `backend/`.** Goal 01–03 are Python; the crawler seeds the
  FastAPI backend that later goals build on. `backend/output/` is gitignored;
  validation reports under `backend/validation/` are committed.
