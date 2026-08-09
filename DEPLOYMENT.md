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

1. Landing page loads; "Field data" shows benchmark numbers (`GET /api/benchmark`
   is public).
2. *(Public funnel)* submit a URL → job progresses
   queued→crawling→extracting→scoring→done → the free **teaser**
   (`GET /api/teaser/<domain>`: grade + #1 gap) appears.
3. *(Internal, admin-gated)* the gallery and full report require `ADMIN_API_KEY`:
   `GET /api/sites` and `GET /api/sites/<domain>/report` return `401` without the
   key and `200` with `X-Admin-Key: <key>` (or `?admin=<key>` for the download).
   Open the dashboard at `https://<your-vercel-domain>/?admin=<key>`.
4. *(Paid path)* a buyer report link `…/?report=<token>` resolves via
   `GET /api/reports/<token>`; `…/?report=sample` serves the configured
   `SAMPLE_DOMAIN`.

The repo's `e2e_test.py` pattern (pipeline + API checks) can be pointed at the
prod base URL for an automated check.

---

## 4. Production hardening (do before any public link)

**🔴 `POST /api/runs` triggers a live crawl + paid LLM call.** The public funnel
(landing → free teaser) needs it on, so `ALLOW_PUBLIC_RUNS` now **defaults to
true** and the endpoint is protected by built-in safeguards:

- **Per-IP + global rate limiting** (`backend/api/ratelimit.py`): defaults 3/hour
  and 10/day per IP, 300/day global. Tune via `RUNS_PER_IP_HOUR` /
  `RUNS_PER_IP_DAY` / `RUNS_GLOBAL_DAY`. (In-memory/per-process — fine for one
  Railway instance; move to Redis/Supabase if you scale out.)
- **Cached-domain reuse** (`jobs.py` `reuse_crawl=True`): a re-audit of a known
  domain skips the browser crawl, cutting cost to the LLM step only.

Defence in depth (recommended on top): **Vercel Firewall / WAF** rate rules on
`/api/runs`, a spend limit on the OpenAI key, and `ALLOW_PUBLIC_RUNS=false` if you
ever want to take the live funnel offline and serve only cached audits. The
recommended launch posture and the three cost controls are detailed in
**§4a Cost controls** below.

**💳 Payments.** Checkout is gated on `STRIPE_SECRET_KEY`; without it,
`POST /api/checkout` returns a clean 503 and the rest of the API runs normally.
For production set the Stripe keys, `PUBLIC_BASE_URL`, and a webhook to
`POST /api/stripe/webhook` for `checkout.session.completed`. **`STRIPE_WEBHOOK_SECRET`
is required for the webhook** — the signature is always verified and there is no
unverified fallback, so a forged event can never mint a report grant (a 503 is
returned until the secret is set). The verify-on-redirect path
(`GET /api/checkout/{session_id}`) remains the primary grant path. Buyer report
links (`?report=<token>`) are minted on payment and stored under
`backend/output/_grants/` — keep that on the Railway volume so links survive redeploys.

**🔒 Internal dashboard.** The operator-only endpoints (`/api/sites`,
`/api/sites/{domain}`, `/api/sites/{domain}/report`) expose the full paid
breakdown and are **not public**. Set **`ADMIN_API_KEY`** in prod: these routes
then require it via an `X-Admin-Key` header (or `?admin=` for the report download
link), which the `?admin=<key>` dashboard URL forwards. With `ADMIN_API_KEY`
unset the routes are reachable only from loopback (local dev) and return 403 to
remote callers, so a deployed instance is closed by default. The anonymous funnel
(teaser, runs, checkout, token-gated `/api/reports/{token}`) is unaffected.

**🌐 Rate-limit accuracy behind a proxy.** With the Vercel→Railway topology the
backend sees the proxy IP, which collapses the per-IP run caps. Set
**`TRUST_PROXY=true`** so the limiter reads the client IP from `X-Forwarded-For`
(only enable behind a trusted edge — the header is spoofable otherwise).

**Other hardening:**
- **CORS:** with the Vercel rewrite you don't need it (same-origin). If you ever
  call Railway directly from the browser, set `allow_origins` from an env var
  (the prod domain), not `*`.
- **Cost controls:** cap concurrent jobs (`JobManager(max_workers=...)`) and see
  **§4a** for the OpenAI budget alert, Vercel WAF rules, and daily audit caps.
- **Secrets:** `OPENAI_API_KEY` only in Railway env (never in the repo / frontend
  bundle). The frontend needs no secrets.
- **Persistence:** Railway volume for `backend/output/`; longer term, move
  artifacts to object storage / Supabase (PRD direction) for durability + scale.
- **Observability:** Railway logs; add a `/api/health` uptime check; the pipeline
  already records per-run cost/tokens in `pipeline.json`.

### 4a. Cost controls (launch posture)

The live funnel spends real money (crawl + per-page LLM). Use **three
independent controls** — an OpenAI alert, the app-level throttle, and a Vercel
WAF rule. Recommended launch posture, tightened later as you observe real
conversion and per-audit cost:

> **2 audits/IP/hour, 5/IP/day, 25 globally/day, a $25/month OpenAI budget alert.**

**1) OpenAI project budget (monitoring, not a hard cap).** Create a dedicated
OpenAI **project + API key** for AIVE so its spend is isolated, and put that key
in `OPENAI_API_KEY` on Railway. Set a monthly budget of ~**$25** with alerts at
**50%** (informational), **75%** (investigate traffic), **90%** (consider
`ALLOW_PUBLIC_RUNS=false`), and **100%** (emergency). ⚠️ OpenAI project budgets
are currently **soft thresholds** — requests keep succeeding after the budget is
exceeded, so treat this as monitoring only, never a dependable spend cap.
See: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform

**2) Application throttle (in `ratelimit.py`).** The public run + checkout
endpoints share a per-IP + global daily cap. Defaults are now the conservative
launch numbers above (`RUNS_PER_IP_HOUR=2`, `RUNS_PER_IP_DAY=5`,
`RUNS_GLOBAL_DAY=25`). This is **best-effort**: it is in-memory and per-process,
so counts reset on every deploy/restart and it counts *requests*, not *dollars*.
`ALLOW_PUBLIC_RUNS=false` is the operator kill switch.

**3) Vercel WAF rules.** Protect the two expensive endpoints at the edge. Roll
each out in **Log** mode first, inspect legitimate traffic, then switch to
rate-limit/deny (Vercel recommends testing rules with logging before blocking).
See: https://vercel.com/docs/vercel-firewall/vercel-waf/custom-rules and
https://vercel.com/docs/vercel-firewall/vercel-waf/rule-configuration

    Rule — Protect live audits
      IF   Request Path equals /api/runs  AND  Method equals POST
      THEN Rate limit by IP · fixed window 2 requests / hour · 429 · persist 1 hour

    Rule — Protect checkout
      IF   Request Path equals /api/checkout  AND  Method equals POST
      THEN Rate limit by IP · fixed window 5 requests / 10 minutes · 429

A separate checkout rule keeps checkout abuse from consuming the live-audit
budget (the app-level limiter currently shares one counter across both).

**⚠️ WAF bypass caveat.** A client can skip the Vercel WAF entirely by hitting
the **public Railway URL directly**. So treat any WAF/edge rule as a first layer
only. To close this, route all traffic through a Vercel **server-side function**
that injects a secret header (e.g. `X-Edge-Secret`) and have Railway require that
secret on the expensive endpoints; rotate it periodically and never expose it to
browser JavaScript. **(Deferred — not yet enforced in code.)**

**Deferred hard cap.** A true dollar-denominated hard stop
(reserve estimated cost on accept → reconcile against actual tokens on finish →
`429/503` once a $2/day or $25/month ceiling is hit) needs **persistent storage
with atomic reservation** (Redis/Supabase/Postgres). The current file-based,
single-instance architecture doesn't provide that, so this is intentionally left
as a follow-up for when real traffic justifies it. Size the per-audit ceiling
conservatively from *max pages × input chars × output tokens × retries × current
model price* — do **not** rely on the ~$0.004/site average alone
(`gpt-4o-mini` at $0.15/$0.60 per 1M input/output tokens).

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
| Railway (backend) | `OPENAI_API_KEY` | ✅ | Per-page extraction model. Use a **dedicated OpenAI project + key** with a ~$25/mo budget alert (see §4a) |
| Railway | `ALLOW_PUBLIC_RUNS` | ⚪ | Live-audit endpoint; **default on** (the public funnel needs it). Set `false` to disable (operator kill switch). |
| Railway | `RUNS_PER_IP_HOUR` / `RUNS_PER_IP_DAY` / `RUNS_GLOBAL_DAY` | ⚪ | Per-IP + global run caps (launch defaults **2 / 5 / 25**; see §4a) |
| Railway | `ADMIN_API_KEY` | 🔴 (prod) | Required to reach the internal `/api/sites*` routes remotely; unset ⇒ loopback-only. Sent as `X-Admin-Key` / `?admin=` |
| Railway | `TRUST_PROXY` | ⚪ | `true` behind Vercel/Railway so rate limiting reads the client IP from `X-Forwarded-For` (default `false`) |
| Railway | `STRIPE_SECRET_KEY` | ⚪ | Enables `$399` Pilot checkout; if unset, checkout returns 503 |
| Railway | `STRIPE_WEBHOOK_SECRET` | 🔴 (if webhook used) | Verifies the `checkout.session.completed` webhook; **required** — no unverified fallback, so the webhook returns 503 until it is set |
| Railway | `STRIPE_PRICE_ID` / `PILOT_PRICE_CENTS` | ⚪ | Use a Stripe Price, or set the inline amount (default `39900`) |
| Railway | `PUBLIC_BASE_URL` | ⚪ | Site origin for Stripe success/cancel redirects |
| Railway | `SAMPLE_DOMAIN` | ⚪ | Domain served behind the public `?report=sample` link (default `proplansolutions.io`) |
| Railway | `GRANT_TTL_DAYS` | ⚪ | Days a paid report link stays valid; `0` = never expires (default). Existing links keep working when changed |
| Railway | `CORS_ORIGINS` | ⚪ | Comma-separated allowed origins (default localhost dev) |
| Railway | `PORT` | (auto) | Injected by Railway |

---

## 7. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `/api/health` 404 on Vercel | `vercel.json` rewrite missing or wrong Railway URL. |
| Crawl jobs fail with browser errors | Not using the Playwright base image, or Chromium not installed — use the Dockerfile in §1. |
| Audits vanish after redeploy | No Railway volume on `/app/backend/output` (§1.3). |
| `429`/quota errors mid-audit | OpenAI rate/limit; lower concurrency, add retries/backoff. |
| Anyone can rack up cost | Apply the §4a cost controls (OpenAI budget alert, lower run caps, Vercel WAF). |
| Dashboard empty in prod | No artifacts seeded; run a few audits or copy cached `output/`. |
```
