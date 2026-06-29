"""Tests for the public funnel: free teaser, token grants, gated reports.

These exercise the API surface that turns an anonymous visitor into a buyer:
the teaser must never leak the paid breakdown, and the full report must be
reachable only with a valid grant token (or the public sample).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import grants, main, store

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
