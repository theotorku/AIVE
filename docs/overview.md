# AI Visibility Audit Overview

## Product

The **AI Visibility Audit** helps businesses understand how readable and
actionable their websites are for AI systems.

The audit is the market-facing product. The **Agent Business Index (ABI)** is
the scoring methodology inside the audit.

The audit answers a practical question:

> If an AI assistant reads this website, can it understand, retrieve,
> recommend, and act on this business with confidence?

## Audit Workflow

1. User submits a website URL.
2. The crawler renders and captures the website.
3. The extraction pipeline builds a structured business profile.
4. The ABI scorer evaluates the profile deterministically.
5. The dashboard displays the score, evidence, recommendations, and report.

## Output

For each website, the audit produces:

- extracted business profile,
- overall ABI score,
- five dimension scores,
- letter grade and label,
- evidence-backed criteria,
- prioritized recommendations,
- downloadable HTML report,
- crawl coverage diagnostics.

## ABI v0.1.1 Scope

ABI v0.1.1 is calibrated for **local service businesses** such as HVAC,
plumbing, electrical, roofing, remodeling, movers, and similar categories.

This scope is intentional. Local-service criteria include service areas,
physical address, business hours, booking, phone contact, FAQs, reviews, and
schema.org LocalBusiness signals.

Future **ABI Profiles** may add industry-specific variants for:

- agencies,
- SaaS,
- professional services,
- multi-location businesses,
- franchises.

Do not dilute v0.1.1 to support every category at once.

## Current Benchmark

The current generated benchmark contains **54 scored profiles**.

Current generated benchmark artifacts:

- `backend/validation/abi_validation_report.md`
- `backend/validation/abi_validation_summary.json`

Treat those generated files as the source of truth for benchmark numbers.
