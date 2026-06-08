# FAQ Validity Validation — Implementation Plan

**Status:** Design only. No production code changed. Tests below are written to
drop into `backend/tests/test_faq_validator.py` when implementation begins.

---

## 1. Problem & evidence

The rule extractor promotes any markdown line ending in `?` into an FAQ, on
**every** page, with no validity check. On `proplansolutions.io` this produced 5
fake FAQs that scored full marks in three criteria (Retrieval FAQ coverage 35/35,
FAQ answer quality 10/10, Authority knowledge depth 15/15 ≈ **+13.5 ABI** the
site did not earn):

| "question" | "answer" | defect |
|---|---|---|
| `something real?` | Book a free strategy call. We'll map your biggest… | fragment Q + CTA A |
| `your business?` | Stop wasting time on manual processes. Let's build… | fragment Q + CTA A |
| `in your business?` | Book a free strategy call and discover… | fragment Q + CTA A |
| `Prefer to Talk First?` | Skip the form. Book a 15-minute intro call… | CTA A |
| `Read moresuccess story?` | Let's discuss how AI automation… | nav-glue Q + CTA A |

**Root causes (two, independent):**
1. `rule_extractor._faq_from_markdown` runs on the markdown of *every* page and
   accepts any `?`-terminated line 8–200 chars, taking the next non-`?` line as
   the "answer" — so marketing/CTA blocks become Q/A pairs.
2. Nothing downstream validates question/answer quality. `semantic_profile`
   merges them and `abi_score` counts *items*, never inspecting validity.

---

## 2. Requirements → design mapping

| Requirement | Mechanism |
|---|---|
| FAQ must contain question **and** answer pair | `validate_faq` rejects unless both pass |
| Minimum answer length | `MIN_ANSWER_CHARS` + `MIN_ANSWER_WORDS` |
| Reject CTA-only answers | `_is_cta_answer` (CTA start-verbs + CTA phrases) |
| Reject heading fragments | `_looks_like_fragment` (lowercase start, word count) + `_has_nav_glue` |
| Prefer FAQPage schema.org | source tier `schema` → trusted (light validation) |
| Prefer explicit FAQ sections | restrict markdown heuristic to FAQ-context pages; source tier `faq_section` |

---

## 3. Design overview

Two layers, defense-in-depth:

**Layer A — restrict the markdown heuristic at the source.** `_faq_from_markdown`
only runs when the page is genuinely FAQ-context (classified `faq`, or its
markdown/headings contain an FAQ marker). This removes most garbage before it is
ever created. (For ProPlan this alone yields 0 markdown FAQs — correct, the site
has no FAQ.)

**Layer B — a validity gate at the single merge choke point.** A new
`faq_validator.validate_faq(question, answer, source)` filters **all** FAQ
candidates — schema, explicit FAQ section, LLM, and any surviving markdown — in
`semantic_profile.build_profile`, just before `_simple_evidence`. Source-aware
strictness: schema is trusted; everything else is validated hard.

No `abi_score` formula changes. The scoring criteria stay as-is; they simply
receive a clean `faqs[]` list. (Consequence: ProPlan's FAQ scores drop to 0,
which is the intended correction — see §8.)

---

## 4. New module: `backend/app/services/faq_validator.py`

```python
"""FAQ validity gate. A real FAQ is a genuine question paired with an
informative answer — not a marketing fragment ending in '?' followed by a CTA."""

# tunable thresholds (declared, not magic)
MIN_Q_WORDS = 4
MIN_Q_CHARS = 12
MAX_Q_CHARS = 200
MIN_ANSWER_CHARS = 40
MIN_ANSWER_WORDS = 8

INTERROGATIVES = {"how", "what", "why", "when", "where", "who", "which",
                  "can", "do", "does", "did", "is", "are", "was", "were",
                  "will", "would", "should", "could", "has", "have", "may",
                  "might", "should", "whats", "hows"}

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


def validate_faq(question: str, answer: str, *, source: str = "unknown"
                 ) -> tuple[bool, str]:
    """Return (is_valid, reason). `source` ∈ {schema, faq_section, llm,
    markdown, unknown}; `schema` is trusted and only length-checked."""
    q = (question or "").strip()
    a = (answer or "").strip()
    if not q or not a:
        return False, "missing question or answer"
    if source == "schema":
        # FAQPage markup is the site's own declaration — trust the question,
        # only guard against an empty/trivial answer.
        return (len(a) >= 20, "schema answer too short" if len(a) < 20 else "ok")
    if not _is_question(q):
        return False, "question is a fragment / not a real question"
    ok, why = _answer_ok(a)
    return (ok, why)


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
    import re
    return bool(re.search(r"[a-z][A-Z]", q))     # camelCase concatenation glue


def _answer_ok(a: str) -> tuple[bool, str]:
    if len(a) < MIN_ANSWER_CHARS or len(a.split()) < MIN_ANSWER_WORDS:
        return False, "answer too short"
    if _is_cta_answer(a):
        return False, "answer is a call-to-action, not an explanation"
    return True, "ok"


def _is_cta_answer(a: str) -> bool:
    low = a.lower()
    first = low.split()[0].strip(".,!:'") if low.split() else ""
    hits = sum(1 for p in CTA_PHRASES if p in low)
    if first in CTA_START_VERBS:                 # opens with an imperative ask
        return True
    if hits >= 2:                                # multiple CTA phrases
        return True
    if hits >= 1 and len(a.split()) <= 25:       # short + CTA-flavoured
        return True
    return False
```

---

## 5. Validation rules (precise)

**Question** (skipped for `schema` source):
- ends with `?`, length 12–200 chars;
- ≥ `MIN_Q_WORDS` (4) words → rejects `something real?`, `your business?`,
  `in your business?`;
- first alphabetic char is uppercase → rejects lowercase fragments
  (`something real?`, `your business?`);
- no nav glue: no `read more`/`learn more`/`click here`, no camelCase
  concatenation → rejects `Read moresuccess story?`.

**Answer:**
- ≥ `MIN_ANSWER_CHARS` (40) **and** ≥ `MIN_ANSWER_WORDS` (8);
- not CTA-only: rejected if it opens with a CTA verb (`Book`, `Skip`, `Stop`,
  `Let's`, `Get`, `Schedule`, …) or carries ≥2 CTA phrases → rejects **all 5**
  ProPlan answers (they open with Book/Skip/Stop/Let's).

**Pairing:** both must pass independently; a real Q with a CTA answer, or a
fragment Q with a real answer, is rejected.

**Source tiers (strictness):**
| source | how identified | validation |
|---|---|---|
| `schema` | from `rule_facts.schema_org["faqs"]` (FAQPage JSON-LD) | length only (trusted) |
| `faq_section` | mention's page `category == "faq"`, or under an FAQ heading | full question + answer |
| `llm` | `_mentions(extractions, "faqs")` | full question + answer |
| `markdown` | `_faq_from_markdown` survivors | full question + answer |

---

## 6. Restrict the markdown heuristic (Layer A)

In `rule_extractor.extract_rules`, gate the markdown fallback on FAQ context:

```python
# today:
facts.faq_pairs = facts.schema_org.get("faqs") or _faq_from_markdown(text)
# proposed:
facts.faq_pairs = facts.schema_org.get("faqs") or (
    _faq_from_markdown(text) if _has_faq_context(doc) else [])
```

```python
import re
_FAQ_MARKER = re.compile(r"frequently\s+asked\s+questions|\bFAQs?\b", re.I)

def _has_faq_context(doc) -> bool:
    if getattr(doc, "category", "") == "faq":
        return True
    if any(_FAQ_MARKER.search(h) for h in doc.heading_texts()):
        return True
    return bool(_FAQ_MARKER.search(doc.markdown or ""))
```

(`page_classifier` already runs before rule extraction in the pipeline, so
`doc.category` is populated.) The looser `_faq_from_markdown` body is unchanged
but now only fires on FAQ-context pages.

---

## 7. Integration points (exact)

1. **`rule_extractor.extract_rules`** — gate `_faq_from_markdown` via
   `_has_faq_context(doc)` (Layer A).
2. **`semantic_profile._rule_faq_mentions`** — tag each emitted mention with
   `faq_source` = `"schema"` for `schema_org["faqs"]` pairs, `"markdown"`
   otherwise.
3. **`semantic_profile._mentions(extractions, "faqs")`** — these are LLM faqs;
   tag `faq_source="llm"` (or `"faq_section"` when the mention's
   `category == "faq"`).
4. **`semantic_profile.build_profile`** — one new filter line before
   `_simple_evidence`:
   ```python
   faq_mentions = _mentions(extractions, "faqs") + _rule_faq_mentions(rule_facts, url_category)
   faq_mentions = [m for m in faq_mentions
                   if validate_faq(m["value"], m.get("answer", ""),
                                   source=m.get("faq_source", "unknown"))[0]]
   faqs = _simple_evidence(faq_mentions, ...)
   ```
5. **No change** to `abi_score.py`, `schema.py` (profile contract), or the LLM
   prompt/schema.

Data flow: `crawl → classify → rules (Layer A) → LLM → merge (Layer B gate) →
profile.faqs → score`.

---

## 8. Downstream / scoring impact (expected)

- FAQ criteria now reflect *valid* FAQs only — no scoring-formula change.
- **ProPlan:** 5 → 0 valid FAQs → FAQ coverage 0/35, answer quality 0/10,
  knowledge depth 0/15. ABI ≈ **−13.5**, correcting the inflation documented in
  `abi_calibration_review.md` (#6/#7/#21). This is the goal, not a regression.
- **Regression risk:** real FAQs on HVAC sites must survive. Two protections:
  (a) schema-sourced FAQs are trusted; (b) Layer A still fires on pages with an
  FAQ heading even if mis-classified. Validate against the existing 50 (see §11).

---

## 9. Edge cases, tradeoffs, non-goals

- **Genuine "How do I start?" → "Book a call."** is rejected (CTA answer). Chosen
  tradeoff: better to drop a borderline real-but-CTA FAQ than to readmit
  marketing copy. Documented, tunable via `CTA_PHRASES`.
- **Short but valid answers** ("We serve Charlotte and the surrounding metro.")
  near the 8-word floor — `MIN_ANSWER_WORDS` is deliberately conservative; revisit
  if the regression set shows false rejects.
- **Non-English** sites — out of scope for v1 (interrogatives/CTA lists are
  English).
- **Accordion/`<details>` FAQs without schema** — Layer A's heading marker covers
  most; richer DOM detection is a future enhancement, not v1.
- **Non-goal:** rewriting/repairing bad questions. We *reject*, we don't repair.

---

## 10. Test plan — `backend/tests/test_faq_validator.py`

Offline, deterministic, no network/LLM. Covers every requirement and every
ProPlan failure.

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

# --- real FAQs must be accepted ---
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

# --- requirement: question + answer pair required ---
def test_requires_both_question_and_answer():
    assert validate_faq("Do you offer financing?", "", source="llm")[0] is False
    assert validate_faq("", "Yes we do, for 12 months.", source="llm")[0] is False

# --- requirement: minimum answer length ---
def test_rejects_too_short_answer():
    ok, reason = validate_faq("How long does install take?", "About a day.",
                              source="markdown")
    assert ok is False and "short" in reason

# --- requirement: reject CTA-only answers (valid question) ---
def test_rejects_cta_answer_even_with_valid_question():
    ok, reason = validate_faq("How do I get started?",
                              "Book a free strategy call today!", source="llm")
    assert ok is False and "call-to-action" in reason

# --- requirement: reject heading / fragment questions ---
@pytest.mark.parametrize("q", [
    "your business?", "something real?", "in your business?",   # fragments
    "Read moresuccess story?",                                  # nav glue
    "FAQ?",                                                     # too short
])
def test_rejects_fragment_questions(q):
    a = "This is a perfectly fine and sufficiently long explanatory answer here."
    assert validate_faq(q, a, source="markdown")[0] is False

# --- requirement: prefer FAQPage schema.org (trusted, light validation) ---
def test_schema_source_is_trusted():
    # A terse schema question that strict rules would reject still passes,
    # because FAQPage markup is the site's own declaration.
    ok, _ = validate_faq("Returns?",
                         "We accept returns within 30 days for a full refund.",
                         source="schema")
    assert ok is True

def test_schema_still_rejects_empty_answer():
    assert validate_faq("Returns?", "n/a", source="schema")[0] is False

# --- requirement: prefer explicit FAQ sections (faq_section validated, kept) ---
def test_faq_section_real_pair_accepted():
    ok, _ = validate_faq("What areas do you serve?",
                         "We serve Charlotte, Concord, and the surrounding "
                         "Mecklenburg County area.", source="faq_section")
    assert ok is True
```

Plus an **integration test** (in `test_pipeline.py`) once implemented:
`build_profile` fed a doc whose only "FAQs" are the ProPlan fakes (markdown
source, non-FAQ page) yields `profile["faqs"] == []`; a doc with a real schema
FAQPage yields those FAQs intact.

And a **`_has_faq_context` unit test** (in `test_pipeline.py`): a page classified
`faq` → True; a homepage with a `## Frequently Asked Questions` heading → True; a
plain marketing page → False (so `_faq_from_markdown` won't run there).

---

## 11. Rollout & validation steps (when implemented)

1. Add `faq_validator.py` + tests; all unit tests green.
2. Wire Layer A + Layer B; run `pytest` (existing 46 + new ≈ 60).
3. Re-merge the 50 cached sites for free (`reuse_extraction`, no LLM cost) and
   diff `faqs[]` counts before/after:
   - **expect:** ProPlan 5→0; sites with schema FAQPage unchanged; spot-check
     that no site loses *real* markdown FAQs (if any do, relax `MIN_ANSWER_WORDS`
     or broaden FAQ-context detection).
4. Re-score (`run_abi_validation --passed-only`); confirm ProPlan ABI drops by
   ~13 and the benchmark's "FAQ coverage" weakness count rises (more sites
   correctly flagged as lacking real FAQs).
5. Update `abi_calibration_review.md` findings #6/#7/#21 to "resolved".

**Acceptance:** ProPlan reports 0 FAQs; every FAQ in the 50-site set is a
genuine Q/A pair on manual spot-check; no net loss of schema-sourced FAQs.
