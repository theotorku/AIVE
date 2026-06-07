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

## Extraction (Goal 02)

Extract a structured business profile from crawled markdown:

```powershell
# crawl + extract a fresh URL
python -m backend.extract_cli https://example-hvac.com

# extract from an already-crawled domain
python -m backend.extract_cli --domain morrisjenkins.com
```

Writes `backend/output/<domain>/extraction.json` conforming to the stable
schema in `extraction/schema.py`. Extraction uses OpenAI Structured Outputs
(strict `json_schema`, `temperature=0`) and a local validator.

### Extraction validation (Goal 02 acceptance)

```powershell
python -m backend.run_extraction_validation --target 20 --max-pages 6
```

Crawls (if needed) + extracts the sites in `validation/extraction_sites.txt`
until 20 pass, reusing cached `extraction.json` files (`--fresh` to force
re-extraction). Writes `validation/extraction_validation_report.md` and
`validation/extraction_validation_summary.json`. Schema stability is measured
over successfully-crawled sites. Exit code is non-zero unless the target is met
*and* the schema is stable.

## Tests

Offline unit tests (no network/API) for cleaning, markdown, discovery, and the
extraction schema/validator:

```powershell
python -m pytest backend/tests -q
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `crawler/fetch.py` | Playwright (Chromium) page rendering with scroll + settle |
| `crawler/clean.py` | Noise removal + HTML→markdown (trafilatura, bs4 fallback) |
| `crawler/discover.py` | Same-domain internal link discovery + prioritization |
| `crawler/crawl.py` | Orchestration: fetch → discover → clean → export |
| `cli.py` | Single-site crawl entrypoint |
| `run_validation.py` | Goal 01 validation harness |
| `extraction/schema.py` | Stable JSON schema + local validator |
| `extraction/extract.py` | OpenAI Structured-Outputs extraction + token accounting |
| `extraction/engine.py` | crawl markdown → `extraction.json`; reuse/cache |
| `extract_cli.py` | Single-site extraction entrypoint |
| `run_extraction_validation.py` | Goal 02 validation harness |
