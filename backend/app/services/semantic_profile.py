"""Site-level profile assembly (stages 6-7).

Each page yields partial extraction. This stage merges them into one business
profile: union values across pages, normalize duplicates, score confidence from
structural signals, and keep evidence + source pages for every fact. Conflicts
are preserved (not dropped) and traceable to their source.
"""

from __future__ import annotations

from collections import Counter

from backend.app.schema import EvidenceItem, PageDocument
from backend.app.services import normalizer
from backend.app.services.actionability import detect_actionability
from backend.app.services.confidence import RELEVANT_CATEGORIES, Signals, score
from backend.app.services.faq_validator import validate_faq
from backend.app.services.llm_extractor import PageExtraction
from backend.app.services.provenance import (
    classify_offer, classify_service, classify_trust)
from backend.app.services.rule_extractor import RuleFacts


def _mentions(extractions: list[PageExtraction], field: str) -> list[dict]:
    """Flatten a per-page evidence array into mentions tagged with provenance."""
    out = []
    for ex in extractions:
        for item in ex.data.get(field, []) or []:
            if not isinstance(item, dict) or not item.get("value"):
                continue
            out.append({
                "value": item["value"],
                "evidence": item.get("evidence", ""),
                "llm_confidence": float(item.get("confidence", 0) or 0),
                "source_url": ex.url,
                "category": ex.category,
                "answer": item.get("answer"),
                "details": item.get("details"),
                "city": item.get("city"),
                "state": item.get("state"),
                "address": item.get("address"),
                "cta_type": item.get("cta_type"),
            })
    return out


def _rule_faq_mentions(rule_facts: list[RuleFacts],
                       url_category: dict[str, str]) -> list[dict]:
    """Deterministic FAQ pairs (schema.org FAQPage + markdown Q/A) as mentions.

    The LLM pass can miss FAQ content, and FAQ JSON-LD can live outside visible
    markdown, so we seed FAQs from RuleFacts directly. Schema-derived pairs get
    high confidence; markdown-heuristic pairs get moderate confidence.
    """
    out: list[dict] = []
    for rf in rule_facts:
        schema_faqs = rf.schema_org.get("faqs") or []
        schema_qs = {q.get("question", "").strip().lower() for q in schema_faqs}
        # Union schema FAQPage pairs with rf.faq_pairs (markdown/heuristic),
        # deduped by question — schema pairs count even if faq_pairs is empty.
        pairs = list(schema_faqs) + [
            p for p in rf.faq_pairs
            if (p.get("question") or "").strip().lower() not in schema_qs]
        for pair in pairs:
            q = (pair.get("question") or "").strip()
            if not q:
                continue
            from_schema = q.lower() in schema_qs
            out.append({
                "value": q,
                "evidence": (pair.get("answer") or "")[:300],
                "llm_confidence": 0.85 if from_schema else 0.6,
                "source_url": rf.url,
                "category": url_category.get(rf.url, "unknown"),
                "answer": pair.get("answer"),
                "faq_source": "schema" if from_schema else "markdown",
            })
    return out


def _structured_data(rule_facts: list[RuleFacts]) -> dict:
    """Profile-level schema.org signal, independent of which facts it backed.

    A site can carry valid LocalBusiness/Organization schema (name/phone/address)
    without it attaching to any extracted service/area/faq, so we surface a
    standalone signal the ABI authority criterion can read directly.
    """
    has_name = has_phone = has_addr = has_area = has_faq = False
    for rf in rule_facts:
        s = rf.schema_org or {}
        has_name = has_name or bool(s.get("name"))
        has_phone = has_phone or bool(s.get("telephone"))
        has_addr = has_addr or bool(s.get("address"))
        has_area = has_area or bool(s.get("area_served"))
        has_faq = has_faq or bool(s.get("faqs"))
    has_business = has_name or has_phone or has_addr
    return {
        "schema_org_detected": bool(has_business or has_area or has_faq),
        "has_business": has_business,
        "has_faq_schema": has_faq,
        "has_name": has_name,
        "has_phone": has_phone,
        "has_address": has_addr,
        "has_area_served": has_area,
    }


def _schema_facts(rule_facts: list[RuleFacts]) -> dict:
    names, phones, addresses, areas, faqs = [], [], [], [], []
    for rf in rule_facts:
        s = rf.schema_org or {}
        if s.get("name"):
            names.append(s["name"])
        if s.get("telephone"):
            phones.append(s["telephone"])
        if s.get("address"):
            addresses.append(s["address"])
        areas.extend(s.get("area_served", []) or [])
        faqs.extend(q.get("question", "") for q in (s.get("faqs") or []))
    return {
        "names": names, "phones": phones, "addresses": addresses,
        # str() guards against any non-string schema value slipping through.
        "areas_lower": {str(a).lower() for a in areas if a},
        "faq_q_lower": {str(q).lower() for q in faqs if q},
    }


def _grouped_evidence(
    mentions: list[dict], groups: list[dict], *,
    heading_blob: str, nav_blob: str, schema_match: set[str],
) -> list[EvidenceItem]:
    """Turn normalized groups into scored EvidenceItems."""
    items: list[EvidenceItem] = []
    for grp in groups:
        canonical = grp["canonical"]
        aliases = grp.get("aliases", [])
        names_lower = {canonical.lower(), *(a.lower() for a in aliases)}

        related = [m for m in mentions if m["value"].lower() in names_lower]
        if not related:
            related = [m for m in mentions
                       if any(n in m["value"].lower() for n in names_lower)]

        source_urls = sorted({m["source_url"] for m in related})
        categories = {m["category"] for m in related}
        best = max(related, key=lambda m: m["llm_confidence"], default=None)

        sig = Signals(
            llm_confidence=best["llm_confidence"] if best else 0.5,
            in_headings=any(n in heading_blob for n in names_lower),
            in_nav=any(n in nav_blob for n in names_lower),
            schema_supported=bool(names_lower & schema_match) or any(
                n in s for n in names_lower for s in schema_match),
            page_count=len(source_urls),
            on_relevant_page=bool(categories & RELEVANT_CATEGORIES),
            from_blog_only=bool(categories) and categories <= {"blog", "unknown"},
        )
        conf, reason = score(sig)
        items.append(EvidenceItem(
            value=canonical, confidence=conf,
            evidence=(best["evidence"] if best else "")[:300],
            source_url=source_urls[0] if source_urls else "",
            confidence_reason=reason,
            extras={"aliases": aliases, "source_pages": source_urls},
        ))
    items.sort(key=lambda i: i.confidence, reverse=True)
    return items


def _simple_evidence(mentions: list[dict], *, heading_blob: str,
                     schema_q_lower: set[str] | None = None,
                     value_key: str = "value", extra_keys: tuple = ()) -> list[EvidenceItem]:
    """Dedupe free-text mentions (faqs/offers/trust/ctas) into scored items."""
    seen: dict[str, dict] = {}
    order: list[str] = []
    for m in mentions:
        key = (m[value_key] or "").strip().lower()
        if not key:
            continue
        if key not in seen:
            seen[key] = {"mentions": [], "value": m[value_key]}
            order.append(key)
        seen[key]["mentions"].append(m)

    items: list[EvidenceItem] = []
    for key in order:
        group = seen[key]
        ms = group["mentions"]
        source_urls = sorted({m["source_url"] for m in ms})
        categories = {m["category"] for m in ms}
        best = max(ms, key=lambda m: m["llm_confidence"])
        sig = Signals(
            llm_confidence=best["llm_confidence"],
            in_headings=key in heading_blob,
            schema_supported=bool(schema_q_lower and key in schema_q_lower),
            page_count=len(source_urls),
            on_relevant_page=bool(categories & RELEVANT_CATEGORIES),
            from_blog_only=categories <= {"blog", "unknown"},
        )
        conf, reason = score(sig)
        extras = {"source_pages": source_urls}
        for ek in extra_keys:
            if best.get(ek) is not None:
                extras[ek] = best[ek]
        items.append(EvidenceItem(
            value=group["value"], confidence=conf,
            evidence=(best["evidence"] or "")[:300],
            source_url=source_urls[0] if source_urls else "",
            confidence_reason=reason, extras=extras,
        ))
    items.sort(key=lambda i: i.confidence, reverse=True)
    return items


def _merge_contact(extractions: list[PageExtraction], rule_facts: list[RuleFacts],
                   schema: dict) -> dict:
    """Prefer deterministic facts, fill gaps from the LLM."""
    phones = [p for rf in rule_facts for p in rf.phones]
    emails = [e for rf in rule_facts for e in rf.emails]
    addresses = list(schema["addresses"]) + [a for rf in rule_facts for a in rf.addresses]

    llm_hours = llm_booking = llm_addr = None
    for ex in extractions:
        c = ex.data.get("contact_information", {}) or {}
        llm_hours = llm_hours or c.get("hours")
        llm_booking = llm_booking or c.get("booking_url")
        llm_addr = llm_addr or c.get("address")

    def most_common(values):
        return Counter(values).most_common(1)[0][0] if values else None

    return {
        "phone": most_common(phones) or (schema["phones"][0] if schema["phones"] else None),
        "email": most_common(emails),
        "address": (addresses[0] if addresses else None) or llm_addr,
        "hours": llm_hours,
        "booking_url": llm_booking,
    }


def _partition_services(services: list[EvidenceItem], url_category: dict[str, str]
                        ) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
    """Split services into first-party vs blog-example (Goal 03E). Conservative:
    a service is blog_example only when sourced exclusively from blog content."""
    first_party, blog_examples = [], []
    for it in services:
        cats = {url_category.get(u) for u in it.extras.get("source_pages", [])}
        label = classify_service(it.value, it.evidence, cats)
        it.extras["provenance"] = label
        (blog_examples if label == "blog_example" else first_party).append(it)
    return first_party, blog_examples


def _partition_trust(trust: list[EvidenceItem]
                     ) -> tuple[list[EvidenceItem], list[EvidenceItem], list[EvidenceItem]]:
    """Split trust signals into first-party trust vs case_study vs testimonial."""
    keep, case_studies, testimonials = [], [], []
    for it in trust:
        label = classify_trust(it.value, it.evidence)
        it.extras["provenance"] = label
        if label == "case_study":
            case_studies.append(it)
        elif label == "testimonial":
            testimonials.append(it)
        else:
            keep.append(it)
    return keep, case_studies, testimonials


def _partition_offers(offers: list[EvidenceItem]
                      ) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
    """Split offers into genuine promotions vs pricing tiers."""
    keep, tiers = [], []
    for it in offers:
        label = classify_offer(it.value, it.extras.get("details", ""))
        it.extras["provenance"] = label
        (tiers if label == "pricing_tier" else keep).append(it)
    return keep, tiers


def build_profile(
    docs: list[PageDocument],
    extractions: list[PageExtraction],
    rule_facts: list[RuleFacts],
) -> dict:
    heading_blob = " ".join(h.lower() for d in docs for h in d.heading_texts())
    nav_blob = " ".join(l.text.lower() for d in docs for l in d.links)
    nav_blob += " " + " ".join(s for rf in rule_facts for s in rf.service_slugs)
    schema = _schema_facts(rule_facts)

    # business_name: schema.org first, else most common LLM value, else og.
    llm_names = [ex.data.get("business_name") for ex in extractions if ex.data.get("business_name")]
    og_names = [d.metadata.get("og", {}).get("site_name") for d in docs
                if d.metadata.get("og", {}).get("site_name")]
    business_name = (schema["names"][0] if schema["names"]
                     else (Counter(llm_names).most_common(1)[0][0] if llm_names
                           else (og_names[0] if og_names else None)))

    llm_industries = [ex.data.get("industry") for ex in extractions if ex.data.get("industry")]
    industry = Counter(llm_industries).most_common(1)[0][0] if llm_industries else None

    svc_mentions = _mentions(extractions, "services")
    services = _grouped_evidence(
        svc_mentions, normalizer.normalize_services([m["value"] for m in svc_mentions]),
        heading_blob=heading_blob, nav_blob=nav_blob, schema_match=set())

    area_mentions = _mentions(extractions, "service_areas")
    service_areas = _grouped_evidence(
        area_mentions, normalizer.normalize_areas([m["value"] for m in area_mentions]),
        heading_blob=heading_blob, nav_blob=nav_blob, schema_match=schema["areas_lower"])

    loc_mentions = _mentions(extractions, "locations")
    locations = _simple_evidence(loc_mentions, heading_blob=heading_blob,
                                 extra_keys=("city", "state", "address"))

    # FAQs: union of LLM-extracted mentions and deterministic rule FAQ pairs
    # (schema.org FAQPage + markdown Q/A), so FAQ content the LLM missed still
    # counts. _simple_evidence dedupes by question text.
    url_category = {d.url: d.category for d in docs}
    llm_faq_mentions = _mentions(extractions, "faqs")
    for m in llm_faq_mentions:
        m["faq_source"] = "faq_section" if m.get("category") == "faq" else "llm"
    faq_mentions = llm_faq_mentions + _rule_faq_mentions(rule_facts, url_category)
    # Pillar 1 — Layer B: reject marketing fragments / CTA-only "answers" at the
    # single merge choke point; schema-sourced FAQs are trusted (length-only).
    faq_mentions = [
        m for m in faq_mentions
        if validate_faq(m["value"], m.get("answer") or "",
                        source=m.get("faq_source", "unknown"))[0]
    ]
    faqs = _simple_evidence(faq_mentions, heading_blob=heading_blob,
                            schema_q_lower=schema["faq_q_lower"], extra_keys=("answer",))
    offers = _simple_evidence(_mentions(extractions, "offers"),
                              heading_blob=heading_blob, extra_keys=("details",))
    trust_signals = _simple_evidence(_mentions(extractions, "trust_signals"),
                                     heading_blob=heading_blob)
    ctas = _simple_evidence(_mentions(extractions, "ctas"),
                            heading_blob=heading_blob, extra_keys=("cta_type",))

    contact = _merge_contact(extractions, rule_facts, schema)

    # Extraction hygiene (Goal 03E): label every fact's provenance and route
    # non-first-party facts OUT of the scored lists. Scoring is unchanged; it
    # just sees believable services / attributable trust / real offers. Nothing
    # is discarded — separated facts move to sibling fields (kept for ABI
    # Profiles), so scored + sibling is loss-less.
    services, blog_examples = _partition_services(services, url_category)
    trust_signals, case_studies, testimonials = _partition_trust(trust_signals)
    offers, pricing_tiers = _partition_offers(offers)

    profile = {
        "schema_version": "2.0",
        "business_name": business_name,
        "industry": industry,
        "services": [i.to_dict() for i in services],
        "service_areas": [i.to_dict() for i in service_areas],
        "locations": [i.to_dict() for i in locations],
        "faqs": [i.to_dict() for i in faqs],
        "offers": [i.to_dict() for i in offers],
        "trust_signals": [i.to_dict() for i in trust_signals],
        "ctas": [i.to_dict() for i in ctas],
        "contact_information": contact,
        "structured_data": _structured_data(rule_facts),
        # Provenance-separated, non-scored sibling fields (like structured_data).
        "blog_examples": [i.to_dict() for i in blog_examples],
        "case_studies": [i.to_dict() for i in case_studies],
        "testimonials": [i.to_dict() for i in testimonials],
        "pricing_tiers": [i.to_dict() for i in pricing_tiers],
        "source_pages": [{"url": d.url, "category": d.category} for d in docs],
    }
    # Agent-actionability (Pillar 3): tiered booking detection from the already-
    # crawled link graph + schema potentialAction + CTAs. Kept out of the
    # extraction contract, like structured_data.
    profile["actionability"] = detect_actionability(docs, profile)
    return profile
