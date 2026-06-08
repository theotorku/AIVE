# AIVE — Sales & Go-To-Market Strategy

The strategy layer above the tactical kit ([offer](offer.md) · [qualification](qualification.md)
· [outreach](outreach.md) · [objections](objections.md) · [demo_script](demo_script.md)
· [landing_page_copy](landing_page_copy.md) · [launch_checklist](launch_checklist.md)).
Read this for the *why and the sequence*; read those for the *words*.

---

## 1. Thesis

A new visibility channel is opening — customers ask ChatGPT, Claude, Gemini, and
Perplexity for recommendations — and **most businesses are unreadable to it**
(our benchmark: 54 sites, average grade **C**, ~31% score D/F). SEO agencies
optimize for Google; nobody owns "is your business legible to AI?"

We sell the **AI Visibility Audit** — a concrete, evidence-backed grade of how
well AI systems understand, retrieve, recommend, and act on a business — and then
sell the **fix**. The score (ABI) is the proprietary instrument; the audit is the
product; the fix and monitoring are the recurring revenue.

**Category we're claiming:** *AI Visibility* (the AEO/agent-era successor to SEO).
Win by owning the term, the benchmark, and the measurement standard.

---

## 2. The strategic wedge: audit-led growth

The defining economic fact: **an audit costs ~$0.004 + a crawl and is fully
automated.** That changes the sales motion from "pitch, then maybe demo" to
**"show them their grade first."**

> Pre-audit a list of prospects, then open with their *actual result*:
> *"We ran an AI Visibility Audit on \[their site] — it scores a **D**. AI can't
> reliably tell what you do or how to book you. Here's the 1-page report."*

Nothing else in the outreach stack converts like a real, specific, free finding
about the prospect's own business. This is the growth engine; everything below
serves it.

---

## 3. Beachhead market

Go narrow to build repeatable proof and benchmark density. **Start with one local-
service vertical** (HVAC is the calibration target for ABI v0.1.1), then expand to
adjacent home services.

ICP (see [qualification.md](qualification.md)): inbound-lead-dependent local
service businesses with a real website, a service area, existing SEO/ads spend,
margin to pay, and the ability to edit their site. Buying signals: recent
redesign, running ads, no schema.org, weak/missing FAQs.

Why a single vertical first: identical failure modes → a reusable fix playbook,
word-of-mouth inside a tight network, and a **vertical benchmark** ("we audited
50 HVAC sites") that becomes both proof and content. Expand vertical-by-vertical;
do **not** chase SaaS/agencies until ABI Profiles ship (out of v0.1.1 scope).

---

## 4. Positioning

- **Sell clarity, not rankings.** We never promise "rank #1 in ChatGPT." We prove
  what AI can and cannot understand from their site *today*, and the path to fix
  it. (See "What Not To Sell Yet" in [offer.md](offer.md).)
- **Lead with the business outcome**, not the scoring system. ABI is the
  instrument; "get found, recommended, and booked by AI" is the pitch.
- **Proof assets:** the live grade + evidence, the downloadable report, the
  industry benchmark, and a **before→after re-audit** that quantifies the fix.

---

## 5. The product ladder (land → expand)

Each rung maps to an asset we already have. Land cheap and concrete; expand into
recurring.

| Rung | Offer | Price | Delivery asset | Goal |
|---|---|---:|---|---|
| 0 | **Free teaser** — grade + top gap only | $0 | landing "Run free audit" / pre-audit | Open the conversation (the wedge, §2) |
| 1 | **Pilot Audit** | $399 | dashboard + HTML report + 30-min call | First 5–10 logos + testimonials |
| 2 | **Standard Audit** | $950 | report + 60-min call + written fix list | Repeatable cash, learn objections |
| 3 | **Audit + Fix** | $2,500 | the **[Agent-Visible Website Fixer](../playbooks/agent-visible-website-fixer.prompt.md)** + [spec](../playbooks/agent-visible-website-spec.md) + 30-day re-audit | Higher ACV, prove the lift |
| 4 | **Monitoring retainer** | $300–$1,000/mo | scheduled re-score, ABI history, alerts | **Recurring revenue / SaaS path** |

The fix engagement (rung 3) is the strategic hinge: it's where the
[fixer skill](../.claude/skills/agent-visible-website-fixer/SKILL.md) turns a
report into delivered outcomes, and where the **re-audit proves a number went
up** — which justifies the monitoring retainer (rung 4). Don't lead with a SaaS
subscription; earn it by delivering rungs 1–3 first.

---

## 6. Unit economics (why this works)

- **COGS per audit ≈ $0.004 LLM + a crawl** → audit gross margin is effectively
  ~99%. A $399–$950 audit is almost pure margin.
- **Fix delivery is leveraged** by the fixer skill + spec (the same playbook every
  time; generate JSON-LD/FAQ artifacts from the audit — see the worked example in
  `playbooks/examples/`, which moved a real site **ABI 39→53**).
- **Monitoring is near-zero marginal cost** — re-scoring cached crawls is free
  (`reuse_extraction`), so a $300–$1,000/mo retainer is high-margin recurring.
- **Implication:** price on *value delivered* (found + booked customers), not on
  cost. Spend the margin on audit-led outbound (§2) and proof.

---

## 7. Channels (in priority order)

1. **Audit-led outbound** (primary). Build a target list (ICP, §3), batch-run
   audits, personalize outreach with each grade. Scripts: [outreach.md](outreach.md).
2. **Agency / web-designer partnerships** (leverage). SEO shops, web designers,
   and marketing agencies serving local businesses can **white-label/resell** the
   audit as a new line item. They have the relationships; we have the instrument.
3. **Content / benchmark PR** (demand gen). Publish the vertical benchmark
   ("We audited 50 HVAC websites for AI visibility — here's what we found"),
   teardown threads, and a public "AI Visibility Index." The frozen ABI standard
   makes these credible and repeatable.
4. **Inbound from the landing page** — free teaser audit as the top-of-funnel
   capture.

---

## 8. Sales motion

1. **Trigger:** a real grade (pre-audit) lands in front of a qualified owner.
2. **Discovery + live demo:** run/replay their audit on the call; walk the grade,
   the 5 signals, and the top-3 fixes in plain language (the dashboard is built
   for 60-second comprehension). Flow: [demo_script.md](demo_script.md).
3. **Close the audit** (rung 1/2) — low-friction, fixed-scope, fast.
4. **Expand to fix** (rung 3): the report's prioritized fixes become the SOW; the
   fixer delivers JSON-LD/FAQ/schema; 30-day re-audit shows the lift.
5. **Convert to monitoring** (rung 4) on the strength of the proven improvement.
6. Objection handling throughout: [objections.md](objections.md).

---

## 9. North star & funnel metrics

**North star:** ABI adoption (audits delivered + sites improved). Early business
milestones (from the PRD): **first paying audit → first fix engagement → first
recurring customer → first vertical benchmark.**

| Stage | Metric | Early target |
|---|---|---|
| Top | audits run (incl. free pre-audits) | 100+ |
| Outreach | pre-audit → reply rate | ≥ 15% (grade hook) |
| Sales | audit close rate | ≥ 25% of demos |
| Expansion | audit → fix attach | ≥ 30% |
| Recurring | fix → monitoring conversion | ≥ 40% |
| Proof | avg ABI lift after fix | +15 points |

---

## 10. 30 / 60 / 90

- **0–30 — prove it sells.** Pick HVAC. Build a 100-prospect list. Pre-audit all.
  Outreach with grades. Goal: **first 3 paid pilot audits + 3 testimonials.**
- **30–60 — make delivery repeatable.** Standardize the audit→report→call flow and
  the fix playbook (fixer skill). Land **first Audit+Fix**; capture a before→after
  case study. Sign **first agency reseller** conversation.
- **60–90 — start recurring + own the narrative.** Convert a fix client to
  **monitoring**. Publish the **HVAC AI-Visibility benchmark** as content/PR.
  Decide the second vertical.

---

## 11. Moat & defensibility

- **Proprietary, frozen instrument (ABI v0.1.1).** A stable, explainable,
  benchmarked standard — not a black box. Re-audits are comparable over time.
- **Accumulating benchmark data.** Every audit enriches per-vertical benchmarks
  that become a product (Industry Benchmarks, ABI history — PRD Phase 3) and a
  content moat competitors can't fabricate.
- **The closed loop:** audit (find) → fix (the skill/spec) → re-audit (prove) →
  monitor (recur). We grade *and* fix *and* verify with the same instrument.
- **Category ownership.** First credible "AI Visibility" standard for SMBs.

---

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| "Is AI visibility real revenue yet?" skepticism | Sell clarity + readiness, not rankings; cite the adoption trend; price the pilot low to de-risk. |
| Over-promising AI rankings | Hard rule: never promise rankings/leads/algorithm access ([offer.md](offer.md)). |
| Audit feels like a one-off | Lead the ladder toward fix + monitoring; the re-audit creates the recurring hook. |
| Non-local prospects score unfairly | Stay in-scope (ABI v0.1.1 = local services); defer SaaS/agencies to ABI Profiles. |
| Open audit endpoint abused for cost | Gate `/api/runs` before public launch (see [DEPLOYMENT.md](../DEPLOYMENT.md) §4). |
| Commoditization | Lean on the benchmark dataset, the fix-delivery loop, and category ownership. |
```
