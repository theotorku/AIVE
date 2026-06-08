"""Confidence-aware scoring tests (Goal 03D, Pillar 2).

earned = max * evidence * _conf_factor(conf), _conf_factor = min(1, conf/0.7).
Genuinely confident facts (>= 0.7) are unaffected; weak evidence is discounted.
"""

import pytest

from backend.app.services.abi_score import _conf_factor, _eff_count, score_abi


def _profile(**over):
    base = {
        "schema_version": "2.0", "business_name": "X", "industry": "HVAC",
        "services": [], "service_areas": [], "locations": [], "faqs": [],
        "offers": [], "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                                "hours": None, "booking_url": None},
        "source_pages": [],
    }
    base.update(over)
    return base


def _loc(conf):
    return {"value": "Austin, TX", "confidence": conf, "evidence": "...",
            "source_url": "https://x.com/", "confidence_reason": "single mention",
            "city": "Austin", "state": "TX"}


def _crit(score, dim, name):
    return next(c for c in score["dimensions"][dim]["criteria"] if c["name"] == name)


# --- the confidence factor itself ---
def test_conf_factor_saturates_and_discounts():
    assert _conf_factor(0.9) == 1.0
    assert _conf_factor(0.7) == 1.0
    assert _conf_factor(0.15) == pytest.approx(0.214, abs=0.01)
    assert _conf_factor(0.0) == 0.0


def test_eff_count_discounts_low_confidence_items():
    weak = [{"confidence": 0.14, "value": f"svc{i}"} for i in range(10)]
    strong = [{"confidence": 0.9, "value": f"svc{i}"} for i in range(10)]
    assert _eff_count(weak) == pytest.approx(2.0, abs=0.1)    # 10 * 0.2
    assert _eff_count(strong) == pytest.approx(10.0, abs=0.1)


# --- THE FLAGSHIP BUG: Austin, TX @ 0.15 must NOT score 20/20 ---
def test_low_confidence_location_is_not_full_marks():
    score = score_abi(_profile(locations=[_loc(0.15)]))
    earned = _crit(score, "ai_understanding", "Location presence")["earned"]
    assert earned < 8.0           # was 20/20 — the documented #5 defect
    assert 3.5 <= earned <= 5.0   # 20 * _conf_factor(0.15) ~= 4.3


def test_high_confidence_location_earns_full_marks():
    score = score_abi(_profile(locations=[_loc(0.9)]))
    earned = _crit(score, "ai_understanding", "Location presence")["earned"]
    assert earned == 20.0         # confident evidence is NOT penalized


def test_structured_address_string_earns_strong_location_credit():
    p = _profile()
    p["contact_information"]["address"] = "100 Main St, Austin, TX"
    score = score_abi(p)
    earned = _crit(score, "ai_understanding", "Location presence")["earned"]
    assert earned >= 18.0         # a real address string is high-trust


def test_offers_count_is_confidence_weighted():
    offers = [{"value": f"Pkg {i}", "confidence": 0.3, "evidence": "",
               "source_url": "", "confidence_reason": ""} for i in range(4)]
    score = score_abi(_profile(offers=offers))
    earned = _crit(score, "ai_recommendation", "Offers & incentives")["earned"]
    assert earned < 20.0          # 4 * _conf_factor(0.3)=0.43 -> ~1.7/2 -> ~17


# --- regression guard: high-confidence sites are NOT penalized ---
def test_high_confidence_profile_unaffected_by_confidence_weighting():
    def ev(v, conf=0.9):
        return {"value": v, "confidence": conf, "evidence": "...",
                "source_url": "https://x.com/", "confidence_reason": "schema.org"}
    p = _profile(
        business_name="Acme HVAC", industry="HVAC",
        services=[ev(f"S{i}") for i in range(8)],
        trust_signals=[ev(f"T{i}") for i in range(5)],
        ctas=[ev("Book"), ev("Call"), ev("Quote")],
    )
    score = score_abi(p)
    assert _crit(score, "ai_understanding", "Service coverage")["earned"] == 30.0
    assert _crit(score, "ai_recommendation", "Trust signals")["earned"] == 40.0
    assert _crit(score, "agent_readiness", "Calls to action")["earned"] == 15.0
