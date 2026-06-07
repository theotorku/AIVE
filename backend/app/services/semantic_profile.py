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
from backend.app.services.confidence import RELEVANT_CATEGORIES, Signals, score
from backend.app.services.llm_extractor import PageExtraction
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
        "areas_lower": {a.lower() for a in areas if a},
        "faq_q_lower": {q.lower() for q in faqs if q},
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

    faqs = _simple_evidence(_mentions(extractions, "faqs"), heading_blob=heading_blob,
                            schema_q_lower=schema["faq_q_lower"], extra_keys=("answer",))
    offers = _simple_evidence(_mentions(extractions, "offers"),
                              heading_blob=heading_blob, extra_keys=("details",))
    trust_signals = _simple_evidence(_mentions(extractions, "trust_signals"),
                                     heading_blob=heading_blob)
    ctas = _simple_evidence(_mentions(extractions, "ctas"),
                            heading_blob=heading_blob, extra_keys=("cta_type",))

    contact = _merge_contact(extractions, rule_facts, schema)

    return {
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
        "source_pages": [{"url": d.url, "category": d.category} for d in docs],
    }
