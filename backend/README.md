# Backend — Crawler + Extraction (Goals 01–02)

Website crawling, markdown conversion, and semantic extraction for the ProPlan
ABI MVP.

- **Goal 01 — Crawler:** crawl a URL, render JS pages, strip nav/footer noise,
  export clean markdown.
- **Goal 02 — Extraction:** LLM-based extraction of a stable business profile
  (services, locations, FAQs, contact info, offers) from the crawled markdown.

## Setup

```powershell
cd backend
python -m pip install -r requirements.txt
python -m playwright install chromium
# Goal 02 needs an OpenAI key:
$env:OPENAI_API_KEY = "sk-..."
```

## Usage

Crawl a single site (run from the repo root so `backend` is importable):

```powershell
python -m backend.cli https://example-hvac.com --max-pages 6
```

Output goes to `backend/output/<domain>/`:
- one `<page>.md` per crawled page (clean markdown),
- `_site.md` — all pages combined,
- `_crawl.json` — per-page status/metrics.

## Validation (Goal 01 acceptance)

```powershell
python -m backend.run_validation --target 10 --max-pages 6
```

Crawls the HVAC sites in `validation/hvac_sites.txt` until 10 pass, then
writes `validation/validation_report.md` and `validation/validation_summary.json`.
A site passes if at least one page renders cleanly and total readable markdown
clears the threshold. Exit code is non-zero if the target is not met.

## Extraction pipeline (Goal 02)

A staged pipeline — the LLM is one component, not the engine:

```txt
crawl -> clean -> markdown -> classify -> rule extract -> llm extract
      -> normalize -> confidence -> merge profile -> ABI evidence
```

Run the full pipeline for one site:

```powershell
# crawl + extract a fresh URL
python -m backend.extract_cli https://example-hvac.com

# reuse a cached rich crawl for a domain
python -m backend.extract_cli --domain morrisjenkins.com
```

Artifacts under `backend/output/<domain>/`:
- `page_documents.json` — rich per-page crawl (title, headings, links, metadata,
  JSON-LD, markdown); cached so re-runs skip the browser,
- `profile.json` — merged business profile (every fact carries `confidence`,
  `evidence`, `source_url`) plus an `abi_evidence` block,
- `pipeline.json` — run metadata (tokens, page categories, per-page errors).

Rules extract facts → the LLM interprets meaning per page → the normalizer
resolves duplicates → the confidence engine scores reliability from structural
signals (headings/nav/schema.org/repetition) → the ABI layer emits evidence.

### Validation (Goal 02 acceptance)

```powershell
python -m backend.run_extraction_validation --target 20 --max-pages 6
# re-run instantly using cached profiles:
python -m backend.run_extraction_validation --reuse-profile
```

Runs the pipeline over `validation/extraction_sites.txt` until 20 pass. Writes
`validation/extraction_validation_report.md` + `..._summary.json`. Schema
stability is checked against the profile contract over successfully-crawled
sites; exit code is non-zero unless the target is met *and* the schema is stable.

## Tests

Offline unit tests (no network/API) — crawl cleaning/markdown/discovery, and
the pipeline's deterministic stages (classification, rules, normalization,
confidence, profile merge):

```powershell
python -m pytest backend/tests -q
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `crawler/` | Goal 01 crawl layer: Playwright fetch, noise removal, markdown, discovery |
| `cli.py` / `run_validation.py` | Goal 01 crawl entrypoint + validation harness |
| `app/schema.py` | Data shapes, per-page LLM JSON schema, profile contract + validator |
| `app/services/crawler.py` | Rich crawl → `PageDocument` (reuses Goal 01 fetch) |
| `app/services/cleaner.py` | Noise removal + structural parsing (headings/links/JSON-LD) |
| `app/services/markdown_converter.py` | HTML → markdown wrapper |
| `app/services/page_classifier.py` | Classify pages (home/services/faq/...) |
| `app/services/rule_extractor.py` | Deterministic facts (phone/email/address/schema.org/FAQ) |
| `app/services/llm_extractor.py` | Per-page LLM extraction with evidence + confidence |
| `app/services/normalizer.py` | Canonical services/areas + aliases |
| `app/services/confidence.py` | Multi-signal confidence scoring with reasons |
| `app/services/semantic_profile.py` | Merge page results → site profile (conflict-aware) |
| `app/services/abi_evidence.py` | ABI evidence across the 5 PRD dimensions |
| `app/pipeline.py` | Orchestrates all stages; crawl/profile caching |
| `extract_cli.py` / `run_extraction_validation.py` | Goal 02 entrypoint + validation harness |
