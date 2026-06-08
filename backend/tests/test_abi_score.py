"""Offline unit tests for the ABI scoring engine (Goal 03).

Scoring is deterministic and LLM-free, so these tests fully exercise it: a rich
profile scores high, an empty one scores low, the structure is explainable, and
the same input always yields the same output (repeatability).
"""

import pytest

from backend.app.schema import (
    ABI_DIMENSION_WEIGHTS, SchemaError, validate_abi_score)
from backend.app.services.abi_score import DIMENSION_WEIGHTS, grade_for, score_abi


def _rich_profile() -> dict:
    """A strong profile: identity, deep services, FAQs, trust, contact, schema."""
    def ev(value, conf=0.9, reason="supported by schema.org markup; appears in "
           "page headings; repeated across 3 pages", **extra):
        return {"value": value, "confidence": conf, "evidence": "...",
                "source_url": "https://x.com/", "confidence_reason": reason, **extra}

    return {
        "schema_version": "2.0",
        "business_name": "Acme HVAC",
        "industry": "HVAC",
        "services": [ev(f"Service {i}") for i in range(8)],
        "service_areas": [ev(f"City {i}") for i in range(5)],
        "locations": [ev("Charlotte, NC", city="Charlotte", state="NC")],
        "faqs": [ev(f"Q{i}?", answer="A clear answer.") for i in range(5)],
        "offers": [ev("0% financing"), ev("$50 off")],
        "trust_signals": [ev("Licensed & insured"), ev("Award-winning service"),
                          ev("Family owned since 1985"), ev("5-star Google reviews"),
                          ev("100% satisfaction guarantee")],
        "ctas": [ev("Book online"), ev("Call now"), ev("Get a quote")],
        "contact_information": {"phone": "(704) 555-1212", "email": "a@x.com",
                                "address": "1 Main St", "hours": "M-F 8-5",
                                "booking_url": "https://x.com/book"},
        "source_pages": [{"url": "https://x.com/", "category": "home"},
                         {"url": "https://x.com/services", "category": "services"},
                         {"url": "https://x.com/about", "category": "about"},
                         {"url": "https://x.com/contact", "category": "contact"},
                         {"url": "https://x.com/faq", "category": "faq"}],
    }


def _empty_profile() -> dict:
    return {
        "schema_version": "2.0", "business_name": None, "industry": None,
        "services": [], "service_areas": [], "locations": [], "faqs": [],
        "offers": [], "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                                "hours": None, "booking_url": None},
        "source_pages": [],
    }


def test_weights_sum_to_one():
    assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9


def test_weights_match_prd():
    # PRD ABI Framework: Understanding 25 / Retrieval 25 / Recommendation 20 /
    # Agent Readiness 15 / Semantic Authority 15.
    assert DIMENSION_WEIGHTS is ABI_DIMENSION_WEIGHTS
    assert DIMENSION_WEIGHTS["ai_understanding"] == 0.25
    assert DIMENSION_WEIGHTS["ai_retrieval"] == 0.25
    assert DIMENSION_WEIGHTS["ai_recommendation"] == 0.20
    assert DIMENSION_WEIGHTS["agent_readiness"] == 0.15
    assert DIMENSION_WEIGHTS["semantic_authority"] == 0.15


def test_grade_bands():
    assert grade_for(95)[0] == "A"
    assert grade_for(80)[0] == "B"
    assert grade_for(65)[0] == "C"
    assert grade_for(45)[0] == "D"
    assert grade_for(10)[0] == "F"


def test_rich_profile_scores_high_and_validates():
    score = score_abi(_rich_profile())
    validate_abi_score(score)
    assert score["overall"] >= 85
    assert score["grade"] in ("A", "B")
    # All five dimensions present, each 0-100.
    assert set(score["dimensions"]) == set(DIMENSION_WEIGHTS)
    for dim in score["dimensions"].values():
        assert 0 <= dim["score"] <= 100
        assert dim["criteria"]  # explainable: every dimension has criteria


def test_empty_profile_scores_low_with_recommendations():
    score = score_abi(_empty_profile())
    validate_abi_score(score)
    assert score["overall"] < 25
    assert score["grade"] in ("D", "F")
    # Actionable: an empty profile yields prioritized, impact-ranked fixes.
    recs = score["top_recommendations"]
    assert len(recs) >= 3
    impacts = [r["impact"] for r in recs]
    assert impacts == sorted(impacts, reverse=True)
    assert all(r["recommendation"] for r in recs)
    assert recs[0]["priority"] == 1


def test_every_criterion_is_explainable():
    score = score_abi(_rich_profile())
    for dim in score["dimensions"].values():
        for c in dim["criteria"]:
            assert c["name"] and c["rationale"]
            assert c["max"] > 0
            assert 0 <= c["earned"] <= c["max"]
            # A maxed criterion carries no recommendation; a gap carries one.
            if c["ratio"] >= 1.0:
                assert c["recommendation"] is None


def test_repeatable_identical_output():
    p = _rich_profile()
    assert score_abi(p) == score_abi(p)


def test_scorer_ignores_provenance_sibling_fields():
    # Goal 03E adds non-scored sibling fields; the scorer must ignore them, so a
    # profile with them scores identically to one without (scoring unchanged).
    p = _rich_profile()
    base = score_abi(p)
    p2 = dict(p, blog_examples=[{"value": "x", "confidence": 0.1}],
              case_studies=[{"value": "y", "confidence": 0.1}],
              testimonials=[{"value": "z", "confidence": 0.1}],
              pricing_tiers=[{"value": "w", "confidence": 0.1}])
    assert score_abi(p2) == base


def test_overall_is_weighted_average_of_dimensions():
    score = score_abi(_rich_profile())
    expected = round(sum(d["score"] * d["weight"]
                         for d in score["dimensions"].values()), 1)
    assert abs(score["overall"] - expected) < 0.05


def test_missing_faq_is_high_impact_recommendation():
    p = _rich_profile()
    p["faqs"] = []
    score = score_abi(p)
    rec_criteria = [r["criterion"] for r in score["top_recommendations"]]
    assert "FAQ coverage" in rec_criteria


def test_structured_data_uses_profile_level_signal():
    # No schema.org in any fact's confidence_reason, but a profile-level
    # structured_data signal should still earn the authority criterion.
    p = _empty_profile()
    p["business_name"] = "Acme"
    p["structured_data"] = {"schema_org_detected": True, "has_business": True,
                            "has_faq_schema": True}
    score = score_abi(p)
    crit = next(c for c in score["dimensions"]["semantic_authority"]["criteria"]
                if c["name"] == "Structured data (schema.org)")
    assert crit["earned"] == 35  # business (20) + FAQ (15)


def test_structured_data_graduated_partial_credit():
    p = _empty_profile()
    p["structured_data"] = {"schema_org_detected": True, "has_business": True,
                            "has_faq_schema": False}
    score = score_abi(p)
    crit = next(c for c in score["dimensions"]["semantic_authority"]["criteria"]
                if c["name"] == "Structured data (schema.org)")
    assert crit["earned"] == 20  # business only
    assert "FAQPage" in (crit["recommendation"] or "")


# ---- validator strictness --------------------------------------------------

def test_validator_rejects_wrong_grade():
    score = score_abi(_rich_profile())  # a high-scoring profile
    score["grade"] = "F"  # never correct for a high overall
    with pytest.raises(SchemaError):
        validate_abi_score(score)


def test_validator_rejects_tampered_weight():
    score = score_abi(_rich_profile())
    score["dimensions"]["ai_retrieval"]["weight"] = 0.50
    with pytest.raises(SchemaError):
        validate_abi_score(score)


def test_validator_rejects_inconsistent_overall():
    score = score_abi(_rich_profile())
    score["overall"] = min(100.0, score["overall"] + 10)
    with pytest.raises(SchemaError):
        validate_abi_score(score)


def test_validator_rejects_out_of_bounds_criterion():
    score = score_abi(_rich_profile())
    score["dimensions"]["ai_understanding"]["criteria"][0]["earned"] = 999
    with pytest.raises(SchemaError):
        validate_abi_score(score)
