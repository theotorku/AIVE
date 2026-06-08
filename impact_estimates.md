# Goal 03D — Impact Estimates

Expected ABI movement from the three calibration pillars. Estimates are derived
from the traced ProPlan scorecard in
[abi_calibration_review.md](abi_calibration_review.md) and the 54-site corpus
measurements in [agent_actionability_model.md](agent_actionability_model.md).
**All deltas come from changing *how points are earned inside existing
criteria* — no dimension, weight, criterion, or grade band changes.**

Dimension weights used throughout: U .25 / R .25 / Rec .20 / Agent .15 /
Auth .15. A criterion's ABI delta = (Δ earned within its dimension, as a % of
that dimension's 100 points) × dimension weight.

---

## 1. Worked example — ProPlan (proplansolutions.io), today 59.7 / D

ProPlan is the calibration witness: an AI-automation agency scored by the
local-service-calibrated ABI v0.1. Its 59.7 is "plausible for the wrong reasons"
— inflating defects roughly cancel deflating ones. Goal 03D removes the
inflation and the one big deflation, yielding a more *honest* (lower, but
correct) score.

### Pillar 1 — FAQ validity (removes inflation)

The 5 fake FAQs drop to 0, zeroing three criteria across two dimensions:

| Dimension | Criterion | Earned → | Dim earned | Dim Δ | × weight | **ABI Δ** |
|---|---|---|---|---|---|---|
| Retrieval | FAQ coverage | 35 → 0 | 67.0 → 22.0 | −45.0 | .25 | **−11.25** |
| Retrieval | FAQ answer quality | 10 → 0 | *(in above)* | | | |
| Authority | Knowledge depth (FAQ) | 15 → 0 | 38.6 → 23.6 | −15.0 | .15 | **−2.25** |

**Pillar 1 total: ≈ −13.5 ABI.** (Correcting the documented #6/#7/#21
inflation — the goal, not a regression.)

### Pillar 3 — Confidence-aware scoring (removes inflation)

Austin, TX at confidence 0.15 stops earning full location marks; low-confidence
count items contribute fractionally.

| Dimension | Criterion | Earned → | Note |
|---|---|---|---|
| Understanding | Location presence | 20 → ~4.3 | `20 × _conf_factor(0.15)` = 20 × 0.21 |
| Recommendation | Offers & incentives | 20 → ~17 | 4 low-conf "offers" → eff-count ~1.7/2 |
| Understanding | Service coverage | 30 → 30 | count far exceeds target even after weighting → still capped (extraction-hygiene issue, deferred) |

- Understanding: 85.4 → ~69.7 (−15.7) × .25 = **−3.9 ABI**
- Recommendation: 67.8 → ~64.8 (−3.0) × .20 = **−0.6 ABI**

**Pillar 3 total: ≈ −4.5 ABI.** (Most of it the Location fix; service-count
inflation is an *extraction* problem, out of 03D scope, so it persists.)

### Pillar 2 — Actionability / booking (corrects a deflation)

ProPlan's live Calendly link is detected at T3 → booking 0 → 20.

| Dimension | Criterion | Earned → | Dim earned | Dim Δ | × weight | **ABI Δ** |
|---|---|---|---|---|---|---|
| Agent Readiness | Online booking | 0 → 20 | 15.0 → 35.0 | +20.0 | .15 | **+3.0** |

**Pillar 2 total: ≈ +3.0 ABI.**

### Net ProPlan

```
59.7  (today, "plausible for the wrong reasons")
 −13.5  Pillar 1  FAQ validity
  −4.5  Pillar 3  confidence-aware
  +3.0  Pillar 2  booking actionability
 ─────
≈44.7  (still grade D — Low Visibility, but now correct, not propped up)
```

The headline drops ~15 points and stays in the D band. That is the intended
outcome: the FAQ defect was the prop holding 59.7 up; once removed, ProPlan
reads as the genuinely under-optimized site it is — and the single most
actionable true finding (**no schema.org markup**, #18) remains its headline
opportunity.

---

## 2. Corpus-level estimates (54 cached sites)

Directional, from the corpus signals already measured. Re-score is free
(cached), so these are validated empirically at rollout, not just modeled.

### Pillar 1 — FAQ validity

- Affects any site whose FAQs came from the `?`-line markdown heuristic on a
  non-FAQ page. Schema-sourced FAQs are trusted and unchanged.
- **Direction:** ABI *falls* on sites that were inflating via fake FAQs; the
  benchmark's "FAQ coverage" weakness count *rises* (more sites correctly
  flagged as lacking real FAQs). Net benchmark average: small decrease.
- **Risk:** real markdown FAQs on local-service sites must survive — protected
  by trusting schema + Layer A's heading-marker fallback. Verified by the
  before/after `faqs[]` diff.

### Pillar 2 — Booking actionability (largest corpus effect)

| Signal | Sites | % |
|---|---|---|
| `booking_url` set today (what the criterion reads) | 3 | 6% |
| Booking-intent CTA present | 41 | 76% |
| Real booking link in crawled HTML | 24 | 44% |

- Booking detection fires on ~3 → **~40+** sites. ~24 gain T3/T2 credit from a
  real link; the rest of the booking CTAs resolve to T1 intent (+6) where no
  destination is found.
- **Per-site Agent Readiness gain:** up to +20 within the dimension (+3.0 ABI)
  at T3, +12 (+1.8) at T2, +6 (+0.9) at T1. Most local-service sites already
  earn phone/CTA points, so the *relative* lift is smaller than ProPlan's but
  strictly upward and correct.
- **Direction:** benchmark Agent Readiness average *rises*; ~38 sites move from
  a false "no booking" to a true tier.

### Pillar 3 — Confidence-aware scoring

- Hits sites carrying low-confidence single-mention facts (incidental cities,
  blog-derived services/areas). High-confidence sites (schema-backed,
  headings, cross-page) are unaffected because `_conf_factor` saturates at 0.7.
- **Direction:** ABI *falls* modestly on sites that were earning presence/count
  points from weak evidence; no movement on strong sites.
- **Regression guard:** the rich HVAC fixture (conf 0.9 throughout) must remain
  ≥ 83 overall. If a band of medium-confidence sites over-corrects, the single
  tunable is `FULL_CONF` — not any criterion or weight.

### Net benchmark shape

| Pillar | Direction | Magnitude | Mechanism |
|---|---|---|---|
| 1 FAQ validity | ↓ average | moderate | removes fake-FAQ inflation |
| 2 Booking | ↑ Agent Readiness | large reach (~38 sites) | removes ~90% false-negative |
| 3 Confidence | ↓ on weak-evidence sites | small–moderate | Evidence × Confidence |

The benchmark becomes **more dispersed and more correct**: genuinely
agent-ready sites separate upward (booking), while sites coasting on fake FAQs
or incidental mentions fall to where they belong. Average ABI may move only
slightly net, but per-site *accuracy* improves materially — which is the point
of calibration.

---

## 3. Confidence-factor reference (Pillar 3 sensitivity)

`earned = max × evidence × _conf_factor(conf)`, `_conf_factor = min(1, conf/0.7)`.

| conf | factor | Location (20) | Offers/2 needs eff≥2 |
|---|---|---|---|
| 0.90 | 1.00 | 20.0 | full |
| 0.70 | 1.00 | 20.0 | full |
| 0.57 | 0.81 | 16.3 | strong |
| 0.40 | 0.57 | 11.4 | partial |
| 0.27 | 0.39 | 7.7 | weak |
| 0.15 | 0.21 | **4.3** | barely credible |
| 0.05 | 0.07 | 1.4 | floor |

Raising `FULL_CONF` makes scoring stricter (more sites discounted); lowering it
makes it more lenient. The corpus re-score selects the value; `0.7` is the
proposed start (aligns with the existing `confidence.label()` "high/medium"
bands).

---

## 4. Cost

All three pillars validate against **cached** crawls and profiles via
`reuse_extraction` / `run_abi_validation`. Expected incremental runtime cost:
**≈ $0** (no crawling, no LLM calls). Build cost is engineering time only; log
the calibration run in [cost/cost_ledger.md](cost/cost_ledger.md) at completion.
