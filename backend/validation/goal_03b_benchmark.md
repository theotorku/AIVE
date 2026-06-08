# Goal 03B — ABI Benchmark

> **Single source of truth:** the live benchmark is the *generated*
> [abi_validation_report.md](abi_validation_report.md) /
> `abi_validation_summary.json`, produced by `python -m backend.run_abi_validation`
> (deterministic, free to re-run). This note is a human-readable companion and
> must be kept in sync with — never ahead of — that generated artifact. Any
> business/dashboard claim should cite the generated numbers.

Current generated figures (refreshed after Goal 03D calibration hardening and
Goal 03E extraction hygiene; both re-scored for free, no LLM):

## ABI distribution (54 sites scored)

| Metric | Value |
|--------|-------|
| Sites scored | 54 |
| Average ABI | 61.5 |
| Highest ABI | 85.7 |
| Lowest ABI | 0.8 |
| Grade distribution | B: 11, C: 26, D: 10, F: 7 |
| Explainable / Repeatable / Schema-valid | 54 / 54 / 54 (PASS, min 50) |

**Why lower than the earlier 68.2 snapshot:** the drop is the *intended* effect
of calibration, not a regression. 03D removed fake-FAQ inflation and made
location/booking confidence-aware; 03E routed blog-example services, third-party
case studies, and pricing tiers out of the scored lists. Scores are now lower
*for the right reasons* — the framework (dimensions/weights/grade bands) is
unchanged.

### Component averages

| Dimension | Avg | Weight |
|-----------|-----|--------|
| AI Understanding | 80.7 | 25% |
| AI Retrieval | 53.3 | 25% |
| AI Recommendation | 61.9 | 20% |
| Agent Readiness | 48.4 | 15% |
| Semantic Authority | 55.6 | 15% |

## Top 5 highest-scoring

| # | Domain | ABI |
|---|--------|-----|
| 1 | fhfurr.com | 85.7 |
| 2 | mauzy.com | 84.8 |
| 3 | servicechampions.com | 82.2 |
| 4 | snellheatingandair.com | 82.1 |
| 5 | fixmyhome.com | 82.0 |

## Bottom 5 lowest-scoring

| # | Domain | ABI |
|---|--------|-----|
| 1 | reliablehomecomfort.com | 0.8 |
| 2 | johnmooreservices.com | 0.8 |
| 3 | cmcservice.com | 3.8 |
| 4 | goodberlet.com | 12.5 |
| 5 | allproplumbing.com | 34.5 |

## Most common top weakness (per site)

| Criterion | Sites |
|-----------|-------|
| FAQ coverage | 30 |
| Heading structure | 11 |
| Geographic specificity | 4 |
| Location presence | 3 |
| Structured data (schema.org) | 3 |
| Reputation diversity | 2 |

## Dataset construction (historical — extraction expansion, 03B)

| Metric | Value |
|--------|-------|
| Attempted sites | 70 |
| Successful crawls | 52 |
| Model | gpt-4o-mini |
| Estimated extraction API cost | ~$0.098 (incremental) + ~$0.18 hardening re-extraction |

Crawling and ABI scoring add no external cost; calibration (03D) and extraction
hygiene (03E) re-scored the cached corpus for $0. See
[cost/cost_ledger.md](../../cost/cost_ledger.md).
