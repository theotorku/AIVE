"""ABI v0.1.1 freeze guard.

The ABI measurement instrument is frozen at v0.1.1: scoring dimensions, weights,
grade bands, extraction contracts, and the provenance taxonomy do not change
without a benchmark review (see abi_spec_v0.1.1.md). These tests pin the exact
frozen values — if you change one, this test fails on purpose. To make a
deliberate change: run the benchmark review, update abi_spec, bump ABI_VERSION,
then update the expected values here in the same commit.
"""

from backend.app.schema import (
    ABI_DIMENSION_WEIGHTS, ABI_DIMENSIONS, ABI_GRADE_BANDS, ABI_VERSION,
    CONTACT_FIELDS, EVIDENCE_LIST_FIELDS, PROFILE_FIELDS, SCHEMA_VERSION)
from backend.app.services.abi_score import score_abi
from backend.app.services.provenance import PROVENANCE_LABELS


def test_frozen_version():
    assert ABI_VERSION == "0.1.1"


def test_frozen_dimensions():
    assert ABI_DIMENSIONS == [
        "ai_understanding", "ai_retrieval", "ai_recommendation",
        "agent_readiness", "semantic_authority"]


def test_frozen_weights():
    assert ABI_DIMENSION_WEIGHTS == {
        "ai_understanding": 0.25,
        "ai_retrieval": 0.25,
        "ai_recommendation": 0.20,
        "agent_readiness": 0.15,
        "semantic_authority": 0.15,
    }
    assert abs(sum(ABI_DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9


def test_frozen_grade_bands():
    assert ABI_GRADE_BANDS == [
        (90, "A", "AI-Optimized"),
        (75, "B", "AI-Ready"),
        (60, "C", "Partially Visible"),
        (40, "D", "Low Visibility"),
        (0, "F", "Invisible to AI"),
    ]


def test_frozen_extraction_contract():
    assert SCHEMA_VERSION == "2.0"
    assert PROFILE_FIELDS == [
        "schema_version", "business_name", "industry", "services",
        "service_areas", "locations", "faqs", "offers", "trust_signals",
        "ctas", "contact_information", "source_pages"]
    assert EVIDENCE_LIST_FIELDS == [
        "services", "service_areas", "locations", "faqs", "offers",
        "trust_signals", "ctas"]
    assert CONTACT_FIELDS == ["phone", "email", "address", "hours", "booking_url"]


def test_frozen_provenance_taxonomy():
    assert PROVENANCE_LABELS == frozenset({
        "first_party_service", "blog_example", "trust_signal",
        "case_study", "testimonial", "offer", "pricing_tier"})


# Exact per-dimension criterion names — pins the scoring surface so a renamed,
# added, or removed criterion is caught (would silently change reports/weights).
FROZEN_CRITERIA = {
    "ai_understanding": ["Business identity", "Industry clarity",
                         "Service coverage", "Service clarity",
                         "Location presence"],
    "ai_retrieval": ["FAQ coverage", "FAQ answer quality", "Heading structure",
                     "Geographic specificity", "Content breadth"],
    "ai_recommendation": ["Trust signals", "Reputation diversity",
                          "Offers & incentives", "Trust signal strength"],
    "agent_readiness": ["Phone number", "Contact email", "Address",
                        "Business hours", "Online booking", "Calls to action"],
    "semantic_authority": ["Structured data (schema.org)", "Service depth",
                           "Geographic authority", "Knowledge depth (FAQ)",
                           "Cross-page corroboration"],
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


def test_frozen_criteria_names_per_dimension():
    score = score_abi(_empty_profile())
    for dim, expected in FROZEN_CRITERIA.items():
        actual = [c["name"] for c in score["dimensions"][dim]["criteria"]]
        assert actual == expected, f"{dim} criteria changed: {actual}"


def test_frozen_criteria_max_points_sum_to_100_per_dimension():
    score = score_abi(_empty_profile())
    for dim in ABI_DIMENSIONS:
        total = sum(c["max"] for c in score["dimensions"][dim]["criteria"])
        assert abs(total - 100) < 1e-6, f"{dim} max points = {total}, not 100"
