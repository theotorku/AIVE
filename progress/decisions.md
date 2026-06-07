# Decisions

Architecture and product decisions, newest first.

## 2026-06-06 — Goal 02 extraction stack

- **OpenAI for LLM extraction (`gpt-4o-mini`).** Chosen because an
  `OPENAI_API_KEY` was available in the environment and no Anthropic key was;
  confirmed with the user. The engine is provider-shaped (single call site in
  `extract.py`) so swapping providers later is contained.
- **Structured Outputs (strict `json_schema`) + local validator.** The model is
  forced to return schema-conforming JSON; a dependency-free validator re-checks
  every payload so schema stability never relies on trusting the provider.
- **`temperature=0`.** Repeatable, defensible outputs — aligns with the ABI
  principle that results be repeatable.
- **Schema beyond the 5 required fields.** Added `business_name` and a distinct
  `service_areas` (cities/regions served vs. physical `locations`), both in the
  PRD extraction list and useful for ABI scoring.
- **Crawl failure ≠ schema failure.** No-markdown sites return a schema-valid
  empty payload with an error flag; validation measures schema stability only
  over successfully-crawled sites.
- **Cached extractions (`reuse`).** `extraction.json` is reused on re-runs to
  keep iteration fast and cost near-zero; `--fresh` forces re-extraction.

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
