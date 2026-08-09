"""FastAPI app for the ABI dashboard.

Run from repo root:
    uvicorn backend.api.main:app --reload --port 8000
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from backend.api import billing, grants, jobs, ratelimit, report, ssrf, store

# Live audits crawl an arbitrary site and call the (paid) LLM. The public funnel
# needs this on, so it defaults to true here and is protected by per-IP rate
# limiting (ratelimit.py) + cached-domain dedupe. Set ALLOW_PUBLIC_RUNS=false to
# turn the live endpoint off entirely. See DEPLOYMENT.md §4.
ALLOW_PUBLIC_RUNS = os.getenv("ALLOW_PUBLIC_RUNS", "true").lower() == "true"

# The domain served read-only behind the public "View sample" report link.
SAMPLE_DOMAIN = os.getenv("SAMPLE_DOMAIN", "proplansolutions.io")

# Internal (operator-only) endpoints — the all-sites gallery and per-domain full
# report — are the paid deliverable and must not be public. When ADMIN_API_KEY is
# set it is required (via X-Admin-Key header or ?admin= query param). When it is
# unset the internal endpoints are usable only from loopback (local dev); remote
# callers get 403 so a deployed instance is secure by default. The public funnel
# (teaser, runs, checkout, token-gated /api/reports/{token}) is never gated here.
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# Set true only when a trusted proxy (Vercel/Railway) fronts the API, so we can
# read the real client IP from X-Forwarded-For for rate limiting. Left false by
# default because X-Forwarded-For is client-spoofable without a trusted edge.
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"

_LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def _client_ip(request: Request) -> str:
    if TRUST_PROXY:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_admin(request: Request) -> None:
    """Guard internal endpoints. See ADMIN_API_KEY note above."""
    provided = request.headers.get("x-admin-key") or request.query_params.get("admin")
    if ADMIN_API_KEY:
        if provided != ADMIN_API_KEY:
            raise HTTPException(401, "Admin authentication required.")
        return
    host = request.client.host if request.client else ""
    if host not in _LOCAL_HOSTS:
        raise HTTPException(403, "Internal API is disabled. Set ADMIN_API_KEY.")

app = FastAPI(title="ABI Dashboard API", version="1.0")

# Dev convenience: the Vite dev server proxies /api, but allow direct CORS too.
_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
    allow_methods=["*"], allow_headers=["*"],
)


class RunRequest(BaseModel):
    url: str


class CheckoutRequest(BaseModel):
    domain: str


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "billing": billing.is_configured()}


@app.get("/api/sites", dependencies=[Depends(require_admin)])
def get_sites() -> dict:
    """Catalogue of every scored site (internal browse gallery)."""
    return {"sites": store.list_sites()}


@app.get("/api/benchmark")
def get_benchmark() -> dict:
    bench = store.load_benchmark()
    if bench is None:
        raise HTTPException(404, "benchmark summary not available")
    return bench


@app.get("/api/sites/{domain}", dependencies=[Depends(require_admin)])
def get_site(domain: str) -> dict:
    site = store.load_site(domain)
    if site is None:
        raise HTTPException(404, f"no scored profile for {domain}")
    return site


@app.get("/api/sites/{domain}/report", response_class=HTMLResponse,
         dependencies=[Depends(require_admin)])
def get_report(domain: str):
    site = store.load_site(domain)
    if site is None:
        raise HTTPException(404, f"no scored profile for {domain}")
    html_doc = report.render_report(site)
    return HTMLResponse(content=html_doc, headers={
        "Content-Disposition": f'attachment; filename="abi-report-{domain}.html"',
    })


# ---------------------------------------------------------------------------
# Public funnel: free teaser
# ---------------------------------------------------------------------------

@app.get("/api/teaser/{domain}")
def get_teaser(domain: str) -> dict:
    """Free teaser: grade + #1 gap only (sales/strategy.md §5, rung 0)."""
    teaser = store.load_teaser(domain)
    if teaser is None:
        raise HTTPException(404, f"no scored profile for {domain}")
    return teaser


@app.post("/api/runs")
def create_run(req: RunRequest, request: Request) -> dict:
    if not ALLOW_PUBLIC_RUNS:
        raise HTTPException(
            403, "Live audits are disabled on this instance.")
    if not req.url or not req.url.strip():
        raise HTTPException(400, "url is required")
    # SSRF guard first, so a blocked internal URL never consumes rate budget.
    norm = jobs._normalize_url(req.url.strip())
    ok, reason = ssrf.check_url(norm)
    if not ok:
        raise HTTPException(400, reason or "That URL cannot be audited.")
    allowed, rl_reason = ratelimit.check(_client_ip(request))
    if not allowed:
        raise HTTPException(429, rl_reason or "Rate limit exceeded.")
    job = jobs.manager.submit(norm)
    return job.to_dict()


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    job = jobs.manager.get(run_id)
    if job is None:
        raise HTTPException(404, "unknown run_id")
    return job.to_dict()


# ---------------------------------------------------------------------------
# Paid conversion: Stripe checkout -> report grant
# ---------------------------------------------------------------------------

@app.post("/api/checkout")
def create_checkout(req: CheckoutRequest, request: Request) -> dict:
    if store.load_teaser(req.domain) is None:
        raise HTTPException(404, f"no audit for {req.domain}; run it first")
    # Creating Stripe sessions is a (small) cost + spam vector, so it shares the
    # same per-IP budget as live runs.
    allowed, rl_reason = ratelimit.check(_client_ip(request))
    if not allowed:
        raise HTTPException(429, rl_reason or "Rate limit exceeded.")
    try:
        url = billing.create_checkout(req.domain)
    except RuntimeError:
        raise HTTPException(503, "Payments are not configured on this instance.")
    return {"url": url}


@app.get("/api/checkout/{session_id}")
def verify_checkout(session_id: str) -> dict:
    """After Stripe redirect: verify payment and return the report grant."""
    try:
        result = billing.grant_for_session(session_id)
    except RuntimeError:
        raise HTTPException(503, "Payments are not configured on this instance.")
    if result is None:
        raise HTTPException(402, "Payment not completed.")
    token, domain = result
    return {"token": token, "domain": domain}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        billing.handle_webhook(payload, sig)
    except RuntimeError:
        raise HTTPException(503, "Payments are not configured on this instance.")
    except Exception as exc:  # noqa: BLE001 — signature/parse failures
        raise HTTPException(400, f"webhook error: {exc}")
    return JSONResponse({"received": True})


# ---------------------------------------------------------------------------
# Token-gated full report (paying customers + the public sample)
# ---------------------------------------------------------------------------

@app.get("/api/reports/{token}")
def get_report_by_token(token: str) -> dict:
    domain = grants.resolve(token, sample_domain=SAMPLE_DOMAIN)
    if domain is None:
        raise HTTPException(404, "invalid or expired report link")
    site = store.load_site(domain)
    if site is None:
        raise HTTPException(404, "report not available")
    return site


@app.get("/api/reports/{token}/report", response_class=HTMLResponse)
def download_report_by_token(token: str):
    domain = grants.resolve(token, sample_domain=SAMPLE_DOMAIN)
    if domain is None:
        raise HTTPException(404, "invalid or expired report link")
    site = store.load_site(domain)
    if site is None:
        raise HTTPException(404, "report not available")
    html_doc = report.render_report(site)
    return HTMLResponse(content=html_doc, headers={
        "Content-Disposition": f'attachment; filename="abi-report-{domain}.html"',
    })
