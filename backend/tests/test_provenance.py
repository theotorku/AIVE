"""Provenance classification tests (Goal 03E — Extraction Hygiene).

Deterministic, offline. Conservative bias: ambiguous -> keep first-party.
"""

import pytest

from backend.app.services.provenance import (
    classify_offer, classify_service, classify_trust)


# --- services: blog example vs first-party (conservative) -------------------
def test_blog_only_service_is_blog_example():
    assert classify_service("Returns Processing Automation", "...",
                            {"blog"}) == "blog_example"


def test_service_on_service_page_is_first_party():
    assert classify_service("AI Lead Scoring", "we build", {"home", "blog"}) \
        == "first_party_service"
    assert classify_service("AC Repair", "we repair AC",
                            {"service_detail"}) == "first_party_service"


def test_service_corroborated_on_blog_and_service_stays_first_party():
    # The regression guard: a real service linked from a blog must NOT be stripped.
    assert classify_service("AC Repair", "...",
                            {"blog", "services"}) == "first_party_service"


def test_unknown_only_service_stays_first_party():
    # Unclassified-only (no actual blog page) is ambiguous -> keep first-party.
    assert classify_service("Duct Cleaning", "...", {"unknown"}) \
        == "first_party_service"


def test_service_with_no_categories_stays_first_party():
    assert classify_service("AC Repair", "...", set()) == "first_party_service"


# --- trust: case study / testimonial / first-party --------------------------
@pytest.mark.parametrize("text", [
    "Lead conversion jumped from 19% to 43%",
    "Quote prep time dropped by 72%",
    "Reduced manual work by 60%",
    "Saved the client 15 hours per week",
])
def test_quantified_outcome_is_case_study(text):
    assert classify_trust(text) == "case_study"


@pytest.mark.parametrize("text", [
    "Licensed & insured",
    "Family owned since 1985",
    "100% satisfaction guarantee",       # has 100% but no change-verb -> trust
    "5-star Google reviews",
    "15+ businesses served",             # a count, not an outcome delta
    "HIPAA-compliant systems",
])
def test_first_party_credentials_stay_trust(text):
    assert classify_trust(text) == "trust_signal"


def test_quoted_endorsement_is_testimonial():
    assert classify_trust('"Best HVAC company we have ever used" — Jane D., Acme Co.') \
        == "testimonial"


# --- offers: pricing tier vs offer ------------------------------------------
@pytest.mark.parametrize("value", [
    "Starter Package", "Growth Package", "Enterprise Package",
    "Pro Plan", "Business Tier",
])
def test_packages_are_pricing_tiers(value):
    assert classify_offer(value) == "pricing_tier"


def test_recurring_price_is_pricing_tier():
    assert classify_offer("Standard", "$99/mo") == "pricing_tier"


@pytest.mark.parametrize("value,details", [
    ("Free Strategy Call", ""),
    ("0% financing for 12 months", ""),
    ("$50 off first service", ""),
    ("Premium Tune-Up Special", ""),   # tier-name word but a promotion -> offer
])
def test_genuine_promotions_stay_offers(value, details):
    assert classify_offer(value, details) == "offer"
