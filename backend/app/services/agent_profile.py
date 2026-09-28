"""Evidence-first, additive profile for agents acting on a business website.

This block is deliberately separate from the frozen ABI v0.1.1 score contract.
Missing facts stay empty; a link or text claim never proves live availability.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from backend.app.schema import PageDocument
from backend.app.services.actionability import (
    _is_booking_path, _is_contact_path, _potential_action, _scheduler_in,
)

AGENT_PROFILE_VERSION = "1.0"
_PRICE = re.compile(r"(?<!\w)\$\s?\d[\d,]*(?:\.\d{2})?(?!\w)")
_PRICE_CONTEXT = re.compile(
    r"\b(price|cost|rate|fee|start(?:s|ing)? at|from \$|per hour|"
    r"per month|estimate|quote|financing|discount|special)\b", re.I)
_QUALIFIER = re.compile(
    r"\b(start(?:s|ing)? at|from|up to|per (?:hour|visit|month|year|unit)|"
    r"plus tax|before tax|subject to|terms apply|new customers? only|"
    r"minimum|expires?\b[^.;]*)", re.I)
_AVAILABILITY = re.compile(
    r"\b(24\s*[/\-]?\s*7|24.hour|same.day|next.day|emergency service|"
    r"weekend (?:hours|service|appointments?)|by appointment|walk.ins?|"
    r"available (?:today|tomorrow))\b", re.I)
_POLICIES = {
    "cancellation": re.compile(r"\b(cancell?ation|reschedul\w*|no.show)\b", re.I),
    "refund": re.compile(r"\b(refund|money.back|return policy)\b", re.I),
    "payment": re.compile(r"\b(payment (?:terms|methods|policy)|deposit required|pay on completion)\b", re.I),
    "warranty": re.compile(r"\b(warranty|warranties|workmanship guarantee)\b", re.I),
    "estimate": re.compile(r"\b(estimate policy|diagnostic fee|quote valid)\b", re.I),
}


def _record(value: str, source_url: str, evidence: str, *,
            confidence: float = 1.0, **fields) -> dict:
    return {"value": value, "confidence": confidence,
            "evidence": evidence[:300], "source_url": source_url, **fields}


def _lines(docs: list[PageDocument]):
    for doc in docs:
        for raw in (doc.markdown or "").splitlines():
            line = re.sub(r"^\s*(?:#+\s*|[-*]\s*)", "", raw).strip()
            if line and len(line) <= 400:
                yield doc, line


def _dedupe(items: list[dict], *keys: str) -> list[dict]:
    seen, out = set(), []
    for item in items:
        key = tuple(str(item.get(k, "")).casefold() for k in keys)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _evidence_items(items: list[dict]) -> list[dict]:
    """Carry the scored profile's facts into the agent view without re-scoring."""
    return [{k: v for k, v in item.items() if k != "confidence_reason"}
            for item in items]


def _contact_provenance(docs: list[PageDocument], contact: dict) -> dict:
    result = {}
    for field, value in contact.items():
        if not value:
            continue
        needle = re.sub(r"\W", "", value).casefold()
        for doc, line in _lines(docs):
            compact = re.sub(r"\W", "", line).casefold()
            if value.casefold() in line.casefold() or (len(needle) >= 7 and needle in compact):
                result[field] = _record(value, doc.url, line, confidence=1.0,
                                        source_type="visible_text")
                break
        if field not in result:
            for doc in docs:
                for block in (doc.metadata or {}).get("json_ld", []) or []:
                    if not isinstance(block, dict):
                        continue
                    schema_key = {"phone": "telephone", "address": "address",
                                  "hours": "openingHours"}.get(field)
                    if schema_key and value.casefold() in str(block.get(schema_key, "")).casefold():
                        result[field] = _record(value, doc.url,
                                                f"schema.org {schema_key}: {value}",
                                                source_type="schema_org")
                        break
                if field in result:
                    break
        if field not in result:
            # Preserve the value but state that the page-level source is unknown.
            result[field] = _record(value, "", "", confidence=0.0,
                                    source_type="unattributed")
    return result


def _identity_provenance(docs: list[PageDocument], profile: dict) -> dict:
    identity = {}
    for field in ("business_name", "industry"):
        value = profile.get(field)
        if not value:
            continue
        for doc, line in _lines(docs):
            if value.casefold() in line.casefold():
                identity[field] = _record(value, doc.url, line,
                                          source_type="visible_text")
                break
        if field not in identity:
            identity[field] = _record(value, "", "", confidence=0.0,
                                      source_type="unattributed")
    return identity


def _booking_endpoints(docs: list[PageDocument], contact: dict,
                       contact_sources: dict) -> list[dict]:
    items = []
    for doc in docs:
        for link in doc.links:
            url = link.href
            scheme = urlparse(url).scheme.lower()
            if scheme not in {"http", "https"}:
                continue
            scheduler = _scheduler_in(url)
            if scheduler:
                kind, tier = "scheduler", "T3"
            elif _is_booking_path(url):
                kind, tier = "booking_or_quote_page", "T2"
            elif _is_contact_path(url):
                kind, tier = "contact_page", "T1"
            else:
                continue
            items.append(_record(url, doc.url, link.text or url,
                                 kind=kind, tier=tier, verified=False))
    booking_url = contact.get("booking_url")
    if booking_url and urlparse(booking_url).scheme.lower() in {"http", "https"}:
        src = contact_sources.get("booking_url", {})
        items.append(_record(booking_url, src.get("source_url", ""),
                             src.get("evidence", ""), kind="declared_booking_url",
                             tier="T3", verified=False))
    for doc in docs:
        action = _potential_action([doc])
        if action and urlparse(action).scheme.lower() in {"http", "https"}:
            items.append(_record(action, doc.url, "schema.org potentialAction",
                                 kind="schema_action", tier="T3", verified=False))
    return _dedupe(items, "value")


def build_agent_profile(docs: list[PageDocument], profile: dict) -> dict:
    """Build a provenance-bearing read model from facts already collected.

    `verified=False` on endpoints means discovery only: no form submission,
    scheduler slot query, or policy enforcement check has occurred.
    """
    contact = profile.get("contact_information") or {}
    contact_sources = _contact_provenance(docs, contact)
    availability, pricing, policies = [], [], []
    if contact.get("hours"):
        source = contact_sources.get("hours", {})
        availability.append(_record(contact["hours"], source.get("source_url", ""),
                                    source.get("evidence", ""),
                                    confidence=source.get("confidence", 0.0),
                                    kind="business_hours", live_slots=False))
    for doc, line in _lines(docs):
        if _AVAILABILITY.search(line):
            availability.append(_record(line, doc.url, line,
                                        kind="stated_availability", live_slots=False))
        if _PRICE.search(line) and _PRICE_CONTEXT.search(line):
            qualifiers = [m.group(0).strip() for m in _QUALIFIER.finditer(line)]
            pricing.append(_record(line, doc.url, line, currency=None,
                                   currency_symbol="$",
                                   amounts=_PRICE.findall(line), qualifiers=qualifiers,
                                   kind="stated_price"))
        for kind, pattern in _POLICIES.items():
            if pattern.search(line):
                policies.append(_record(line, doc.url, line, kind=kind))
    # Offer and tier claims may not contain a parseable amount; retain them as
    # pricing context without inventing a numeric price or applying conditions.
    for kind, source_items in (("promotion", profile.get("offers") or []),
                               ("pricing_tier", profile.get("pricing_tiers") or [])):
        for item in source_items:
            claim = " ".join(x for x in (item.get("value"), item.get("details")) if x)
            pricing.append(_record(claim, item.get("source_url", ""),
                                   item.get("evidence", ""),
                                   confidence=item.get("confidence", 0.0),
                                   currency=None,
                                   currency_symbol="$" if _PRICE.search(claim) else None,
                                   amounts=_PRICE.findall(claim),
                                   qualifiers=[m.group(0).strip() for m in _QUALIFIER.finditer(claim)],
                                   kind=kind))
    return {
        "version": AGENT_PROFILE_VERSION,
        "identity": _identity_provenance(docs, profile),
        "canonical_services": _evidence_items(profile.get("services") or []),
        "service_areas": _evidence_items(profile.get("service_areas") or []),
        "availability": _dedupe(availability, "kind", "value"),
        "pricing": _dedupe(pricing, "kind", "value"),
        "booking_endpoints": _booking_endpoints(docs, contact, contact_sources),
        "policies": _dedupe(policies, "kind", "value"),
        "trust_signals": _evidence_items(profile.get("trust_signals") or []),
        "contact_information": contact_sources,
        "live_availability_checked": False,
    }
