"""Offline unit tests for the extraction schema, validator, and input prep.

No network / no OpenAI calls — these verify the schema contract and the local
guards that keep schema stability independent of the provider.
"""

import json

import pytest

from backend.extraction.schema import (
    EXTRACTION_JSON_SCHEMA,
    TOP_LEVEL_FIELDS,
    SchemaError,
    empty_extraction,
    validate_extraction,
)
from backend.extraction.extract import MAX_INPUT_CHARS, _prepare_input


def _valid_payload() -> dict:
    return {
        "business_name": "Acme HVAC",
        "services": [{"name": "AC Repair", "description": "Fast repairs"},
                     {"name": "Furnace Install", "description": None}],
        "locations": [{"name": "HQ", "city": "Dallas", "state": "TX",
                       "address": "1 Main St"}],
        "service_areas": ["Dallas", "Fort Worth"],
        "faqs": [{"question": "Do you offer financing?", "answer": "Yes."}],
        "contact_information": {"phone": "555-1234", "email": None,
                                "address": "1 Main St", "hours": "24/7",
                                "booking_url": None},
        "offers": [{"title": "$50 off", "details": "First-time customers"}],
    }


def test_empty_extraction_is_valid():
    data = empty_extraction()
    assert validate_extraction(data) is data
    assert set(data) == set(TOP_LEVEL_FIELDS)


def test_full_payload_validates():
    payload = _valid_payload()
    assert validate_extraction(payload) is payload


def test_missing_top_level_key_rejected():
    payload = _valid_payload()
    del payload["offers"]
    with pytest.raises(SchemaError):
        validate_extraction(payload)


def test_unexpected_top_level_key_rejected():
    payload = _valid_payload()
    payload["random"] = 1
    with pytest.raises(SchemaError):
        validate_extraction(payload)


def test_service_must_have_exact_keys():
    payload = _valid_payload()
    payload["services"][0] = {"name": "AC Repair"}  # missing description
    with pytest.raises(SchemaError):
        validate_extraction(payload)


def test_contact_must_have_all_fields():
    payload = _valid_payload()
    payload["contact_information"].pop("booking_url")
    with pytest.raises(SchemaError):
        validate_extraction(payload)


def test_service_area_items_must_be_strings():
    payload = _valid_payload()
    payload["service_areas"] = [{"city": "Dallas"}]
    with pytest.raises(SchemaError):
        validate_extraction(payload)


def test_non_dict_rejected():
    with pytest.raises(SchemaError):
        validate_extraction(["not", "a", "dict"])


def test_openai_schema_is_strict_and_serializable():
    # Strict mode + JSON-serializable are required for Structured Outputs.
    assert EXTRACTION_JSON_SCHEMA["strict"] is True
    assert EXTRACTION_JSON_SCHEMA["schema"]["additionalProperties"] is False
    json.dumps(EXTRACTION_JSON_SCHEMA)  # must not raise


def test_input_truncation():
    short = "hello"
    text, truncated = _prepare_input(short)
    assert text == "hello" and truncated is False

    long = "x" * (MAX_INPUT_CHARS + 100)
    text, truncated = _prepare_input(long)
    assert len(text) == MAX_INPUT_CHARS and truncated is True
