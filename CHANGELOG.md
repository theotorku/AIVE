# Changelog

ProPlan AI Visibility Platform — Agent Business Index (ABI).

## v0.1.1 — 2026-06-08 — Calibration & freeze

The ABI measurement instrument is **frozen** at this release: scoring
dimensions, weights, grade bands, extraction contracts, and the provenance
taxonomy do not change without a benchmark review. See
[abi_spec_v0.1.1.md](abi_spec_v0.1.1.md) (change policy §6), enforced by
`backend/tests/test_abi_freeze.py`.

### Calibration hardening (Goal 03D)
- FAQ validity gate: marketing fragments / CTA-only "answers" no longer count
  as FAQs (two-layer: source restriction + merge-time validation).
- Confidence-aware scoring: `earned = max × evidence × min(1, conf/0.7)`;
  count criteria are confidence-weighted and Location presence is
  confidence-gated (fixes "0.15-confidence city = full marks").
- Booking actionability: the binary Online-booking criterion is graduated
  (T3 scheduler / T2 form / T1 intent / T0), sourced from the crawled link
  graph + schema `potentialAction` + CTAs.

### Extraction hygiene (Goal 03E)
- Provenance taxonomy (frozen): `first_party_service`, `blog_example`,
  `trust_signal`, `case_study`, `testimonial`, `offer`, `pricing_tier`.
- Non-first-party facts are routed out of the scored lists into sibling fields
  (`blog_examples`, `case_studies`, `testimonials`, `pricing_tiers`) — believable
  service counts, attributable trust. Conservative bias: ambiguous → first-party.

### Review fixes
- Crawler: offsite sitemap `loc` entries are rejected before host-normalization
  (no more rewriting `other.com/foo` onto the target host).
- Actionability: a bare `/contact` link is T1 intent, not T2 form booking.
- Docs: `goal_03b_benchmark.md` reconciled to the generated report (single
  source of truth).
- Frontend: `noEmit` on the node tsconfig + removed/ignored stray build
  artifacts that could shadow `vite.config.ts`.

### Effect (cached re-score, $0, scoring unchanged)
- ProPlan: ABI 59.7 → **42.0 → 39.0**, lower for the right reasons (fake FAQs
  removed, confidence-gated location, blog examples / case studies / pricing
  tiers separated; booking correctly credited at T3).
- Benchmark: 54 sites, avg ABI **61.5**, all explainable / repeatable /
  schema-valid. 122 backend tests pass.

### Forward focus (post-freeze)
User experience, report generation, workflow, and explainability — built on top
of the frozen ABI. No new scoring features or dimensions.

## v0.1.0 — ABI MVP
Crawler (Goal 01), extraction (Goal 02), scoring engine + 50+ site benchmark
(Goal 03), dashboard (Goal 04).
