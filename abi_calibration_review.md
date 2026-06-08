# ABI Calibration Review — ProPlan Solutions

**Subject:** proplansolutions.io
**ABI:** 59.7 / 100 (D — Low Visibility)
**Crawl:** 10/10 meaningful pages (full coverage), 0 schema.org blocks
**Date:** 2026-06-07
**Scope:** Analysis only. No code or scoring changed. Every finding is traced to
its extraction evidence (`profile.json`) and its scoring criterion
(`backend/app/services/abi_score.py`).

ProPlan is an **AI automation agency / SaaS hybrid** (product: ScopeAI). ABI
v0.1 was calibrated against **local service businesses (HVAC)**. This review
separates *engine defects* (wrong regardless of industry) from *industry-context
gaps* (the local-service bias) so the two are not conflated.

> **Calibration update (Goal 03D, 2026-06-08).** The three engine defects have
> been fixed and the cached profile re-scored (free, no LLM). **ProPlan ABI
> 59.7 → 42.0 (D).** It dropped *for the right reasons*, each traceable to a
> resolved finding:
> - **FAQ validity gate (#6/#7/#21 → resolved):** the 5 garbled fragments are
>   filtered; ProPlan now reports **0 FAQs**. Retrieval 67.0 → 18.0, Authority
>   38.6 → 20.9.
> - **Confidence-aware location (#5 → resolved):** Austin, TX @ 0.15 now earns
>   `20 × conf_factor(0.15)` = **4.3/20**, not 20/20. Understanding 85.4 → 69.7.
>   (Confidence-weighting also discounts other low-confidence ProPlan facts.)
> - **Booking actionability (#16 → resolved):** the live Calendly link is
>   detected at **T3 → 20/20** (was 0/20). Agent Readiness 15.0 → 34.1.
>
> Corpus: booking credit now fires on **42/54** sites (T3 4 · T2 16 · T1 22) vs
> the old 3. The headline finding **#18 (no schema.org)** remains correct and is
> still ProPlan's top opportunity.

> **Extraction-hygiene update (Goal 03E, 2026-06-08).** Findings #3/#11/#13/#19
> resolved by provenance labelling (no scoring change). ProPlan: services
> **44 → 14** (29 separated as `blog_example`), trust signals **12 → 4** (8
> separated as `case_study`), offers **4 → 1** (3 separated as `pricing_tier`),
> ABI **42.0 → 39.0** — moved *only* because the scorer received cleaner lists.
> Real first-party HVAC services across the benchmark were preserved (0
> reclassified). The deferred buckets (#9/#10/#15/#20 industry profiles;
> reputation buckets; a pricing *criterion*) remain future ABI Profiles work.

---

## 1. Summary scorecard

| # | Dimension · Criterion | Score | Verdict | Primary cause |
|---|------------------------|-------|---------|---------------|
| 1 | Understanding · Business identity | 15/15 | ✅ Correct | name extracted |
| 2 | Understanding · Industry clarity | 15/15 | ✅ Correct | industry extracted |
| 3 | Understanding · Service coverage | 30/30 | 🟡 Partial | 44 inflated by blog noise (cap hides it) |
| 4 | Understanding · Service clarity | 5.4/20 | ✅ Correct | low confidence rightly flags noise |
| 5 | Understanding · Location presence | 20/20 | ❌ Incorrect | 1 low-conf city = full marks; contradicts "no address" |
| 6 | Retrieval · FAQ coverage | 35/35 | ❌ Incorrect | "FAQs" are garbled marketing fragments |
| 7 | Retrieval · FAQ answer quality | 10/10 | ❌ Incorrect | "answers" are CTA copy |
| 8 | Retrieval · Heading structure | 5/20 | 🟡 Partial | true signal, denominator inflated by 44 |
| 9 | Retrieval · Geographic specificity | 5/20 | 🟦 Needs context | geo irrelevant for non-local SaaS |
| 10 | Retrieval · Content breadth | 12/15 | 🟦 Needs context | 6 blog pages excluded as low-signal |
| 11 | Recommendation · Trust signals | 40/40 | 🟡 Partial | mix of real proof + value-props + blog stats |
| 12 | Recommendation · Reputation diversity | 6/30 | 🟡 Partial (too low) | keyword buckets miss SaaS proof |
| 13 | Recommendation · Offers & incentives | 20/20 | ❌ Incorrect | pricing tiers mis-classified as promos |
| 14 | Recommendation · Trust signal strength | 1.8/10 | 🟡 Partial | conflates quality with extraction confidence |
| 15 | Agent Readiness · Phone/Email/Address/Hours | 0/65 | 🟦 Needs context | factually absent, but local-service weighting |
| 16 | Agent Readiness · Online booking | 0/20 | ❌ Incorrect | booking CTAs ignored (silo bug) |
| 17 | Agent Readiness · Calls to action | 15/15 | ✅ Correct | CTAs detected |
| 18 | Authority · Structured data (schema.org) | 0/35 | ✅ Correct | verified 0 JSON-LD blocks |
| 19 | Authority · Service depth | 20/20 | 🟡 Partial | inflated by blog services |
| 20 | Authority · Geographic authority | 3/15 | 🟦 Needs context | geo irrelevant for SaaS |
| 21 | Authority · Knowledge depth (FAQ) | 15/15 | ❌ Incorrect | same garbled FAQs as #6 |
| 22 | Authority · Cross-page corroboration | 0.6/15 | ✅ Correct | facts genuinely scattered |

**Tally:** Correct 6 · Partial 6 · Incorrect 6 · Needs-context 4. Plus 5 *missing*
findings (§4).

**Net effect on the 59.7:** the **incorrect** criteria roughly cancel — FAQ
(#6/#7/#21 ≈ **+13.5 ABI** too high), Location (#5 ≈ **+5**), and mis-filed Offers
(#13 ≈ **+2 to +4**) *inflate*; Online booking (#16 ≈ **−3**) and under-counted
Reputation diversity (#12 ≈ **−2 to −5**) *deflate*. Inflation (~+20) outweighs
deflation (~−5 to −8), so the **true ABI is likely lower than 59.7** — the
headline looks plausible largely because the FAQ defect props it up. (Deltas =
criterion point change × dimension weight; weights U/R/Rec/Agent/Auth =
.25/.25/.20/.15/.15.)

Legend: ✅ Correct · 🟡 Partially correct · ❌ Incorrect · 🟦 Directionally
correct, needs industry context · (➕ Missing, §4)

---

## 2. Detailed trace by dimension

### AI Understanding — 85.4/100 (B)

**[1] Business identity — 15/15 ✅ Correct**
- *Extraction:* `business_name = "ProPlan Solutions"`.
- *Criterion:* 15 pts if a business name is present, else 0.
- *Why assigned:* name present → 15.
- *Why it may be wrong:* it isn't. Accurate.

**[2] Industry clarity — 15/15 ✅ Correct**
- *Extraction:* `industry = "AI Strategy & Automation Solutions"`.
- *Criterion:* 15 pts if industry present.
- *Why assigned:* present → 15.
- *Why it may be wrong:* the label is verbose/marketing ("…Solutions") rather
  than a clean category ("AI automation agency"), but it is correct and useful.

**[3] Service coverage — 30/30 🟡 Partially correct**
- *Extraction:* **44** services. The top 9 (conf 0.55–0.67) are genuine ScopeAI
  features (AI Lead Scoring, Live Analytics, Custom AI Workflows, SOW Conversion,
  Risk Detection…). The long tail (conf **0.14**) is scraped from **blog posts**
  about *other* industries — "Intelligent Waitlist Management", "Returns
  Processing Automation", "Automated Showing Scheduler" — i.e. example
  automations, not ProPlan's own catalogue.
- *Criterion:* `min(1, len(services)/6) × 30`. 44 ≥ 6 → 30.
- *Why assigned:* count far exceeds the target of 6, so full marks.
- *Why it may be wrong:* the **count is inflated ~5×** by blog-derived
  pseudo-services. The cap at 6 hides this (it would score 30/30 even with only
  the 9 real features), so the *number* is misleading even though the *score* is
  defensible. The real defect is upstream (extraction pulling blog examples into
  the site's own services); the score launders it.

**[4] Service clarity — 5.4/20 ✅ Correct**
- *Extraction:* average service confidence = **0.27** (dragged down by the 0.14
  blog tail).
- *Criterion:* `avg_confidence(services) × 20`.
- *Why assigned:* 0.27 × 20 = 5.4.
- *Why it may be wrong:* this is the engine working as intended — it correctly
  penalizes the low-confidence noise from #3. If extraction stopped importing
  blog examples, the average over the 9 real features (~0.57) would score ~11.4.
  The signal is honest; it's the right counter-weight to the inflated count.

**[5] Location presence — 20/20 ❌ Incorrect**
- *Extraction:* `locations = ["Austin, TX"]` at confidence **0.15**;
  `contact_information.address = null`.
- *Criterion:* 20 pts if `locations` non-empty **or** `contact.address` present
  (binary — any hit = full marks).
- *Why assigned:* one location object exists → 20.
- *Why it may be wrong:* (a) **internal contradiction** — Agent Readiness [15]
  reads the same profile and reports "No address detected" (0/15). Understanding
  says the location is present; Agent Readiness says it isn't. (b) A single
  **0.15-confidence** city mention (likely incidental copy, not a verified HQ)
  earns the *same* 20 points as a fully-verified LocalBusiness address. The
  criterion is confidence-blind and binary. For a distributed SaaS/agency,
  "physical location present" is also weakly relevant.

### AI Retrieval — 67.0/100 (C)

**[6] FAQ coverage — 35/35 ❌ Incorrect** *(highest-impact defect)*
- *Extraction:* 5 "FAQs", but the **questions are garbled fragments**:
  `"something real?"`, `"Prefer to Talk First?"`, `"your business?"`,
  `"in your business?"`, `"Read moresuccess story?"`. These come from the rule
  extractor's markdown heuristic (`_faq_from_markdown`) grabbing any line ending
  in "?" — it sliced sentence-fragments out of marketing copy. The "answers" are
  **CTA blurbs** ("Book a free strategy call…"), not Q&A.
- *Criterion:* `min(1, len(faqs)/5) × 35`. 5 ≥ 5 → 35 (the single highest-weighted
  retrieval criterion).
- *Why assigned:* five items exist in `faqs[]`, so full marks — the criterion
  counts *items*, never inspects question/answer *validity*.
- *Why it may be wrong:* ProPlan has **essentially no real FAQ content**, yet
  this is its strongest retrieval score. A garbage-in/full-marks-out failure that
  also propagates to [21] Knowledge depth. This single defect adds ~13 ABI points
  the site has not earned.

**[7] FAQ answer quality — 10/10 ❌ Incorrect**
- *Extraction:* all 5 "answers" are non-empty (they're CTA copy).
- *Criterion:* `(faqs with non-empty answer)/len × 10`. 5/5 → 10.
- *Why assigned:* every item has a non-empty `answer` string.
- *Why it may be wrong:* "non-empty" ≠ "substantive answer to a real question."
  The rationale even prints "5/5 FAQs include a substantive answer," which is
  false. Compounds #6.

**[8] Heading structure — 5/20 🟡 Partially correct**
- *Extraction:* 11 of 44 services appear in page headings.
- *Criterion:* `(services_in_headings)/len(services) × 20`. 11/44 = 0.25 → 5.0.
- *Why assigned:* ratio of heading-reinforced services.
- *Why it may be wrong:* directionally right (ProPlan's services genuinely aren't
  all in H1/H2), but the **denominator is the inflated 44** from #3, so the ratio
  is artificially deflated. Against the 9 real features, the ratio would be far
  healthier. The score punishes the site for extraction noise.

**[9] Geographic specificity — 5/20 🟦 Needs industry context**
- *Extraction:* `service_areas = ["Denver"]` at confidence **0.14** (almost
  certainly from the real-estate blog post, not a declared service area).
- *Criterion:* `min(1, len(areas)/4) × 20`. 1/4 → 5.0.
- *Why assigned:* one area named out of a target of 4.
- *Why it may be wrong:* **ProPlan is not a geographically-bounded business.**
  "Cities served" is a local-service concept; penalizing a national SaaS for not
  listing service areas is a category error. The one area it *did* find is blog
  noise, making the signal doubly meaningless. ~3.75 ABI points are being
  decided by an irrelevant criterion.

**[10] Content breadth — 12/15 🟦 Needs industry context**
- *Extraction:* `source_pages` categories: home, service_detail, contact, about
  (=4 "relevant") + **6 blog** (blog index + 5 posts).
- *Criterion:* `min(1, relevant_pages/5) × 15` where "relevant" excludes
  `blog`/`unknown`. 4/5 → 12.0.
- *Why assigned:* 4 non-blog pages out of a target of 5.
- *Why it may be wrong:* this is the "10 crawled but only 4 relevant" discrepancy.
  It is **internally consistent** (blog is deliberately discounted), so it's not
  a bug — but for an agency/SaaS the blog *is* substantive retrieval surface
  (case studies, use-cases). The local-service assumption "blog = low signal"
  doesn't hold here. Classification of `/products/scopeai` as `service_detail`
  was correct.

### AI Recommendation — 67.8/100 (C)

**[11] Trust signals — 40/40 🟡 Partially correct**
- *Extraction:* 12 trust signals — a genuine mix: real proof ("15+ businesses
  served", "HIPAA-compliant systems"), case-study outcomes ("Lead conversion
  jumped from 19% to 43%", "Quote prep time dropped by 72%"), and value-props
  ("No monthly subscriptions or hidden fees").
- *Criterion:* `min(1, len(trust)/4) × 40`. 12 ≥ 4 → 40.
- *Why assigned:* count exceeds target → full marks.
- *Why it may be wrong:* several "trust signals" are pricing value-props or
  blog-derived stats from *other companies' case studies*, not ProPlan's own
  credentials. The count (and full score) is partly inflated by the same
  blog-bleed as #3.

**[12] Reputation diversity — 6/30 🟡 Partially correct (likely too low)**
- *Extraction:* the bucket matcher hit only `guarantee` (1/5).
- *Criterion:* `(buckets hit)/5 × 30`, buckets = guarantee/certification/awards/
  experience/reviews via keyword lists.
- *Why assigned:* only one bucket's keywords matched.
- *Why it may be wrong:* the keyword lists are **HVAC-flavoured** and miss real
  SaaS proof present in the data: "15+ businesses served" is *experience* (no
  "years/since" keyword), "HIPAA-compliant" is *certification* (no
  "certified/licensed/EPA/NATE" keyword). So diversity is **under-counted** —
  the score is probably too harsh, not too generous. A keyword gap, not a real
  reputation gap.

**[13] Offers & incentives — 20/20 ❌ Incorrect**
- *Extraction:* `offers = ["Starter Package", "Growth Package", "Enterprise
  Package", "Free Strategy Call"]`.
- *Criterion:* `min(1, len(offers)/2) × 20`. 4 ≥ 2 → 20.
- *Why assigned:* four "offers" ≥ target of 2.
- *Why it may be wrong:* three of the four are **pricing tiers**, not
  promotions/discounts/financing. They were mis-classified into `offers`. Only
  "Free Strategy Call" is a genuine incentive. For a SaaS, transparent **pricing
  tiers are a strong positive signal** — but ABI has *no pricing criterion*, so
  it both mis-files them and fails to credit them where they'd count (§4).

**[14] Trust signal strength — 1.8/10 🟡 Partially correct**
- *Extraction:* average trust-signal confidence = **0.18**.
- *Criterion:* `avg_confidence(trust) × 10`.
- *Why assigned:* 0.18 × 10 = 1.8.
- *Why it may be wrong:* it conflates *credibility* with *extraction confidence*.
  The low average mostly reflects that these stats were scraped once each from
  scattered blog pages — an artifact of provenance, not necessarily of how
  credible the claim is. Reasonable as a proxy, but it's measuring the wrong
  thing precisely.

### Agent Readiness — 15.0/100 (F)

**[15] Phone 0/20 · Email 0/15 · Address 0/15 · Hours 0/15 🟦 Needs context**
- *Extraction:* `contact_information = {phone:null, email:null, address:null,
  hours:null, booking_url:null}`.
- *Criterion:* each is binary on the corresponding contact field.
- *Why assigned:* all fields null → 0 across 65 of 100 Agent-Readiness points.
- *Why it may be wrong:* **factually these are probably absent** (ProPlan routes
  through a contact form + booking), so the individual zeros may be *correct*.
  The problem is **weighting**: 65% of Agent Readiness rides on phone/address/
  hours — the contact pattern of a *local service business*. A SaaS that is
  perfectly agent-actionable via booking + form is scored "F" for not publishing
  a street address and business hours it has no reason to post. Address=0 also
  contradicts Location-presence=20 (#5). (Email *may* be a true miss worth
  flagging — a contact email is reasonable for any business.)

**[16] Online booking — 0/20 ❌ Incorrect** *(the booking/CTA silo bug)*
- *Extraction:* `booking_url = null`, **but** `ctas` contains
  `{"Book a 15-minute intro call", cta_type:"book"}`,
  `{"Book Your Free Strategy Call", cta_type:"book"}`, and "Book a free strategy
  call". `offers` also has "Free Strategy Call".
- *Criterion:* `20 if contact.booking_url else 0` — reads **only** `booking_url`.
- *Why assigned:* the LLM never populated `booking_url` (the booking links are
  external Cal/Calendly-style hrefs it didn't lift into that field), so 0.
- *Why it may be wrong:* the site **obviously offers booking** — three booking
  CTAs prove it — yet the criterion prints "No online booking detected." The
  booking signal is captured in `ctas` but the booking criterion is siloed to
  `booking_url`. This is the clearest engine defect: a self-contradiction within
  one report. Crediting booking-intent CTAs would move Agent Readiness 15 → 35
  (overall +3).

**[17] Calls to action — 15/15 ✅ Correct**
- *Extraction:* 6 CTAs (book/call/contact types).
- *Criterion:* `min(1, len(ctas)/3) × 15`. 6 ≥ 3 → 15.
- *Why assigned:* count ≥ target.
- *Why it may be wrong:* correct. (Ironically the same CTAs that prove [16] is
  wrong are fully credited here.)

### Semantic Authority — 38.6/100 (F)

**[18] Structured data (schema.org) — 0/35 ✅ Correct** *(the valuable finding)*
- *Extraction:* `structured_data.schema_org_detected = false`; verified **0
  JSON-LD blocks across all 10 crawled pages**.
- *Criterion:* business schema (20) + FAQPage schema (15); both absent → 0.
- *Why assigned:* no schema.org markup anywhere.
- *Why it may be wrong:* it isn't — this is true and the highest-value, most
  actionable finding in the whole report. ProPlan genuinely gives AI systems no
  machine-readable structure. This is the audit category that matters.

**[19] Service depth — 20/20 🟡 Partially correct**
- *Extraction:* 44 services (see #3).
- *Criterion:* `min(1, len(services)/8) × 20`. 44 ≥ 8 → 20.
- *Why assigned:* count ≥ authority target of 8.
- *Why it may be wrong:* inflated by the same blog-derived services as #3. The
  real product *does* have depth (9 solid features), so the score isn't crazy —
  but it's full marks for partly the wrong reason.

**[20] Geographic authority — 3/15 🟦 Needs context**
- *Extraction:* 1 service area ("Denver", 0.14).
- *Criterion:* `min(1, len(areas)/5) × 15`. 1/5 → 3.0.
- *Why assigned:* one area / target 5.
- *Why it may be wrong:* same category error as #9 — geographic coverage is a
  local-service authority signal, not a SaaS one.

**[21] Knowledge depth (FAQ) — 15/15 ❌ Incorrect**
- *Extraction:* the same 5 garbled "FAQs" from #6.
- *Criterion:* `min(1, len(faqs)/5) × 15`. 5 → 15.
- *Why assigned:* five FAQ items exist.
- *Why it may be wrong:* inherits the #6 defect — full "knowledge depth" credit
  for marketing fragments. The bad FAQ extraction is now inflating *two*
  dimensions (Retrieval and Authority).

**[22] Cross-page corroboration — 0.6/15 ✅ Correct**
- *Extraction:* only 2 of 51 facts carry a "repeated across" confidence reason.
- *Criterion:* `(facts repeated across pages)/total × 15`. 2/51 → 0.6.
- *Why assigned:* almost nothing is corroborated across pages.
- *Why it may be wrong:* it's accurate — ProPlan's facts are mostly one-off
  mentions (each service stated once, many on a single blog page). Honest signal.

---

## 3. Cross-cutting issues

**A. Internal contradictions (engine, not industry).**
1. *Booking:* [16] "No online booking detected" vs three `cta_type:book` CTAs.
2. *Location:* [5] "Physical location/address information present" (20/20) vs
   [15] "No address detected" (0/15) — same profile, opposite conclusions.
These are the findings a founder will point at first; they read as the tool
"not even agreeing with itself."

**B. Garbage FAQ extraction propagates.** One upstream defect (`_faq_from_markdown`
slicing "?"-terminated fragments) produces 5 fake FAQs that earn full marks in
**three** criteria (#6, #7, #21) = ~28 raw points across two dimensions. Extraction
quality, not scoring logic, but the scorer has no validity gate to catch it.

**C. Blog-content bleed.** Services (#3), service depth (#19), and some trust
signals (#11) are inflated by automations/stats lifted from blog posts about
*other* industries. The confidence engine partially compensates (#4 drags
clarity down), but counts remain misleading.

**D. Local-service bias is structural, not incidental.** Four criteria (#9, #10,
#15, #20 — geographic ×2, blog-discount, physical-contact ×4) bake in
assumptions that only fit local service businesses. For ProPlan they collectively
suppress Retrieval, Agent Readiness, and Authority for reasons that don't apply.
This is the v0.1 calibration target showing through — expected, but now visible.

**E. Keyword-matched buckets don't travel across industries.** Reputation
diversity (#12) under-credits real SaaS proof because its keyword lists were
tuned for HVAC certifications.

---

## 4. Missing findings (things ABI should have surfaced but didn't)

- **Pricing transparency (SaaS positive).** ProPlan publishes Starter/Growth/
  Enterprise tiers — a strong "AI can understand your commercial model" signal.
  ABI has no pricing criterion, so it mis-files them as "offers" (#13) and never
  credits them.
- **Booking as agent-actionability.** Captured in `ctas` but not counted toward
  Agent Readiness (#16). The single most agent-relevant affordance ProPlan has is
  invisible to the dimension named "Agent Readiness."
- **Case-study / outcomes as a distinct signal.** Strong quantified results
  ("19%→43% conversion", "72% less quote prep") are diluted into `trust_signals`
  rather than recognized as the agency's core proof type.
- **Integrations / docs / onboarding (SaaS).** Not modeled at all; these are the
  SaaS equivalents of "service area / hours" and would matter for an AI deciding
  whether it can *work with* ProPlan.
- **Email contact.** Among the four contact zeros, a missing contact email is the
  one genuinely worth flagging for any business type — currently lumped in with
  the local-service-biased phone/address/hours.

---

## 5. Conclusion (analysis only)

The 59.7 / D is **plausible for the wrong reasons**: inflating defects (fake FAQs
≈ +13.5, location +5, mis-filed offers +2–4 ≈ **+20**) outweigh deflating ones
(booking bug −3, reputation under-count −2–5 ≈ **−5 to −8**), so the *true* ABI is
likely **somewhat lower** than 59.7. The headline survives mainly because the FAQ
defect is propping it up; the sub-scores are not yet trustworthy.

Priorities the data supports, in order of how clearly "wrong" they are
(no changes made — for discussion):

1. **Engine defects (industry-agnostic):** booking/CTA silo (#16), FAQ-validity
   gate (#6/#7/#21), location confidence/contradiction (#5 vs #15).
2. **Extraction hygiene:** stop blog-example automations and other-industry stats
   bleeding into the site's own services/trust (#3/#11/#19).
3. **Cross-industry robustness:** reputation buckets that recognize SaaS proof
   (#12); pricing as a first-class signal (§4).
4. **Industry-aware ABI profiles:** Local-Service vs SaaS vs Agency criteria/
   weights for the geographic + physical-contact assumptions (#9/#10/#15/#20).

The most defensible, owner-surprising finding — **"no schema.org structured
data"** (#18) — is correct and is exactly the value proposition of the product.
