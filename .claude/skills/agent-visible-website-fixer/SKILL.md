---
name: agent-visible-website-fixer
description: >-
  Remediate a website so AI agents and answer engines (ChatGPT, Claude, Gemini,
  Perplexity) can understand, retrieve, recommend, and act on it — i.e. raise its
  Agent Business Index (ABI) / AI Visibility Audit score. Use when a user wants to
  make a site "agent-visible" or "AI-visible", fix the gaps an AIVE/ABI audit
  surfaced (missing schema.org, weak or fake FAQs, ambiguous services, no online
  booking, inconsistent NAP, thin trust signals), add JSON-LD / FAQPage /
  LocalBusiness / potentialAction markup, or build a new AI-optimized website.
  Pairs with the AIVE audit and follows the Agent-Visible Website Specification.
---

# Agent-Visible Website Fixer

You remediate a website so machines can understand, retrieve, recommend, and act
on the business — raising its **ABI v0.1.1** score. You make *true* facts
machine-readable; you never invent them.

**Read first:** [the Agent-Visible Website Specification](../../../playbooks/agent-visible-website-spec.md).
It is the source of truth for every fix and the JSON-LD blueprints. The ABI
framework is frozen ([abi_spec_v0.1.1.md](../../../abi_spec_v0.1.1.md)), so fixes
map to stable, measurable signals.

**Worked example** of the expected output (a real audit → drop-in artifacts +
report, verified to move ABI 39→53): see
[playbooks/examples/](../../../playbooks/examples/) — `*-jsonld.html`,
`*-faq.html`, and `*-remediation.md` for `proplansolutions.io`.

## When to use
- A user shares an AIVE audit (`abi_score.json`, the report, or top fixes) and
  wants the problems fixed.
- A user asks to make a site "AI-visible / agent-visible" or to add schema.org /
  FAQPage / booking markup.
- A user wants a new website built to be agent-readable from day one.

## Inputs
- The **target** (a repo/site to edit, or a framework + page templates), and
- An **audit** — either provided, or obtained first: run the site through AIVE
  (`POST /api/runs {url}` or `python -m backend.run_abi_validation`) and read
  `abi_score.json` → `top_recommendations` (ranked by ABI impact) and each
  dimension's per-criterion `rationale` + `evidence`.

If no audit exists, **audit first** so fixes are evidence-driven, not guessed.

## Workflow

1. **Ingest & prioritize.** Parse the audit. Build a worklist from
   `top_recommendations` (highest ABI impact first) plus any criterion scoring
   below full. Note the business's *real* facts available to you (existing copy,
   prior site, what the owner provided) — you may only use these.
2. **Confirm facts, never fabricate.** For any gap needing facts you don't have
   (real FAQs, certifications, license #, review counts, hours, booking URL),
   **ask the user** or mark it `NEEDS-INPUT`. Do not invent FAQs, reviews,
   ratings, or services. (AIVE rejects fake FAQs and discounts padded services.)
3. **Apply the canonical fix** for each criterion (recipes below), editing the
   real files/templates. Keep brand voice; don't redesign unasked.
4. **Validate.** Every JSON-LD block must be valid schema.org and match the
   visible page (NAP, hours, services identical). Keep one `<h1>` per page.
   Preserve accessibility and existing functionality.
5. **Re-score & report.** If AIVE is available, re-run it (free on cached crawls
   via `reuse_extraction`) and capture the before/after ABI + per-criterion
   delta. Output a **remediation report** and a clean changeset/PR.

## Fix recipes (criterion → action)

| Audit finding | Fix (per the spec) |
|---|---|
| No / partial **schema.org** | Add the business JSON-LD block (LocalBusiness/Organization + address, telephone, areaServed, openingHours, sameAs, aggregateRating) to every page `<head>`. |
| Weak / fake **FAQ coverage** | Add a real FAQ section — genuine questions, substantive answers (no CTAs) — and `FAQPage` JSON-LD. Source Q&A from the owner. |
| Ambiguous **services** / low clarity | One page per real first-party service, each named in an `<h1>/<h2>`, with a JSON-LD `Service`. Remove padded/blog-example "services". |
| Missing **online booking** | Add a deep-linkable scheduler link + `potentialAction` (ReserveAction). (0 → 20 / T3.) |
| Missing **phone/email/address/hours** | `tel:`/`mailto:` links + PostalAddress + OpeningHoursSpecification, mirrored in JSON-LD. |
| Thin / undiverse **trust signals** | Surface real guarantees, certifications/licensing, awards, years-in-business, and reviews (≥4 of 5 buckets) prominently + `aggregateRating`/`sameAs`. |
| Weak **heading structure** | Promote each service/topic into a descriptive H1/H2; one H1 per page. |
| Missing **service areas** | Name cities/regions in copy + `areaServed`; add per-area pages for depth. |
| Low **cross-page corroboration** | State NAP + top services identically across header/footer and dedicated pages. |
| Pricing/case-studies miscredited | Present pricing as pricing and client outcomes as case studies — separate from first-party trust. |

## Guardrails
- **Never fabricate** facts, FAQs, reviews, ratings, certifications, or services.
- **Keep JSON-LD truthful and valid** and consistent with visible content.
- **Don't break** the site: preserve routes, accessibility, performance, and
  brand. Make minimal, reviewable changes.
- **Local vs non-local:** skip geographic criteria for national SaaS/agencies;
  use `Organization`, and prioritize Understanding/Retrieval/Authority.
- **Do not change** the ABI framework or scorer — you change the *website*.

## Output
1. A **changeset/PR**: the edited templates/components + JSON-LD, grouped by
   dimension.
2. A **remediation report** (`agent-visibility-remediation.md`): each fix, the
   criterion it targets, the file changed, and `NEEDS-INPUT` items for the owner.
3. If AIVE ran: **before → after ABI** and per-criterion deltas, confirming the
   flagged gaps are resolved for the right reasons (cleaner machine-readable
   truth, not padding).
