"""Stable JSON schema for semantic extraction (Goal 02).

The schema is the contract for everything downstream (ABI scoring, dashboard),
so it is defined explicitly here rather than inferred from a model class. It is
used two ways:

  1. As an OpenAI Structured Outputs `json_schema` (strict mode) so the model
     is *forced* to return conforming JSON.
  2. As a local validator so we can prove schema stability across many sites
     without trusting the provider.

Goal 02 required fields: services, locations, faqs, contact_information, offers.
business_name and service_areas are included as useful, low-cost extras
(both appear in the PRD extraction list).

Strict-mode rules followed below: every object lists all properties in
`required`, `additionalProperties` is false, and optional values are expressed
as nullable types (e.g. ["string", "null"]) rather than omitted keys.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0"

# Top-level keys, in canonical order. Used by the validator and reporting.
TOP_LEVEL_FIELDS = [
    "business_name",
    "services",
    "locations",
    "service_areas",
    "faqs",
    "contact_information",
    "offers",
]

CONTACT_FIELDS = ["phone", "email", "address", "hours", "booking_url"]

# The JSON Schema passed to OpenAI Structured Outputs (response_format).
EXTRACTION_JSON_SCHEMA = {
    "name": "business_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "business_name": {"type": ["string", "null"]},
            "services": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": ["string", "null"]},
                    },
                    "required": ["name", "description"],
                },
            },
            "locations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": ["string", "null"]},
                        "city": {"type": ["string", "null"]},
                        "state": {"type": ["string", "null"]},
                        "address": {"type": ["string", "null"]},
                    },
                    "required": ["name", "city", "state", "address"],
                },
            },
            "service_areas": {
                "type": "array",
                "items": {"type": "string"},
            },
            "faqs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                    },
                    "required": ["question", "answer"],
                },
            },
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
                "required": CONTACT_FIELDS,
            },
            "offers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "details": {"type": ["string", "null"]},
                    },
                    "required": ["title", "details"],
                },
            },
        },
        "required": TOP_LEVEL_FIELDS,
    },
}


class SchemaError(ValueError):
    """Raised when an extraction payload does not match the stable schema."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SchemaError(message)


def validate_extraction(data: object) -> dict:
    """Validate a payload against the stable schema; return it unchanged.

    Lightweight, dependency-free structural validation. Mirrors the JSON
    schema above so schema stability can be asserted offline and in tests.
    """
    _check(isinstance(data, dict), "extraction must be an object")
    assert isinstance(data, dict)  # for type checkers

    extra = set(data) - set(TOP_LEVEL_FIELDS)
    _check(not extra, f"unexpected top-level keys: {sorted(extra)}")
    missing = set(TOP_LEVEL_FIELDS) - set(data)
    _check(not missing, f"missing top-level keys: {sorted(missing)}")

    _check(data["business_name"] is None or isinstance(data["business_name"], str),
           "business_name must be string or null")

    _check(isinstance(data["services"], list), "services must be a list")
    for s in data["services"]:
        _check(isinstance(s, dict) and set(s) == {"name", "description"},
               "each service must have exactly {name, description}")
        _check(isinstance(s["name"], str), "service.name must be a string")
        _check(s["description"] is None or isinstance(s["description"], str),
               "service.description must be string or null")

    _check(isinstance(data["locations"], list), "locations must be a list")
    for loc in data["locations"]:
        _check(isinstance(loc, dict) and set(loc) == {"name", "city", "state", "address"},
               "each location must have exactly {name, city, state, address}")

    _check(isinstance(data["service_areas"], list), "service_areas must be a list")
    for area in data["service_areas"]:
        _check(isinstance(area, str), "service_areas items must be strings")

    _check(isinstance(data["faqs"], list), "faqs must be a list")
    for f in data["faqs"]:
        _check(isinstance(f, dict) and set(f) == {"question", "answer"},
               "each faq must have exactly {question, answer}")
        _check(isinstance(f["question"], str) and isinstance(f["answer"], str),
               "faq question/answer must be strings")

    contact = data["contact_information"]
    _check(isinstance(contact, dict) and set(contact) == set(CONTACT_FIELDS),
           f"contact_information must have exactly {CONTACT_FIELDS}")
    for key in CONTACT_FIELDS:
        _check(contact[key] is None or isinstance(contact[key], str),
               f"contact_information.{key} must be string or null")

    _check(isinstance(data["offers"], list), "offers must be a list")
    for o in data["offers"]:
        _check(isinstance(o, dict) and set(o) == {"title", "details"},
               "each offer must have exactly {title, details}")
        _check(isinstance(o["title"], str), "offer.title must be a string")

    return data


def empty_extraction() -> dict:
    """A schema-valid, fully-empty extraction (used as a safe fallback)."""
    return {
        "business_name": None,
        "services": [],
        "locations": [],
        "service_areas": [],
        "faqs": [],
        "contact_information": {k: None for k in CONTACT_FIELDS},
        "offers": [],
    }
