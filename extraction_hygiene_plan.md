# Goal 03E — Extraction Hygiene · Plan

**Status:** Design + plan. No extraction/scoring code changed yet.
**Scope (fixed):** clean *what gets extracted into the scored lists* so counts
are believable and trust is attributable — by labelling every fact's
**provenance** and routing non-first-party facts out of the scored lists.
**Guardrails (do not cross):** **do not modify ABI scoring; do not modify ABI
dimensions/weights/grade bands.** `abi_score.py` and the `validate_abi_score`
contract are untouched. ABI will still move — but *only because the scorer
receives a cleaner `services[]` / `trust_signals[]` / `offers[]`*, never because
a formula changed.

> This is the deferred "extraction hygiene" bucket from
> [abi_calibration_review.md](abi_calibration_review.md) §3C / findings
> #3, #11, #13, #19 — the bleed that confidence-weighting (Goal 03D) softened
> but could not remove, because a 44-item service list is still 44 items.

---

## 1. The defect, grounded in the code

`semantic_profile._mentions(extractions, "services")` flattens service mentions
from **every** page — including blog posts — then `_grouped_evidence` unions
them into `services[]`. The confidence engine tags blog-only facts
(`from_blog_only` → ×0.6) but they **still appear in the list**.

ProPlan (from the review):

| Field | Today | Reality |
|---|---|---|
| `services` | **44** | ~9 real ScopeAI features + ~35 *blog examples* ("Intelligent Waitlist Management", "Returns Processing Automation") — automations described in posts about *other* industries, not ProPlan's catalogue |
| `trust_signals` | 12 | mix of first-party ("HIPAA-compliant", "15+ businesses served") and **third-party case-study outcomes** ("Lead conversion jumped 19%→43%", "Quote prep down 72%") lifted from clients' results |
| `offers` | 4 | 3 **pricing tiers** ("Starter/Growth/Enterprise Package") + 1 real incentive ("Free Strategy Call") |

The data needed to tell these apart is **already present** on each mention:
`category` (page type), `source_url`, `evidence` text, and the set of pages a
fact appears on. So provenance is derivable **deterministically at merge time —
no LLM re-extraction** (free `reuse_extraction` re-merge).

---

## 2. Provenance taxonomy (the six labels)

Every evidence item in a scored list gets a `provenance` label in its `extras`
(so it self-describes and stays explainable):

| Label | Meaning | Routing |
|---|---|---|
| `first_party_service` | an offering the business itself performs | **stays in `services`** |
| `blog_example` | a service/automation named as an *example* in blog/editorial content, not the company's own offering | **out of `services`** → `blog_examples[]` |
| `case_study` | a quantified outcome from a client/third-party engagement | **out of `trust_signals`** → `case_studies[]` |
| `testimonial` | a customer quote/endorsement | **out of `trust_signals`** → `testimonials[]` |
| `offer` | a genuine promotion / incentive / financing | **stays in `offers`** |
| `pricing_tier` | a productized price package/plan | **out of `offers`** → `pricing_tiers[]` |

The four new sibling fields (`blog_examples`, `case_studies`, `testimonials`,
`pricing_tiers`) are **non-contract** profile keys, exactly like
`structured_data` and `actionability` — present for transparency and future
ABI Profiles, but **not read by v0.1 scoring**.

---

## 3. Deterministic classification rules

New module `backend/app/services/provenance.py` (style mirrors
[confidence.py](backend/app/services/confidence.py) /
[faq_validator.py](backend/app/services/faq_validator.py): pure functions +
declared pattern tables, no LLM, no network). Each rule consumes signals already
on the mention/group.

### 3a. Service provenance — `classify_service(group, mentions) -> str`
`blog_example` when the service is **sourced only from editorial pages and not
corroborated as an offering**:
- every contributing mention's `category ∈ {blog, unknown}` (i.e. `from_blog_only`),
  **and** it appears on no `services`/`service_detail`/`home` page; **or**
- its `evidence` is third-person/exemplary ("for a *real-estate* client",
  "businesses can automate…", a named *other* company) rather than first-person
  ("we build", "our platform").

Otherwise `first_party_service`. **Bias toward keeping** a service: any
corroboration on a first-party page, or ≥2 distinct pages including a non-blog
one, keeps it first-party. (Protects real HVAC services that happen to be linked
from a blog.)

### 3b. Trust-signal provenance — `classify_trust(item) -> str`
- `case_study` when the `value`/`evidence` carries a **quantified third-party
  outcome**: a percentage/multiplier delta or "from X to Y", "reduced/increased
  … by N", "saved N hours", attributed to a client/customer rather than to the
  business itself ("we are", "we hold", "certified", "licensed", "years").
- `testimonial` when it is a **quoted endorsement** with attribution (quote
  marks + "— Name", "Name, Title/Company", "said", "reviewed").
- else stays a first-party `trust_signal` (guarantee/certification/award/
  experience/licensing — the kinds the Recommendation dimension is meant to score).

### 3c. Offer provenance — `classify_offer(item) -> str`
- `pricing_tier` when it matches a **package/plan** pattern: ends in
  Package/Plan/Tier/Edition, or a known tier name (Starter/Basic/Growth/Pro/
  Premium/Business/Enterprise), or carries a recurring price ("$N/mo", "/month",
  "per seat").
- else `offer` (discount/financing/free-consult/seasonal special).

Each rule returns the label **and** every credit keeps its evidence, so the
partition is auditable per item.

---

## 4. Service canonicalization & provenance improvements (req. 3)

[normalizer.py](backend/app/services/normalizer.py)'s `_SERVICE_CANON` is
HVAC-specific; for non-local businesses every service falls to the generic
`_token_key`, so near-duplicates and marketing-padded names don't collapse.
Modest, deterministic improvements (no ML):
- **Strip marketing qualifiers** before keying (lead-in adjectives like
  "Custom", "Advanced", "AI-Powered", "Smart", "Automated", "End-to-End") so
  "Custom AI Workflows" and "AI Workflows" group.
- **Extend the generic stopword set** and singularize consistently in
  `_token_key` to reduce spurious distinct groups.
- **Attach group provenance + corroboration count** to each canonical service
  (`source_pages`, `page_count`, `provenance`) so "believable count" is
  inspectable: a first-party service seen on ≥1 service/home page reads as real;
  a single-blog-mention example reads as `blog_example`.

Canonicalization stays deterministic and order-preserving; the win for a
"believable count" comes mostly from the §3a partition, with grouping as a
secondary tightening.

---

## 5. Integration points (exact)

1. **`provenance.py`** (new) — `classify_service`, `classify_trust`,
   `classify_offer`, plus pattern tables.
2. **`normalizer.py`** — qualifier-stripping + stopword/singularization tweaks
   in `_token_key` / `_clean` (behind the existing functions; HVAC table
   unchanged so local-service grouping is preserved).
3. **`semantic_profile.build_profile`** — after each scored list is built,
   label provenance and **partition**:
   ```python
   services, blog_examples = _partition_services(services)         # 3a
   trust_signals, case_studies, testimonials = _partition_trust(trust_signals)  # 3b
   offers, pricing_tiers = _partition_offers(offers)               # 3c
   ```
   Tag `item.extras["provenance"]` on every item (kept and routed).
4. **profile dict** — add sibling fields `blog_examples`, `case_studies`,
   `testimonials`, `pricing_tiers` (non-contract, like `structured_data`).
5. **No change** to `abi_score.py`, `schema.py` scoring contract, the LLM
   prompt, or `PAGE_EXTRACTION_SCHEMA`. `validate_profile` still passes
   (`provenance` rides in `extras`; new keys are additive).

Data flow unchanged except one new partition step at the merge choke point:
`… → merge → provenance partition → profile → score`.

---

## 6. Why ABI still moves (and that's correct)

Scoring is untouched, but the scorer now sees cleaner inputs:
- `services` shrinks to first-party only → Service coverage / Service depth fall
  to a **believable** level (count-based, confidence-weighted from 03D).
- `trust_signals` drops third-party case studies → Trust signals / Reputation
  reflect the business's *own* proof.
- `offers` drops pricing tiers → Offers reflects real incentives only.

This is the explicit success condition: **"ABI changes only due to cleaner
extraction."** Pricing tiers and case studies are *labelled and preserved*
(not discarded) for the future ABI Profiles work — v0.1 simply stops mis-scoring
them.

---

## 7. Expected ProPlan effect (to verify on re-merge)

| Field | Before | After (expected) |
|---|---|---|
| `services` | 44 | ~9 first-party (believable); ~35 → `blog_examples` |
| `trust_signals` | 12 | ~5–7 first-party; quantified client outcomes → `case_studies` |
| `offers` | 4 | 1 (`Free Strategy Call`); 3 → `pricing_tiers` |

ABI will shift on Understanding (service coverage/clarity now over real
features), Recommendation (attributable trust, fewer offers), and Authority
(service depth). Direction is *toward correctness*; magnitude is reported, not
targeted — the criterion that matters most (#18 no schema.org) is unaffected.

---

## 8. Validation plan (free — cached re-merge, no LLM)

1. Implement + unit tests green (§9).
2. Re-merge all 54 cached sites via `reuse_extraction` (no crawl, no LLM) and
   diff `services` / `trust_signals` / `offers` counts before/after.
3. **Regression guard (the real risk): do not strip genuine local-service
   offerings.** For the HVAC corpus, assert first-party service counts stay
   ≈stable (a real "AC Repair" must not be reclassified `blog_example`). Any
   site that loses a clearly-real service → loosen §3a (require *exclusive* blog
   sourcing + non-corroboration).
4. Spot-check 10 sites: does each `blog_example` / `case_study` / `pricing_tier`
   label match a human read of the evidence? Tune patterns on false positives.
5. Re-score (free) and confirm ABI moves are attributable to the partition, not
   to scoring; `validate_abi_score` passes for all 54.
6. Update review findings #3/#11/#13/#19 to "resolved (extraction)".

### Acceptance
- **ProPlan service count is believable** (~9 first-party, not 44); the rest are
  labelled `blog_example`, not deleted.
- **Trust signals are attributable**: first-party credentials vs `case_studies`
  vs `testimonials`, each carrying evidence.
- **ABI changes only via cleaner lists** — `abi_score.py` diff is empty.
- **No regression** on the HVAC benchmark: real services/trust survive; ABI
  contract still valid for all 54 sites.

---

## 9. Test cases (drop into `backend/tests/`)

`test_provenance.py` (pure, offline):
- `classify_service`: a blog-only "Returns Processing Automation" → `blog_example`;
  "AC Repair" corroborated on a service page → `first_party_service`; an
  HVAC service linked from a blog but also on `/services` → `first_party_service`
  (regression guard).
- `classify_trust`: "Lead conversion jumped from 19% to 43%" → `case_study`;
  "Licensed & insured" → trust; '"Best company ever" — Jane, Acme Co.' →
  `testimonial`.
- `classify_offer`: "Starter Package" / "$99/mo" → `pricing_tier`; "0% financing
  for 12 months" / "Free Strategy Call" → `offer`.

`test_pipeline.py` integration:
- `build_profile` over ProPlan-shaped mentions partitions blog examples out of
  `services` while keeping the real features; `services + blog_examples` is
  loss-less (nothing dropped, only routed).
- A pure-HVAC profile is unchanged: no `blog_examples`, services intact.

`test_abi_score.py` guard:
- the `abi_score.py` source is unchanged (scoring contract test stays green);
  a profile with the new sibling fields scores identically to one without them
  (scorer ignores `blog_examples`/`case_studies`/`pricing_tiers`).

---

## 10. Out of scope (restated)
- Any change to ABI scoring, dimensions, weights, grade bands, or criteria.
- Creating a pricing or case-study *scoring* criterion (deferred — ABI Profiles).
- LLM prompt / schema changes or re-extraction (provenance is derived at merge).
- Dashboard / report rendering (Goal 04).
