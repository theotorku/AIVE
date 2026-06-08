"""Provenance classification (Goal 03E — Extraction Hygiene).

Labels each extracted fact by where it came from / what it really is, so the
merge stage can route non-first-party facts out of the scored lists. Pure,
deterministic, no LLM — every signal is already on the merged item (source page
categories, evidence text). Scoring is untouched; it simply receives cleaner
`services` / `trust_signals` / `offers`.

Labels (the 03E taxonomy):
    first_party_service   an offering the business itself performs   (kept)
    blog_example          a service named only as a blog example     (separated)
    case_study            a quantified third-party/client outcome     (separated)
    testimonial           a quoted customer endorsement               (separated)
    offer                 a genuine promotion / incentive             (kept)
    pricing_tier          a productized price package/plan            (separated)
    trust_signal          residual first-party proof (kept)

**Conservative bias (explicit requirement):** when classification is ambiguous,
prefer the *kept* label. A false `blog_example` (dropping a real first-party
service from scoring) is more damaging than a false `first_party_service`, so a
service is only `blog_example` when sourced *exclusively* from blog content and
not corroborated on any first-party page. The same bias applies to trust/offers:
`case_study` / `testimonial` / `pricing_tier` require a clear positive pattern,
else the item stays first-party.
"""

from __future__ import annotations

import re

# Frozen provenance taxonomy (ABI v0.1.1). The six separation labels plus the
# `trust_signal` residual (kept first-party trust). Every classify_* function
# returns one of these; the freeze test pins the set. No additions without a
# benchmark review.
PROVENANCE_LABELS = frozenset({
    "first_party_service", "blog_example",   # services
    "trust_signal", "case_study", "testimonial",  # trust
    "offer", "pricing_tier",                  # offers
})

# --- services ---------------------------------------------------------------
# Categories that are editorial rather than first-party offering surfaces.
EDITORIAL_CATEGORIES = {"blog", "unknown"}


def classify_service(value: str, evidence: str, categories: set[str]) -> str:
    """first_party_service unless the service is sourced ONLY from blog content.

    Requires an actual `blog` page (not merely `unknown`) and no first-party
    page (home/services/service_detail/about/...) — so an unclassified-only or
    blog+service service stays first-party. Conservative by design."""
    cats = {c for c in (categories or set()) if c}
    if cats and cats <= EDITORIAL_CATEGORIES and "blog" in cats:
        return "blog_example"
    return "first_party_service"


# --- trust signals ----------------------------------------------------------
_CHANGE_VERB = (r"(?:jump\w*|drop\w*|increas\w*|reduc\w*|grew|grow\w*|cut|"
                r"sav\w*|boost\w*|improv\w*|rose|fell|climb\w*|slash\w*|"
                r"decreas\w*|doubl\w*|tripl\w*)")
# A quantified outcome delta: "from 19% to 43%", "dropped by 72%", "saved 10 hours".
_OUTCOME_RE = re.compile(
    r"from\s+\$?\d[\d.,]*\s*%?\s*(?:to|–|—|->|→)\s*\$?\d[\d.,]*\s*%?"
    r"|" + _CHANGE_VERB + r"[^.]{0,40}?\b\d[\d.,]*\s*(?:%|percent|hours?|x\b|times|days?)"
    r"|\b\d[\d.,]*\s*(?:%|percent|hours?|x)\b[^.]{0,25}?" + _CHANGE_VERB,
    re.I)
# A quoted endorsement with an attribution marker.
_QUOTE_RE = re.compile(r"[\"“”].{8,}?[\"“”]")
_ATTRIB_RE = re.compile(r"(?:—|–|--|\bby\b|-\s)\s*[A-Z][a-z]+", re.I)


def classify_trust(value: str, evidence: str = "") -> str:
    """case_study (quantified third-party outcome) / testimonial (quoted
    endorsement) / trust_signal (first-party credential — the default)."""
    text = f"{value} {evidence or ''}".strip()
    if _OUTCOME_RE.search(text):
        return "case_study"
    if _QUOTE_RE.search(text) and _ATTRIB_RE.search(text):
        return "testimonial"
    return "trust_signal"


# --- offers -----------------------------------------------------------------
_TIER_WORD_RE = re.compile(r"\b(package|plan|tier|edition|bundle|subscription)\b", re.I)
_TIER_NAME_RE = re.compile(
    r"\b(starter|basic|standard|growth|pro|professional|premium|business|"
    r"enterprise|plus|elite|ultimate)\b", re.I)
# A *recurring* price marks a plan/tier; a bare "$50 off" is a promotion, not a
# price point, so require a per-period suffix rather than any dollar amount.
_PRICE_RE = re.compile(
    r"\$?\s*\d[\d.,]*\s*(?:/\s*mo\b|/\s*month|per\s+month|per\s+seat|monthly|"
    r"/\s*yr\b|/\s*year|per\s+year|annually)", re.I)
# Words that mark a genuine promotion (protect offers from the tier-name rule).
_PROMO_RE = re.compile(
    r"\b(free|off|discount|save|saving|financing|deal|special|coupon|"
    r"rebate|promo|%|consult)\b", re.I)


def classify_offer(value: str, details: str = "") -> str:
    """pricing_tier (a productized package/plan/price) vs offer (promotion)."""
    text = f"{value} {details or ''}"
    if _PRICE_RE.search(text):
        return "pricing_tier"
    if _TIER_WORD_RE.search(text):
        return "pricing_tier"
    if _TIER_NAME_RE.search(value) and not _PROMO_RE.search(text):
        return "pricing_tier"
    return "offer"
