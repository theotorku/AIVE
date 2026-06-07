# Backend — Crawler (Goal 01)

Website crawling and markdown conversion for the ProPlan ABI MVP.

Scope (Goal 01 only): crawl a URL, render JS pages, strip navigation/footer
noise, and export clean markdown. No extraction, scoring, or dashboard.

## Setup

```powershell
cd backend
python -m pip install -r requirements.txt
python -m playwright install chromium
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

## Tests

Offline unit tests for cleaning, markdown conversion, and link discovery:

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
| `cli.py` | Single-site command-line entrypoint |
| `run_validation.py` | Goal 01 validation harness over the HVAC site list |
