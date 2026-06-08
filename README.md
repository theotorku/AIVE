# AI Visibility Audit

ProPlan measures how understandable a business is to AI systems, answer
engines, and future autonomous agents.

The MVP product is the **AI Visibility Audit**: a website audit that shows how
well AI systems can understand, retrieve, recommend, and act on a business.

The audit is powered by the **Agent Business Index (ABI)**, a deterministic,
explainable 0-100 score across five dimensions:

- AI Understanding
- AI Retrieval
- AI Recommendation
- Agent Readiness
- Semantic Authority

ABI v0.1.1 is frozen for local service businesses. Scoring dimensions, weights,
grade bands, extraction contracts, and provenance labels are documented in
[abi_spec_v0.1.1.md](abi_spec_v0.1.1.md).

## Current MVP

The audit app can:

- crawl a business website,
- extract a structured semantic profile,
- score the site with ABI,
- show the result in a dashboard,
- explain every score with evidence and recommendations,
- download a self-contained HTML report.

## Quick Start

Backend API:

```powershell
python -m pip install -r backend/requirements.txt
python -m playwright install chromium
$env:OPENAI_API_KEY = "sk-..."
python -m uvicorn backend.api.main:app --port 8000
```

Frontend dashboard:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The dashboard reads real artifacts from `backend/output/`; it does not use mock
data.

## Documentation

- [docs/overview.md](docs/overview.md) — audit product and MVP overview
- [docs/quickstart.md](docs/quickstart.md) — local setup and common commands
- [docs/architecture.md](docs/architecture.md) — crawler, extraction, scoring,
  API, and dashboard architecture
- [docs/abi_interpretation.md](docs/abi_interpretation.md) — how to read ABI
  scores, grades, dimensions, and recommendations
- [docs/validation.md](docs/validation.md) — test, benchmark, and E2E validation
  workflow

## Sales Kit

- [sales/README.md](sales/README.md) — sales positioning and offer map
- [sales/offer.md](sales/offer.md) — productized AI Visibility Audit package
- [sales/landing_page_copy.md](sales/landing_page_copy.md) — one-page website copy
- [sales/outreach.md](sales/outreach.md) — cold email, LinkedIn, and phone scripts
- [sales/demo_script.md](sales/demo_script.md) — discovery and demo call flow
- [sales/objections.md](sales/objections.md) — objection handling
- [sales/qualification.md](sales/qualification.md) — best-fit first customers
- [sales/launch_checklist.md](sales/launch_checklist.md) — first outreach launch plan

## Important Files

| File | Purpose |
|---|---|
| `PRD.md` | Product requirements and long-term vision |
| `ROADMAP.md` | Goal sequence, freeze status, future phases |
| `abi_spec_v0.1.1.md` | Frozen ABI scoring/spec contract |
| `CHANGELOG.md` | Release history |
| `backend/README.md` | Backend-specific implementation notes |
| `single_page_bias_review.md` | Investigation into page-count scoring bias |

## Status

MVP is functional. The current benchmark contains 54 scored profiles with ABI
v0.1.1. Generated benchmark outputs live in `backend/validation/`.

Post-freeze work should focus on UX, reporting, workflow, and explainability.
Do not change frozen ABI scoring behavior without following the benchmark review
policy in [abi_spec_v0.1.1.md](abi_spec_v0.1.1.md).
