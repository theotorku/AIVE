"""FastAPI app for the ABI dashboard.

Run from repo root:
    uvicorn backend.api.main:app --reload --port 8000
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from backend.api import billing, grants, jobs, ratelimit, report, store

# Live audits crawl an arbitrary site and call the (paid) LLM. The public funnel
# needs this on, so it defaults to true here and is protected by per-IP rate
# limiting (ratelimit.py) + cached-domain dedupe. Set ALLOW_PUBLIC_RUNS=false to
# turn the live endpoint off entirely. See DEPLOYMENT.md §4.
ALLOW_PUBLIC_RUNS = os.getenv("ALLOW_PUBLIC_RUNS", "true").lower() == "true"

# The domain served read-only behind the public "View sample" report link.
SAMPLE_DOMAIN = os.getenv("SAMPLE_DOMAIN", "proplansolutions.io")

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


@app.get("/api/sites")
def get_sites() -> dict:
    """Catalogue of every scored site (internal browse gallery)."""
    return {"sites": store.list_sites()}


@app.get("/api/benchmark")
def get_benchmark() -> dict:
    bench = store.load_benchmark()
    if bench is None:
        raise HTTPException(404, "benchmark summary not available")
    return bench


@app.get("/api/sites/{domain}")
def get_site(domain: str) -> dict:
    site = store.load_site(domain)
    if site is None:
        raise HTTPException(404, f"no scored profile for {domain}")
    return site


@app.get("/api/sites/{domain}/report", response_class=HTMLResponse)
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
    client_ip = request.client.host if request.client else "unknown"
    allowed, reason = ratelimit.check(client_ip)
    if not allowed:
        raise HTTPException(429, reason or "Rate limit exceeded.")
    job = jobs.manager.submit(req.url.strip())
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
def create_checkout(req: CheckoutRequest) -> dict:
    if store.load_teaser(req.domain) is None:
        raise HTTPException(404, f"no audit for {req.domain}; run it first")
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
