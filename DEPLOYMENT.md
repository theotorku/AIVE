# AIVE — Deployment Guide

How to take the **AI Visibility Audit** (FastAPI backend + crawler + React
dashboard/landing) from local to production.

**Recommended topology (matches the stack in CLAUDE.md):**

```
  Browser ──HTTPS──▶  Vercel (static React: landing + dashboard)
                         │  /api/*  rewrite (server-side proxy, no CORS)
                         ▼
                      Railway (FastAPI + Playwright + OpenAI)   ── OPENAI_API_KEY
                         │
                         ▼
                      output/  (audit artifacts — Railway volume)
```

Why split: the frontend is a static SPA (perfect for Vercel's CDN); the backend
**crawls with Playwright (Chromium) and runs long, in-process audit jobs** — that
needs a real always-on container with a browser, which Railway/Render/Fly provide
and Vercel's serverless functions do not.

---

## 0. Prerequisites

- An `OPENAI_API_KEY` (the per-page extraction model; ~**$0.004/site** + crawl).
- Accounts: [Railway](https://railway.app) (backend) + [Vercel](https://vercel.com) (frontend).
- `git` repo pushed (origin already set: `github.com/theotorku/AIVE`).
- Local: Python 3.11+, Node 18+.

---

## 1. Backend → Railway (FastAPI + Playwright)

The crawler needs Chromium + system deps. The cleanest, most reproducible path is
a **Dockerfile built on Microsoft's Playwright image** (browsers preinstalled and
version-matched to `playwright==1.49.1`).

**Create `Dockerfile` at the repo root:**

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble
WORKDIR /app

# Python deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code (output/ is created at runtime; mount a volume for persistence)
COPY backend ./backend

ENV PYTHONUNBUFFERED=1
# Railway injects $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

**Add `.dockerignore`:**

```
**/__pycache__/
backend/output/
frontend/
.venv/
.git/
```

**Deploy:**

1. Railway → **New Project → Deploy from GitHub repo** → select `AIVE`.
2. It detects the `Dockerfile`. Set **Variables**:
   - `OPENAI_API_KEY` = your key (required).
   - *(optional)* `ALLOW_PUBLIC_RUNS` = `false` — see §4 (recommended for a public demo).
3. **Add a Volume** mounted at `/app/backend/output` so completed audits survive
   redeploys. (Without it, artifacts are ephemeral — re-runnable, but the gallery
   resets on each deploy.)
4. Deploy. Note the public URL, e.g. `https://aive-backend.up.railway.app`.

**Verify:**

```bash
curl https://aive-backend.up.railway.app/api/health      # {"status":"ok"}
curl https://aive-backend.up.railway.app/api/benchmark    # benchmark JSON (if output seeded)
```

> **Seed the benchmark/gallery (optional but recommended):** the 54 cached audits
> live under `backend/output/` (gitignored) and `backend/validation/`. To show a
> populated dashboard on day one, either commit a curated subset, copy them onto
> the volume, or run a few audits in production. The landing page's "Field data"
> falls back to the real benchmark numbers even with an empty backend.

---

## 2. Frontend → Vercel (static SPA + API proxy)

The app fetches **relative `/api/...`** (see `frontend/src/api.ts`) — in dev the
Vite proxy handles it; in prod a **Vercel rewrite** proxies `/api` to Railway
**server-side**, so the browser sees one origin and there is **no CORS** to
configure.

**Create `frontend/vercel.json`:**

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://aive-backend.up.railway.app/api/:path*" }
  ]
}
```

(Replace the destination with your Railway URL.)

**Deploy:**

1. Vercel → **Add New Project → Import** the repo.
2. **Root Directory:** `frontend`. Framework preset: **Vite**.
   Build: `npm run build` · Output: `dist` (defaults are correct).
3. Deploy. You get `https://aive.vercel.app` (or your custom domain).

**Verify the full path:**

```bash
curl https://aive.vercel.app/api/health      # proxied → {"status":"ok"}
```

Open the site: the landing page renders, **"See a real audit"** loads a cached
audit, and **"Run free audit"** submits to the backend.

---

## 3. End-to-end smoke test (prod)

1. Landing page loads; "Field data" shows benchmark numbers.
2. `GET /api/sites` returns the gallery; selecting a site shows grade + 5
   dimensions + evidence + report download.
3. *(If public runs enabled)* submit a URL → job progresses
   queued→crawling→extracting→scoring→done → score appears.
4. Report download (`/api/sites/<domain>/report`) returns the HTML.

The repo's `e2e_test.py` pattern (pipeline + API checks) can be pointed at the
prod base URL for an automated check.

---

## 4. Production hardening (do before any public link)

**🔴 Protect `POST /api/runs` — it triggers a live crawl + paid LLM call.** Left
open, anyone can spend your OpenAI budget and run your crawler against arbitrary
sites. Pick one:

- **Disable public runs for the marketing demo** (recommended first). Gate the
  endpoint on an env flag and serve only cached audits + benchmark publicly; run
  audits internally:
  ```python
  # backend/api/main.py — in create_run()
  import os
  if os.getenv("ALLOW_PUBLIC_RUNS", "false").lower() != "true":
      raise HTTPException(403, "Live audits are not enabled on this instance.")
  ```
- **Shared-secret header** for an internal tool (`X-AIVE-Token` checked against an
  env var).
- **Rate-limit + bot protection** via the **Vercel Firewall / WAF** on `/api/runs`
  (and a per-IP cap) if you keep it public.

**Other hardening:**
- **CORS:** with the Vercel rewrite you don't need it (same-origin). If you ever
  call Railway directly from the browser, set `allow_origins` from an env var
  (the prod domain), not `*`.
- **Cost controls:** cap concurrent jobs (`JobManager(max_workers=...)`), set a
  spend limit on the OpenAI key, and consider a daily audit quota.
- **Secrets:** `OPENAI_API_KEY` only in Railway env (never in the repo / frontend
  bundle). The frontend needs no secrets.
- **Persistence:** Railway volume for `backend/output/`; longer term, move
  artifacts to object storage / Supabase (PRD direction) for durability + scale.
- **Observability:** Railway logs; add a `/api/health` uptime check; the pipeline
  already records per-run cost/tokens in `pipeline.json`.

---

## 5. Run a production build locally (preview before deploy)

```bash
# Backend (Docker, mirrors prod)
docker build -t aive-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... -v "$PWD/backend/output:/app/backend/output" aive-backend

# Frontend (static build + preview)
cd frontend && npm ci && npm run build && npm run preview   # serves dist/ on :4173
```

For the frontend preview to reach the backend, run with the Vite dev proxy
(`npm run dev`, backend on :8000) or set the `vercel.json` destination to
`http://localhost:8000` for a local proxy test.

---

## 6. Environment variable reference

| Service | Variable | Required | Purpose |
|---|---|---|---|
| Railway (backend) | `OPENAI_API_KEY` | ✅ | Per-page extraction model |
| Railway | `ALLOW_PUBLIC_RUNS` | ⚪ | Gate the paid live-audit endpoint (default off) |
| Railway | `PORT` | (auto) | Injected by Railway |
| Vercel (frontend) | *(none)* | — | No secrets; API base is set in `vercel.json` |

---

## 7. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `/api/health` 404 on Vercel | `vercel.json` rewrite missing or wrong Railway URL. |
| Crawl jobs fail with browser errors | Not using the Playwright base image, or Chromium not installed — use the Dockerfile in §1. |
| Audits vanish after redeploy | No Railway volume on `/app/backend/output` (§1.3). |
| `429`/quota errors mid-audit | OpenAI rate/limit; lower concurrency, add retries/backoff. |
| Anyone can rack up cost | `POST /api/runs` is unprotected — apply §4. |
| Dashboard empty in prod | No artifacts seeded; run a few audits or copy cached `output/`. |
```
