# Goal 03D — ABI Calibration Hardening · Calibration Plan

**Status:** Design + plan. No production scoring/extraction code changed yet.
**Scope (fixed):** improve score *correctness* on three axes only —
(1) FAQ validity, (2) booking / agent-actionability detection, (3)
confidence-aware scoring.
**Guardrails (do not cross):** no dashboard features; **no change to the ABI
framework** — same five dimensions, same weights
(U .25 / R .25 / Rec .20 / Agent .15 / Auth .15), same named criteria, same
grade bands. The `abi_score` contract in [schema.py](backend/app/schema.py)
(`validate_abi_score`) stays byte-for-byte valid; this work changes *how points
are earned inside criteria*, never the criteria, weights, or output shape.

> We are no longer debugging software — we are calibrating the ruler. Every
> change here makes a score *more correct*, and is traceable to a specific
> defect documented in [abi_calibration_review.md](abi_calibration_review.md).

---

## 0. Why these three (and nothing else)

The ProPlan calibration review ([abi_calibration_review.md](abi_calibration_review.md))
sorted every defect into four buckets. Goal 03D takes **only the
industry-agnostic engine defects** — the ones that are wrong *regardless* of
industry — and explicitly defers the rest:

| Bucket | Example findings | In 03D? |
|---|---|---|
| **Engine defects (industry-agnostic)** | FAQ validity (#6/#7/#21), booking/CTA silo (#16), confidence-blind presence (#5) | **Yes — all three pillars** |
| Extraction hygiene (blog bleed) | inflated services/trust (#3/#11/#19) | No — extraction goal, not scoring |
| Cross-industry robustness | SaaS reputation buckets (#12), pricing as a signal (§4) | No — needs new criteria |
| Industry-aware ABI profiles | geographic + physical-contact weighting (#9/#10/#15/#20) | No — deferred to ABI Profiles ([ROADMAP](ROADMAP.md)) |

Each deferred bucket would require changing the framework (new criteria, new
weights, or new categories) — explicitly out of scope. The three chosen pillars
are pure correctness fixes that leave the framework intact.

---

## 1. Pillar 1 — FAQ validity

**Defect (review #6/#7/#21):** the rule extractor promotes any markdown line
ending in `?` into an FAQ on every page, with no validity check. ProPlan got 5
fake FAQs (`"something real?"`, `"Prefer to Talk First?"` … answers are CTA
copy) that scored full marks in **three** criteria
(Retrieval FAQ coverage 35/35 + answer quality 10/10, Authority knowledge depth
15/15) — **≈ +13.5 ABI the site never earned.**

**Design:** already specified in detail in
[faq_validation_plan.md](faq_validation_plan.md). Summary of the two-layer,
defense-in-depth approach:

- **Layer A — restrict at source.** `rule_extractor._faq_from_markdown` only
  fires on FAQ-context pages (`category == "faq"`, or an FAQ marker in
  headings/markdown) via a new `_has_faq_context(doc)`. Most garbage never
  gets created.
- **Layer B — validity gate at the merge choke point.** A new
  `backend/app/services/faq_validator.py` exposes
  `validate_faq(question, answer, *, source) -> (bool, reason)`, applied to
  **all** FAQ candidates in `semantic_profile.build_profile` just before
  `_simple_evidence`. Source-aware strictness: `schema` (FAQPage JSON-LD) is
  trusted (length-only); `faq_section` / `llm` / `markdown` are validated hard
  (real interrogative question + substantive, non-CTA answer).

**Framework impact:** none. `abi_score.py` is untouched — the FAQ criteria
simply receive a clean `faqs[]`. ProPlan's FAQ scores correctly fall to 0.

**Integration points:** see [faq_validation_plan.md §7](faq_validation_plan.md).
Data flow: `crawl → classify → rules (Layer A) → LLM → merge (Layer B gate) →
profile.faqs → score`.

---

## 2. Pillar 2 — Booking / agent-actionability detection

**Defect (review #16):** Agent Readiness's *Online booking* criterion reads
exactly one field, `contact_information.booking_url`, and scores it 20/0 binary.
That field is set on **6%** of sites, while a booking affordance is actually
present on **~76%** (a ~90% false-negative rate). ProPlan has a live Calendly
link in its crawled HTML and three `cta_type:book` CTAs, yet scores
"No online booking detected (0/20)" — a self-contradiction inside one report.

**Design:** already specified in detail in
[agent_actionability_model.md](agent_actionability_model.md). Summary:

- New `backend/app/services/actionability.py` →
  `detect_actionability(docs, profile)` producing a structured, evidence-bearing
  block (kept **out** of the extraction contract, like `structured_data`):
  tiered booking detection from the **already-crawled link graph** + schema.org
  `potentialAction` + CTAs + `contact_information`.
- **Tiers:** T3 deep-linkable scheduler (Calendly / Cal.com / HubSpot Meetings /
  `booking_url` / `potentialAction`) → 20; T2 fillable form → 12; T1 intent CTA
  or phone-to-book → 6; T0 none → 0. Every credit names the evidence URL.
- Replaces the single binary *Online booking* criterion with a **graduated**
  one **of the same name, same 20 points, in the same Agent Readiness
  dimension** — so the framework is unchanged; only the point formula behind one
  existing criterion becomes multi-signal and graduated.

**Upstream prerequisites (small, in the extraction layer):** capture CTA `href`;
stop dropping `tel:`/`mailto:` in `cleaner.extract_links`; parse
`potentialAction` in `rule_extractor`. See
[agent_actionability_model.md §6](agent_actionability_model.md).

**Framework impact:** none. The criterion keeps its name, dimension, and 20-pt
max; only sites with a *real* booking affordance gain credit, at the correct
tier.

---

## 3. Pillar 3 — Confidence-aware scoring (new design)

This is the one pillar with no prior design doc — the
"Evidence × Confidence, not Evidence-exists = full points" fix.

### 3.1 Defect

> Austin, TX · confidence = 0.15 · Location presence = **20/20**

Review #5: `locations = ["Austin, TX"]` at confidence **0.15** earns the *same*
20 points as a fully-verified LocalBusiness address. The criterion is binary and
**confidence-blind** — and it directly contradicts Agent Readiness #15
("No address detected", 0/15) reading the same profile.

The deeper issue is a scoring-philosophy bug, not one criterion: the engine
already computes a rich per-fact confidence in
[confidence.py](backend/app/services/confidence.py) (schema support, headings,
nav, page count, blog-only penalty → a score in `[0.05, 1.0]` with a reason),
but most scoring criteria **throw that signal away** and reward the mere
*existence* of evidence. A 0.15-confidence incidental mention and a
0.95-confidence, schema-backed, cross-page-corroborated fact score identically.

### 3.2 Principle

> **earned = max_points × evidence_strength × confidence_factor**

A criterion should pay out in proportion to *how much confident evidence*
exists, not how many rows are in a list. The confidence is already computed and
already carries a human-readable reason — so the score stays explainable.

### 3.3 The confidence factor (saturating, not punitive)

```python
FULL_CONF = 0.7   # at/above this, a fact counts as fully credible

def _conf_factor(conf: float) -> float:
    """Map a fact's confidence to a [0,1] weight. Genuinely confident facts
    (>= FULL_CONF) count in full; weak facts are discounted linearly."""
    return max(0.0, min(1.0, (conf or 0.0) / FULL_CONF))
```

`FULL_CONF = 0.7` aligns with `confidence.label()` (`high >= 0.75`,
`medium >= 0.5`). The factor **saturates at 1.0**, so this is *not* a blanket
penalty: a fact the engine is confident about (≥ 0.7) earns full weight; only
weak evidence is discounted. This protects high-quality sites from regressing
(the rich HVAC fixture at conf 0.9 is unaffected) while correcting the
Austin-style inflation.

| Fact confidence | `_conf_factor` | Interpretation |
|---|---|---|
| 0.90 (schema + headings + repeated) | 1.00 | full credit |
| 0.57 (real ScopeAI feature) | 0.81 | strong |
| 0.27 (single mention) | 0.39 | weak |
| 0.15 (Austin incidental) | 0.21 | barely credible |

### 3.4 Two mechanisms

**Mechanism A — confidence-weighted effective count** (count-based criteria).
Replace `_ratio(len(items), target)` with `_ratio(_eff_count(items), target)`:

```python
def _eff_count(items: list[dict]) -> float:
    return sum(_conf_factor(i.get("confidence", 0) or 0) for i in items)
```

A criterion now needs `target` units of *credible* evidence, not `target` rows.
Applies to the count criteria: **Service coverage**, **FAQ coverage**,
**Geographic specificity**, **Trust signals**, **Offers & incentives**, **Calls
to action**, **Service depth**, **Geographic authority**, **Knowledge depth
(FAQ)**.

**Mechanism B — confidence-gated presence** (the Location flagship).
Replace the binary `20 if has_loc else 0` with a confidence-scaled payout driven
by the *best* location evidence:

```python
best = max((_conf_factor(l.get("confidence", 0) or 0) for l in locations),
           default=0.0)
# a structured contact.address string is itself a strong signal -> treat as 0.8
if contact.get("address"):
    best = max(best, _conf_factor(0.8))
earned = 20 * best
```

ProPlan Austin (0.15) → `20 × 0.21 = 4.3 / 20` (was 20/20). A verified address →
full 20. This resolves the #5-vs-#15 contradiction in the right direction.

### 3.5 What stays unchanged (deliberately)

- **Criteria that already measure confidence** — Service clarity
  (`avg_conf × 20`) and Trust signal strength (`avg_conf × 10`) — are left
  as-is. They *are* the confidence axis.
- **Binary criteria with no per-fact confidence** — the phone / email / address
  / hours contact booleans (raw strings, no confidence) and Structured data
  (schema.org flags, inherently machine-trustworthy) — stay binary. Booking is
  handled by Pillar 2.
- **Structural ratios** — Heading structure, Reputation diversity, Content
  breadth, FAQ answer quality, Cross-page corroboration — unchanged (FAQ answer
  quality is corrected upstream by Pillar 1's validity gate).

### 3.6 Double-counting note (explicit tradeoff)

Service coverage (now eff-count) and Service clarity (avg-conf) both move with
confidence, as do Trust signals and Trust signal strength. This is intentional:
the two criteria express **breadth of credible evidence** and **average
certainty** — correlated but distinct axes, and together they realize
"Evidence × Confidence." Because `_conf_factor` saturates at 0.7, a healthy site
is not double-penalized (both factors sit at ~1.0). The 50-site re-score (§5) is
the check: if a class of medium-confidence sites regresses implausibly, the
lever is `FULL_CONF` (raise toward 0.6), **not** removing a criterion — removing
one would change the framework.

### 3.7 Framework impact

None. All payouts stay within `[0, max]`, dimension scores remain
`earned/max × 100`, weights and grade bands are untouched, and
`validate_abi_score` continues to pass. The change is entirely *inside* existing
criterion formulas.

---

## 4. Sequencing & ownership

Implement in this order so each pillar sees clean inputs:

1. **Pillar 1 (FAQ validity)** first — removes fake FAQs so confidence-aware
   counts and the FAQ criteria operate on real data.
2. **Pillar 3 (confidence-aware scoring)** second — pure scorer change in
   [abi_score.py](backend/app/services/abi_score.py); add `_conf_factor` /
   `_eff_count` helpers, swap the count/location formulas.
3. **Pillar 2 (actionability)** third — touches extraction prerequisites + a new
   service + the booking criterion formula; largest blast radius, lands last.

Pillars are independent at the framework level; this order minimizes test churn.

---

## 5. Rollout & validation (free — cached, no LLM cost)

All validation re-uses the cached crawls/profiles; **no new crawling or LLM
spend** (per the harness in [run_abi_validation.py](backend/run_abi_validation.py)
and `reuse_extraction`).

1. Land each pillar with its unit tests green (see
   [calibration_test_cases.md](calibration_test_cases.md)).
2. **Pillar 1:** re-merge the 50 cached sites, diff `faqs[]` counts before/after
   — expect ProPlan 5→0, schema-FAQ sites unchanged, no real markdown FAQ lost.
3. **Pillar 3:** re-score (`python -m backend.run_abi_validation`) and diff
   per-criterion earned — expect Location-presence to fall only where the
   location confidence is low; rich/high-confidence sites unchanged.
4. **Pillar 2:** re-run `detect_actionability` over the 54 cached sites — expect
   booking to fire on ~40+ vs the current 3; ProPlan → T3 (Calendly).
5. Re-run the full benchmark; confirm the score *distribution* shifts toward
   correctness (lower where defects were inflating, higher where booking was a
   false negative) and that `validate_abi_score` passes for every site.
6. Update findings #5/#6/#7/#16/#21 in
   [abi_calibration_review.md](abi_calibration_review.md) to "resolved", and log
   the calibration in [progress/](progress/) + the run cost (≈ $0) in
   [cost/cost_ledger.md](cost/cost_ledger.md).

### Acceptance criteria

- **FAQ:** ProPlan reports 0 FAQs; every surviving FAQ in the 50-site set is a
  genuine Q/A pair on manual spot-check; no net loss of schema-sourced FAQs.
- **Confidence:** no criterion ever exceeds its max; the rich HVAC fixture still
  scores ≥ 83 overall (high-confidence facts are not penalized); a low-confidence
  single-mention location scores **< 8/20**, not 20/20.
- **Booking:** every site with a real scheduler/booking link gets booking credit
  at the correct tier; phone-only sites get T1; no-action sites score 0 — each
  credit names its evidence URL.
- **Framework:** `validate_abi_score` passes for all sites; weights, dimensions,
  criteria names, and grade bands are byte-for-byte unchanged.

---

## 6. Out of scope (restated)

Not in Goal 03D — would change the framework or belong elsewhere:

- Industry ABI profiles / re-weighting for SaaS vs local (deferred — ABI
  Profiles, [ROADMAP](ROADMAP.md)).
- New criteria: pricing transparency, case-study/outcomes, integrations/docs.
- Extraction hygiene (blog-content bleed into services/trust).
- Reputation-bucket keyword expansion for non-local industries.
- Any dashboard / report-rendering work (Goal 04).
