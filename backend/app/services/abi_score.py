"""Agent Business Index (ABI) scoring — Goal 03.

Turns a merged semantic profile (Goal 02 output) into an explainable score of
how visible and usable a business is to AI agents and answer engines.

Design principles (per CLAUDE.md / ABI Principles):

  - **Explainable.** Every point is earned by a *named criterion* that carries
    its own rationale and the supporting evidence pulled from the profile.
  - **Repeatable.** Pure, deterministic functions over the profile dict. No LLM,
    no randomness — the same profile always yields the same score.
  - **Defensible.** Criteria map to the five ABI dimensions from the PRD; weights
    and targets are declared as named constants, not magic numbers buried in code.
  - **Actionable.** Unfilled criteria emit a concrete recommendation; the engine
    ranks them by *ABI impact* (points left on the table × dimension weight) so a
    business knows what to fix first.

Output shape (added to the profile as `abi_score`):

    {
      "overall": 62.3, "grade": "C", "grade_label": "Partially Visible",
      "dimensions": {
        "ai_understanding": {"score": 78.0, "weight": 0.25, "grade": "B",
          "criteria": [{"name", "earned", "max", "ratio", "rationale",
                        "evidence": [...], "recommendation": str|null}, ...]},
        ...
      },
      "top_recommendations": [{"dimension", "criterion", "recommendation",
                               "impact", "priority"}, ...],
      "summary": "ABI 62.3 (C — Partially Visible). Strongest: ... Weakest: ..."
    }

Scoring is intentionally separate from extraction: the profile already carries
per-fact confidence + evidence + provenance, so the score reads structural
signals rather than re-deriving them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.schema import (
    ABI_DIMENSION_WEIGHTS as DIMENSION_WEIGHTS,
    ABI_GRADE_BANDS as GRADE_BANDS,
    abi_grade_for as grade_for,
)

# --- dimension model --------------------------------------------------------
# Weights and grade bands are the scoring *contract*; they live in schema.py so
# the validator can enforce them. Imported here (PRD: Understanding 25 /
# Retrieval 25 / Recommendation 20 / Agent Readiness 15 / Semantic Authority 15).

DIMENSION_LABELS = {
    "ai_understanding": "AI Understanding",
    "ai_retrieval": "AI Retrieval",
    "ai_recommendation": "AI Recommendation",
    "agent_readiness": "Agent Readiness",
    "semantic_authority": "Semantic Authority",
}

# Saturation targets: the count at which a count-based criterion earns full marks.
# Beyond the target, more does not help the score (diminishing ABI returns).
TARGETS = {
    "services": 6,
    "services_authority": 8,   # authority expects deeper coverage than understanding
    "faqs": 5,
    "service_areas": 4,
    "service_areas_authority": 5,
    "offers": 2,
    "trust_signals": 4,
    "ctas": 3,
    "relevant_pages": 5,
}

# Keyword buckets used to gauge the *diversity* of reputation evidence, not just
# the count. Hitting more buckets is stronger social proof for recommendation.
TRUST_BUCKETS = {
    "guarantee": ("guarantee", "warranty", "satisfaction", "money back", "money-back"),
    "certification": ("certified", "licensed", "insured", "accredited", "epa", "nate"),
    "awards": ("award", "best of", "top rated", "voted", "winner"),
    "experience": ("years", "since", "family owned", "family-owned", "established"),
    "reviews": ("review", "rating", "stars", "rated", "bbb", "google", "testimonial"),
}


@dataclass
class CriterionResult:
    name: str
    earned: float
    max: float
    rationale: str
    evidence: list = field(default_factory=list)
    recommendation: str | None = None

    @property
    def ratio(self) -> float:
        return self.earned / self.max if self.max else 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "earned": round(self.earned, 1),
            "max": self.max,
            "ratio": round(self.ratio, 2),
            "rationale": self.rationale,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


# --- confidence-aware scoring (Goal 03D, Pillar 2) --------------------------
# Principle: earned = max_points × evidence × confidence_factor. A criterion
# should pay out for *credible* evidence, not the mere existence of a row. The
# per-fact confidence is already computed (services/areas/faqs/... carry it with
# a reason), so the score stays explainable.

FULL_CONF = 0.7   # at/above this a fact counts as fully credible (approved start)


def _conf_factor(conf: float) -> float:
    """Map a fact's confidence to a [0,1] weight. Saturating, not punitive:
    genuinely confident facts (>= FULL_CONF) count in full; weak evidence is
    discounted linearly toward zero. FULL_CONF=0.7 aligns with the confidence
    engine's high/medium bands, so high-quality sites are never penalized."""
    return max(0.0, min(1.0, (conf or 0.0) / FULL_CONF))


def _eff_count(items: list[dict]) -> float:
    """Confidence-weighted count: how many *credible* units of evidence exist.
    Replaces raw len() in count-based criteria so low-confidence facts (a 0.14
    blog-derived service, a 0.15 incidental city) contribute only fractionally."""
    return sum(_conf_factor(i.get("confidence", 0) or 0) for i in items)


# --- small, shared helpers --------------------------------------------------

def _ratio(count: float, target: float) -> float:
    return min(1.0, count / target) if target else 0.0


def _avg_conf(items: list[dict]) -> float:
    vals = [i.get("confidence", 0) or 0 for i in items]
    return sum(vals) / len(vals) if vals else 0.0


def _values(items: list[dict], n: int = 3) -> list[str]:
    return [str(i.get("value", "")) for i in items[:n] if i.get("value")]


def _count_reason(items: list[dict], substr: str) -> int:
    return sum(1 for i in items if substr in (i.get("confidence_reason", "") or ""))


def _has_reason(groups: list[list[dict]], substr: str) -> bool:
    return any(substr in (i.get("confidence_reason", "") or "")
               for g in groups for i in g)


# --- dimension scorers ------------------------------------------------------
# Each returns list[CriterionResult] summing to max 100 points.

def _score_understanding(p: dict) -> list[CriterionResult]:
    services = p.get("services", []) or []
    locations = p.get("locations", []) or []
    contact = p.get("contact_information", {}) or {}
    out: list[CriterionResult] = []

    # Business identity (15)
    name = p.get("business_name")
    out.append(CriterionResult(
        "Business identity", 15 if name else 0, 15,
        f"Business name identified: {name}." if name
        else "No business name could be confidently identified.",
        [f"business_name: {name}"] if name else [],
        None if name else "Surface the business name clearly in the homepage "
        "title and in schema.org Organization/LocalBusiness markup."))

    # Industry / category (15)
    industry = p.get("industry")
    out.append(CriterionResult(
        "Industry clarity", 15 if industry else 0, 15,
        f"Business category detected as {industry}." if industry
        else "Industry/category is unclear to an AI reader.",
        [f"industry: {industry}"] if industry else [],
        None if industry else "State the industry/category explicitly "
        "(e.g. 'HVAC company') in headings and meta description."))

    # Service coverage (30) — confidence-weighted: credible services, not rows.
    n_svc = len(services)
    r = _ratio(_eff_count(services), TARGETS["services"])
    out.append(CriterionResult(
        "Service coverage", 30 * r, 30,
        f"{n_svc} distinct services identified.",
        _values(services),
        None if r >= 1 else "List more of your services as distinct, named "
        "offerings so AI can understand your full scope."))

    # Service clarity = how confidently services are stated (20)
    avg = _avg_conf(services)
    out.append(CriterionResult(
        "Service clarity", 20 * avg, 20,
        f"Average confidence of identified services is {avg:.2f}." if services
        else "No services to assess clarity on.",
        [f"{i['value']} ({i.get('confidence')})" for i in services[:3]],
        None if avg >= 0.7 else "Reinforce services with clear page headings "
        "and dedicated service pages so they read unambiguously."))

    # Location / address presence (20) — confidence-gated (Pillar 2). A
    # 0.15-confidence incidental city no longer earns the same 20 points as a
    # verified address: earned = 20 × confidence_factor(best evidence). A
    # structured contact.address string is itself a strong signal (treated 0.8).
    best_loc = max((_conf_factor(l.get("confidence", 0) or 0) for l in locations),
                   default=0.0)
    if contact.get("address"):
        best_loc = max(best_loc, _conf_factor(0.8))
    has_loc = bool(locations) or bool(contact.get("address"))
    addr_ev = []
    if locations:
        addr_ev = _values(locations)
    elif contact.get("address"):
        addr_ev = [contact["address"]]
    out.append(CriterionResult(
        "Location presence", 20 * best_loc, 20,
        "Physical location/address information present "
        f"(confidence-weighted {best_loc:.2f})." if has_loc
        else "No physical location or address detected.",
        addr_ev,
        None if best_loc >= 1.0 else (
            "Publish your address and service locations (ideally in "
            "LocalBusiness schema) so agents can place you." if not has_loc
            else "Reinforce your location with a consistent NAP and "
            "LocalBusiness schema so it reads as verified, not incidental.")))
    return out


def _score_retrieval(p: dict) -> list[CriterionResult]:
    services = p.get("services", []) or []
    faqs = p.get("faqs", []) or []
    areas = p.get("service_areas", []) or []
    pages = p.get("source_pages", []) or []
    out: list[CriterionResult] = []

    # FAQ presence (35) — the single strongest answer-engine retrieval asset.
    # Confidence-weighted so low-confidence "FAQs" don't max the criterion.
    n_faq = len(faqs)
    r = _ratio(_eff_count(faqs), TARGETS["faqs"])
    out.append(CriterionResult(
        "FAQ coverage", 35 * r, 35,
        f"{n_faq} FAQ question/answer pairs found." if n_faq
        else "No FAQ content detected — weak for answer-engine retrieval.",
        _values(faqs),
        None if r >= 1 else "Add an FAQ section with real question-and-answer "
        "pairs; this is the highest-leverage change for answer-engine visibility."))

    # FAQ answer quality (10)
    answered = sum(1 for f in faqs if (f.get("answer") or "").strip())
    aq = answered / n_faq if n_faq else 0.0
    out.append(CriterionResult(
        "FAQ answer quality", 10 * aq, 10,
        f"{answered}/{n_faq} FAQs include a substantive answer." if n_faq
        else "No answers to assess (no FAQ content).",
        [],
        None if aq >= 1 and n_faq else "Ensure every FAQ question is paired with "
        "a clear, self-contained answer agents can quote."))

    # Heading reinforcement (20) — content structured enough to be retrieved.
    in_head = _count_reason(services, "heading")
    hr = in_head / len(services) if services else 0.0
    out.append(CriterionResult(
        "Heading structure", 20 * hr, 20,
        f"{in_head}/{len(services)} services are reinforced by page headings."
        if services else "No services to assess heading structure on.",
        [],
        None if hr >= 0.5 else "Use descriptive H1/H2 headings that name each "
        "service so retrieval engines can locate and lift them."))

    # Service-area specificity (20) — confidence-weighted.
    n_area = len(areas)
    ar = _ratio(_eff_count(areas), TARGETS["service_areas"])
    out.append(CriterionResult(
        "Geographic specificity", 20 * ar, 20,
        f"{n_area} service areas specified." if n_area
        else "No service areas named — weak for 'near me' style retrieval.",
        _values(areas),
        None if ar >= 1 else "Name the cities/regions you serve so location-based "
        "queries can retrieve you."))

    # Content breadth (15) — relevant (non-blog) pages give more to retrieve.
    relevant = [sp for sp in pages
                if sp.get("category") not in (None, "blog", "unknown")]
    pr = _ratio(len(relevant), TARGETS["relevant_pages"])
    out.append(CriterionResult(
        "Content breadth", 15 * pr, 15,
        f"{len(relevant)} relevant content pages available to retrieve.",
        [sp.get("category") for sp in relevant[:5]],
        None if pr >= 1 else "Publish dedicated pages (services, about, contact, "
        "areas) so there is more high-signal content to retrieve."))
    return out


def _score_recommendation(p: dict) -> list[CriterionResult]:
    trust = p.get("trust_signals", []) or []
    offers = p.get("offers", []) or []
    out: list[CriterionResult] = []

    # Trust signals present (40) — confidence-weighted.
    n_trust = len(trust)
    r = _ratio(_eff_count(trust), TARGETS["trust_signals"])
    out.append(CriterionResult(
        "Trust signals", 40 * r, 40,
        f"{n_trust} trust signals found." if n_trust
        else "No trust signals detected — weakens recommendation likelihood.",
        _values(trust),
        None if r >= 1 else "Surface guarantees, certifications, awards, and "
        "years in business — agents weigh these when recommending."))

    # Reputation diversity (30) — distinct *kinds* of proof, not just volume.
    blob = " ".join(str(t.get("value", "")).lower() for t in trust)
    hit = [name for name, kws in TRUST_BUCKETS.items() if any(k in blob for k in kws)]
    dr = len(hit) / len(TRUST_BUCKETS)
    missing = [b for b in TRUST_BUCKETS if b not in hit]
    out.append(CriterionResult(
        "Reputation diversity", 30 * dr, 30,
        f"Reputation evidence spans {len(hit)}/{len(TRUST_BUCKETS)} categories: "
        f"{', '.join(hit) or 'none'}.",
        hit,
        None if dr >= 0.8 else "Add the missing kinds of proof: "
        f"{', '.join(missing)}."))

    # Promotional offers (20) — confidence-weighted.
    n_off = len(offers)
    orr = _ratio(_eff_count(offers), TARGETS["offers"])
    out.append(CriterionResult(
        "Offers & incentives", 20 * orr, 20,
        f"{n_off} promotional offers present." if n_off
        else "No promotions or incentives detected.",
        _values(offers),
        None if orr >= 1 else "Publish current offers/financing/specials; these "
        "give agents a concrete reason to surface you."))

    # Trust confidence (10)
    avg = _avg_conf(trust)
    out.append(CriterionResult(
        "Trust signal strength", 10 * avg, 10,
        f"Average confidence of trust signals is {avg:.2f}." if trust
        else "No trust signals to assess strength on.",
        [],
        None if avg >= 0.7 else "Place trust claims in prominent, structured "
        "locations (headings, badges) so they read as credible, not incidental."))
    return out


# Booking actionability tier -> points (of 20). T3 deep-linkable scheduler is
# the clearest agent path; a form is fillable; a bare intent CTA needs a human.
_BOOKING_TIER_POINTS = {"T3": 20, "T2": 12, "T1": 6, "T0": 0}
_BOOKING_TIER_WHY = {
    "T3": "Direct online booking detected (deep-linkable scheduler / "
          "potentialAction) — an agent can act immediately.",
    "T2": "Form-based booking/quote detected — an agent can complete a form.",
    "T1": "Booking intent detected (CTA / phone) but no deep-linkable scheduler.",
    "T0": "No online booking or scheduling affordance detected.",
}


def _booking_criterion(p: dict, contact: dict) -> CriterionResult:
    booking = (p.get("actionability") or {}).get("booking") or {}
    tier = booking.get("tier")
    if tier in _BOOKING_TIER_POINTS:
        earned = _BOOKING_TIER_POINTS[tier]
        evidence = [booking["evidence"]] if booking.get("evidence") else []
    else:
        # Legacy fallback: binary on booking_url when no actionability detected.
        present = bool(contact.get("booking_url"))
        tier = "T3" if present else "T0"
        earned = 20 if present else 0
        evidence = [contact["booking_url"]] if present else []
    rec = None if earned >= 20 else (
        "Add a deep-linkable online scheduler (Calendly, Cal.com, or your "
        "booking platform) — the clearest path for an agent to act on a "
        "customer's behalf." if tier in ("T0", "T1") else
        "Upgrade your booking form to a deep-linkable scheduler so an agent "
        "can reach a specific time slot directly.")
    return CriterionResult("Online booking", earned, 20,
                           _BOOKING_TIER_WHY[tier], evidence, rec)


def _score_agent_readiness(p: dict) -> list[CriterionResult]:
    contact = p.get("contact_information", {}) or {}
    ctas = p.get("ctas", []) or []
    out: list[CriterionResult] = []

    def boolean(label, key, pts, why, rec):
        present = bool(contact.get(key))
        out.append(CriterionResult(
            label, pts if present else 0, pts,
            why if present else f"No {label.lower()} detected.",
            [str(contact.get(key))] if present else [],
            None if present else rec))

    boolean("Phone number", "phone", 20, "Phone number available to agents.",
            "Publish a clickable phone number (tel: link) in a consistent place.")
    boolean("Contact email", "email", 15, "Contact email available.",
            "Publish a contact email so agents have a non-voice channel.")
    boolean("Address", "address", 15, "Street address available.",
            "Publish a full postal address (ideally in schema.org PostalAddress).")
    boolean("Business hours", "hours", 15, "Operating hours available.",
            "Publish business hours so agents can tell when you're reachable.")

    # Online booking (20) — graduated by agent-actionability tier (Pillar 3),
    # not a binary read of contact.booking_url. Detection is in actionability.py;
    # falls back to the legacy booking_url flag when no actionability block is
    # present (older profiles).
    out.append(_booking_criterion(p, contact))

    # Clear CTAs (15) — confidence-weighted.
    n_cta = len(ctas)
    r = _ratio(_eff_count(ctas), TARGETS["ctas"])
    out.append(CriterionResult(
        "Calls to action", 15 * r, 15,
        f"{n_cta} clear calls-to-action identified." if n_cta
        else "No clear calls-to-action detected.",
        _values(ctas),
        None if r >= 1 else "Provide explicit next-step CTAs (Book, Call, Get a "
        "Quote) so agents know the intended action."))
    return out


def _score_semantic_authority(p: dict) -> list[CriterionResult]:
    services = p.get("services", []) or []
    areas = p.get("service_areas", []) or []
    faqs = p.get("faqs", []) or []
    locations = p.get("locations", []) or []
    out: list[CriterionResult] = []

    # Structured data (35) — machine-readable schema.org is the strongest
    # authority signal an AI can consume directly. Read the profile-level signal
    # (which captures LocalBusiness/Organization schema for name/phone/address,
    # not just schema attached to a service/area/faq fact) and fall back to the
    # per-fact confidence reasons. Graduated: business schema (20) + FAQ schema
    # (15), so a site is not all-or-nothing.
    groups = [services, areas, faqs, locations]
    sd = p.get("structured_data") or {}
    has_business = bool(sd.get("has_business")) or _has_reason(groups, "schema.org")
    has_faq_schema = bool(sd.get("has_faq_schema")) or any(
        "schema.org" in (f.get("confidence_reason", "") or "") for f in faqs)
    detected = []
    if has_business:
        detected.append("business (LocalBusiness/Organization)")
    if has_faq_schema:
        detected.append("FAQPage")
    earned = (20 if has_business else 0) + (15 if has_faq_schema else 0)
    missing = []
    if not has_business:
        missing.append("LocalBusiness/Organization")
    if not has_faq_schema:
        missing.append("FAQPage")
    out.append(CriterionResult(
        "Structured data (schema.org)", earned, 35,
        f"schema.org detected: {', '.join(detected)}." if detected
        else "No schema.org structured data detected.",
        detected,
        None if not missing else "Add JSON-LD schema.org markup ("
        + ", ".join(missing) + ") — the highest-impact authority signal."))

    # Service depth (20) — authority expects deeper coverage than understanding.
    sr = _ratio(_eff_count(services), TARGETS["services_authority"])
    out.append(CriterionResult(
        "Service depth", 20 * sr, 20,
        f"{len(services)} services documented (authority target "
        f"{TARGETS['services_authority']}).",
        _values(services),
        None if sr >= 1 else "Build out dedicated, detailed pages for each "
        "service to establish topical authority."))

    # Area depth (15) — confidence-weighted.
    ar = _ratio(_eff_count(areas), TARGETS["service_areas_authority"])
    out.append(CriterionResult(
        "Geographic authority", 15 * ar, 15,
        f"{len(areas)} service areas documented.",
        _values(areas),
        None if ar >= 1 else "Document each service area, ideally with a "
        "location-specific page."))

    # FAQ authority (15) — confidence-weighted.
    fr = _ratio(_eff_count(faqs), TARGETS["faqs"])
    out.append(CriterionResult(
        "Knowledge depth (FAQ)", 15 * fr, 15,
        f"{len(faqs)} FAQ entries contribute to knowledge depth.",
        _values(faqs),
        None if fr >= 1 else "Grow your FAQ/knowledge content to demonstrate "
        "subject-matter depth."))

    # Cross-page corroboration (15) — facts repeated across pages read as
    # authoritative rather than incidental.
    all_items = [i for g in groups for i in g]
    repeated = sum(1 for i in all_items
                   if "repeated across" in (i.get("confidence_reason", "") or ""))
    cr = repeated / len(all_items) if all_items else 0.0
    out.append(CriterionResult(
        "Cross-page corroboration", 15 * cr, 15,
        f"{repeated}/{len(all_items)} facts are corroborated across multiple pages."
        if all_items else "No facts available to corroborate.",
        [],
        None if cr >= 0.3 else "Reinforce key facts consistently across pages so "
        "they corroborate each other."))
    return out


_DIMENSION_SCORERS = {
    "ai_understanding": _score_understanding,
    "ai_retrieval": _score_retrieval,
    "ai_recommendation": _score_recommendation,
    "agent_readiness": _score_agent_readiness,
    "semantic_authority": _score_semantic_authority,
}


# --- public API -------------------------------------------------------------

def score_abi(profile: dict) -> dict:
    """Score a merged profile into the explainable ABI structure (see module doc)."""
    dimensions: dict = {}
    recommendations: list[dict] = []

    for key, scorer in _DIMENSION_SCORERS.items():
        criteria = scorer(profile)
        earned = sum(c.earned for c in criteria)
        # criteria are authored to sum to 100; normalize defensively.
        max_pts = sum(c.max for c in criteria) or 1.0
        dim_score = round(earned / max_pts * 100, 1)
        letter, _label = grade_for(dim_score)
        weight = DIMENSION_WEIGHTS[key]
        dimensions[key] = {
            "label": DIMENSION_LABELS[key],
            "score": dim_score,
            "weight": weight,
            "grade": letter,
            "criteria": [c.to_dict() for c in criteria],
        }
        for c in criteria:
            if c.recommendation and c.ratio < 1.0:
                # ABI impact: unfilled points scaled by how much the dimension
                # matters to the overall index. Drives the priority ordering.
                impact = round((c.max - c.earned) * weight, 2)
                recommendations.append({
                    "dimension": key,
                    "dimension_label": DIMENSION_LABELS[key],
                    "criterion": c.name,
                    "recommendation": c.recommendation,
                    "impact": impact,
                })

    overall = round(
        sum(dimensions[k]["score"] * DIMENSION_WEIGHTS[k] for k in dimensions), 1)
    letter, label = grade_for(overall)

    recommendations.sort(key=lambda r: r["impact"], reverse=True)
    top = recommendations[:5]
    for i, r in enumerate(top, 1):
        r["priority"] = i

    strongest = max(dimensions.items(), key=lambda kv: kv[1]["score"])
    weakest = min(dimensions.items(), key=lambda kv: kv[1]["score"])
    summary = (
        f"ABI {overall} ({letter} — {label}). "
        f"Strongest: {strongest[1]['label']} ({strongest[1]['score']}). "
        f"Weakest: {weakest[1]['label']} ({weakest[1]['score']}). "
        + (f"Top fix: {top[0]['recommendation']}" if top else
           "No high-impact gaps remain."))

    return {
        "overall": overall,
        "grade": letter,
        "grade_label": label,
        "dimensions": dimensions,
        "top_recommendations": top,
        "summary": summary,
        "weights": DIMENSION_WEIGHTS,
    }
