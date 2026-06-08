# Goal 03D — Calibration Test Cases

Concrete, offline, deterministic tests for the three pillars. Written to **drop
into `backend/tests/` when implementation begins** (one file per pillar). Until
the code lands they are the executable specification of "correct"; after it
lands they are the regression suite. No network, no LLM — every case is a pure
function over fixtures.

Each pillar's acceptance bar (from [calibration_plan.md §5](calibration_plan.md))
is encoded below.

---

## Pillar 1 — `backend/tests/test_faq_validator.py`

Targets `faq_validator.validate_faq`. The five real ProPlan fakes must be
rejected; genuine Q/A pairs must survive; schema-sourced FAQs are trusted.
(Authoritative copy lives in
[faq_validation_plan.md §10](faq_validation_plan.md); reproduced here so the
03D suite is self-contained.)

```python
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
```

**Integration (in `test_pipeline.py`):**

```python
def test_build_profile_drops_markdown_fakes_on_non_faq_page():
    # A non-FAQ marketing page whose only "?"-lines are the ProPlan fakes
    # yields zero FAQs after the Layer A + Layer B gates.
    profile = build_profile(... fakes on a category!="faq" page ...)
    assert profile["faqs"] == []

def test_build_profile_keeps_schema_faqpage():
    # A page with a real FAQPage JSON-LD keeps its FAQs intact.
    profile = build_profile(... schema FAQPage ...)
    assert len(profile["faqs"]) >= 1

def test_has_faq_context():
    assert _has_faq_context(page(category="faq")) is True
    assert _has_faq_context(page(headings=["Frequently Asked Questions"])) is True
    assert _has_faq_context(page(category="home", markdown="Book a call")) is False
```

---

## Pillar 3 — `backend/tests/test_confidence_aware_scoring.py`

Targets the confidence-aware formulas in
[abi_score.py](backend/app/services/abi_score.py). These assert the **new**
behavior and will fail until Pillar 3 lands — that is intended.

```python
"""Confidence-aware scoring (Goal 03D, Pillar 3).

earned = max * evidence * _conf_factor(conf), _conf_factor = min(1, conf/0.7).
Genuinely confident facts (>= 0.7) are unaffected; weak evidence is discounted.
"""
import pytest
from backend.app.services.abi_score import score_abi, _conf_factor, _eff_count


def _profile(**over):
    base = {
        "schema_version": "2.0", "business_name": "X", "industry": "HVAC",
        "services": [], "service_areas": [], "locations": [], "faqs": [],
        "offers": [], "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                                "hours": None, "booking_url": None},
        "source_pages": [],
    }
    base.update(over)
    return base


def _loc(conf):
    return {"value": "Austin, TX", "confidence": conf, "evidence": "...",
            "source_url": "https://x.com/", "confidence_reason": "single mention",
            "city": "Austin", "state": "TX"}


def _crit(score, dim, name):
    return next(c for c in score["dimensions"][dim]["criteria"] if c["name"] == name)


# --- the confidence factor itself ---
def test_conf_factor_saturates_and_discounts():
    assert _conf_factor(0.9) == 1.0
    assert _conf_factor(0.7) == 1.0
    assert _conf_factor(0.15) == pytest.approx(0.214, abs=0.01)
    assert _conf_factor(0.0) == 0.0


# --- THE FLAGSHIP BUG: Austin, TX @ 0.15 must NOT score 20/20 ---
def test_low_confidence_location_is_not_full_marks():
    score = score_abi(_profile(locations=[_loc(0.15)]))
    earned = _crit(score, "ai_understanding", "Location presence")["earned"]
    assert earned < 8.0           # was 20/20 — the documented #5 defect
    assert 3.5 <= earned <= 5.0   # 20 * _conf_factor(0.15) ~= 4.3


def test_high_confidence_location_earns_full_marks():
    score = score_abi(_profile(locations=[_loc(0.9)]))
    earned = _crit(score, "ai_understanding", "Location presence")["earned"]
    assert earned == 20.0         # confident evidence is NOT penalized


def test_structured_address_string_earns_strong_location_credit():
    p = _profile()
    p["contact_information"]["address"] = "100 Main St, Austin, TX"
    score = score_abi(p)
    earned = _crit(score, "ai_understanding", "Location presence")["earned"]
    assert earned >= 18.0         # a real address string is high-trust


# --- effective count: weak items contribute fractionally ---
def test_eff_count_discounts_low_confidence_items():
    weak = [{"confidence": 0.14, "value": f"svc{i}"} for i in range(10)]
    strong = [{"confidence": 0.9, "value": f"svc{i}"} for i in range(10)]
    assert _eff_count(weak) == pytest.approx(2.0, abs=0.1)   # 10 * 0.2
    assert _eff_count(strong) == pytest.approx(10.0, abs=0.1)


def test_offers_count_is_confidence_weighted():
    # Four low-confidence "offers" no longer max the 2-target criterion.
    offers = [{"value": f"Pkg {i}", "confidence": 0.3, "evidence": "",
               "source_url": "", "confidence_reason": ""} for i in range(4)]
    score = score_abi(_profile(offers=offers))
    earned = _crit(score, "ai_recommendation", "Offers & incentives")["earned"]
    assert earned < 20.0          # 4 * _conf_factor(0.3)=0.43 -> 1.7/2 -> ~17


# --- regression guard: high-confidence sites are NOT penalized ---
def test_high_confidence_profile_unaffected_by_confidence_weighting():
    def ev(v, conf=0.9):
        return {"value": v, "confidence": conf, "evidence": "...",
                "source_url": "https://x.com/", "confidence_reason": "schema.org"}
    p = _profile(
        business_name="Acme HVAC", industry="HVAC",
        services=[ev(f"S{i}") for i in range(8)],
        trust_signals=[ev(f"T{i}") for i in range(5)],
        ctas=[ev("Book"), ev("Call"), ev("Quote")],
    )
    score = score_abi(p)
    # All these criteria saturate at conf 0.9 -> full marks, as before.
    assert _crit(score, "ai_understanding", "Service coverage")["earned"] == 30.0
    assert _crit(score, "ai_recommendation", "Trust signals")["earned"] == 40.0
    assert _crit(score, "agent_readiness", "Calls to action")["earned"] == 15.0
```

> **Fixture note for `test_abi_score.py`:** `_rich_profile()` uses conf 0.9, so
> `_conf_factor` returns 1.0 and every count/location criterion is unchanged —
> `test_rich_profile_scores_high_and_validates` (`overall >= 85`) should still
> pass. If FAQ-count weighting nudges it, lower the assertion to `>= 83` (per the
> §5 acceptance bar) rather than inflating the fixture.

---

## Pillar 2 — `backend/tests/test_actionability.py`

Targets `actionability.detect_actionability` and the graduated booking
criterion. Uses tiny in-memory `PageDocument`s; no crawl. (Validation plan:
[agent_actionability_model.md §8](agent_actionability_model.md).)

```python
"""Agent-actionability detection (Goal 03D, Pillar 2)."""
import pytest
from backend.app.schema import Link, PageDocument
from backend.app.services.actionability import detect_actionability


def _doc(links=(), ctas=(), json_ld=None):
    d = PageDocument(url="https://x.com/", title="X", markdown="")
    d.links = [Link(text=t, href=h) for t, h in links]
    d.metadata = {"json_ld": json_ld} if json_ld else {}
    return d


def _profile(ctas=(), booking_url=None, phone=None, email=None):
    return {
        "ctas": [{"value": v, "cta_type": t, "confidence": 0.7,
                  "evidence": "", "source_url": "", "confidence_reason": ""}
                 for v, t in ctas],
        "contact_information": {"phone": phone, "email": email, "address": None,
                                "hours": None, "booking_url": booking_url},
    }


# --- THE FLAGSHIP BUG: a real Calendly link must be detected (was 0/20) ---
def test_calendly_link_detected_as_t3():
    docs = [_doc(links=[("View Available Times",
                         "https://calendly.com/proplansolutions")])]
    result = detect_actionability(docs, _profile(ctas=[("Book a call", "book")]))
    assert result["booking"]["tier"] == "T3"
    assert "calendly.com" in result["booking"]["evidence"]


@pytest.mark.parametrize("host", [
    "https://cal.com/acme", "https://meetings.hubspot.com/acme",
    "https://acme.acuityscheduling.com",
])
def test_known_schedulers_are_t3(host):
    result = detect_actionability([_doc(links=[("Book", host)])], _profile())
    assert result["booking"]["tier"] == "T3"


def test_potential_action_schema_is_t3():
    jld = {"@type": "LocalBusiness",
           "potentialAction": {"@type": "ReserveAction",
                               "target": "https://x.com/book"}}
    result = detect_actionability([_doc(json_ld=jld)], _profile())
    assert result["booking"]["tier"] == "T3"


def test_contact_form_is_t2():
    docs = [_doc(links=[("Request service", "https://x.com/request-service")])]
    result = detect_actionability(docs, _profile(ctas=[("Get a quote", "contact")]))
    assert result["booking"]["tier"] in ("T2", "T1")  # form, not a scheduler


def test_unresolved_book_cta_is_t1_intent():
    # A booking CTA with no resolvable scheduler link = intent only.
    result = detect_actionability([_doc()], _profile(ctas=[("Book a call", "book")]))
    assert result["booking"]["tier"] == "T1"


def test_no_action_channel_is_t0():
    result = detect_actionability([_doc()], _profile())
    assert result["booking"]["tier"] == "T0"


def test_generic_path_does_not_false_positive_to_t3():
    # /get-started without a scheduler host must not be mistaken for T3.
    docs = [_doc(links=[("Get started", "https://x.com/get-started")])]
    result = detect_actionability(docs, _profile())
    assert result["booking"]["tier"] != "T3"
```

**Graduated booking criterion (in `test_abi_score.py` once wired):**

```python
@pytest.mark.parametrize("tier,expected", [("T3", 20), ("T2", 12),
                                           ("T1", 6), ("T0", 0)])
def test_booking_criterion_is_graduated(tier, expected):
    p = _empty_profile()
    p["actionability"] = {"booking": {"tier": tier, "evidence": "..."}}
    score = score_abi(p)
    crit = next(c for c in score["dimensions"]["agent_readiness"]["criteria"]
                if c["name"] == "Online booking")
    assert crit["earned"] == expected
    if tier != "T0":
        assert crit["evidence"]            # every credit names its evidence
```

---

## Coverage map (test → acceptance criterion)

| Acceptance bar ([plan §5](calibration_plan.md)) | Test(s) |
|---|---|
| ProPlan reports 0 FAQs | `test_rejects_proplan_marketing_fragments`, `test_build_profile_drops_markdown_fakes_on_non_faq_page` |
| No real / schema FAQ lost | `test_accepts_genuine_faqs`, `test_schema_source_is_trusted`, `test_build_profile_keeps_schema_faqpage` |
| Low-confidence location < 8/20 (not 20/20) | `test_low_confidence_location_is_not_full_marks` |
| High-confidence facts not penalized | `test_high_confidence_location_earns_full_marks`, `test_high_confidence_profile_unaffected_by_confidence_weighting` |
| No criterion exceeds its max | existing `validate_abi_score` + `test_every_criterion_is_explainable` |
| Real booking → correct tier; phone-only → T1; none → T0 | `test_calendly_link_detected_as_t3`, `test_*_t2/t1/t0`, `test_booking_criterion_is_graduated` |
| Every booking credit names evidence | `test_calendly_link_detected_as_t3`, `test_booking_criterion_is_graduated` |
| Framework unchanged (weights/grades/contract) | existing `test_weights_match_prd`, `test_grade_bands`, validator tests |
```
