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

## Goal 03 — ABI  ✅ COMPLETE (2026-06-07)

Build the ABI scoring system. Split into two validation bars (per agreed plan):
**03A — Scoring Engine** (prove formulas/evidence/recs on the 20+ validated
profiles) and **03B — Benchmark** (expand to 50 sites, distribution + averages).

### Success criteria
- [x] Overall ABI score per site
- [x] 5 component scores (AI Understanding, AI Retrieval, AI Recommendation,
      Agent Readiness, Semantic Authority)
- [x] Each score carries rationale + supporting evidence + recommendation
- [x] Scores are explainable, repeatable, defensible, actionable
- [x] 03B — expanded dataset to 50 passed sites, re-scored, benchmark locked

### 03B validation (benchmark) — PASS
Expanded the extraction set and re-scored the **50** sites that passed
extraction (`run_abi_validation.py --min 50 --passed-only`): **50/50
explainable, repeatable, schema-valid**.

Extraction expansion economics (gpt-4o-mini, new sites only — 21 prior profiles
reused at $0):
- Attempted **70**, successful crawls **52**, passed extractions **50**,
  failed **20**; schema stable (52/52).
- Tokens **374,774** (282,150 prompt + 92,624 completion); est. **$0.098**
  (~$0.0034 per newly-extracted site); ~**55.7 min** wall.

### 03C — hardening pass (post-review) — DONE
A code review flagged five issues; all fixed before the dashboard, then the 50
profiles were re-extracted (reuse cached crawl; ~$0.18, ~42 min) to apply the
merge-stage fixes, and re-scored:
- **FAQ merge:** deterministic schema.org FAQPage + markdown Q/A pairs now seed
  the profile FAQ list (previously FAQs came only from the LLM), so FAQ content
  the model missed still counts. (`semantic_profile._rule_faq_mentions`)
- **schema.org signal:** profile-level `structured_data` block (built from
  rule_facts) feeds the ABI authority criterion, which now gives graduated
  credit (business schema 20 + FAQPage 15). Fixes undercounting where valid
  LocalBusiness/Organization schema wasn't attached to an extracted fact.
- **Weights aligned to PRD** (Retrieval 25%, Agent Readiness 15%); weights +
  grade bands single-sourced in `schema.py` so the validator enforces them.
- **Validator tightened:** `validate_abi_score` now checks weight sum = 1,
  weights match the contract, criterion bounds, grade↔score, and overall =
  weighted average — bad/stale score blocks fail loudly.
- **Artifact freshness:** a shared `_persist` writes all artifacts on every
  path; `reuse_profile` refreshes them; new `reuse_extraction` mode re-merges +
  re-scores from cached crawl + cached LLM outputs for free (extractions are now
  cached in `extractions.json`).
- **Robustness:** list/dict-valued schema.org fields no longer crash extraction
  (resolved blocker).

Benchmark (50 sites, after hardening): avg ABI **68.2**, range **3.8–87.0**,
grades **B:16 C:26 D:6 F:2**.
- Component averages: Understanding **86.0**, Recommendation **71.4**, Retrieval
  **64.8** (was 51.3 — FAQ merge), Semantic Authority **62.7** (was 47.7 —
  schema.org now detected), Agent Readiness **45.4** (unchanged signal; weight
  20→15%).
- Top 5: snell (87.0), fhfurr (85.7), mauzy (83.9), petriplumbing (81.5),
  fixmyhome (81.4). Bottom 5: cmcservice (3.8), goodberlet (19.0),
  allproplumbing (48.1), donnellymech (54.0), petro (58.3).
- Most common missing criteria: **FAQ coverage** (19), heading structure (14),
  schema.org (5). Core finding holds and is now better-calibrated: the industry
  describes itself well (Understanding 86) but is weakest on agent-actionability
  (Agent Readiness 45).

Reports: `backend/validation/goal_03b_benchmark.md`,
`backend/validation/abi_validation_report.md`
Summary: `backend/validation/abi_validation_summary.json`
Tests: 36 passing (12 ABI scoring + validator + FAQ/schema merge).

### 03A validation (scoring engine) — PASS
Scored all **21** cached, extraction-valid profiles (no crawl, no LLM — free,
instant, deterministic):
- **21/21 explainable** (overall + 5 components + per-criterion rationale +
  prioritized recommendations),
- **21/21 repeatable** (identical on re-score),
- **21/21 score-block schema-valid**.

Benchmark (21 sites): avg ABI **65.5**, range **0.6–83.6**, grades B:5 C:11 D:4 F:1.
- Component averages: Understanding **85.1**, Recommendation **74.0**, Retrieval
  **55.8**, Agent Readiness **52.1**, Semantic Authority **52.1**.
- Industry-wide weaknesses: missing **FAQ** content (top fix on 9 sites) and
  **schema.org** structured data (7 sites).

Report: `backend/validation/abi_validation_report.md`
Summary: `backend/validation/abi_validation_summary.json`

### Architecture
- `backend/app/services/abi_score.py` — deterministic scoring engine. Five
  dimensions, each a set of named, weighted criteria; every criterion emits
  earned/max points + rationale + evidence + (when short) a recommendation.
  Overall = weighted average → letter grade band. Recommendations are ranked by
  **ABI impact** (points left × dimension weight) so fixes are prioritized.
- `backend/app/schema.py` — `validate_abi_score()` contract.
- `app/pipeline.py` — stage 9 (`score_abi`) added; `abi_score` written into
  `profile.json` + standalone `abi_score.json` artifact; `pipeline.json` carries
  `abi_overall`/`abi_grade`. Deterministic, so the cached-profile fast path
  recomputes it for free.
- `backend/run_abi_validation.py` — Goal 03 harness (`--min 20` = 03A, `--min 50`
  = 03B). Scores cached profiles; checks explainable/repeatable/schema; emits a
  benchmark (avg/low/high, component averages, grade distribution, common
  weaknesses).
- 10 offline scoring tests; **25 tests total**, all passing.

### Score-quality review (before locking formulas)
- The B-grade ceiling is real, not a bug: 7/21 sites have schema.org, 11/21 have
  FAQ — top sites genuinely miss schema/booking/reputation breadth, so they
  legitimately top out in the low 80s. Supports the ABI thesis that most
  businesses are not yet AI-optimized.
- Spot-checked outliers (morrisjenkins 54 D, reliablehomecomfort 0.6 F) — scores
  and recommendations are defensible. The lone F is a near-empty extraction
  (homepage only); kept in the benchmark as a genuine "invisible to AI" case.

### Open issues
- `rotorooter.com` crashed extraction (`'list' object has no attribute 'lower'`)
  — a Goal 02 schema.org coercion bug, logged in `progress/blockers.md`. Dropped
  from the pool; did not block reaching 50.
- Several 03B candidate domains failed to crawl ("no pages crawled" — bot
  protection or bad/fabricated domains); two crawled single-page only
  (cmcservice, goodberlet) and legitimately score F. Non-blocking — 50 reached.
- Goal 02 extraction occasionally files value-props ("upfront pricing") under
  `trust_signals`; ABI's reputation-diversity criterion handles this gracefully
  (flags weak proof) but cleaner extraction would sharpen recommendation scores.

### Lessons learned
- Deterministic scoring paid off: re-scoring 50 profiles is instant and free, and
  the cached-profile reuse meant 03B's $0.098 was spent only on the 29 new sites.
- A bigger sample (21→50) didn't move the shape of the story: Understanding stays
  high (~86), Agent Readiness + Semantic Authority stay low (~45–48). The
  industry-wide FAQ/schema.org gap is the core sellable ABI finding.
- Crawl depth matters for ABI: single-page crawls (cmcservice, goodberlet) score
  F not because the business is weak but because little was retrieved — a crawler
  discovery limitation, not a scoring flaw.

### Next
- Goal 04 — Dashboard. Each of the 50 sites has `profile.json` (with `abi_score`)
  + `abi_score.json` ready to render.

## Goal 04 — Dashboard  ✅ COMPLETE (2026-06-07)

Build the user-facing dashboard that makes ABI understandable to a business
owner. Presentation + workflow only — no scoring/extraction logic changed; every
value is read straight from the real artifacts.

### Success criteria
- [x] Enter a URL (live pipeline run) — `RunPanel` → `POST /api/runs`
- [x] View run status — background job + polling, live stages
      (crawling → extracting → scoring → done)
- [x] View ABI score + grade — `ScoreHero`
- [x] Five dimension cards — `DimensionCards` (PRD weights 25/25/20/15/15)
- [x] Top prioritized recommendations — `Recommendations` (ranked by ABI impact)
- [x] Evidence / rationale view — `EvidenceView` (click a dimension)
- [x] Download report — self-contained HTML (`GET /api/sites/{d}/report`)
- [x] Browse the 50 scored sites + industry benchmark strip

### Validation — complete end-to-end workflow (verified live in-browser)
Drove the running app with Playwright: loaded the gallery (53 scored sites,
benchmark avg 68.2), opened a site (Snell, ABI 87 B — all cards/recs/evidence
bound to real data), then **submitted a live URL (coolray.com)** and watched the
status go crawling → extracting → scoring → done, after which the detail loaded
(ABI 73.9 C) with a working report download. No mocked data anywhere.

### Architecture
- **Backend** `backend/api/` (FastAPI): `store.py` reads the real artifacts;
  `jobs.py` runs the pipeline on worker threads with status polling; `report.py`
  renders the self-contained HTML report; `main.py` exposes
  `/api/sites`, `/api/sites/{d}`, `/api/sites/{d}/report`, `/api/benchmark`,
  `POST /api/runs`, `GET /api/runs/{id}`. The pipeline gained an optional
  `progress` hook (orchestration only — no contract change) for live stages.
- **Frontend** `frontend/` (React + Vite + TS + Chakra UI): typed API client,
  components (RunPanel, SitesGallery, ScoreHero, DimensionCards, Recommendations,
  EvidenceView, BenchmarkBar). Vite proxies `/api` to the backend. `npm run build`
  is clean.

### Run it
```
uvicorn backend.api.main:app --port 8000      # backend (needs OPENAI_API_KEY for live runs)
cd frontend && npm install && npm run dev      # http://localhost:5173
```

### Open issues
- Jobs are in-memory (single process); fine for the MVP/local use, not
  horizontally scalable. A durable queue is a future concern, not MVP.
- Live runs depend on the crawler; bot-blocked sites surface as a run error in
  the UI (handled gracefully), same as the Goal 01/02 behaviour.

### Lessons learned
- Keeping scoring deterministic + artifact-first made the dashboard thin: the UI
  is pure presentation over JSON the pipeline already wrote, so there was nothing
  to mock and no risk of the UI and the score diverging.

---

## Crawl coverage hardening — 2026-06-07

Triggered by an inaccurate ABI report for **proplansolutions.io** (a shallow
crawl). ABI scoring left unchanged.

### Problem
Only 6 of ~10 meaningful pages were crawled — the product page and most blog
posts were missed. Discovery was homepage-only (single hop), `max_pages=6`, the
sitemap was ignored, and priority keywords were HVAC-specific (no signal on a
SaaS site).

### Fix
- Sitemap.xml + robots.txt discovery (recurses a sitemap index); canonical-host
  normalization (www/non-www/http/https/#frag collapse); generalized priority
  keywords; `max_pages` 6→12 + `max_depth=2` BFS fallback.
- First-class crawl diagnostics in `crawl_coverage.json`: `discovered_urls`,
  `skipped_urls` (+reason), `crawled_urls` (+`link_source`/`depth`), canonical
  host, robots/sitemap facts, `final_page_count`, `low_coverage` + `warning`.
  Kept out of `profile.json` (extraction contract untouched).
- HTML report + dashboard show a "Low Crawl Coverage Warning" when fewer pages
  are crawled than the site advertises.

### Result
proplansolutions.io: **10/10 meaningful pages** crawled (privacy/terms skipped),
profile now has business name, industry, 44 services, 5 FAQs; no false warning.
46 tests passing (8 new for discovery/coverage). Files: `backend/crawler/
discover.py`, `backend/app/services/crawler.py`, `backend/app/pipeline.py`,
`backend/api/{store,report}.py`, `frontend/src/App.tsx`.

---

## Goal 03D — ABI Calibration Hardening  ✅ COMPLETE (2026-06-08)

Refined score *correctness* without touching the ABI framework (same 5
dimensions, weights, grade bands, criteria). Three engine defects fixed; cached
profiles re-scored for free (no LLM).

### Completed work
- **Pillar 1 — FAQ validity gate.** New `faq_validator.py`; Layer A restricts the
  markdown FAQ heuristic to FAQ-context pages (`rule_extractor._has_faq_context`);
  Layer B validates every FAQ candidate at the merge choke point in
  `semantic_profile.build_profile` (schema-sourced FAQs trusted, all else hard-
  validated). Fake "?"-fragment + CTA-answer FAQs no longer count.
- **Pillar 2 — Confidence-aware scoring.** `abi_score` now earns
  `points × evidence × conf_factor`, `conf_factor = min(1, conf/FULL_CONF)`,
  `FULL_CONF=0.7` (saturating — high-confidence facts unaffected). Count criteria
  use a confidence-weighted effective count; Location presence is confidence-
  gated (the Austin, TX @ 0.15 → 20/20 bug).
- **Pillar 3 — Booking/actionability.** New `actionability.py` detects tiered
  booking (T3 scheduler/`potentialAction`/`booking_url` → T2 form → T1 intent CTA
  → T0) from the already-crawled link graph + schema + CTAs. The binary *Online
  booking* criterion is now graduated (T3 20 / T2 12 / T1 6 / T0 0), evidence-
  bearing. `abi_evidence` booking line made actionability-aware.

### Result
- **ProPlan 59.7 → 42.0 (D)** — down for the right reasons: 0 FAQs (fakes gone),
  Location 20→4.3 (conf-gated), Booking 0→20 (Calendly T3). Retrieval 67→18,
  Authority 38.6→20.9, Agent Readiness 15→34.1.
- **Corpus:** booking credit now fires on **42/54** sites (T3 4 · T2 16 · T1 22)
  vs the old 3. Benchmark: 54 sites, avg ABI 61.7, all explainable/repeatable/
  schema-valid (PASS).
- **Tests:** 90 passing (68 → 90; +22 across `test_faq_validator`,
  `test_confidence_aware_scoring`, `test_actionability` + pipeline integration).
  `validate_abi_score` unchanged and green for all 54.

### Lessons learned
- The ProPlan fakes are caught by fragment-question + CTA-answer detection, not
  the answer-length floor — so length thresholds could be relaxed (15 chars / 3
  words) to keep legitimately terse real FAQs without readmitting fakes.
- `FULL_CONF=0.7` saturation is what makes confidence-aware scoring safe: the
  high-confidence HVAC fixture is unaffected (still ≥85), only weak evidence is
  discounted. Left at 0.7 per plan — to be tuned only after distribution review.
- Two existing fixtures encoded behavior the gate deliberately changes (a
  markdown FAQ on a non-FAQ page; a trivial `"Yes."` schema answer) and were
  updated to realistic inputs.

---

## Goal 03E — Extraction Hygiene  ✅ COMPLETE (2026-06-08)

Labelled every fact's provenance and routed non-first-party facts out of the
scored lists so counts are believable and trust is attributable. **No ABI
scoring/dimension/weight/grade-band change** — ABI moves only because the scorer
receives cleaner inputs.

### Completed work
- New `provenance.py`: `classify_service` / `classify_trust` / `classify_offer`
  (pure, deterministic, no LLM). Six labels: first_party_service, blog_example,
  case_study, testimonial, offer, pricing_tier (+ residual trust_signal).
- **Conservative bias (per instruction):** a service is `blog_example` only when
  sourced *exclusively* from an actual blog page and uncorroborated elsewhere;
  ambiguous → first_party. case_study/testimonial/pricing_tier require a clear
  positive pattern, else the item stays first-party.
- `normalizer._token_key`: strip leading marketing qualifiers (Custom/Advanced/
  AI-Powered/…) while keeping core domain nouns, so near-duplicates collapse
  without over-merging distinct offerings. HVAC canon table untouched.
- `semantic_profile.build_profile`: partition services/trust/offers at the merge
  choke point; tag `provenance` on every item; add non-scored sibling fields
  `blog_examples` / `case_studies` / `testimonials` / `pricing_tiers`. Routing is
  loss-less (scored + sibling = all facts).

### Result (cached re-merge + re-score, free)
- **ProPlan:** services **44 → 14** (believable; 29 → blog_examples), trust
  **12 → 4** (8 → case_studies), offers **4 → 1** (3 → pricing_tiers), ABI
  **42.0 → 39.0** — down purely from cleaner extraction.
- **Corpus (54):** services 1001→963, trust 490→482, offers 152→129; separated
  37 blog_examples · 8 case_studies · 23 pricing_tiers; avg ABI 61.7→61.5.
- **No regression:** 0 sites lost all services; HVAC benchmark service counts
  unchanged (real local-service offerings preserved). Diff:
  `backend/validation/extraction_hygiene_diff.md`.
- **Scoring untouched:** `abi_score.py` not edited; a guard test confirms the
  scorer ignores the new sibling fields. 119 tests pass (+29 since 03D).

### Lessons learned
- Provenance is fully derivable at merge from already-cached signals (page
  category, evidence text) — no LLM re-extraction, so the whole goal re-runs free.
- The conservative bias is what protects the HVAC benchmark: requiring an actual
  `blog` page (not merely `unknown`) before reclassifying keeps real services in.
- One borderline case study ("satisfaction increased from 3.2/5 to 4.7/5") stays
  in trust because the outcome regex doesn't match ratio "/5" deltas — a safe
  false-negative (keeps first-party), acceptable under the stated bias.

---

## ABI v0.1.1 — FROZEN release  🔒 (2026-06-08)

Froze the ABI measurement instrument and shifted the project into its UX/report
phase. **No code path that computes a score changed** — this release is a freeze,
a version stamp, enforcement, and documentation.

### What was frozen (no change without a benchmark review)
Scoring dimensions, scoring weights, grade bands, extraction contracts, and the
provenance taxonomy. Authoritative spec: `abi_spec_v0.1.1.md`; change policy in
its §6.

### Delivered
- `schema.ABI_VERSION = "0.1.1"` (single source of truth) and
  `provenance.PROVENANCE_LABELS` (frozen 7-label set).
- `backend/tests/test_abi_freeze.py` — pins dimensions, weights, bands,
  extraction-contract field lists, provenance labels, per-dimension criterion
  names, and the 100-point-per-dimension invariant. Changing any frozen value
  fails this test on purpose (the enforcement teeth).
- Version stamped onto release artifacts (`abi_score.json`, `pipeline.json`) for
  traceability — the score block/logic is untouched (stamp is metadata).
- `CHANGELOG.md` (v0.1.1 history) + ROADMAP freeze banner + Phase 2 focus
  (UX / report generation / workflow / explainability).

### Verification
130 backend tests pass (+8 freeze guards). All 54 cached artifacts re-stamped to
v0.1.1 (free, $0); benchmark unchanged (54 sites, avg ABI 61.5, all
explainable/repeatable/schema-valid). ProPlan 39.0 (deterministic, unchanged).

---

## Funnel + Payments — Landing → Teaser → Pilot $399 → Gated Report (2026-06-28)

Aligned the product flow with the sales ladder (`sales/strategy.md` §5). The
landing CTA no longer dumps anonymous visitors into the full internal dashboard
(the paid deliverable). New flow: **enter URL → live audit → free teaser (grade +
#1 gap) → Stripe $399 checkout → unique buyer report link.**

### Delivered
- **Backend**
  - `GET /api/teaser/{domain}` (`store.load_teaser`) — grade + single top gap
    only; the dimension/criteria/evidence breakdown is never sent to anonymous
    clients.
  - `billing.py` — Stripe Checkout for the Pilot Audit ($399); `create_checkout`,
    `grant_for_session` (verify-on-redirect), and a `checkout.session.completed`
    webhook as backup. Degrades to a clean 503 when `STRIPE_SECRET_KEY` is unset.
  - `grants.py` — file-based purchase grants under `output/_grants/`; opaque token
    → domain, idempotent per Stripe session, sample token for the public demo.
  - `ratelimit.py` — per-IP (2/hr, 5/day) + global (25/day) caps (conservative
    launch defaults, env-overridable); `ALLOW_PUBLIC_RUNS` now defaults **on** so
    the funnel works, protected by these caps + crawl reuse.
  - Token-gated `GET /api/reports/{token}` (+ HTML download).
- **Frontend**
  - `Landing.tsx` — inline audit state machine + grade/teaser overlay + buy button
    (no longer switches to the dashboard).
  - `BuyerReport.tsx` — the paid report, scoped to one token-fetched domain (reuses
    `ScoreHero`/`DimensionCards`/`Recommendations`/`EvidenceView`; no gallery/run panel).
  - `Root.tsx` — query-param routing: `?report=<token>` (buyer/sample),
    `?session_id=` (verify payment), `?admin=<secret>` (internal dashboard), else landing.

### Open issues
- Rate limiting + jobs are in-memory/per-process — move to Redis/Supabase before
  scaling the API horizontally (counts reset on deploy/restart).
- Grant store is file-based under `output/_grants/` — keep on the Railway volume
  so buyer links survive redeploys.

### Verification
149 backend tests pass. Frontend `tsc -b` clean; production build OK.
Live payment path requires Stripe keys (test card `4242…`) to exercise end-to-end.

---

## GTM Package — Complete (2026-07-06)

Full go-to-market package delivered in `gtm/` (16 deliverables, indexed in
`gtm/00_README.md`), built on the existing `sales/` kit.

### Completed work
- ICP (HVAC owner-operator primary; agency reseller secondary) + TAM/SAM/SOM
  (~$600M / ~$210M / $100–150k yr-1) + competitive landscape (6 classes; open
  lane = SMB site-side instrument + fix loop)
- Vertical decision: **HVAC first** (benchmark-calibrated), plumbing at day 60+
- Pricing/packaging ladder finalized: $0 grade / $399 founding / $749 audit /
  $2,500 fix / $299mo monitoring + guarantee + reseller terms
- Landing page copy v2 (HVAC-specific, free-grade capture), sales deck
  (gtm/AIVE_sales_deck.pptx, QA'd), sales call script, 5-touch audit-led email
  sequence, LinkedIn + Facebook strategies
- 90-day launch roadmap (weekly), KPI dashboard (md + AIVE_kpi_tracker.xlsx,
  formulas verified 0 errors), risk register w/ kill criteria, pre-launch
  product P0/P1/P2 list
- New skill: `.claude/skills/audit-led-outreach/` (pre-audit → personalize →
  sequence workflow)

### Open issues
- P0 product items block public launch: gate /api/runs, teaser output mode,
  Stripe links, report branding, batch CLI hardening (gtm/15)
- Social accounts + sending domain not yet provisioned

### Lessons learned
- The audit-led wedge (pre-audit every prospect, lead with their grade) is the
  single conversion lever every channel doc reuses — protect audit quality
- Market research confirms pricing gap: self-serve monitors $29–699/mo,
  agencies $1.5k+/mo; the $399–749 one-off evidence-backed audit is unoccupied

---

## Marketing Demo Videos (2026-07-10)

Built platform cuts from the e2e demo recording, saved to `gtm/video/`
(specs + post copy in `gtm/video/16_demo_videos.md`; README updated):

- `aive_demo_linkedin.mp4` — 16:9, 32.4s: hook → captioned demo → benchmark → CTA
- `aive_demo_facebook.mp4` — 1:1, 22.8s: square bands, 2.5× mid-section, CTA

Caption-driven (muted-autoplay); voiceover script remains available for a
sound-on variant. QA'd frame-by-frame (fixed caption-boundary overlap and
white page-load lead-in by trimming demo start to t=3s).

---

## Security hardening + deploy readiness (2026-08-09)

Launch-readiness security review of the funnel/payments/public-run paths, all
fixes landed with tests. This closes the P0 security items flagged in the
2026-07-06 GTM "open issues" (gate `/api/runs`, teaser-only anonymous output,
verified Stripe path).

### Delivered
- **C1** — internal `/api/sites*` routes gated behind `ADMIN_API_KEY`
  (`X-Admin-Key` header or `?admin=`); loopback-only when unset (closed by
  default remotely). Closes a paywall bypass that served the full paid report
  unauthenticated.
- **C2** — Stripe webhook signature always verified; the unverified fallback is
  removed, so a forged `checkout.session.completed` can never mint a grant (503
  until `STRIPE_WEBHOOK_SECRET` is set).
- **H1** — SSRF guard (`backend/api/ssrf.py`) resolves the target host to IPs and
  blocks private/loopback/link-local ranges before the crawl.
- **H2** — proxy-aware client IP: rate limiting reads `X-Forwarded-For` when
  `TRUST_PROXY=true` (correct keying behind Vercel/Railway).
- **M1** — domain-slug validation in `store.py` (no path traversal).
- **M2** — `POST /api/checkout` is rate-limited on the same per-IP/global caps.
- **L1** — optional grant TTL (`GRANT_TTL_DAYS`, default `0` = never expires).
- **L2** — background-job errors sanitized (detail logged server-side, generic
  message returned to the client).

### Cost controls (launch posture)
- Rate-limit defaults lowered to **2/IP-hour, 5/IP-day, 25 global/day**
  (env-overridable), sized to a ~$25/mo OpenAI budget alert.
- Documented OpenAI budget alert + Vercel WAF rules in `DEPLOYMENT.md §4/§4a`.

### Deploy artifacts
- Added `Dockerfile` (MS Playwright python image, `$PORT`-aware uvicorn),
  `.dockerignore`, and `frontend/vercel.json` (`/api/*` → Railway rewrite,
  placeholder destination).

### Open issues
- `frontend/vercel.json` destination is a placeholder — fill in the real Railway
  URL after the backend deploys.
- Rate limiting/jobs remain in-memory/per-process (counts reset on restart); move
  to Redis/Supabase for a real hard spend cap.

### Verification
149 backend tests pass; frontend `tsc -b` + production build clean. Shipped on
branch `funnel-payments-pricing` (PR #1).
