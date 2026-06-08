# The Agent-Visible Website Specification

**Version:** 1.0 · aligned to **ABI v0.1.1** (frozen — see
[abi_spec_v0.1.1.md](../abi_spec_v0.1.1.md))
**Audience:** developers/agencies building (or an agent fixing) a website that AI
systems can understand, retrieve, recommend, and act on.
**Promise:** every requirement below maps to a *specific signal the AIVE AI
Visibility Audit actually measures*. Build to this spec and the ABI score rises —
verifiably, because the scorer is frozen.

---

## 0. What "agent-visible" means

Search-era sites are built for human eyes and ranked by links. Agent-era systems
(ChatGPT, Claude, Gemini, Perplexity, and autonomous agents) **read** a site and
build a machine representation of the business, then decide whether they can
understand it, retrieve it for a query, recommend it, and *act* on it (book,
contact, quote).

A website is **agent-visible** when a machine can, from the markup and copy
alone, answer:

1. **What is this business and what does it do?** (Understanding)
2. **Can I find and lift the right content for a query?** (Retrieval)
3. **Is it credible enough to recommend?** (Recommendation)
4. **Can I take the next action on the user's behalf?** (Agent Readiness)
5. **Is its knowledge complete and corroborated?** (Semantic Authority)

These are the five ABI dimensions (weights 25/25/20/15/15). The rest of this spec
is how to satisfy each — with the exact mechanism AIVE detects.

> **The golden rule: never fabricate.** Agent-visibility is about making *true*
> facts machine-readable, not inventing them. AIVE rejects fake FAQs and
> separates third-party claims from first-party ones (see §8). Padding backfires.

---

## 1. The canonical JSON-LD blueprint

schema.org JSON-LD is the **single highest-impact** signal (Authority: 20 pts for
business schema + 15 for FAQ schema, and it feeds Understanding, Agent Readiness,
and Recommendation). AIVE's extractor reads `name`, `telephone`, `address`,
`areaServed`, `FAQPage`, and `potentialAction` from JSON-LD directly.

Put one `<script type="application/ld+json">` block in every page's `<head>`.
Adapt this template (a local service business; use `Organization` for
non-local):

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HVACBusiness",                /* or LocalBusiness / Plumber / Electrician / ProfessionalService / Organization */
  "@id": "https://acme-hvac.com/#business",
  "name": "Acme Heating & Air",
  "url": "https://acme-hvac.com",
  "telephone": "+1-704-555-0142",
  "email": "service@acme-hvac.com",
  "image": "https://acme-hvac.com/og.jpg",
  "priceRange": "$$",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "120 Main St",
    "addressLocality": "Charlotte",
    "addressRegion": "NC",
    "postalCode": "28202",
    "addressCountry": "US"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 35.2271, "longitude": -80.8431 },
  "areaServed": [
    { "@type": "City", "name": "Charlotte" },
    { "@type": "City", "name": "Concord" },
    { "@type": "City", "name": "Matthews" }
  ],
  "openingHoursSpecification": [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
    "opens": "08:00", "closes": "18:00"
  }],
  "sameAs": [
    "https://www.google.com/maps/place/?q=place_id:...",
    "https://www.facebook.com/acmehvac",
    "https://www.bbb.org/us/nc/charlotte/profile/.../acme-hvac"
  ],
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "312" },
  "makesOffer": [
    { "@type": "Offer", "name": "AC Repair",
      "itemOffered": { "@type": "Service", "name": "AC Repair",
        "description": "Diagnosis and repair of central and ductless air conditioning systems." } }
  ],
  "potentialAction": {
    "@type": "ReserveAction",
    "name": "Book service",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://calendly.com/acme-hvac/service",
      "actionPlatform": ["http://schema.org/DesktopWebPlatform","http://schema.org/MobileWebPlatform"]
    },
    "result": { "@type": "Reservation", "name": "Service appointment" }
  }
}
</script>
```

Add a separate **FAQPage** block on your FAQ page (and optionally home):

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    { "@type": "Question",
      "name": "Do you offer financing on new systems?",
      "acceptedAnswer": { "@type": "Answer",
        "text": "Yes. We offer 0% financing for 12 months on qualifying systems, with approved credit. Most applications are approved the same day." } },
    { "@type": "Question",
      "name": "How long does an AC installation take?",
      "acceptedAnswer": { "@type": "Answer",
        "text": "A typical residential AC installation takes 4 to 8 hours, depending on system size and whether ductwork needs modification." } }
  ]
}
</script>
```

**Validate** every block (Google Rich Results Test / schema.org validator) — a
broken block scores zero. Keep JSON-LD facts identical to the visible page (NAP,
hours, services); agents cross-check.

---

## 2. AI Understanding (25%) — "Can AI tell what you do?"

| Build requirement | Mechanism AIVE detects |
|---|---|
| **Business name** stated in the homepage `<title>`, an `<h1>`, and JSON-LD `name`. | Business identity (15 pts). |
| **Industry/category** stated in plain words in a heading and the meta description ("Charlotte HVAC company"), and via the JSON-LD `@type`. | Industry clarity (15). |
| **Named services** as distinct, plain offerings ("AC Repair", "Furnace Installation") — not marketing phrases. Target ≥ 6 real services. | Service coverage (30, confidence-weighted — see §8). |
| Each service stated **clearly and confidently**: its own page + heading + JSON-LD `Service`. | Service clarity (20 = avg confidence). |
| **Address / service location** present as visible NAP **and** JSON-LD `PostalAddress`, at credible confidence (don't bury one incidental city). | Location presence (20, confidence-gated). |

**Do:** one clean category label; plain service nouns; consistent business name
everywhere. **Don't:** describe services only in prose paragraphs, or use clever
names ("Comfort Solutions") with no plain equivalent.

---

## 3. AI Retrieval (25%) — "Can AI find and lift your content?"

| Build requirement | Mechanism |
|---|---|
| A **real FAQ section**: genuine questions paired with substantive, self-contained answers (≥ ~15 chars, not a CTA). Mark up as `FAQPage`. Target ≥ 5. | FAQ coverage (35) + FAQ answer quality (10). **This is the #1 most common gap.** |
| **Descriptive heading hierarchy**: each service/topic in an `<h1>`/`<h2>` that names it. One `<h1>` per page; logical `<h2>`/`<h3>` nesting. | Heading structure (20 = share of services reinforced by headings). |
| **Service areas named** (cities/regions) in copy + JSON-LD `areaServed`. Target ≥ 4. *(Local businesses; skip for national SaaS.)* | Geographic specificity (20). |
| **Dedicated, high-signal pages** (services, about, contact, areas) — not everything crammed on the homepage. Target ≥ 5 relevant pages. | Content breadth (15; blog pages are discounted). |

**FAQ rules (AIVE enforces these):** a question must read like a real question
(≥ 3 words, ends in `?`, not a sentence fragment); an answer must *explain*, not
sell. `"Prefer to talk first?" → "Book a call."` is **rejected** as a fake FAQ.
Write answers an agent can quote verbatim to a user.

---

## 4. AI Recommendation (20%) — "Will AI recommend you?"

Surface **diverse, first-party** proof. AIVE buckets trust into five kinds —
hit as many as apply:

| Proof bucket | Make machine-readable as… |
|---|---|
| **Guarantee** | "100% satisfaction guarantee", "12-month workmanship warranty" in copy. |
| **Certification / licensing** | "Licensed & insured", "NATE-certified", license #; `sameAs` to the licensing body. |
| **Awards** | "Best of [City] 2024", "Top Rated" with the source. |
| **Experience** | "Family-owned since 1998", "20+ years" — concrete and dated. |
| **Reviews** | `aggregateRating` JSON-LD + `sameAs` to Google/BBB; visible rating + count. |

| Build requirement | Mechanism |
|---|---|
| ≥ 4 trust signals spanning ≥ 4 of the 5 buckets above. | Trust signals (40) + Reputation diversity (30). |
| Real **offers/incentives** (financing, seasonal specials, free estimate) — kept separate from pricing tiers. | Offers & incentives (20). |
| Trust claims placed **prominently** (headings, badges, structured data), not buried once in a footer. | Trust signal strength (10 = avg confidence). |

**Don't** present another company's case-study numbers as your own trust signal
(AIVE separates `case_study`/`testimonial` from first-party `trust_signal`), and
don't file pricing tiers as "offers".

---

## 5. Agent Readiness (15%) — "Can an agent act for the user?"

Rank mechanisms by how directly an agent can operate them
(see [agent_actionability_model.md](../agent_actionability_model.md)):

| Build requirement | Mechanism / tier |
|---|---|
| **Deep-linkable online booking** — a scheduler URL (Calendly, Cal.com, HubSpot Meetings, Acuity, Housecall/Jobber) **and** a JSON-LD `potentialAction` (`ReserveAction`/`ScheduleAction`). | Online booking **T3 = 20/20**. A quote/contact *form* is T2 (12); a bare "Book" CTA with no link is T1 (6). |
| **Clickable phone** as `<a href="tel:+1...">` + JSON-LD `telephone`. | Phone number (20). |
| **Contact email** as `<a href="mailto:...">` + JSON-LD `email`. | Contact email (15). |
| **Postal address** (PostalAddress) and **business hours** (OpeningHoursSpecification). | Address (15) + Hours (15). |
| **Explicit CTAs** with clear intent ("Book online", "Call now", "Get a quote"). Target ≥ 3. | Calls to action (15). |

**The booking fix is the highest-leverage agent action:** a real scheduler link +
`potentialAction` moves Online booking 0 → 20.

---

## 6. Semantic Authority (15%) — "Are you complete and corroborated?"

| Build requirement | Mechanism |
|---|---|
| **schema.org markup present** (business block + FAQPage). | Structured data (35 = 20 business + 15 FAQ). **The single most valuable, most-missed signal.** |
| **Depth**: a dedicated page per service with real detail. Target ≥ 8 documented services. | Service depth (20). |
| **Location depth**: a page (or rich section) per major service area. Target ≥ 5. | Geographic authority (15). |
| **Knowledge depth**: a substantive FAQ/knowledge base. Target ≥ 5. | Knowledge depth (15). |
| **Consistency**: the same key facts (name, phone, address, top services) stated **identically across multiple pages**. | Cross-page corroboration (15). |

NAP and core services repeated consistently (header/footer + dedicated pages)
make facts read as authoritative rather than incidental.

---

## 7. Information architecture (the page model)

A minimal agent-visible IA:

```
/                 home — name, category, top services, NAP, primary CTA, FAQ teaser, JSON-LD business block
/services         services index — every service linked, named in headings
/services/<slug>  one page per service — detail, JSON-LD Service, CTA
/areas (+/areas/<city>)  service areas — named, areaServed, local detail
/about            story, experience, certifications, team (trust + authority)
/contact          NAP, map, hours, form, tel:/mailto:, booking link, JSON-LD
/faq              real Q&A, FAQPage JSON-LD
/reviews          testimonials + aggregateRating + sameAs
```

Every page: one `<h1>`, descriptive `<h2>`s, consistent header/footer NAP, the
business JSON-LD block, and a clear next-step CTA.

---

## 8. Anti-patterns (what AIVE penalizes or rejects)

- **Fake FAQs** — marketing fragments ending in "?" with CTA "answers". *Rejected.*
- **Service padding** — listing blog-example services you don't actually offer.
  AIVE confidence-weights and provenance-tags these; they don't count. List only
  **first-party** services.
- **Third-party claims as your own** — other companies' case-study metrics filed
  as your trust signals. Separated out; won't score.
- **Pricing tiers labeled as offers** — separated; won't score as incentives.
- **Low-confidence facts** — a single incidental mention of a city/service is
  discounted (confidence-aware scoring). State facts clearly and repeat them.
- **Broken or fabricated JSON-LD** — scores zero and erodes agent trust.
- **Keyword stuffing / clever names with no plain equivalent** — ambiguous to a
  machine.

---

## 9. Pre-launch checklist (maps to the 22 ABI criteria)

**Understanding**
- [ ] Business name in title, H1, and JSON-LD `name`
- [ ] Plain industry/category in a heading + meta + `@type`
- [ ] ≥ 6 first-party services named as distinct offerings
- [ ] Each service on its own page with a naming heading
- [ ] Visible NAP + JSON-LD `PostalAddress`

**Retrieval**
- [ ] ≥ 5 real Q&A pairs with substantive answers + `FAQPage`
- [ ] Services reinforced by H1/H2 headings (one H1/page)
- [ ] Service areas named in copy + `areaServed` *(if local)*
- [ ] ≥ 5 dedicated content pages

**Recommendation**
- [ ] ≥ 4 trust signals across ≥ 4 proof buckets
- [ ] `aggregateRating` + `sameAs` to review/licensing profiles
- [ ] Real offers/incentives (separate from pricing)
- [ ] Trust claims placed prominently

**Agent Readiness**
- [ ] Deep-linkable scheduler + `potentialAction` (booking T3)
- [ ] `tel:` phone + `mailto:` email
- [ ] Address + hours (PostalAddress + OpeningHoursSpecification)
- [ ] ≥ 3 explicit CTAs

**Semantic Authority**
- [ ] Business + FAQ JSON-LD present and valid
- [ ] ≥ 8 documented services, ≥ 5 area pages, ≥ 5 FAQ entries
- [ ] NAP + top services repeated identically across pages

---

## 10. Verify with AIVE

Don't guess — measure. Run the site through the AI Visibility Audit before and
after:

```bash
# from repo root — scores a URL end-to-end (crawl → extract → ABI)
python -m backend.run_abi_validation           # benchmark the cached corpus
# or via the dashboard API:  POST /api/runs { "url": "https://yoursite.com" }
```

Re-score after each batch of fixes (free on cached crawls via `reuse_extraction`)
and confirm the targeted criteria moved. **Acceptance: the gaps the audit
flagged are resolved and the ABI grade improves for the right reasons** — cleaner,
more machine-readable truth, not padding.
