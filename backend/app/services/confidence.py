"""Confidence scoring (stage 7).

Every merged fact gets a reliability score from multiple signals, not just the
LLM's self-report. High confidence: found in headings, on a relevant page,
repeated across pages, supported by schema.org. Low confidence: appears once,
buried in a blog, inferred by the LLM alone. The score ships with a
human-readable reason so ABI scores stay explainable.
"""

from __future__ import annotations

from dataclasses import dataclass

# Page categories where a service/area mention is meaningful (vs. a blog aside).
RELEVANT_CATEGORIES = {"home", "services", "service_detail", "location", "contact", "about"}


@dataclass
class Signals:
    llm_confidence: float = 0.0
    in_headings: bool = False
    in_nav: bool = False
    schema_supported: bool = False
    page_count: int = 1                 # how many pages mention it
    on_relevant_page: bool = False
    from_blog_only: bool = False


def score(signals: Signals) -> tuple[float, str]:
    """Return (confidence in [0.05, 1.0], reason)."""
    value = 0.0
    reasons: list[str] = []

    if signals.schema_supported:
        value += 0.35
        reasons.append("supported by schema.org markup")
    if signals.in_headings:
        value += 0.20
        reasons.append("appears in page headings")
    if signals.in_nav:
        value += 0.15
        reasons.append("appears in site navigation")
    if signals.on_relevant_page:
        value += 0.15
        reasons.append("found on a relevant page")
    if signals.page_count >= 2:
        bump = min(0.20, 0.10 * (signals.page_count - 1))
        value += bump
        reasons.append(f"repeated across {signals.page_count} pages")

    # LLM is a contributor, not the decider.
    value += 0.25 * max(0.0, min(1.0, signals.llm_confidence))
    if signals.llm_confidence >= 0.8:
        reasons.append("clearly stated in content")

    if signals.from_blog_only and not signals.schema_supported:
        value *= 0.6
        reasons.append("only found in blog content")

    if not reasons:
        reasons.append("single low-signal mention")

    value = max(0.05, min(1.0, value))
    return round(value, 2), "; ".join(reasons)


def label(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"
