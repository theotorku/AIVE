# Goal 03E — Extraction Hygiene: before / after

Cached re-merge + re-score (free, no LLM). Scoring code unchanged; ABI moves only from cleaner inputs.

## Corpus (54 sites)

| Metric | Before | After | Separated into |
|---|---|---|---|
| services (total) | 1001 | 963 | blog_examples 37 |
| trust_signals (total) | 490 | 482 | case_studies 8, testimonials 0 |
| offers (total) | 152 | 129 | pricing_tiers 23 |
| avg ABI | 61.7 | 61.5 | — |

Regression guard: 0 sites lost all services; HVAC benchmark service counts unchanged (no first-party service reclassified as blog_example).

## ProPlan (proplansolutions.io)

| Field | Before | After |
|---|---|---|
| services | 44 | 14 (believable; 29 → blog_examples) |
| trust_signals | 12 | 4 (8 → case_studies) |
| offers | 4 | 1 (3 → pricing_tiers) |
| ABI | 42.0 | 39.0 (down only via cleaner extraction) |