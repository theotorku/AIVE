# ABI Specification — v0.1.1 (FROZEN)

**Status:** Frozen measurement instrument. **No changes to anything in §1–§5
without a benchmark review** (see §6 change policy). Enforced by
[backend/tests/test_abi_freeze.py](backend/tests/test_abi_freeze.py); the single
source of truth for the frozen values is
[backend/app/schema.py](backend/app/schema.py) (`ABI_VERSION = "0.1.1"`) and
[backend/app/services/provenance.py](backend/app/services/provenance.py)
(`PROVENANCE_LABELS`).

ABI v0.1.1 is calibrated for **Local Service businesses** (its benchmark
dataset). Non-local categories (SaaS/agency) are correctly measured but
intentionally not yet re-weighted — that is deferred to the future *ABI Profiles*
work, which is the only sanctioned path to changing weights.

---

## 1. Scoring dimensions (frozen)

Five dimensions, fixed identifiers and order:

| # | Dimension | Weight |
|---|-----------|--------|
| 1 | `ai_understanding` — AI Understanding | 0.25 |
| 2 | `ai_retrieval` — AI Retrieval | 0.25 |
| 3 | `ai_recommendation` — AI Recommendation | 0.20 |
| 4 | `agent_readiness` — Agent Readiness | 0.15 |
| 5 | `semantic_authority` — Semantic Authority | 0.15 |

Weights sum to 1.0. Overall ABI = Σ (dimension score × weight).

## 2. Scoring weights & criteria (frozen)

Each dimension's criteria sum to 100 points. The named criteria are frozen
(renaming/adding/removing any is a contract change):

- **AI Understanding** — Business identity, Industry clarity, Service coverage,
  Service clarity, Location presence.
- **AI Retrieval** — FAQ coverage, FAQ answer quality, Heading structure,
  Geographic specificity, Content breadth.
- **AI Recommendation** — Trust signals, Reputation diversity, Offers &
  incentives, Trust signal strength.
- **Agent Readiness** — Phone number, Contact email, Address, Business hours,
  Online booking, Calls to action.
- **Semantic Authority** — Structured data (schema.org), Service depth,
  Geographic authority, Knowledge depth (FAQ), Cross-page corroboration.

Scoring mechanics frozen in this release (from Goal 03D): confidence-aware
scoring (`earned = max × evidence × min(1, conf/0.7)`), confidence-gated Location
presence, and the graduated Online-booking tiers (T3 20 / T2 12 / T1 6 / T0 0).
`FULL_CONF = 0.7`.

## 3. Grade bands (frozen)

| Lower bound | Grade | Label |
|---|---|---|
| 90 | A | AI-Optimized |
| 75 | B | AI-Ready |
| 60 | C | Partially Visible |
| 40 | D | Low Visibility |
| 0 | F | Invisible to AI |

## 4. Extraction contracts (frozen)

`SCHEMA_VERSION = "2.0"`.

- **Profile fields** (`PROFILE_FIELDS`): schema_version, business_name,
  industry, services, service_areas, locations, faqs, offers, trust_signals,
  ctas, contact_information, source_pages.
- **Evidence-list fields** (`EVIDENCE_LIST_FIELDS`): services, service_areas,
  locations, faqs, offers, trust_signals, ctas — each item carries
  value, confidence, evidence, source_url (+ confidence_reason, provenance).
- **Contact fields** (`CONTACT_FIELDS`): phone, email, address, hours,
  booking_url.
- **Per-page LLM schema** (`PAGE_EXTRACTION_SCHEMA`): unchanged.
- **Non-contract sibling blocks** (present, not part of the frozen contract, not
  scored): `structured_data`, `actionability`, `blog_examples`, `case_studies`,
  `testimonials`, `pricing_tiers`, `source_pages`. These may evolve under the
  UX/report focus *without* a benchmark review, as long as scored fields and the
  contract above are untouched.

## 5. Provenance taxonomy (frozen)

`PROVENANCE_LABELS` — seven labels, fixed:

| Label | Applies to | Routing |
|---|---|---|
| `first_party_service` | services | scored |
| `blog_example` | services | sibling (`blog_examples`) |
| `trust_signal` | trust | scored |
| `case_study` | trust | sibling (`case_studies`) |
| `testimonial` | trust | sibling (`testimonials`) |
| `offer` | offers | scored |
| `pricing_tier` | offers | sibling (`pricing_tiers`) |

---

## 6. Change policy

**No change to §1–§5 ships without a benchmark review.** A sanctioned change:

1. Propose the change with a hypothesis and the benchmark impact you expect.
2. Run the full benchmark (`python -m backend.run_abi_validation --min 50`),
   free re-score, and diff before/after (per-site + distribution).
3. Confirm the change is *correctness*, not drift, and that ProPlan + the HVAC
   benchmark behave as intended.
4. In one commit: update this spec, bump `ABI_VERSION`, and update the expected
   values in `test_abi_freeze.py`.

Anything outside §1–§5 — UX, report generation, workflow, explainability,
sibling blocks, dashboard — is **open for iteration** and needs no review.

---

## 7. Provenance / history

- **v0.1.0** — ABI MVP: crawler, extraction, scoring engine, 50+ site benchmark.
- **v0.1.1** — Calibration hardening (03D: FAQ validity, confidence-aware
  scoring, booking actionability), extraction hygiene (03E: provenance
  taxonomy + partitioning), and review fixes (offsite sitemap, /contact tier,
  benchmark single-source, frontend build artifacts). Framework frozen here.
  See [CHANGELOG.md](CHANGELOG.md).
