"""Agent-actionability detection tests (Goal 03D, Pillar 3).

Tiny in-memory PageDocuments; no crawl, no LLM. Covers the booking false-negative
the criterion used to produce (a live Calendly link scoring 0/20).
"""

import pytest

from backend.app.schema import Link, PageDocument
from backend.app.services.abi_score import score_abi
from backend.app.services.actionability import detect_actionability


def _doc(links=(), json_ld=None):
    d = PageDocument(url="https://x.com/", title="X", markdown="")
    d.links = [Link(text=t, href=h) for t, h in links]
    d.metadata = {"json_ld": json_ld} if json_ld else {}
    return d


def _profile(ctas=(), booking_url=None, phone=None, email=None):
    return {
        "ctas": [{"value": v, "cta_type": t, "confidence": 0.7,
                  "evidence": "", "source_url": "", "confidence_reason": ""}
                 for v, t in ctas],
        "contact_information": {"phone": phone, "email": email, "address": None,
                                "hours": None, "booking_url": booking_url},
    }


# --- THE FLAGSHIP BUG: a real Calendly link must be detected (was 0/20) ---
def test_calendly_link_detected_as_t3():
    docs = [_doc(links=[("View Available Times",
                         "https://calendly.com/proplansolutions")])]
    result = detect_actionability(docs, _profile(ctas=[("Book a call", "book")]))
    assert result["booking"]["tier"] == "T3"
    assert "calendly.com" in result["booking"]["evidence"]


@pytest.mark.parametrize("host", [
    "https://cal.com/acme", "https://meetings.hubspot.com/acme",
    "https://acme.acuityscheduling.com",
])
def test_known_schedulers_are_t3(host):
    result = detect_actionability([_doc(links=[("Book", host)])], _profile())
    assert result["booking"]["tier"] == "T3"


def test_potential_action_schema_is_t3():
    jld = [{"@type": "LocalBusiness",
            "potentialAction": {"@type": "ReserveAction",
                                "target": "https://x.com/book"}}]
    result = detect_actionability([_doc(json_ld=jld)], _profile())
    assert result["booking"]["tier"] == "T3"


def test_booking_url_is_t3():
    result = detect_actionability([_doc()],
                                  _profile(booking_url="https://x.com/book"))
    assert result["booking"]["tier"] == "T3"


def test_contact_form_is_t2():
    docs = [_doc(links=[("Request service", "https://x.com/request-service")])]
    result = detect_actionability(docs, _profile(ctas=[("Get a quote", "contact")]))
    assert result["booking"]["tier"] in ("T2", "T1")


def test_unresolved_book_cta_is_t1_intent():
    result = detect_actionability([_doc()], _profile(ctas=[("Book a call", "book")]))
    assert result["booking"]["tier"] == "T1"


def test_no_action_channel_is_t0():
    result = detect_actionability([_doc()], _profile())
    assert result["booking"]["tier"] == "T0"


def test_generic_path_does_not_false_positive_to_t3():
    docs = [_doc(links=[("Get started", "https://x.com/get-started")])]
    result = detect_actionability(docs, _profile())
    assert result["booking"]["tier"] != "T3"


# --- graduated booking criterion in the scorer ---
@pytest.mark.parametrize("tier,expected", [("T3", 20), ("T2", 12),
                                           ("T1", 6), ("T0", 0)])
def test_booking_criterion_is_graduated(tier, expected):
    p = {
        "schema_version": "2.0", "business_name": "X", "industry": None,
        "services": [], "service_areas": [], "locations": [], "faqs": [],
        "offers": [], "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                                "hours": None, "booking_url": None},
        "source_pages": [],
        "actionability": {"booking": {"tier": tier, "mechanism": "calendly",
                                      "evidence": "https://calendly.com/x"}},
    }
    score = score_abi(p)
    crit = next(c for c in score["dimensions"]["agent_readiness"]["criteria"]
                if c["name"] == "Online booking")
    assert crit["earned"] == expected
    if tier != "T0":
        assert crit["evidence"]


def test_booking_criterion_legacy_fallback_to_booking_url():
    # No actionability block -> fall back to the legacy binary booking_url flag.
    p = {
        "schema_version": "2.0", "business_name": "X", "industry": None,
        "services": [], "service_areas": [], "locations": [], "faqs": [],
        "offers": [], "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                                "hours": None, "booking_url": "https://x.com/book"},
        "source_pages": [],
    }
    score = score_abi(p)
    crit = next(c for c in score["dimensions"]["agent_readiness"]["criteria"]
                if c["name"] == "Online booking")
    assert crit["earned"] == 20
