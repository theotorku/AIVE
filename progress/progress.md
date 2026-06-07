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

## Goal 02 — Extraction  ⏳ NOT STARTED
## Goal 03 — ABI  ⏳ NOT STARTED
## Goal 04 — Dashboard  ⏳ NOT STARTED
