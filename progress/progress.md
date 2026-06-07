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

Also extracted (per the redesign): industry, trust_signals, ctas, and
per-fact evidence + confidence + source provenance.

### Validation (staged pipeline)
- [x] Run against 20 websites — **20/20 passed**
- [x] Outputs are accurate — per-field coverage tracked + spot-checked (e.g.
      morrisjenkins.com: Morris-Jenkins / HVAC, 9 services, Charlotte NC, phone
      from rules, trust signals, CTAs, ABI evidence)
- [x] JSON schema is stable — **21/21 crawled sites profile-valid (STABLE)**

Report: `backend/validation/extraction_validation_report.md`
Summary: `backend/validation/extraction_validation_summary.json`

### Architecture (redesigned per spec — LLM is one component, not the engine)
Staged pipeline in `backend/app/services/`, orchestrated by `app/pipeline.py`:
crawl → clean → markdown → classify → rule extract → llm extract → normalize →
confidence → merge profile → ABI evidence.
- **Rules before AI:** deterministic facts (phone/email/address regex,
  schema.org JSON-LD, headings, slugs, FAQ blocks) ground the LLM.
- **Per-page LLM pass:** strict per-page schema; each item carries an evidence
  snippet + self-confidence.
- **Confidence engine:** reconciles LLM self-confidence with structural signals
  (headings, nav, schema.org, cross-page repetition, page category) → score +
  reason.
- **Normalizer + conflict-aware merge:** canonical services/areas with aliases;
  site profile keeps every value with evidence + source pages.
- **ABI evidence:** qualitative observations across the 5 PRD dimensions
  (scores remain Goal 03).
- **Caching:** rich crawl (`page_documents.json`) + profile reuse for fast/cheap
  re-runs.

### Completed work
- `backend/app/schema.py` (data shapes, per-page LLM schema, profile contract +
  validator) and 10 `app/services/` modules.
- `app/pipeline.py` orchestration; `extract_cli.py` + `run_extraction_validation.py`
  repointed to the pipeline.
- 10 offline pipeline tests (classify/rules/normalize/confidence/merge);
  **15 tests total**. Removed the superseded v1 single-pass extractor.

### Open issues
- 5 sites were crawl-blocked (hellerphc, jacksonsfourseasons, hauke,
  comfortexperts, estesservices) — bot protection / no rendered content. Not
  blocking (target met with spares). Logged in `progress/blockers.md`.
- FAQ coverage is uneven (depends on whether the page budget hit an FAQ page);
  the rule extractor's markdown FAQ heuristic helps but a `/faq` discovery bias
  would help more.

### Lessons learned
- Combining deterministic rules + a per-page LLM + a structural confidence
  engine yields far richer, more defensible output than single-pass extraction,
  while keeping the schema stable across 21 varied sites.
- Rule-derived contact facts (phone/email) are more reliable than LLM guesses;
  using them as grounding hints improved contact accuracy.
- The rich pipeline costs more than v1 (~$0.0036/site vs ~$0.0012) but produces
  evidence + confidence + normalization that Goal 03 needs.

### Next
- Goal 03 — ABI scoring. Each site now has a `profile.json` with `abi_evidence`
  ready to score.

---

## Goal 03 — ABI  ⏳ NOT STARTED
## Goal 04 — Dashboard  ⏳ NOT STARTED
