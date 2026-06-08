# Decisions

Architecture and product decisions, newest first.

## 2026-06-07 — Goal 03: deterministic ABI scoring + two-phase validation

- **Scoring is deterministic, not LLM-based.** ABI scores are pure functions of
  the Goal 02 profile (counts, per-fact confidence, structural signals already
  encoded in `confidence_reason`). This makes scores **repeatable** (same profile
  → same score, every time), **free**, and instant — and re-scoring cached
  profiles costs nothing. Aligns with the ABI principle that scores be
  repeatable and defensible.
- **Criteria-based, evidence-bearing scoring.** Each of the 5 PRD dimensions is a
  set of named, weighted criteria. Every criterion emits earned/max points + a
  rationale + supporting evidence from the profile + (when not maxed) a concrete
  recommendation. No point is unexplained — that is the whole product (audits),
  not an implementation detail.
- **Dimension weights** (sum 1.0): Understanding 0.25, Retrieval / Recommendation
  / Agent Readiness 0.20 each, Semantic Authority 0.15. Understanding leads
  because an agent that can't tell what a business *is* can't retrieve,
  recommend, or act on it.
- **Recommendations ranked by ABI impact** = unfilled points × dimension weight.
  Tells a business the single highest-leverage fix first → actionable.
- **Grade bands** A/B/C/D/F (90/75/60/40/0) with labels (AI-Optimized → Invisible
  to AI). An A is intentionally hard: it requires schema.org + FAQ + full contact
  + booking + depth + reputation breadth. Real HVAC brands top out at B, which is
  the honest, sellable finding.
- **Two-phase validation (user decision).** 03A: prove the engine on the 20+
  already-validated profiles, review quality, stabilize formulas *before*
  crawling more. 03B: only then expand to 50 sites as a separate batch and lock
  the benchmark. Rationale: crawling 50 against an unproven model just
  manufactures noise; the 21 extraction-valid profiles are ideal for ABI v0.1.

## 2026-06-07 — Crawl coverage: sitemap-driven discovery + diagnostics

Investigated a shallow crawl on `proplansolutions.io` (only 6 of ~10 meaningful
pages reached, missing the product page and most blog posts). Root causes:
homepage-only single-hop discovery, `max_pages=6`, HVAC-only priority keywords
(no signal on a SaaS site), and the sitemap being ignored entirely. ABI scoring
was **not** touched.

- **Sitemap.xml is now the authoritative page list.** The crawler reads
  robots.txt (honoring `Disallow` + `Sitemap:` declarations), fetches the
  sitemap(s) (recursing a sitemap index once), and seeds the crawl from it. For
  sites without a sitemap it falls back to on-page links + breadth-first
  expansion up to `max_depth`.
- **One canonical host.** All URLs are normalized (force the homepage's final
  host — e.g. non-www → www — plus https, drop fragments, trim trailing slash)
  so www/non-www/#frag duplicates collapse and "missing" pages aren't miscounted.
- **General priority keywords.** Extended beyond HVAC (product/pricing/features/
  solutions/platform/docs/case-study…) so a SaaS product page ranks above a blog
  post. Sitemap/nav links get a small boost.
- **`max_pages` 6 → 12, added `max_depth=2`.** Captures small sites fully; ~2×
  per-site extraction cost on new crawls, accepted for coverage accuracy.
- **Crawl diagnostics are first-class.** `crawl_documents` now returns a
  `CrawlBundle` (documents + coverage). Coverage records discovered_urls,
  skipped_urls (with reason: offsite/suffix/path-hint/robots-disallow/
  beyond-max-pages), crawled_urls (with link_source + depth), canonical host,
  robots/sitemap facts, final page count, and a low-coverage flag + warning.
- **Coverage lives outside the extraction contract.** It is written to
  `crawl_coverage.json` (+ summary fields in pipeline.json), never into
  profile.json — `validate_profile` and the extraction shape are unchanged.
- **The report warns on shallow crawls.** The HTML report and the dashboard show
  a "Low Crawl Coverage Warning: This report may be incomplete because only X
  pages were crawled." banner whenever fewer pages are crawled than the site
  advertises.

Result on `proplansolutions.io`: 6 → **10/10 meaningful pages** (privacy/terms
correctly skipped), canonical host `www.proplansolutions.io`, no false warning.

## 2026-06-07 — Goal 04: artifact-first dashboard, live runs as background jobs

- **The dashboard is pure presentation over real artifacts.** The FastAPI layer
  reads `profile.json` / `abi_score.json` / `pipeline.json` / the benchmark
  summary and serves them as-is; the React app renders them. No ABI value is
  computed or mocked in the UI, so the dashboard can never disagree with the
  scorer. (Honors the Goal 04 constraint: presentation + workflow only.)
- **Live URL runs execute as background jobs with polled status.** A run can
  take minutes (crawl + per-page LLM), so `POST /api/runs` starts the pipeline on
  a worker thread and the UI polls `GET /api/runs/{id}`. Real stage names come
  from a new optional `progress` hook in `run_pipeline` — orchestration only, it
  touches no data contract or formula.
- **Report = self-contained HTML.** One dependency-free styled `.html` (browser
  Print → Save as PDF covers PDF), instead of adding a server-side PDF library.
  Keeps the backend light and the artifact portable.
- **Stack per CLAUDE.md:** React + Vite + TypeScript + Chakra UI (v2, for a
  stable provider/component API), FastAPI backend. Vite dev-proxies `/api`.
- **Jobs are in-memory.** Single-process registry is right for the MVP; a durable
  queue is explicitly out of scope until there's a reason for it.

## 2026-06-07 — Goal 03 hardening (post-review): merge deterministic evidence, align to PRD

Acted on a code review before starting the dashboard, so `profile.json`,
`abi_score.json`, and the validation summaries can be treated as stable product
contracts:

- **Deterministic FAQ + schema.org evidence merge into the profile.** FAQs were
  built only from LLM mentions; now schema.org FAQPage + markdown Q/A pairs
  (deterministic, from `rule_facts`) are merged too, and a profile-level
  `structured_data` signal carries schema.org presence independent of which fact
  it backed. ABI Retrieval and Authority were being under-scored; both rose
  materially (51→65, 48→63) after the fix — the scores now reflect evidence that
  was always there.
- **Aligned ABI weights to the PRD** (Understanding 25 / Retrieval 25 /
  Recommendation 20 / Agent Readiness 15 / Authority 15), superseding the earlier
  20/20 split. The PRD is the authoritative contract; the weights + grade bands
  now live once in `schema.py` and are imported by the scorer, so they can't
  drift and the validator enforces them.
- **The scoring validator must fail loudly.** `validate_abi_score` now checks the
  arithmetic (weights sum to 1, weights match the contract, criterion bounds,
  grade matches score, overall equals the weighted average), not just shape — a
  stale score block (e.g. old weights) is now rejected, not silently accepted.
- **Cache per-page LLM outputs (`extractions.json`).** The merge + score stages
  can now be re-run with zero LLM cost (`reuse_extraction`), so future scoring
  changes re-apply to the whole dataset for free. Every code path writes
  artifacts through one `_persist` helper, so files on disk always match the
  returned/recomputed scores.
- **One-time re-extraction to apply the merge-stage fixes.** The existing 50
  profiles predated extraction caching, so a single LLM re-extraction over the
  cached crawls (~$0.18) was needed to regenerate them; from here, re-merges are
  free.

## 2026-06-07 — Goal 03B: benchmark on *passed* sites only; reuse prior profiles

- **Benchmark scores the 50 sites that passed extraction, not every crawled
  profile.** `run_abi_validation.py --passed-only` reads the extraction summary
  and excludes profiles that crawled but failed accuracy (sparse/near-empty
  content). Keeps the industry benchmark honest — a near-empty single-page crawl
  is an extraction/crawl failure, not a fair "this business has low ABI" data
  point. (Two such sites — cmcservice, goodberlet — still passed the accuracy
  gate on a single page and legitimately score F; that is correct, not a bug.)
- **Reuse prior profiles during expansion.** Ran the expansion with
  `--reuse-profile` so the 21 already-extracted sites cost $0; only the ~29 new
  sites incurred tokens. Made 03B's incremental cost ~$0.098 instead of
  re-paying for the whole set, and the reported tokens/cost reflect only new work.
- **Did not touch ABI formulas during 03B** (per the run rule). The one crash
  (`rotorooter.com`, a Goal 02 schema.org coercion bug) and the crawl failures
  were logged in `progress/blockers.md` and the run continued; 50 was still
  reachable from the candidate pool.

## 2026-06-06 — Goal 02 redesign: staged extraction pipeline

Superseded the v1 single-pass LLM extractor with a staged pipeline (per the
agreed design). Core principle: **the LLM is one component inside a structured
system, not the engine.**

- **Pipeline:** crawl → clean → markdown → classify → rule extract → llm extract
  → normalize → confidence → merge profile → ABI evidence
  (`backend/app/services/`, orchestrated by `app/pipeline.py`).
- **Rules before AI.** Deterministic extraction (phone/email/address regex,
  schema.org JSON-LD, headings, service slugs, FAQ blocks) runs first — cheap,
  reliable, and used to ground the LLM and the confidence engine.
- **Per-page LLM pass.** Each page is sent separately (not the whole site) under
  a strict per-page schema; every item carries an `evidence` snippet and a
  self-`confidence`.
- **Confidence is computed, not trusted.** The confidence engine combines
  signals (headings, navigation, schema.org support, cross-page repetition,
  page category) into a score + human-readable reason; the LLM's self-estimate
  is only one input.
- **Normalization + conflict-aware merge.** Variants collapse into canonical
  entities with aliases; page-level results merge into a site profile that keeps
  every value with its evidence and source pages (conflicts preserved, not
  dropped).
- **ABI-ready evidence, not scores.** The engine emits qualitative evidence
  across the 5 PRD dimensions so Goal 03 scoring is explainable. Scoring stays
  in Goal 03.
- **Caching.** Rich crawl cached as `page_documents.json` (skips Playwright on
  re-run); `profile.json` reuse skips the LLM. Keeps iteration fast/cheap.
- **Layout.** Adopted the recommended `backend/app/services/` structure; the
  crawl/clean/markdown modules wrap the Goal 01 crawler rather than duplicating
  it.

## 2026-06-06 — Goal 02 extraction stack (v1, superseded)

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

## 2026-06-08 — Goal 03D calibration hardening

- **Calibrate inside criteria, never the framework.** All three pillars change
  *how points are earned within an existing criterion* — never the 5 dimensions,
  their weights, the grade bands, or the criterion set. `validate_abi_score`
  stays the contract; it passed unchanged for all 54 sites post-change.
- **Confidence-aware scoring saturates (`FULL_CONF=0.7`), it does not punish.**
  A fact at ≥0.7 confidence counts in full; only weak evidence is discounted.
  This is what lets us correct the "Austin @ 0.15 = 20/20" bug without
  regressing genuinely strong sites. Value approved at 0.7; do not tune until a
  distribution review says so.
- **Two-layer FAQ defense; reject, don't repair.** Restrict the loose markdown
  heuristic at the source (FAQ-context pages only) *and* validate at the merge
  choke point. Schema.org FAQPage is the site's own declaration → trusted
  (length-only). The real defense against marketing fragments is fragment-
  question + CTA-answer detection, so length floors stay low (terse real answers
  survive).
- **Booking is tiered by agent-operability, sourced from the link graph.**
  deep-linkable scheduler (T3) > fillable form (T2) > intent CTA / phone (T1).
  The richest signal (scheduler link in the crawl) was already captured and
  simply unused; no crawler change was needed to read it.
- **Re-merge, don't just re-score.** Pillars 1 & 3 are merge-stage changes, so
  the free re-score uses `reuse_extraction` (rebuild `build_profile` from cached
  crawl + cached LLM), not `reuse_profile` (which only re-runs `score_abi`).

## 2026-06-08 — Goal 03E extraction hygiene

- **Provenance is derived at merge, not extracted by the LLM.** Page category +
  evidence text already carry enough signal; deriving labels deterministically
  keeps re-runs free (`reuse_extraction`) and the LLM schema/contract stable.
- **Clean the inputs, never the scorer.** Non-first-party facts are routed to
  non-scored sibling fields (`blog_examples`/`case_studies`/`testimonials`/
  `pricing_tiers`); `abi_score.py` is untouched. ABI moves only because the
  scored lists got cleaner — the explicit success condition.
- **Asymmetric bias toward first_party_service.** A false `blog_example` (drops a
  real service from scoring) is worse than a false `first_party_service`, so
  reclassification requires *exclusive* blog sourcing on a real blog page. Proven
  safe: HVAC benchmark service counts unchanged, 0 sites zeroed.
- **Separate, don't discard.** Pricing tiers and case studies are labelled and
  preserved for future ABI Profiles, not deleted — v0.1 just stops mis-scoring
  them.
- **Canonicalization strips qualifiers, not nouns.** Marketing adjectives merge
  ("Custom AI Workflows" ≡ "AI Workflows"); core domain nouns are kept so
  distinct offerings ("AI Lead Scoring" ≠ "Lead Scoring") aren't over-merged.

## 2026-06-08 — ABI v0.1.1 freeze

- **Freeze the instrument before iterating on UX.** Dimensions, weights, grade
  bands, extraction contracts, and provenance taxonomy are frozen at v0.1.1.
  Changing a "ruler" while building reports on top of it makes results
  non-comparable; the freeze makes scores stable and longitudinal.
- **Enforce the freeze with a test, not a convention.** `test_abi_freeze.py`
  pins every frozen value; a change fails CI until ABI_VERSION + the spec +
  expected values are updated together. The change policy (benchmark review) is
  documented in `abi_spec_v0.1.1.md §6`.
- **Version is metadata, stamped at the artifact boundary.** `ABI_VERSION` is
  written into `abi_score.json`/`pipeline.json`, not injected into `score_abi`'s
  logic — so the scoring function stays byte-identical and the standalone
  artifacts remain traceable to the frozen spec.
- **Sibling blocks stay outside the freeze.** `structured_data`, `actionability`,
  and the 03E provenance siblings are explicitly non-contract, so the UX/report
  phase can iterate on them without a benchmark review.
