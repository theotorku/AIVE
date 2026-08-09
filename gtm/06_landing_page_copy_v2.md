# Landing Page Copy v2 (HVAC-first)

Supersedes `sales/landing_page_copy.md` for launch. Changes: vertical-specific
hero, free-grade CTA as primary capture, benchmark proof, ladder pricing,
guarantee, FAQ. One page, one goal: run the free grade.

---

## Hero

**Headline:** When homeowners ask ChatGPT for an HVAC company, does it recommend you?

**Subheadline:** Get your AI Visibility Grade — a 0–100 score of whether AI
assistants like ChatGPT, Claude, Gemini, and Perplexity can understand your
services, trust your business, and send you customers.

**Primary CTA:** Get My Free AI Visibility Grade →  *(enter your website URL)*

**Trust line:** Built on the Agent Business Index — benchmarked on 50+ real HVAC
websites. Average grade: C. Nearly 1 in 3 score D or F.

## Problem

Your customers are changing how they search. Instead of ten blue links, they ask
an AI assistant one question — "who's the best HVAC company near me that does
emergency repair?" — and get one answer.

AI reads your website differently than people do. If it can't clearly find your
services, service area, reviews, and how to book, it doesn't guess. It
recommends the competitor it *can* read.

## How it works (3 steps)

1. **We crawl your site** the way AI systems do — every service page, FAQ, and
   contact path.
2. **We score what AI can actually see:** Understanding, Retrieval,
   Recommendation, Agent Readiness, Semantic Authority.
3. **You get the evidence and the fix list** — every finding backed by a quote
   from your own site, ranked by impact.

## Proof

- 50+ HVAC websites benchmarked — average grade **C**; ~31% grade **D or F**
- Real fix engagement moved a site **ABI 39 → 53 in 30 days** (re-audit verified)
- Deterministic scoring: run it twice, get the same number. No black box.

## Offer (pricing section)

**Free Grade** — your letter grade + your single biggest gap. $0.
**AI Visibility Audit — $749** *(founding price $399, first 10 HVAC companies)*
Full report, 5 dimension scores, evidence-backed findings, priority fix list,
review call.
**Audit + Fix — $2,500** We implement the fixes and re-audit in 30 days to prove
the improvement.
**Monitoring — $299/mo** Monthly re-score, alerts when your visibility changes,
quarterly re-audit.

**Guarantee:** if your audit doesn't surface at least 5 actionable findings,
it's free.

## Objection strip

*"Is this SEO?"* — No. SEO gets you ranked by Google. This measures whether AI
assistants can understand and recommend you at all. Different machine, different
rules, and the fixes help your SEO too.

## Final CTA

**Know what AI sees before your competitors do.**
It takes 60 seconds and it's free. → Get My AI Visibility Grade

## Disclaimer (footer)

The AI Visibility Audit does not guarantee rankings or recommendations inside
any specific AI system. It measures the clarity, retrievability,
recommendability, and actionability of your website content.

---

### Implementation notes

- URL field + email gate on the grade result (lead capture), not on the form
- Grade result page shows letter + top gap + blurred dimension bars → "Unlock
  the full audit" (rung 1/2 checkout)
- Gate `/api/runs` before this goes live (see 15_prelaunch_product_improvements.md)
