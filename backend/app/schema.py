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


# --- ABI scoring contract (single source of truth) -------------------------
# Weights follow the PRD's ABI Framework (Understanding 25 / Retrieval 25 /
# Recommendation 20 / Agent Readiness 15 / Semantic Authority 15). They live
# here, not in the scorer, so the validator can enforce them and the scorer
# imports them — one definition, no drift.
#
# ABI_VERSION is the FROZEN measurement-instrument version. As of v0.1.1 the
# scoring dimensions, weights, grade bands, extraction contracts, and provenance
# taxonomy are frozen: no changes without a benchmark review (see
# abi_spec_v0.1.1.md). `tests/test_abi_freeze.py` enforces this — bumping any
# frozen value fails that test until ABI_VERSION and the spec are updated together.
ABI_VERSION = "0.1.1"

ABI_DIMENSIONS = [
    "ai_understanding", "ai_retrieval", "ai_recommendation",
    "agent_readiness", "semantic_authority",
]

ABI_DIMENSION_WEIGHTS = {
    "ai_understanding": 0.25,
    "ai_retrieval": 0.25,
    "ai_recommendation": 0.20,
    "agent_readiness": 0.15,
    "semantic_authority": 0.15,
}

# (lower_bound, grade, label) — highest band first.
ABI_GRADE_BANDS = [
    (90, "A", "AI-Optimized"),
    (75, "B", "AI-Ready"),
    (60, "C", "Partially Visible"),
    (40, "D", "Low Visibility"),
    (0, "F", "Invisible to AI"),
]


def abi_grade_for(score: float) -> tuple[str, str]:
    """Map a 0-100 score to its (letter, label) band. Contract-level so the
    scorer and the validator agree on grade boundaries."""
    for lower, letter, label in ABI_GRADE_BANDS:
        if score >= lower:
            return letter, label
    return "F", "Invisible to AI"


def validate_abi_score(data: object) -> dict:
    """Validate an ABI score block against its contract; return unchanged.

    A scoring contract must fail loudly on bad or stale output, so this checks
    not just shape but arithmetic: dimension weights match the canonical set and
    sum to 1, every criterion's earned/max are numeric and bounded, the grade
    matches the overall score, and overall equals the weighted average of the
    dimension scores. This is what lets the dashboard treat abi_score.json as a
    stable product contract.
    """
    tol = 0.6  # rounding slack (dimension scores + overall are each rounded)
    if not isinstance(data, dict):
        raise SchemaError("abi_score must be an object")
    for key in ("overall", "grade", "grade_label", "dimensions",
                "top_recommendations", "summary"):
        if key not in data:
            raise SchemaError(f"abi_score missing '{key}'")
    overall = data["overall"]
    if not isinstance(overall, (int, float)) or not 0 <= overall <= 100:
        raise SchemaError("abi_score.overall must be a number in [0, 100]")

    # Grade must match the overall score per the canonical bands.
    exp_letter, exp_label = abi_grade_for(overall)
    if data["grade"] != exp_letter:
        raise SchemaError(
            f"grade {data['grade']!r} does not match overall {overall} "
            f"(expected {exp_letter!r})")
    if data["grade_label"] != exp_label:
        raise SchemaError(
            f"grade_label {data['grade_label']!r} does not match overall {overall}")

    dims = data["dimensions"]
    if not isinstance(dims, dict) or set(dims) != set(ABI_DIMENSIONS):
        raise SchemaError(f"abi_score.dimensions must have exactly {ABI_DIMENSIONS}")

    weighted_sum = 0.0
    weight_total = 0.0
    for name, dim in dims.items():
        if not isinstance(dim, dict):
            raise SchemaError(f"dimension {name} must be an object")
        for key in ("score", "weight", "grade", "criteria"):
            if key not in dim:
                raise SchemaError(f"dimension {name} missing '{key}'")
        if not isinstance(dim["score"], (int, float)) or not 0 <= dim["score"] <= 100:
            raise SchemaError(f"dimension {name}.score must be in [0, 100]")
        # Weight must match the canonical contract exactly.
        if abs(dim["weight"] - ABI_DIMENSION_WEIGHTS[name]) > 1e-9:
            raise SchemaError(
                f"dimension {name}.weight {dim['weight']} != contract "
                f"{ABI_DIMENSION_WEIGHTS[name]}")
        if dim["grade"] != abi_grade_for(dim["score"])[0]:
            raise SchemaError(f"dimension {name}.grade does not match its score")
        if not isinstance(dim["criteria"], list) or not dim["criteria"]:
            raise SchemaError(f"dimension {name}.criteria must be a non-empty list")
        crit_max = crit_earned = 0.0
        for c in dim["criteria"]:
            for key in ("name", "earned", "max", "rationale"):
                if key not in c:
                    raise SchemaError(f"{name} criterion missing '{key}'")
            if not isinstance(c["earned"], (int, float)) or not isinstance(c["max"], (int, float)):
                raise SchemaError(f"{name} criterion earned/max must be numeric")
            if c["max"] <= 0 or not -1e-6 <= c["earned"] <= c["max"] + 1e-6:
                raise SchemaError(
                    f"{name} criterion '{c['name']}' earned {c['earned']} "
                    f"out of bounds [0, {c['max']}]")
            crit_max += c["max"]
            crit_earned += c["earned"]
        # Dimension score must be the criteria's earned/max as a percentage.
        exp_dim = round(crit_earned / crit_max * 100, 1) if crit_max else 0.0
        if abs(dim["score"] - exp_dim) > tol:
            raise SchemaError(
                f"dimension {name}.score {dim['score']} != criteria %% {exp_dim}")
        weighted_sum += dim["score"] * dim["weight"]
        weight_total += dim["weight"]

    if abs(weight_total - 1.0) > 1e-9:
        raise SchemaError(f"dimension weights sum to {weight_total}, not 1.0")
    if abs(overall - weighted_sum) > tol:
        raise SchemaError(
            f"overall {overall} != weighted average {round(weighted_sum, 1)}")

    if not isinstance(data["top_recommendations"], list):
        raise SchemaError("abi_score.top_recommendations must be a list")
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
