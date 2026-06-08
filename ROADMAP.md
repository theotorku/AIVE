# ROADMAP

ProPlan AI Visibility Platform — Agent Business Index (ABI)

Goals are executed sequentially. Do not skip. Do not merge.
No goal is complete until validated against real websites.

---

## 🔒 ABI v0.1.1 — FROZEN (2026-06-08)

The ABI measurement instrument is frozen: **scoring dimensions, weights, grade
bands, extraction contracts, and the provenance taxonomy do not change without a
benchmark review.** Spec: [abi_spec_v0.1.1.md](abi_spec_v0.1.1.md) ·
Changelog: [CHANGELOG.md](CHANGELOG.md) · Enforced by
`backend/tests/test_abi_freeze.py`.

**Phase 2 focus (post-freeze):** user experience, report generation, workflow,
and explainability — built on the frozen ABI. No new dimensions, no new scoring
features. Sibling/report data and UX iterate freely; the frozen core does not.

---

## Phase 1 — ABI MVP

### Goal 01 — Crawler

Crawl a target website and capture its content.

- Validation: minimum 10 websites
- Spec: goals/goal_01_crawler.md

### Goal 02 — Extraction

Extract business intelligence from crawled content.

- Priority 1: services, locations, FAQs
- Priority 2: testimonials, offers, trust signals
- Priority 3: certifications, competitive positioning
- Validation: minimum 20 websites
- Spec: goals/goal_02_extraction.md

### Goal 03 — ABI

Calculate the Agent Business Index score and recommendations.

- Scores must be explainable, repeatable, defensible, actionable
- Every score includes rationale, recommendation, supporting evidence
- Validation: minimum 50 websites
- Spec: goals/goal_03_abi.md

### Goal 04 — Dashboard

Deliver the end-to-end workflow and downloadable report.

- Validation: complete end-to-end workflow
- Spec: goals/goal_04_dashboard.md

### Goal 03D — ABI Calibration Hardening

Refine score *correctness* without changing the ABI framework (same 5
dimensions, weights, and criteria). Scope: (1) FAQ validity, (2) booking /
actionability detection, (3) confidence-aware scoring. No dashboard features,
no new dimensions, no new categories.

- Spec: calibration_plan.md · Impact: impact_estimates.md · Tests: calibration_test_cases.md

### Goal 03E — Extraction Hygiene

Clean *what is extracted into the scored lists* so counts are believable and
trust is attributable — by labelling every fact's provenance and routing
non-first-party facts out of the scored lists. **No ABI scoring/dimension
changes**; ABI moves only because the scorer receives cleaner inputs.

- Provenance labels: first_party_service · blog_example · case_study ·
  testimonial · offer · pricing_tier
- Separates blog examples from first-party services, and third-party case-study
  outcomes from company trust signals; improves service canonicalization.
- Spec: extraction_hygiene_plan.md

---

## ABI scope & profiles

**ABI v0.1 is calibrated for Local Service businesses (HVAC/plumbing/etc.) —
that is its benchmark dataset, and its assumptions (geographic service area,
physical address, business hours, phone-first contact) are explicitly
local-service.** This is a deliberate scope, not a limitation to paper over.
Validation against non-local businesses (e.g. an AI agency/SaaS like ProPlan)
correctly surfaces category-specific signals ABI v0.1 does not yet model
(pricing, integrations, documentation, case studies) — evidence the benchmark
is maturing, not that v0.1 is broken.

### Future — ABI Profiles (do not build in v0.1)

Industry-specific criteria/weights layered on the *same* framework:

- **Local Services** (v0.1): service area, address, hours, booking, reviews
- **Agencies**: case studies, process, testimonials, consultation flow
- **SaaS**: pricing, docs, integrations, onboarding, API
- **Professional Services**: credentials, practice areas, intake

Do not dilute v0.1 trying to support everyone first.

---

## Out Of Scope (Future Phases)

- Agent marketplace
- MCP integrations
- Multi-agent framework
- Graph database
- Revenue operations engine
- Semantic graph platform

---

## Future Direction

AI Visibility → Semantic Infrastructure → Revenue Operations → Agent Ecosystem

The MVP must remain focused.
