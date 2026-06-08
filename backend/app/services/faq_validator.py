"""FAQ validity gate (Goal 03D, Pillar 1).

A real FAQ is a genuine question paired with an informative answer — not a
marketing fragment ending in '?' followed by a CTA. Without this gate the rule
extractor's markdown heuristic promotes any '?'-terminated line into an FAQ, so
sliced sentence-fragments ("something real?", "your business?") with CTA copy as
"answers" earned full marks across three ABI criteria.

This is a pure, deterministic filter — no LLM, no network. It runs at the single
FAQ merge choke point in `semantic_profile.build_profile`, source-aware:
schema.org FAQPage is the site's own declaration (trusted, length-only); every
other source (llm / faq_section / markdown) is validated hard.
"""

from __future__ import annotations

import re

# Tunable thresholds (declared, not magic numbers). The real defense against
# marketing fragments is the fragment-question + CTA-answer detection below, not
# these floors — so the floors stay low enough to admit legitimately terse but
# real FAQ answers ("Yes, fully licensed.") while still rejecting non-answers
# ("About a day."). Two-word fakes ("something real?") are caught by MIN_Q_WORDS.
MIN_Q_WORDS = 3
MIN_Q_CHARS = 12
MAX_Q_CHARS = 200
MIN_ANSWER_CHARS = 15
MIN_ANSWER_WORDS = 3
MIN_SCHEMA_ANSWER_CHARS = 20

# A CTA-style answer typically *opens* with an imperative ask.
CTA_START_VERBS = {"book", "schedule", "call", "contact", "get", "start",
                   "try", "sign", "request", "claim", "join", "let", "lets",
                   "skip", "stop", "discover", "unlock", "grab", "reach"}
CTA_PHRASES = ("book a call", "book a free", "book your", "strategy call",
               "intro call", "get started", "contact us", "sign up",
               "free consultation", "no commitment", "skip the form",
               "schedule a", "let's build", "let's talk", "let's discuss",
               "request a demo", "fill out the form", "reach out", "today",
               "this week", "free strategy")
NAV_GLUE = ("read more", "learn more", "click here", "see more", "view all")

_CAMEL_GLUE = re.compile(r"[a-z][A-Z]")


def validate_faq(question: str, answer: str, *, source: str = "unknown"
                 ) -> tuple[bool, str]:
    """Return (is_valid, reason).

    `source` ∈ {schema, faq_section, llm, markdown, unknown}. `schema` is the
    site's own FAQPage declaration — trusted, only guarded against an
    empty/trivial answer. Everything else is validated hard.
    """
    q = (question or "").strip()
    a = (answer or "").strip()
    if not q or not a:
        return False, "missing question or answer"
    if source == "schema":
        if len(a) < MIN_SCHEMA_ANSWER_CHARS:
            return False, "schema answer too short"
        return True, "ok"
    if not _is_question(q):
        return False, "question is a fragment / not a real question"
    return _answer_ok(a)


def _is_question(q: str) -> bool:
    if not q.endswith("?") or not (MIN_Q_CHARS <= len(q) <= MAX_Q_CHARS):
        return False
    if _looks_like_fragment(q) or _has_nav_glue(q):
        return False
    return True


def _looks_like_fragment(q: str) -> bool:
    first_alpha = next((c for c in q if c.isalpha()), "")
    if first_alpha and first_alpha.islower():   # "your business?", "in your…?"
        return True
    if len(q.split()) < MIN_Q_WORDS:            # "something real?" (2 words)
        return True
    return False


def _has_nav_glue(q: str) -> bool:
    low = q.lower()
    if any(g in low for g in NAV_GLUE):          # "Read moresuccess story?"
        return True
    return bool(_CAMEL_GLUE.search(q))           # camelCase concatenation glue


def _answer_ok(a: str) -> tuple[bool, str]:
    # CTA detection first: a "Book a call today!" answer is a call-to-action
    # whether it is short or long — report it as such, not merely "too short".
    if _is_cta_answer(a):
        return False, "answer is a call-to-action, not an explanation"
    if len(a) < MIN_ANSWER_CHARS or len(a.split()) < MIN_ANSWER_WORDS:
        return False, "answer too short"
    return True, "ok"


def _is_cta_answer(a: str) -> bool:
    low = a.lower()
    words = low.split()
    first = words[0].strip(".,!:'") if words else ""
    hits = sum(1 for p in CTA_PHRASES if p in low)
    if first in CTA_START_VERBS:                 # opens with an imperative ask
        return True
    if hits >= 2:                                # multiple CTA phrases
        return True
    if hits >= 1 and len(words) <= 25:           # short + CTA-flavoured
        return True
    return False
