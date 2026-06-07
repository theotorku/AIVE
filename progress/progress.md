# Progress

## Goal 01 — Crawler  ✅ COMPLETE (2026-06-06)

Build website crawling and markdown conversion.

### Success criteria
- [x] Crawl website URL
- [x] Support JS-rendered pages (Playwright / Chromium, scroll + network settle)
- [x] Convert pages to clean markdown (trafilatura, bs4 fallback)
- [x] Remove navigation/footer noise (verified on real output)
- [x] Export markdown (per-page `.md`, combined `_site.md`, `_crawl.json`)

### Validation
- [x] Successfully process 10 HVAC websites — **10/10 passed**
- [x] Markdown is readable — spot-checked; main content preserved, chrome stripped
- [x] No critical errors — every accepted site produced readable markdown

Report: `backend/validation/validation_report.md`
Summary: `backend/validation/validation_summary.json`

### Completed work
- `backend/crawler/` package: `fetch` (Playwright render), `clean`
  (noise removal + HTML→markdown), `discover` (same-domain link prioritization),
  `crawl` (orchestration + export).
- `backend/cli.py` single-site entrypoint; `backend/run_validation.py` harness.
- 5 offline unit tests (cleaning, markdown, discovery) — all passing.
- Validated against 11 HVAC sites; 10 passed (target met).

### Open issues
- `hortonservices.com` failed to render (timed out / blocked at fetch, 0 pages).
  Not blocking — target met with spare sites. Logged in `progress/blockers.md`.
- `networkidle` never settles on some sites (chat widgets/analytics); handled
  with an 8s cap, but very heavy sites add latency (e.g. goettl.com ~88s).

### Lessons learned
- JS rendering is mandatory: several sites return little/no usable content
  without it. Auto-scroll meaningfully improves lazy-loaded capture.
- trafilatura gives clean main-content markdown across varied templates; the
  bs4 fallback is rarely needed but worth keeping for odd/small pages.
- Per-site crawl time is dominated by network settle, not parsing.

### Next
- Goal 02 — Extraction. Do not start until Goal 01 validation is accepted (it is).

---

## Goal 02 — Extraction  ✅ COMPLETE (2026-06-06)

Build semantic extraction engine.

### Success criteria (extract)
- [x] Services
- [x] Locations  (+ service_areas as a distinct field)
- [x] FAQs
- [x] Contact Information (phone, email, address, hours, booking_url)
- [x] Offers
- [x] business_name (bonus, per PRD)

### Validation
- [x] Run against 20 websites — **20/20 passed**
- [x] Outputs are accurate — coverage tracked per field; spot-checked
      (e.g. morrisjenkins.com: correct services, Charlotte NC, phone, offer)
- [x] JSON schema is stable — **21/21 crawled sites schema-valid (STABLE)**

Report: `backend/validation/extraction_validation_report.md`
Summary: `backend/validation/extraction_validation_summary.json`

### Approach
- LLM extraction via OpenAI (`gpt-4o-mini`) using **Structured Outputs**
  (strict `json_schema`) so the model is forced to emit conforming JSON,
  `temperature=0` for repeatability.
- Stable schema defined once in `backend/extraction/schema.py` and enforced
  again by a dependency-free local validator (provider-independent guarantee).
- Engine reads Goal 01 crawl markdown -> `extraction.json`; `reuse` flag caches
  results so re-runs are fast/cheap; crawl failures yield a schema-valid empty
  payload (counted as crawl failure, never as schema instability).

### Completed work
- `backend/extraction/` package: `schema`, `extract` (OpenAI call + token
  accounting), `engine` (crawl->extract orchestration).
- `backend/extract_cli.py` single-site entrypoint; `run_extraction_validation.py`
  harness with crawl/schema/accuracy reporting.
- 10 offline extraction tests (schema contract + guards); **15 tests total**.

### Open issues
- 4 sites were crawl-blocked (hellerphc, jacksonsfourseasons, hauke,
  comfortexperts, estesservices) — bot protection / no rendered content. Not
  blocking (target met with spares). Logged in `progress/blockers.md`.
- FAQ coverage is uneven: depends on whether the crawler's page budget hit an
  FAQ page. Future: bias discovery toward `/faq` when present.

### Lessons learned
- Structured Outputs + a local validator gives genuinely stable schema across
  20+ varied sites with zero post-processing.
- Schema stability must be measured over *successfully crawled* sites; mixing in
  crawl failures falsely reads as schema instability.
- Per-site extraction is cheap (~6.9k tokens, ~$0.0012 on gpt-4o-mini).

### Next
- Goal 03 — ABI scoring. Inputs (extraction.json) are now available per site.

---

## Goal 03 — ABI  ⏳ NOT STARTED
## Goal 04 — Dashboard  ⏳ NOT STARTED
