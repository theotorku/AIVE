"""Tests for the public funnel: free teaser, token grants, gated reports.

These exercise the API surface that turns an anonymous visitor into a buyer:
the teaser must never leak the paid breakdown, and the full report must be
reachable only with a valid grant token (or the public sample).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import billing, grants, jobs, main, ssrf, store

client = TestClient(main.app)


@pytest.fixture()
def grants_dir(monkeypatch):
    """A throwaway grants dir under the repo (sandbox blocks the system temp)."""
    d = Path(__file__).resolve().parent / "_tmp_grants"
    shutil.rmtree(d, ignore_errors=True)
    monkeypatch.setattr(grants, "GRANTS_DIR", d)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _a_scored_domain() -> str:
    sites = store.list_sites()
    if not sites:
        pytest.skip("no scored sites in backend/output")
    return sites[0]["domain"]


def test_teaser_returns_only_teaser_fields():
    domain = _a_scored_domain()
    r = client.get(f"/api/teaser/{domain}")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "domain", "business_name", "overall", "grade",
        "grade_label", "grade_meaning", "top_gap",
    }
    # The paid breakdown must not be exposed to anonymous clients.
    assert "dimensions" not in body
    assert "abi_score" not in body


def test_teaser_unknown_domain_404():
    assert client.get("/api/teaser/not-a-real-domain.invalid").status_code == 404


def test_grant_mint_resolve_roundtrip(grants_dir):
    token = grants.mint("example.com", session_id="cs_test_1")
    assert grants.resolve(token) == "example.com"
    # Idempotent per Stripe session.
    assert grants.mint("example.com", session_id="cs_test_1") == token


def test_resolve_rejects_bad_and_handles_sample(grants_dir):
    assert grants.resolve("deadbeefdeadbeef") is None
    assert grants.resolve("../etc/passwd") is None
    assert grants.resolve("sample", sample_domain="demo.com") == "demo.com"


def test_report_by_token_requires_valid_grant():
    assert client.get("/api/reports/deadbeefdeadbeef").status_code == 404


def test_sample_report_serves_configured_domain(monkeypatch):
    domain = _a_scored_domain()
    monkeypatch.setattr(main, "SAMPLE_DOMAIN", domain)
    r = client.get("/api/reports/sample")
    assert r.status_code == 200
    assert r.json()["domain"] == domain


def test_checkout_unconfigured_returns_503(monkeypatch):
    domain = _a_scored_domain()
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    r = client.post("/api/checkout", json={"domain": domain})
    assert r.status_code == 503


# --- C1: internal /api/sites* must not be public -------------------------------

def test_internal_sites_requires_admin_key_when_configured(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_API_KEY", "s3cret")
    assert client.get("/api/sites").status_code == 401
    assert client.get("/api/sites", headers={"X-Admin-Key": "wrong"}).status_code == 401


def test_internal_sites_accepts_valid_admin_key(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_API_KEY", "s3cret")
    r = client.get("/api/sites", headers={"X-Admin-Key": "s3cret"})
    assert r.status_code == 200
    assert "sites" in r.json()


def test_internal_site_report_admin_key_via_query_param(monkeypatch):
    domain = _a_scored_domain()
    monkeypatch.setattr(main, "ADMIN_API_KEY", "s3cret")
    # <a href> downloads can't set headers, so the key rides as ?admin=.
    assert client.get(f"/api/sites/{domain}").status_code == 401
    assert client.get(f"/api/sites/{domain}?admin=s3cret").status_code == 200


# --- C2: a forged Stripe webhook must never mint a grant -----------------------

def test_webhook_rejects_when_signing_secret_unset(monkeypatch, grants_dir):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    forged = (
        b'{"type":"checkout.session.completed","data":{"object":'
        b'{"id":"cs_forged","payment_status":"paid","metadata":{"domain":"evil.com"}}}}'
    )
    r = client.post("/api/stripe/webhook", content=forged,
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 503
    # No grant was minted for the forged event.
    assert grants.find_by_session("cs_forged") is None


# --- H1: SSRF guard on the public live-audit endpoint --------------------------

def test_ssrf_blocks_non_public_and_non_http():
    for bad in ("http://127.0.0.1", "http://169.254.169.254",
                "http://10.1.2.3", "http://localhost", "ftp://example.com"):
        ok, _ = ssrf.check_url(bad)
        assert ok is False, bad


def test_runs_rejects_ssrf_target(monkeypatch):
    monkeypatch.setattr(main, "ALLOW_PUBLIC_RUNS", True)
    # 169.254.169.254 is the cloud metadata endpoint; must be refused (400),
    # not crawled — and refused before any job is submitted.
    r = client.post("/api/runs", json={"url": "http://169.254.169.254"})
    assert r.status_code == 400


# --- M1: domain slug validation (no path traversal / invalid dirs) -------------

def test_store_rejects_traversal_domain_slugs():
    for bad in ("../etc", "..", "a/b", "foo/../bar", "-leading"):
        assert store.load_site(bad) is None
        assert store.load_teaser(bad) is None
        assert store.has_profile(bad) is False


def test_gated_routes_404_on_bad_slug(monkeypatch):
    # No 500 leaking a ValueError/traceback — an invalid slug is just "not found".
    monkeypatch.setattr(main, "ADMIN_API_KEY", "s3cret")
    assert client.get("/api/sites/..?admin=s3cret").status_code == 404
    assert client.get("/api/teaser/..").status_code == 404


# --- M2: /api/checkout is rate-limited -----------------------------------------

def test_checkout_is_rate_limited(monkeypatch):
    domain = _a_scored_domain()
    monkeypatch.setattr(main.ratelimit, "check", lambda ip: (False, "slow down"))
    r = client.post("/api/checkout", json={"domain": domain})
    assert r.status_code == 429


# --- L1: grant TTL / expiry ----------------------------------------------------

def test_grant_without_ttl_never_expires(grants_dir, monkeypatch):
    monkeypatch.setattr(grants, "GRANT_TTL_DAYS", 0)
    token = grants.mint("example.com", session_id="cs_ttl_none")
    assert grants.resolve(token) == "example.com"


def test_expired_grant_resolves_to_none(grants_dir, monkeypatch):
    monkeypatch.setattr(grants, "GRANT_TTL_DAYS", 7)
    token = grants.mint("example.com", session_id="cs_ttl_set")
    assert grants.resolve(token) == "example.com"
    # Backdate expires_at into the past; the token must stop resolving.
    path = grants._grant_path(token)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "expires_at" in data
    data["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()
    path.write_text(json.dumps(data), encoding="utf-8")
    assert grants.resolve(token) is None


# --- L2: unexpected pipeline errors are genericized ----------------------------

def test_job_unexpected_error_is_generic(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("secret internal path /srv/app/xyz leaked")

    monkeypatch.setattr(jobs, "run_pipeline", boom)
    job = jobs.Job(run_id="t1", url="https://example.com", domain="example.com")
    jobs.manager._run(job)
    assert job.status == "error"
    assert job.error == jobs._GENERIC_ERROR
    assert "secret internal path" not in (job.error or "")
