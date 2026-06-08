# Cost Ledger

Every goal completion must update this ledger.

Track: build cost, runtime cost, E2E processing cost.
Per entry: tokens, model, duration, estimated spend.

---

| Date       | Goal               | Type                 | Tokens                            | Model           | Duration                                                              | Est. Spend      | Notes                                                                                                           |
| ---------- | ------------------ | -------------------- | --------------------------------- | --------------- | --------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------------------------------------------- |
| 2026-06-06 | Goal 01            | Build                | ~250k (est.)                      | claude-opus-4-8 | single session                                                        | ~$5–8 (est.)    | Crawler design, implementation, tests, validation. Token figure estimated, not metered.                         |
| 2026-06-06 | Goal 01            | Runtime (validation) | n/a                               | n/a (local)     | ~8.2 min wall (11 sites)                                              | ~$0.00          | Playwright + trafilatura run locally; no paid API. Compute/bandwidth only.                                      |
| 2026-06-06 | Goal 01            | E2E processing       | n/a                               | n/a (local)     | ~49 s/site avg                                                        | ~$0.00 / site   | Goal 01 (crawl + markdown) has no LLM cost. Extraction/scoring costs arrive in Goal 02/03.                      |
| 2026-06-06 | Goal 02            | Build                | ~300k (est.)                      | claude-opus-4-8 | single session                                                        | ~$6–9 (est.)    | v1 single-pass extractor (superseded). Token figure estimated, not metered.                                     |
| 2026-06-06 | Goal 02 v1         | Runtime (validation) | 137,095                           | gpt-4o-mini     | ~8 min wall                                                           | ~$0.025         | v1 full run (superseded by the staged pipeline below).                                                          |
| 2026-06-06 | Goal 02 (pipeline) | Build                | ~600k (est.)                      | claude-opus-4-8 | single session                                                        | ~$12–16 (est.)  | Staged pipeline redesign (10 services modules, schema, tests, validation). Token figure estimated, not metered. |
| 2026-06-06 | Goal 02 (pipeline) | Runtime (validation) | 288,277 (218,035 in + 70,242 out) | gpt-4o-mini     | ~25 min wall (21 sites, full rich re-crawl + ~120 per-page LLM calls) | ~$0.075         | Per-page extraction with evidence/confidence. Re-runs reuse cached crawl/profile (~$0).                         |
| 2026-06-06 | Goal 02 (pipeline) | E2E processing       | ~13,700 tokens/site avg           | gpt-4o-mini     | ~90 s/site (rich crawl + ~6 page LLM calls)                           | ~$0.0036 / site | Richer than v1 (~$0.0012); adds evidence, confidence, normalization, ABI evidence.                              |
| 2026-06-07 | Goal 03A           | Build                | ~250k (est.)                      | claude-opus-4-8 | single session                                                        | ~$5–8 (est.)    | ABI scoring engine, schema validator, pipeline wiring, 10 tests, validation harness + score-quality review.      |
| 2026-06-07 | Goal 03A           | Runtime (validation) | 0 (no LLM)                        | n/a (local)     | <2 s (21 profiles, deterministic re-score ×2)                         | $0.00           | Scoring is pure/deterministic over cached profiles — no API calls. Re-scoring is always free.                    |
| 2026-06-07 | Goal 03            | E2E processing       | 0 (no LLM)                        | n/a (local)     | <0.1 s / site                                                         | $0.00 / site    | ABI scoring adds no per-site API cost; it reads the existing profile. Crawl/extract cost stays in Goal 02.       |
| 2026-06-07 | Goal 03B           | Runtime (extraction) | 374,774 (282,150 in + 92,624 out) | gpt-4o-mini     | ~55.7 min wall (70 attempted, 29 newly crawled+extracted; 21 reused $0) | ~$0.098         | Expanded benchmark 21→50 passed sites. Cost is incremental — prior 21 profiles reused at $0. ~$0.0034/new site.  |
| 2026-06-07 | Goal 03B           | Runtime (ABI score)  | 0 (no LLM)                        | n/a (local)     | <2 s (50 profiles, deterministic re-score ×2)                        | $0.00           | Re-scored all 50 passed sites; explainable/repeatable/schema-valid 50/50. Scoring never costs API spend.         |
| 2026-06-07 | Goal 03 (hardening) | Build               | ~300k (est.)                      | claude-opus-4-8 | single session                                                        | ~$6–9 (est.)    | Post-review fixes: FAQ/schema merge, structured_data, PRD weights, validator, extraction cache, schema coercion. |
| 2026-06-07 | Goal 03 (hardening) | Runtime (re-extract)| 674,379 (498,713 in + 175,666 out) | gpt-4o-mini     | ~41.9 min wall (50 sites, LLM-only over cached crawls)                | ~$0.180         | One-time re-extraction to apply merge-stage fixes + cache extractions.json. Future re-merges are $0.            |
| 2026-06-07 | Goal 04            | Build                | ~350k (est.)                      | claude-opus-4-8 | single session                                                        | ~$7–10 (est.)   | FastAPI app + HTML report + React/Vite/Chakra dashboard + live browser verification. Estimated, not metered.     |
| 2026-06-07 | Goal 04            | Runtime (dashboard)  | 0 serving + per-run extraction    | n/a / gpt-4o-mini | instant for cached views; live runs ~$0.004/site                    | $0.00 / view    | Browsing scored sites + report download cost $0 (reads artifacts). Live URL runs cost the same as Goal 02.       |

## Notes

- **Build cost** = agent time to design/implement/validate. Token counts are
  estimates (the session is not metered here); refine if exact usage is needed.
- **Runtime / E2E cost** for Goal 01 is effectively $0 in external spend — the
  crawler uses no paid APIs. Per-website monetary cost begins in Goal 02 when
  LLM-based extraction is introduced.
- Goal 01 processing time is dominated by network settle, ~49 s/site average
  over 6 pages each (range ~25–88 s depending on site weight).

## Goal 02 Cost Summary

Model: gpt-4o-mini  
Attempted Sites: 26  
Successful Crawls: 21  
Passed Sites: 20

Prompt Tokens: 218,035  
Completion Tokens: 70,242  
Total Tokens: 288,277

Average Tokens Per Passed Site:
14,414

Schema Stable:
Yes

Goal 02 Status:
Complete

## Goal 03 Cost Summary

Scoring Engine: deterministic, no LLM — $0 runtime, repeatable and free to re-run.

03B benchmark expansion (extraction only; ABI scoring adds no API cost):
Model: gpt-4o-mini
Attempted Sites: 70
Successful Crawls: 52
Passed Extractions: 50
Failed Sites: 20

Prompt Tokens: 282,150
Completion Tokens: 92,624
Total Tokens: 374,774
Estimated API Cost: ~$0.098 (incremental; 21 prior profiles reused at $0)
Avg Cost / newly-extracted site: ~$0.0034
Wall-clock: ~55.7 min

Hardening re-extraction (one-time, to apply FAQ/schema merge + PRD weights):
Tokens: 674,379 (498,713 in + 175,666 out)
Estimated API Cost: ~$0.180
Wall-clock: ~41.9 min

Benchmark (50 sites, after hardening): avg ABI 68.2, range 3.8–87.0,
grades B:16 C:26 D:6 F:2. Component avgs — Understanding 86.0, Recommendation
71.4, Retrieval 64.8, Semantic Authority 62.7, Agent Readiness 45.4.

Total Goal 03 external spend: ~$0.098 (dataset expansion) + ~$0.180 (hardening
re-extraction) = ~$0.278. ABI scoring itself is deterministic and free.

Goal 03 Status:
Complete (hardened)

## Goal 04 Cost Summary

Dashboard (FastAPI + React/Vite/Chakra). Presentation + workflow only.

Serving cost: $0 — the API reads the real artifacts; browsing scored sites and
downloading reports make no API calls. Live URL runs reuse the Goal 02 pipeline
(~$0.004/site). Verified the complete end-to-end workflow live in-browser
(browse → submit URL → status → score → report).

Goal 04 Status:
Complete

---

## MVP total external spend (Goals 01–04)

~$0.10 (Goal 02 extraction) + ~$0.098 (Goal 03B expansion) + ~$0.180 (Goal 03
hardening re-extraction) ≈ **~$0.38** in LLM cost across 50 benchmarked sites.
Crawling and ABI scoring add no external cost. All ABI MVP success criteria met.

---

## Goal 03D — ABI Calibration Hardening (2026-06-08)

Calibration only — FAQ validity gate, confidence-aware scoring, booking
actionability. No new dimensions/weights/categories.

- **Build cost:** engineering time only.
- **Re-score cost: $0.** All 54 cached profiles re-merged + re-scored via
  `reuse_extraction` (cached crawl + cached LLM) — no crawling, no LLM calls.
- **Runtime cost:** unchanged. Detection (`actionability`, `faq_validator`) and
  confidence-aware scoring are pure deterministic functions over already-crawled
  data; they add no external spend to a live run.

MVP total external spend unchanged (~$0.38).

---

## Goal 03E — Extraction Hygiene (2026-06-08)

Provenance classification + partitioning only. No scoring/dimension changes.

- **Build cost:** engineering time only.
- **Re-score cost: $0.** All 54 cached profiles re-merged + re-scored via
  `reuse_extraction` / `reuse_profile` — no crawling, no LLM calls. Provenance is
  derived deterministically from already-cached signals.
- **Runtime cost:** unchanged. `provenance` classification is pure regex/string
  work over already-extracted facts; adds no external spend to a live run.

MVP total external spend unchanged (~$0.38).

---

## ABI v0.1.1 — Freeze release (2026-06-08)

Freeze + version stamp + enforcement + docs. No scoring change.

- **Build cost:** engineering time only.
- **Re-stamp cost: $0.** All 54 cached artifacts re-persisted via
  `reuse_extraction` / `reuse_profile` to stamp `abi_version` — no crawl, no LLM.
- **Runtime cost:** unchanged.

MVP total external spend unchanged (~$0.38).
