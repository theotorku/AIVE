# Agent Actionability Model — Investigation & Proposal

**Status:** Investigation + design. No scoring/extraction code changed.

---

## 1. The problem, proven

Agent Readiness's *Online booking* criterion reads exactly one field —
`contact_information.booking_url` — and scores it 20/0 binary. That field is
populated by the LLM and is almost never set.

**ProPlan smoking gun:** the crawled HTML contains
`"View Available Times" → https://calendly.com/proplansolutions` (a live,
deep-linkable scheduler an agent could open directly), plus three `cta_type:book`
CTAs. Yet `booking_url = null`, so the report says **"No online booking
detected" (0/20)**. The site is fully agent-bookable; the model is blind to it.

**Corpus evidence (54 crawled sites):**

| Signal | Sites | % |
|---|---|---|
| `contact_information.booking_url` set (what the criterion reads) | **3** | 6% |
| Booking-intent CTA (`cta_type:book` / "book/schedule/consult") | **41** | 76% |
| Real booking link in HTML (scheduler host, booking path, booking subdomain) | **24** | 44% |
| Scheduler *platform* link (Calendly / Cal.com / ServiceTitan…) | 3 | 6% |
| `contact.phone` | 43 | 80% |
| `contact.email` | 4 | 7% |

The booking criterion fires on **6%** of sites while a booking affordance is
actually present on **~76%** — roughly a **90% false-negative rate.** Booking is
the most under-detected actionability signal in the system, and it's the one that
matters most for "can an AI agent act here."

**Two structural extraction gaps surfaced:**
- **CTAs carry no `href`** (the LLM schema captures `value`/`cta_type` but not the
  link), so a "Book a call" CTA can't be resolved to its destination.
- **`cleaner.extract_links` drops `tel:`/`mailto:`** (0 of 54 in the link graph),
  so click-to-call / click-to-email affordances are invisible to any
  link-based detector — they survive only via `contact_information`.

The richest, most reliable booking signal (the scheduler link in
`PageDocument.links`) is **already crawled and simply unused.**

---

## 2. What "Agent Actionability" means

Distinct from human *contactability*. **Agent Actionability = how readily an AI
agent can take a concrete next action on a user's behalf** — book, request a
quote, contact, transact — weighted by how *machine-actionable* the mechanism is:

> deep-linkable URL  >  fillable form  >  voice/manual

A phone number is great for a human and weak for an agent (needs a voice call);
a Calendly URL is the opposite. ABI measures the *agent's* world, so the model
ranks mechanisms by agent-operability, not by human convenience.

---

## 3. The four questions, answered

| Signal | Counts? | Tier | Why |
|---|---|---|---|
| **CTA-based booking** ("Book a call" text) | **Yes — as intent** | T1 by default; **upgrades** to T3/T2 if its link resolves to a scheduler/form | Text proves intent; an agent still needs a destination. Resolve the CTA's `href` (once captured) to promote it. |
| **Calendly** | **Yes — strongest** | **T3** | Deep-linkable structured scheduler; an agent can open the booking surface directly. |
| **HubSpot Meetings** (`meetings.hubspot.com`) | **Yes — strongest** | **T3** | Same as Calendly — a dedicated, deep-linkable scheduler. |
| **Contact-form scheduling** | **Yes — mid-tier** | **T2** | Agent-fillable via browser automation, but not a deep link to a specific slot; one step removed from a true scheduler. |

So: **all four count**, but tiered by how directly an agent can execute, not
treated as one binary flag.

---

## 4. The model

### 4a. Action channels (what the agent can do)
1. **Scheduling/Booking** — appointments, consultations, demos.
2. **Quote / Estimate request** — "request a free estimate".
3. **Contact** — form / email / phone / chat.
4. **Transaction** — buy/checkout (rare for services; future).

### 4b. Actionability tiers (how machine-actionable), per channel
| Tier | Meaning | Examples |
|---|---|---|
| **T3 Direct** | Deep-linkable surface an agent can open/operate | Calendly, Cal.com, HubSpot Meetings, Acuity, Square Appointments, Setmore, ServiceTitan/Housecall/Jobber online booking, explicit `booking_url`, schema.org `potentialAction` (ReserveAction/ScheduleAction/OrderAction), `/book-online` deep links |
| **T2 Form** | Agent can complete a form | contact/quote/appointment-request forms, `/contact`, `/request-service` |
| **T1 Intent / human-mediated** | Affordance exists but needs a human or unresolved step | booking-intent CTA with no resolvable URL, `tel:`/click-to-call, `mailto:`, phone-to-book |
| **T0** | None | — |

A site is credited at the **highest tier achieved per channel**; channels are
independent (booking + contact can both contribute).

### 4c. Signal sources, in precedence (authoritative → weakest)
1. **schema.org `potentialAction`** — explicit machine-readable action → T3,
   highest confidence.
2. **Outbound link host/path** (`PageDocument.links`, already captured):
   scheduler-platform host → T3; booking subdomain/path or form page → T2/T3.
3. **CTA text + resolved `href`**: `cta_type:book` whose link is a scheduler →
   T3; a form → T2; unresolved → T1 (intent).
4. **`contact_information`** (`booking_url`, `phone`, `email`): one input, not the
   sole one. Covers `tel:`/`mailto:` that the link graph drops.

Confidence-weighted: a detected Calendly host is high-confidence; a bare "Book a
call" CTA is medium; an inferred booking from a generic `/book` path is lower.
Every credit carries **evidence** (the actual host/URL) so it stays explainable.

---

## 5. Scoring proposal (replaces one binary criterion)

Swap Agent Readiness's binary *Online booking* (0/20) for a **graduated
Booking/Scheduling actionability** criterion:

| Detected | Points (of 20) | Evidence shown |
|---|---|---|
| T3 direct scheduler / `potentialAction` / `booking_url` | 20 | the scheduler URL |
| T2 form-based booking | 12 | the form/booking page |
| T1 intent CTA / phone-to-book only | 6 | the CTA text / phone |
| T0 none | 0 | recommendation to add a scheduler |

Keep phone/email/address/hours criteria, but:
- **Fix email** detection (read `mailto:` or `contact.email`; currently 7%).
- **Re-weight by industry profile** (ties into the industry-ABI work): for
  SaaS/agency, scheduling is the *primary* action and should dominate Agent
  Readiness; phone/address/hours matter less. For local service, phone +
  book-online dominate. The *detection* is industry-agnostic; only the *weights*
  vary.

This is a scoring change — **not made here.** With it, ProPlan's booking goes
0 → 20 (Calendly T3), Agent Readiness 15 → ~35, overall ≈ +3, and ~38 more
corpus sites gain correct booking credit.

---

## 6. Detection spec (for implementation, later)

New module `backend/app/services/actionability.py`:
- `detect_actionability(docs, profile) -> dict` producing a structured block
  (kept **out** of the extraction contract, like `crawl_coverage` /
  `structured_data`):
  ```json
  {
    "booking": {"tier": "T3", "mechanism": "calendly",
                "evidence": "https://calendly.com/proplansolutions"},
    "quote":   {"tier": "T2", "evidence": ".../request-estimate"},
    "contact": {"phone": true, "email": false, "form": true},
    "agent_actionability_score": 0.0   // optional rollup
  }
  ```
- Inputs: `PageDocument.links` (scheduler hosts/paths), `metadata.json_ld`
  `potentialAction`, `ctas`, `contact_information`.
- Host/platform allowlist + booking-path regex (reuse the patterns validated in
  this investigation; require host match or path-in-context to avoid `/get-started`
  false positives).

**Prerequisites** (small extraction changes the model depends on):
1. **Capture CTA `href`** in the page-extraction schema (so CTA→destination
   resolution works). Today CTAs are textual only.
2. **Stop dropping `tel:`/`mailto:`** in `cleaner.extract_links` (or read them
   from `contact_information`) so click-to-call/email count.
3. Add `potentialAction` parsing to `rule_extractor._schema_org_facts`.

---

## 7. Edge cases & stance
- **Phone-only booking is T1** for an agent even though it's fine for a human —
  deliberate (agents prefer URL/form). Documented tradeoff.
- **Generic paths** (`/get-started`, `/book`) need host match or page-context to
  avoid false T3; default such cases to T2 (form) unless a scheduler host is seen.
- **Login-gated schedulers** can't be verified end-to-end; credit by presence at
  T2/T3, not by completing a booking.
- **Non-goal:** actually performing the booking. The model scores *capability to
  act*, not action.

---

## 8. Validation plan (when built)
1. Run `detect_actionability` over the 54 cached sites (free — uses cached
   crawl). **Expect:** booking actionability fires on ~40+ vs the current 3;
   ProPlan → T3 (Calendly).
2. Spot-check 10 sites: does the detected tier match the real booking mechanism?
   Tune the host allowlist / path regex on false positives.
3. After wiring the graduated criterion, re-score (`reuse_extraction`, no LLM
   cost) and confirm Agent Readiness rises only where a real booking affordance
   exists; update `abi_calibration_review.md` finding #16 to "resolved".

**Acceptance:** every site with a real scheduler/booking link gets booking credit
at the correct tier; phone-only sites get T1; sites with no action channel score
0 — and each credit names the evidence URL.

---

## 9. Recommendation summary
- **Yes to all four**, tiered: Calendly/HubSpot = T3 (direct), contact-form = T2,
  CTA-based = T1 intent that *upgrades* when its link resolves.
- Replace the single `booking_url` flag with a **multi-signal, tiered, evidence-
  bearing** Booking/Scheduling detector sourced primarily from the **already-
  crawled link graph** + schema `potentialAction`.
- Fold the weighting into **industry ABI profiles** (scheduling dominant for
  SaaS/agency; phone+book-online for local service).
- Fix the two upstream gaps first: capture CTA `href`, and stop discarding
  `tel:`/`mailto:`.
