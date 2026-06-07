"""Core data shapes for the extraction pipeline.

Two kinds of shapes live here:

  1. Python dataclasses passed *between* pipeline stages (PageDocument,
     EvidenceItem, ...). These are internal and ergonomic.
  2. The OpenAI Structured-Outputs JSON schema used for the per-page LLM pass
     (PAGE_EXTRACTION_SCHEMA). Strict mode: every property listed in
     `required`, `additionalProperties` false, optionals expressed as nullable.

Everything an extracted fact carries — value, confidence, evidence snippet, and
source URL — is preserved so the ABI layer (Goal 03) can explain every score.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = "2.0"

# ---------------------------------------------------------------------------
# Page-level structures (stage 1: crawl + clean)
# ---------------------------------------------------------------------------

PAGE_CATEGORIES = [
    "home", "services", "service_detail", "about", "contact",
    "faq", "reviews", "pricing", "location", "blog", "unknown",
]


@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Link:
    text: str
    href: str


@dataclass
class PageDocument:
    """One crawled, cleaned page. The unit the pipeline operates on."""
    url: str
    title: str
    markdown: str
    headings: list[Heading] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)  # description, lang, json_ld, og
    category: str = "unknown"

    def heading_texts(self) -> list[str]:
        return [h.text for h in self.headings]


# ---------------------------------------------------------------------------
# Evidence-bearing facts (stages 3-7)
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    """An extracted value with provenance and a reliability score."""
    value: str
    confidence: float = 0.0
    evidence: str = ""
    source_url: str = ""
    confidence_reason: str = ""
    extras: dict = field(default_factory=dict)  # e.g. {city, state} for locations

    def to_dict(self) -> dict:
        out = {
            "value": self.value,
            "confidence": round(self.confidence, 2),
            "evidence": self.evidence,
            "source_url": self.source_url,
            "confidence_reason": self.confidence_reason,
        }
        if self.extras:
            out.update(self.extras)
        return out


# ---------------------------------------------------------------------------
# Per-page LLM extraction schema (stage 4) — OpenAI Structured Outputs
# ---------------------------------------------------------------------------

def _evidence_array(extra_props: dict | None = None) -> dict:
    """An array of {value, evidence, confidence} objects (+ optional extras)."""
    props = {
        "value": {"type": "string"},
        "evidence": {"type": "string"},
        "confidence": {"type": "number"},
    }
    required = ["value", "evidence", "confidence"]
    if extra_props:
        props.update(extra_props)
        required = list(props.keys())
    return {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": props,
            "required": required,
        },
    }


PAGE_EXTRACTION_SCHEMA = {
    "name": "page_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "business_name": {"type": ["string", "null"]},
            "industry": {"type": ["string", "null"]},
            "services": _evidence_array(),
            "service_areas": _evidence_array(),
            "locations": _evidence_array({
                "city": {"type": ["string", "null"]},
                "state": {"type": ["string", "null"]},
                "address": {"type": ["string", "null"]},
            }),
            "faqs": _evidence_array({"answer": {"type": "string"}}),
            "offers": _evidence_array({"details": {"type": ["string", "null"]}}),
            "trust_signals": _evidence_array(),
            "ctas": _evidence_array({"cta_type": {"type": "string"}}),
            "contact_information": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "phone": {"type": ["string", "null"]},
                    "email": {"type": ["string", "null"]},
                    "address": {"type": ["string", "null"]},
                    "hours": {"type": ["string", "null"]},
                    "booking_url": {"type": ["string", "null"]},
                },
                "required": ["phone", "email", "address", "hours", "booking_url"],
            },
        },
        "required": [
            "business_name", "industry", "services", "service_areas",
            "locations", "faqs", "offers", "trust_signals", "ctas",
            "contact_information",
        ],
    },
}

CONTACT_FIELDS = ["phone", "email", "address", "hours", "booking_url"]


# ---------------------------------------------------------------------------
# Site-level profile contract (output of stages 6-8)
# ---------------------------------------------------------------------------

PROFILE_FIELDS = [
    "schema_version", "business_name", "industry", "services", "service_areas",
    "locations", "faqs", "offers", "trust_signals", "ctas",
    "contact_information", "source_pages",
]
EVIDENCE_LIST_FIELDS = ["services", "service_areas", "locations", "faqs",
                        "offers", "trust_signals", "ctas"]


class SchemaError(ValueError):
    """Raised when a profile does not match the stable profile contract."""


def validate_profile(data: object) -> dict:
    """Validate a merged profile against the stable contract; return unchanged.

    Checks top-level keys, contact fields, and that every evidence item carries
    value/confidence/evidence/source_url — the provenance the ABI layer needs.
    """
    if not isinstance(data, dict):
        raise SchemaError("profile must be an object")
    missing = set(PROFILE_FIELDS) - set(data)
    if missing:
        raise SchemaError(f"missing profile keys: {sorted(missing)}")

    for field_name in EVIDENCE_LIST_FIELDS:
        items = data[field_name]
        if not isinstance(items, list):
            raise SchemaError(f"{field_name} must be a list")
        for item in items:
            if not isinstance(item, dict):
                raise SchemaError(f"{field_name} items must be objects")
            for key in ("value", "confidence", "evidence", "source_url"):
                if key not in item:
                    raise SchemaError(f"{field_name} item missing '{key}'")
            if not isinstance(item["confidence"], (int, float)):
                raise SchemaError(f"{field_name}.confidence must be numeric")

    contact = data["contact_information"]
    if not isinstance(contact, dict) or set(contact) != set(CONTACT_FIELDS):
        raise SchemaError(f"contact_information must have exactly {CONTACT_FIELDS}")
    return data


def empty_page_extraction() -> dict:
    """A schema-valid empty per-page LLM payload (safe fallback)."""
    return {
        "business_name": None,
        "industry": None,
        "services": [],
        "service_areas": [],
        "locations": [],
        "faqs": [],
        "offers": [],
        "trust_signals": [],
        "ctas": [],
        "contact_information": {k: None for k in CONTACT_FIELDS},
    }
