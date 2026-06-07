"""LLM-based semantic extraction via OpenAI Structured Outputs.

Takes clean markdown (from the Goal 01 crawler) and returns a schema-valid
business profile. Structured Outputs (strict json_schema) guarantees the
shape; we additionally validate locally so schema stability never depends on
trusting the provider.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from openai import OpenAI

from .schema import EXTRACTION_JSON_SCHEMA, empty_extraction, validate_extraction

DEFAULT_MODEL = "gpt-4o-mini"

# Cap input so cost/latency stay bounded. ~48k chars ≈ ~12k tokens, plenty for
# a multi-page service-business site once nav/footer noise is already stripped.
MAX_INPUT_CHARS = 48_000

SYSTEM_PROMPT = (
    "You extract structured business information from website content for a "
    "local service business (e.g. HVAC, plumbing, electrical).\n"
    "Rules:\n"
    "- Extract ONLY information explicitly present in the provided content.\n"
    "- Never invent, guess, or infer values that are not stated.\n"
    "- If a field is not present, use null (for scalars) or an empty list.\n"
    "- 'services' are offerings the business performs (e.g. 'AC Repair').\n"
    "- 'locations' are physical offices/branches; 'service_areas' are cities or "
    "regions served (names only).\n"
    "- 'faqs' must be genuine question/answer pairs found in the content.\n"
    "- 'offers' are promotions/specials/discounts/financing deals.\n"
    "- Deduplicate. Keep values concise and verbatim where possible."
)


@dataclass
class ExtractionResult:
    data: dict
    model: str
    prompt_tokens: int
    completion_tokens: int
    input_chars: int
    truncated: bool
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def _prepare_input(markdown: str) -> tuple[str, bool]:
    text = markdown.strip()
    if len(text) <= MAX_INPUT_CHARS:
        return text, False
    return text[:MAX_INPUT_CHARS], True


def extract_from_markdown(
    markdown: str,
    *,
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
    source_url: str | None = None,
) -> ExtractionResult:
    """Extract a schema-valid business profile from markdown.

    Errors (API/parse/validation) are captured on the result with a
    schema-valid empty payload, so a batch run never aborts on one site.
    """
    client = client or OpenAI()
    text, truncated = _prepare_input(markdown)

    if not text:
        return ExtractionResult(
            data=empty_extraction(), model=model, prompt_tokens=0,
            completion_tokens=0, input_chars=0, truncated=False,
            error="empty input",
        )

    context = f"Source URL: {source_url}\n\n" if source_url else ""
    user_content = (
        f"{context}Extract the business profile from the website content below.\n\n"
        f"---\n{text}\n---"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,  # determinism -> repeatable, stable outputs
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": EXTRACTION_JSON_SCHEMA,
            },
        )
    except Exception as exc:  # noqa: BLE001 - capture API failure, keep batch alive
        return ExtractionResult(
            data=empty_extraction(), model=model, prompt_tokens=0,
            completion_tokens=0, input_chars=len(text), truncated=truncated,
            error=f"{type(exc).__name__}: {exc}",
        )

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    raw = response.choices[0].message.content or "{}"

    try:
        data = validate_extraction(json.loads(raw))
        error = None
    except Exception as exc:  # noqa: BLE001 - schema/JSON guard
        data = empty_extraction()
        error = f"validation: {type(exc).__name__}: {exc}"

    return ExtractionResult(
        data=data, model=response.model, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, input_chars=len(text),
        truncated=truncated, error=error,
    )
