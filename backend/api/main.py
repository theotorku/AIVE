"""FastAPI app for the ABI dashboard.

Run from repo root:
    uvicorn backend.api.main:app --reload --port 8000
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.api import jobs, report, store

# Live audits crawl an arbitrary site and call the (paid) LLM, so the endpoint is
# an abuse/cost vector if left open publicly. Off by default; set
# ALLOW_PUBLIC_RUNS=true on a trusted/internal instance to enable. See DEPLOYMENT.md §4.
ALLOW_PUBLIC_RUNS = os.getenv("ALLOW_PUBLIC_RUNS", "false").lower() == "true"

app = FastAPI(title="ABI Dashboard API", version="1.0")

# Dev convenience: the Vite dev server proxies /api, but allow direct CORS too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


class RunRequest(BaseModel):
    url: str


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/sites")
def get_sites() -> dict:
    """Catalogue of every scored site (for the browse gallery)."""
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


@app.post("/api/runs")
def create_run(req: RunRequest) -> dict:
    if not ALLOW_PUBLIC_RUNS:
        raise HTTPException(
            403, "Live audits are disabled on this instance. "
            "Browse the scored sites, or enable ALLOW_PUBLIC_RUNS on a trusted deployment.")
    if not req.url or not req.url.strip():
        raise HTTPException(400, "url is required")
    job = jobs.manager.submit(req.url.strip())
    return job.to_dict()


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    job = jobs.manager.get(run_id)
    if job is None:
        raise HTTPException(404, "unknown run_id")
    return job.to_dict()
