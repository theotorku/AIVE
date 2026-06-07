"""Rule-based first pass (stage 3).

Deterministic extraction runs *before* the LLM: it is cheap, reliable, and
gives the LLM and confidence engine hard facts to anchor on. We pull phones,
emails, addresses, schema.org (JSON-LD) data, headings, service slugs, and FAQ
blocks straight from the page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from backend.app.schema import PageDocument

PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ADDRESS_RE = re.compile(
    r"\d{1,6}\s+(?:[A-Za-z0-9.'\-]+\s){1,5}"
    r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|"
    r"Court|Ct|Suite|Ste|Highway|Hwy|Parkway|Pkwy|Circle|Cir|Place|Pl)\b\.?"
    r"(?:,?\s+[A-Za-z .]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?)?",
    re.IGNORECASE,
)

_SERVICE_SLUG_HINTS = (
    "service", "repair", "installation", "install", "maintenance", "replacement",
    "tune-up", "heating", "cooling", "ac", "air-conditioning", "furnace",
    "heat-pump", "plumbing", "drain", "water-heater", "duct", "thermostat",
)

# JSON-LD @types we treat as the business entity.
_BUSINESS_TYPES = {
    "localbusiness", "organization", "hvacbusiness", "plumber", "electrician",
    "homeandconstructionbusiness", "professionalservice", "corporation",
}


@dataclass
class RuleFacts:
    url: str
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    addresses: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    service_slugs: list[str] = field(default_factory=list)
    faq_pairs: list[dict] = field(default_factory=list)
    schema_org: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "phones": self.phones,
            "emails": self.emails,
            "addresses": self.addresses,
            "headings": self.headings,
            "service_slugs": self.service_slugs,
            "faq_pairs": self.faq_pairs,
            "schema_org": self.schema_org,
        }


def _dedupe(seq: list[str]) -> list[str]:
    seen, out = set(), []
    for x in seq:
        key = x.strip()
        low = key.lower()
        if key and low not in seen:
            seen.add(low)
            out.append(key)
    return out


def _normalize_phone(p: str) -> str:
    digits = re.sub(r"\D", "", p)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"
    return p.strip()


def _schema_org_facts(json_ld: list[dict]) -> dict:
    facts: dict = {}
    faqs: list[dict] = []
    for block in json_ld:
        types = block.get("@type", "")
        types = [types] if isinstance(types, str) else (types or [])
        types_l = {str(t).lower() for t in types}

        if types_l & _BUSINESS_TYPES:
            facts.setdefault("name", block.get("name"))
            if block.get("telephone"):
                facts.setdefault("telephone", block["telephone"])
            addr = block.get("address")
            if isinstance(addr, dict):
                parts = [addr.get(k) for k in
                         ("streetAddress", "addressLocality", "addressRegion", "postalCode")]
                facts.setdefault("address", ", ".join(p for p in parts if p))
            elif isinstance(addr, str):
                facts.setdefault("address", addr)
            area = block.get("areaServed")
            if area:
                facts.setdefault("area_served", _flatten_area(area))

        if "faqpage" in types_l:
            for q in block.get("mainEntity", []) or []:
                if not isinstance(q, dict):
                    continue
                ans = q.get("acceptedAnswer") or {}
                text = ans.get("text") if isinstance(ans, dict) else None
                if q.get("name") and text:
                    faqs.append({"question": q["name"], "answer": _strip_html(text)})

    if faqs:
        facts["faqs"] = faqs
    return facts


def _flatten_area(area) -> list[str]:
    if isinstance(area, str):
        return [area]
    if isinstance(area, dict):
        return [area.get("name")] if area.get("name") else []
    if isinstance(area, list):
        out = []
        for a in area:
            out.extend(_flatten_area(a))
        return [x for x in out if x]
    return []


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _faq_from_markdown(markdown: str) -> list[dict]:
    """Heuristic Q/A: a line that is a question, followed by answer text."""
    pairs: list[dict] = []
    lines = [ln.strip() for ln in markdown.splitlines()]
    for i, line in enumerate(lines):
        q = re.sub(r"^#+\s*", "", line).strip()
        if q.endswith("?") and 8 <= len(q) <= 200:
            answer = ""
            for nxt in lines[i + 1:i + 5]:
                if nxt and not nxt.endswith("?"):
                    answer = re.sub(r"^#+\s*", "", nxt).strip()
                    break
            if answer:
                pairs.append({"question": q, "answer": answer[:600]})
    return pairs[:25]


def extract_rules(doc: PageDocument) -> RuleFacts:
    text = doc.markdown or ""
    facts = RuleFacts(url=doc.url)

    facts.phones = _dedupe([_normalize_phone(m) for m in PHONE_RE.findall(text)])
    facts.emails = _dedupe(EMAIL_RE.findall(text))
    facts.addresses = _dedupe([m.strip() for m in ADDRESS_RE.findall(text)])[:5]
    facts.headings = _dedupe(doc.heading_texts())

    slugs = []
    for link in doc.links:
        path = urlparse(link.href).path.lower()
        if any(h in path for h in _SERVICE_SLUG_HINTS):
            last = [s for s in path.split("/") if s]
            if last:
                slugs.append(last[-1])
    facts.service_slugs = _dedupe(slugs)[:40]

    facts.schema_org = _schema_org_facts(doc.metadata.get("json_ld", []))
    # Prefer structured FAQs; fall back to markdown heuristic.
    facts.faq_pairs = facts.schema_org.get("faqs") or _faq_from_markdown(text)

    return facts
