"""FAQ validity gate tests (Goal 03D, Pillar 1).

Deterministic, offline. The five real ProPlan fakes must be rejected; genuine
Q/A pairs must survive; schema-sourced FAQPage markup is trusted.
"""

import pytest

from backend.app.services.faq_validator import validate_faq

# --- the five real ProPlan fakes must all be rejected ---
PROPLAN_FAKES = [
    ("something real?", "Book a free strategy call. We'll map your biggest "
     "operational bottleneck and show you exactly how AI solves it."),
    ("your business?", "Stop wasting time on manual processes. Let's build "
     "automation that actually moves the needle starting this week."),
    ("in your business?", "Book a free strategy call and discover what AI "
     "automation can do for your operations no commitment required."),
    ("Prefer to Talk First?", "Skip the form. Book a 15-minute intro call "
     "directly with our solutions team and let's get to the point."),
    ("Read moresuccess story?", "Let's discuss how AI automation can produce "
     "results like these in your business with a free strategy session."),
]


@pytest.mark.parametrize("q,a", PROPLAN_FAKES)
def test_rejects_proplan_marketing_fragments(q, a):
    ok, reason = validate_faq(q, a, source="markdown")
    assert ok is False and reason


REAL_FAQS = [
    ("Do you offer financing?",
     "Yes, we offer 0% financing for 12 months on qualifying systems."),
    ("How long does an AC installation take?",
     "A typical residential AC installation takes 4 to 8 hours depending on "
     "the size and complexity of the system."),
    ("Are you licensed and insured?",
     "Yes, we are fully licensed, bonded, and insured in North Carolina."),
]


@pytest.mark.parametrize("q,a", REAL_FAQS)
def test_accepts_genuine_faqs(q, a):
    ok, _ = validate_faq(q, a, source="markdown")
    assert ok is True


def test_requires_both_question_and_answer():
    assert validate_faq("Do you offer financing?", "", source="llm")[0] is False
    assert validate_faq("", "Yes we do, for 12 months.", source="llm")[0] is False


def test_rejects_too_short_answer():
    ok, reason = validate_faq("How long does install take?", "About a day.",
                              source="markdown")
    assert ok is False and "short" in reason


def test_rejects_cta_answer_even_with_valid_question():
    ok, reason = validate_faq("How do I get started?",
                              "Book a free strategy call today!", source="llm")
    assert ok is False and "call-to-action" in reason


@pytest.mark.parametrize("q", [
    "your business?", "something real?", "in your business?",
    "Read moresuccess story?", "FAQ?",
])
def test_rejects_fragment_questions(q):
    a = "This is a perfectly fine and sufficiently long explanatory answer here."
    assert validate_faq(q, a, source="markdown")[0] is False


def test_schema_source_is_trusted():
    ok, _ = validate_faq("Returns?",
                         "We accept returns within 30 days for a full refund.",
                         source="schema")
    assert ok is True


def test_schema_still_rejects_empty_answer():
    assert validate_faq("Returns?", "n/a", source="schema")[0] is False


def test_faq_section_real_pair_accepted():
    ok, _ = validate_faq("What areas do you serve?",
                         "We serve Charlotte, Concord, and the surrounding "
                         "Mecklenburg County area.", source="faq_section")
    assert ok is True
