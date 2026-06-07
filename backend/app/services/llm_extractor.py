"""LLM extraction pass (stage 4).

The LLM interprets *meaning* one page at a time (never the whole site at once),
returning evidence-bearing items under a strict schema. Rule-based facts are
passed in as grounding hints. Every item carries an `evidence` snippet and the
model's own `confidence`; the confidence engine (stage 7) reconciles that with
structural signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from openai import OpenAI

from backend.app.schema import PAGE_EXTRACTION_SCHEMA, PageDocument, empty_page_extraction
from backend.app.services.rule_extractor import RuleFacts

DEFAULT_MODEL = "gpt-4o-mini"
MAX_PAGE_CHARS = 16_000  # per-page cap keeps each call small and cheap

SYSTEM_PROMPT = (
    "You extract structured business information from a SINGLE web page of a "
    "local service business (HVAC, plumbing, electrical, etc.).\n"
    "Rules:\n"
    "- Extract ONLY what is explicitly on this page. Never invent or infer.\n"
    "- For every item, include a short verbatim `evidence` quote from the page "
    "and a `confidence` in [0,1] for how clearly the page states it.\n"
    "- 'services' = offerings performed (e.g. 'AC Repair').\n"
    "- 'service_areas' = cities/regions served (names only).\n"
    "- 'locations' = physical offices/branches (with city/state/address if shown).\n"
    "- 'faqs' = real question/answer pairs ('answer' field required).\n"
    "- 'offers' = promotions/specials/discounts/financing.\n"
    "- 'trust_signals' = guarantees, certifications, awards, years in business, "
    "licensing, insurance, BBB, review counts.\n"
    "- 'ctas' = calls to action; set 'cta_type' to one of call/book/quote/contact/form.\n"
    "- Use null / empty lists when something is absent. Deduplicate."
)


@dataclass
class PageExtraction:
    url: str
    category: str
    data: dict
    prompt_tokens: int = 0
    completion_tokens: int = 0
    error: str | None = None
    rule_facts: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def _hint_block(facts: RuleFacts | None) -> str:
    if not facts:
        return ""
    bits = []
    if facts.phones:
        bits.append(f"phones: {', '.join(facts.phones[:3])}")
    if facts.emails:
        bits.append(f"emails: {', '.join(facts.emails[:2])}")
    if facts.schema_org.get("name"):
        bits.append(f"schema.org name: {facts.schema_org['name']}")
    if facts.schema_org.get("address"):
        bits.append(f"schema.org address: {facts.schema_org['address']}")
    if not bits:
        return ""
    return ("Deterministic hints already found on this page (trust these for "
            "contact fields):\n- " + "\n- ".join(bits) + "\n\n")


def extract_page(
    doc: PageDocument,
    *,
    rule_facts: RuleFacts | None = None,
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
) -> PageExtraction:
    client = client or OpenAI()
    text = (doc.markdown or "").strip()[:MAX_PAGE_CHARS]
    if not text:
        return PageExtraction(url=doc.url, category=doc.category,
                              data=empty_page_extraction(), error="empty page")

    user = (
        f"Page URL: {doc.url}\n"
        f"Page category: {doc.category}\n"
        f"Page title: {doc.title}\n\n"
        f"{_hint_block(rule_facts)}"
        f"Extract the business information from this page content:\n\n---\n{text}\n---"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_schema", "json_schema": PAGE_EXTRACTION_SCHEMA},
        )
    except Exception as exc:  # noqa: BLE001
        return PageExtraction(url=doc.url, category=doc.category,
                              data=empty_page_extraction(),
                              error=f"{type(exc).__name__}: {exc}")

    import json
    usage = resp.usage
    try:
        data = json.loads(resp.choices[0].message.content or "{}")
    except ValueError as exc:
        return PageExtraction(url=doc.url, category=doc.category,
                              data=empty_page_extraction(),
                              prompt_tokens=usage.prompt_tokens if usage else 0,
                              completion_tokens=usage.completion_tokens if usage else 0,
                              error=f"json: {exc}")

    return PageExtraction(
        url=doc.url, category=doc.category, data=data,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        rule_facts=rule_facts.to_dict() if rule_facts else {},
    )
