"""ABI evidence layer (stage 8).

The pipeline does not just output data — it outputs *evidence* organized by the
five ABI dimensions (per the PRD), so Goal 03 scoring is explainable. This
stage produces qualitative observations (positives and gaps) only; it computes
no scores (scoring is Goal 03).
"""

from __future__ import annotations


def _count_conf(items: list[dict], threshold: float = 0.5) -> int:
    return sum(1 for i in items if i.get("confidence", 0) >= threshold)


def build_abi_evidence(profile: dict) -> dict:
    services = profile.get("services", [])
    areas = profile.get("service_areas", [])
    locations = profile.get("locations", [])
    faqs = profile.get("faqs", [])
    offers = profile.get("offers", [])
    trust = profile.get("trust_signals", [])
    ctas = profile.get("ctas", [])
    contact = profile.get("contact_information", {}) or {}

    understanding: list[str] = []
    if profile.get("business_name"):
        understanding.append(f"Business name identified: {profile['business_name']}.")
    else:
        understanding.append("Business name could not be clearly identified.")
    if profile.get("industry"):
        understanding.append(f"Business category detected as {profile['industry']}.")
    if services:
        understanding.append(f"{len(services)} distinct services identified "
                             f"({_count_conf(services)} high/medium confidence).")
    else:
        understanding.append("No clearly listed services found.")
    if locations or contact.get("address"):
        understanding.append("Physical location/address information present.")

    retrieval: list[str] = []
    if faqs:
        retrieval.append(f"FAQ content found: {len(faqs)} question/answer pairs.")
    else:
        retrieval.append("No FAQ content detected - weak for answer-engine retrieval.")
    if areas:
        retrieval.append(f"{len(areas)} service areas specified.")
    retrieval.append("Service pages use clear headings."
                     if any(s.get("confidence", 0) >= 0.5 and "heading" in s.get("confidence_reason", "")
                            for s in services)
                     else "Few services reinforced by page headings.")

    recommendation: list[str] = []
    if trust:
        recommendation.append(f"{len(trust)} trust signals found "
                              "(guarantees/certifications/awards/experience).")
    else:
        recommendation.append("No trust signals detected — weakens recommendation likelihood.")
    if offers:
        recommendation.append(f"{len(offers)} promotional offers present.")

    agent_readiness: list[str] = []
    agent_readiness.append("Phone number detected." if contact.get("phone")
                           else "No phone number detected.")
    agent_readiness.append("Online booking link found." if contact.get("booking_url")
                           else "No online booking link found.")
    agent_readiness.append("Contact email present." if contact.get("email")
                           else "No contact email detected.")
    if ctas:
        agent_readiness.append(f"{len(ctas)} calls-to-action identified.")

    semantic_authority: list[str] = []
    semantic_authority.append(f"Service coverage: {len(services)} services, "
                              f"{len(areas)} areas.")
    semantic_authority.append(f"FAQ coverage: {len(faqs)} entries.")
    has_schema = any("schema.org" in s.get("confidence_reason", "")
                     for group in (services, areas, faqs, locations) for s in group)
    semantic_authority.append("Structured data (schema.org) detected."
                              if has_schema else
                              "No structured data (schema.org) detected.")

    return {
        "understanding": understanding,
        "retrieval": retrieval,
        "recommendation": recommendation,
        "agent_readiness": agent_readiness,
        "semantic_authority": semantic_authority,
    }
