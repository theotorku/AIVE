# Architecture

## System Shape

```text
URL
  -> crawler
  -> cleaner + markdown converter
  -> page classifier
  -> rule extractor
  -> LLM extractor
  -> normalizer
  -> confidence engine
  -> semantic profile merge
  -> provenance / actionability / structured-data signals
  -> ABI evidence
  -> ABI score
  -> FastAPI
  -> React dashboard
```

The LLM is one component in the pipeline, not the engine. Deterministic rules,
confidence scoring, provenance labels, and ABI scoring make the result
repeatable and explainable.

## Backend

### Crawler

Location:

```text
backend/crawler/
backend/app/services/crawler.py
```

Responsibilities:

- render JS pages with Playwright,
- follow same-site links,
- use robots/sitemap signals,
- capture rich `PageDocument` objects,
- record crawl coverage diagnostics.

### Extraction

Location:

```text
backend/app/services/
```

Key stages:

- `rule_extractor.py` extracts deterministic facts such as phone, email,
  address, schema.org, and FAQ pairs.
- `llm_extractor.py` performs per-page structured extraction.
- `normalizer.py` groups service and area aliases.
- `confidence.py` scores extracted facts using structural evidence.
- `semantic_profile.py` merges page-level facts into a site-level profile.

### Provenance Hygiene

Location:

```text
backend/app/services/provenance.py
```

Scored lists are cleaned by provenance:

- first-party services stay in `services`.
- blog examples move to `blog_examples`.
- first-party trust signals stay in `trust_signals`.
- case studies move to `case_studies`.
- testimonials move to `testimonials`.
- real offers stay in `offers`.
- pricing tiers move to `pricing_tiers`.

Separated sibling fields are preserved for transparency and future report UX,
but are not scored by ABI v0.1.1.

### ABI Scoring

Location:

```text
backend/app/services/abi_score.py
backend/app/schema.py
```

ABI scoring is deterministic. It uses the merged profile, not a fresh LLM call.

The frozen contract lives in `schema.py`; the implementation reads those values
so validation can catch drift.

### API

Location:

```text
backend/api/
```

Main endpoints:

- `GET /api/health`
- `GET /api/sites`
- `GET /api/sites/{domain}`
- `GET /api/sites/{domain}/report`
- `GET /api/benchmark`
- `POST /api/runs`
- `GET /api/runs/{run_id}`

The API serves real files from `backend/output/` and `backend/validation/`.

## Frontend

Location:

```text
frontend/
```

Stack:

- React
- Vite
- Chakra UI

The dashboard supports:

- URL submission,
- run progress polling,
- benchmark summary,
- scored site gallery,
- ABI score hero,
- dimension cards,
- evidence panel,
- prioritized recommendations,
- report download.

## Contracts

Frozen ABI contracts:

- `SCHEMA_VERSION`
- profile fields,
- evidence list fields,
- contact fields,
- dimension IDs,
- dimension weights,
- criteria names,
- grade bands,
- provenance labels.

See:

```text
abi_spec_v0.1.1.md
backend/tests/test_abi_freeze.py
```
