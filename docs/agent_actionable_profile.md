# Agent-Actionable Business Profile v1.0

`profile.json.agent_profile` is an additive read model for an assistant that
needs to identify a business, explain its claims, and find an action path. It is
generated from the pages already crawled and the merged semantic profile. ABI
v0.1.1 scoring and its frozen extraction contract remain unchanged.

## Shape

| Field | Type | Meaning |
|---|---|---|
| `version` | string | Agent profile version, currently `1.0`. |
| `identity` | object | `business_name` and `industry`, when present, as evidence records. |
| `canonical_services` | evidence record[] | The business's scored canonical services, with aliases and source pages. |
| `service_areas` | evidence record[] | Canonical places served, with aliases and source pages. |
| `availability` | evidence record[] | Published hours and explicit availability claims. `live_slots=false` on every record. |
| `pricing` | evidence record[] | Explicit dollar price statements, promotions, and tiers; includes `amounts`, `currency_symbol`, `currency`, and `qualifiers`. `currency` is null when the symbol alone does not establish it. |
| `booking_endpoints` | evidence record[] | Discovered scheduler, booking or quote page, contact page, declared booking URL, and schema action destinations. Each has `kind`, ABI-compatible `tier`, and `verified=false`. |
| `policies` | evidence record[] | Explicit cancellation, refund, payment, warranty, or estimate statements. |
| `trust_signals` | evidence record[] | Attributable trust facts from the scored profile. |
| `contact_information` | object | Evidence record per nonempty contact field. |
| `live_availability_checked` | boolean | Always false until a future live scheduler integration actually checks slots. |

An evidence record has `value`, `confidence`, `evidence`, and `source_url`.
Existing service and area records may also have `aliases`, `source_pages`, and
`provenance`. A contact or identity value with no retrievable page source has
`source_type="unattributed"`, empty evidence and URL, and zero confidence.
Missing facts are empty lists or absent keys; they are never inferred. A
published claim is not a verified current fact. An endpoint is a discovered
destination, not proof that its form works or accepts an appointment.

## Extraction boundaries

- Services, areas, and trust signals reuse the existing canonical extraction.
- Hours reuse the existing contact field. Additional availability, price, and
  policy claims require an explicit match in visible crawled page text.
- Booking endpoints come from crawled links, a declared booking URL, or
  schema.org `potentialAction`. The full set is retained alongside the older
  strongest-action `actionability.booking` result.
- Price conditions are preserved as source text and extracted qualifier phrases.
  They are not interpreted as complete eligibility rules.
- Source URLs on merged evidence items identify the page that supplied the
  selected quote. `source_pages` retains corroborating pages.

The block does not yet query inventory, verify booking forms, interpret policy
legal effect, or guarantee every policy or qualifier phrase will be recognized.
Future extraction improvements can version this read model without changing
the frozen ABI scoring instrument.
