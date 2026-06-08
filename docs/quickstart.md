# Quickstart

## Prerequisites

- Python 3.13 or compatible Python 3.x
- Node.js / npm
- Chromium installed through Playwright
- `OPENAI_API_KEY` for live extraction runs

## Install Backend

From the repo root:

```powershell
python -m pip install -r backend/requirements.txt
python -m playwright install chromium
```

Set your OpenAI key:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

## Install Frontend

```powershell
cd frontend
npm install
```

## Run The App

Terminal 1:

```powershell
python -m uvicorn backend.api.main:app --port 8000
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

## Common Backend Commands

Run offline tests:

```powershell
python -m pytest backend/tests -q
```

Run ABI validation against cached profiles:

```powershell
python -m backend.run_abi_validation --min 50
```

Run extraction validation:

```powershell
python -m backend.run_extraction_validation --target 20 --max-pages 6
```

Run one website through the pipeline:

```powershell
python -m backend.extract_cli https://example-hvac.com
```

## Cache Modes

The pipeline has three reuse modes:

| Mode | What it reuses | Cost |
|---|---|---|
| `reuse_profile` | final profile; recomputes ABI | free |
| `reuse_extraction` | crawl + LLM outputs; reruns merge and ABI | free |
| `reuse_crawl` | rendered crawl; reruns LLM extraction | OpenAI cost |

Use `reuse_extraction` when testing merge-stage logic such as provenance,
FAQ filtering, or actionability detection.

## Artifacts

Per-site artifacts are written under:

```text
backend/output/<domain>/
```

Important files:

- `page_documents.json`
- `extractions.json`
- `profile.json`
- `pipeline.json`
- `confidence.json`
- `abi_score.json`
- `crawl_coverage.json`
