"""ProPlan ABI — Goal 02 semantic extraction package.

LLM-based extraction of business profile fields (services, locations, FAQs,
contact information, offers) from crawled markdown, with a stable JSON schema.
"""

from .extract import ExtractionResult, extract_from_markdown
from .engine import SiteExtraction, crawl_and_extract, extract_site_from_output
from .schema import (
    EXTRACTION_JSON_SCHEMA,
    SCHEMA_VERSION,
    SchemaError,
    empty_extraction,
    validate_extraction,
)

__all__ = [
    "ExtractionResult",
    "extract_from_markdown",
    "SiteExtraction",
    "crawl_and_extract",
    "extract_site_from_output",
    "EXTRACTION_JSON_SCHEMA",
    "SCHEMA_VERSION",
    "SchemaError",
    "empty_extraction",
    "validate_extraction",
]
