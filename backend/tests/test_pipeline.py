"""Offline unit tests for the staged pipeline (no network / no LLM).

Covers the deterministic stages: classification, rule extraction, entity
normalization, confidence scoring, and profile merging.
"""

from backend.app.schema import Heading, Link, PageDocument
from backend.app.services import normalizer, page_classifier, rule_extractor
from backend.app.services.confidence import Signals, average_confidence, score
from backend.app.services.llm_extractor import PageExtraction
from backend.app.services.rule_extractor import RuleFacts
from backend.app.services.semantic_profile import build_profile


# ---- classification --------------------------------------------------------

def _doc(url, title="", headings=None, links=None, metadata=None):
    return PageDocument(
        url=url, title=title, markdown="",
        headings=[Heading(2, h) for h in (headings or [])],
        links=[Link(t, h) for t, h in (links or [])],
        metadata=metadata or {},
    )


def test_classify_home_and_sections():
    assert page_classifier.classify_page(_doc("https://x.com/")) == "home"
    assert page_classifier.classify_page(_doc("https://x.com/contact-us")) == "contact"
    assert page_classifier.classify_page(_doc("https://x.com/faq")) == "faq"
    assert page_classifier.classify_page(_doc("https://x.com/about-us")) == "about"
    assert page_classifier.classify_page(_doc("https://x.com/reviews")) == "reviews"


def test_classify_service_detail_and_blog():
    assert page_classifier.classify_page(
        _doc("https://x.com/cooling/ac-repair")) == "service_detail"
    assert page_classifier.classify_page(
        _doc("https://x.com/services")) == "services"
    assert page_classifier.classify_page(
        _doc("https://x.com/blog/why-ac-breaks")) == "blog"


def test_classify_faqpage_via_jsonld():
    doc = _doc("https://x.com/help", metadata={"json_ld": [{"@type": "FAQPage"}]})
    assert page_classifier.classify_page(doc) == "faq"


# ---- rule extraction -------------------------------------------------------

def test_rule_extractor_contacts_and_faq():
    # Markdown FAQ extraction only fires on FAQ-context pages (Pillar 1, Layer A),
    # so the page carries an explicit FAQ marker.
    md = ("Call us at (704) 357-0484 or email info@acme-hvac.com.\n"
          "## Frequently Asked Questions\n"
          "Do you offer financing?\nYes, we offer 0% financing for 12 months.\n")
    doc = PageDocument(url="https://acme.com/contact", title="Contact", markdown=md)
    facts = rule_extractor.extract_rules(doc)
    assert "(704) 357-0484" in facts.phones
    assert "info@acme-hvac.com" in facts.emails
    assert any("financing" in f["question"].lower() for f in facts.faq_pairs)


def test_rule_extractor_schema_org():
    doc = PageDocument(
        url="https://acme.com/", title="Home", markdown="",
        metadata={"json_ld": [
            {"@type": "HVACBusiness", "name": "Acme HVAC",
             "telephone": "704-357-0484",
             "address": {"@type": "PostalAddress", "streetAddress": "1 Main St",
                         "addressLocality": "Charlotte", "addressRegion": "NC"},
             "areaServed": ["Charlotte", "Concord"]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": "Are you licensed?",
                 "acceptedAnswer": {"@type": "Answer", "text": "Yes, fully licensed."}}]},
        ]})
    facts = rule_extractor.extract_rules(doc)
    assert facts.schema_org["name"] == "Acme HVAC"
    assert "Charlotte" in facts.schema_org["address"]
    assert "Charlotte" in facts.schema_org["area_served"]
    assert facts.schema_org["faqs"][0]["question"] == "Are you licensed?"


def test_rule_extractor_schema_org_list_valued_fields():
    # Real sites sometimes emit list/object-valued schema.org fields; these must
    # be coerced to strings, not crash with 'list has no attribute lower'.
    doc = PageDocument(
        url="https://acme.com/", title="Home", markdown="",
        metadata={"json_ld": [
            {"@type": ["LocalBusiness", "HVACBusiness"],
             "name": ["Acme HVAC", "Acme Heating"],
             "telephone": ["704-357-0484"],
             "areaServed": [{"@type": "City", "name": "Charlotte"}, "Concord"]},
        ]})
    facts = rule_extractor.extract_rules(doc)
    assert isinstance(facts.schema_org["name"], str)
    assert "Acme HVAC" in facts.schema_org["name"]
    assert isinstance(facts.schema_org["telephone"], str)
    # And the full pipeline merge must not raise on this shape.
    profile = build_profile([doc], [_empty_extraction("https://acme.com/", "home")],
                            [facts])
    assert profile["structured_data"]["has_business"] is True


# ---- normalization ---------------------------------------------------------

def test_normalize_services_groups_aliases():
    groups = normalizer.normalize_services(
        ["AC Repair", "Air Conditioning Repair", "Furnace Installation"])
    canon = {g["canonical"] for g in groups}
    assert "AC Repair" in canon
    ac = next(g for g in groups if g["canonical"] == "AC Repair")
    assert any("Air Conditioning Repair" == a for a in ac["aliases"])


def test_normalize_areas_dfw():
    groups = normalizer.normalize_areas(["DFW", "Dallas-Fort Worth", "North Texas"])
    assert len(groups) == 1
    assert groups[0]["canonical"] == "Dallas-Fort Worth"


# ---- confidence ------------------------------------------------------------

def test_confidence_high_with_strong_signals():
    conf, reason = score(Signals(llm_confidence=0.9, in_headings=True,
                                 schema_supported=True, page_count=3,
                                 on_relevant_page=True))
    assert conf >= 0.75
    assert "schema.org" in reason


def test_confidence_low_single_blog_mention():
    conf, _ = score(Signals(llm_confidence=0.4, page_count=1, from_blog_only=True))
    assert conf < 0.5


# ---- extraction confidence score (site-level) ------------------------------

def test_average_confidence_across_scored_fields():
    profile = {
        "services": [{"value": "AC Repair", "confidence": 0.9},
                     {"value": "Heating", "confidence": 0.7}],
        "faqs": [{"value": "Licensed?", "confidence": 0.5}],
        "trust_signals": [],  # empty fields contribute nothing
        "contact_information": {"phone": "x"},  # non-scored field ignored
    }
    # mean of 0.9, 0.7, 0.5
    assert average_confidence(profile) == 0.7


def test_average_confidence_none_when_no_facts():
    assert average_confidence({"services": [], "faqs": []}) is None
    assert average_confidence({}) is None


# ---- profile merge ---------------------------------------------------------

def test_build_profile_merges_and_scores():
    docs = [
        PageDocument(url="https://acme.com/", title="Acme HVAC", markdown="",
                     headings=[Heading(1, "AC Repair")],
                     links=[Link("AC Repair", "https://acme.com/services/ac-repair")],
                     category="home"),
        PageDocument(url="https://acme.com/services/ac-repair",
                     title="AC Repair", markdown="", category="service_detail"),
    ]
    ex1 = PageExtraction(url="https://acme.com/", category="home", data={
        "business_name": "Acme HVAC", "industry": "HVAC",
        "services": [{"value": "AC Repair", "evidence": "We repair AC", "confidence": 0.9}],
        "service_areas": [], "locations": [], "faqs": [], "offers": [],
        "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                               "hours": None, "booking_url": None}})
    ex2 = PageExtraction(url="https://acme.com/services/ac-repair",
                         category="service_detail", data={
        "business_name": "Acme HVAC", "industry": "HVAC",
        "services": [{"value": "Air Conditioning Repair",
                      "evidence": "AC repair service", "confidence": 0.8}],
        "service_areas": [], "locations": [], "faqs": [], "offers": [],
        "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                               "hours": None, "booking_url": None}})
    rf = [RuleFacts(url="https://acme.com/", phones=["(704) 357-0484"]),
          RuleFacts(url="https://acme.com/services/ac-repair")]

    profile = build_profile(docs, [ex1, ex2], rf)
    assert profile["business_name"] == "Acme HVAC"
    assert profile["industry"] == "HVAC"
    # The two phrasings collapse into one canonical service.
    assert len(profile["services"]) == 1
    svc = profile["services"][0]
    assert svc["value"] == "AC Repair"
    assert "Air Conditioning Repair" in svc["aliases"]
    assert svc["confidence"] >= 0.6  # headings + 2 pages + high llm
    # Contact phone comes from deterministic rule facts.
    assert profile["contact_information"]["phone"] == "(704) 357-0484"


# ---- deterministic FAQ merge + structured-data signal ----------------------

def _empty_extraction(url, category):
    return PageExtraction(url=url, category=category, data={
        "business_name": None, "industry": None, "services": [],
        "service_areas": [], "locations": [], "faqs": [], "offers": [],
        "trust_signals": [], "ctas": [],
        "contact_information": {"phone": None, "email": None, "address": None,
                               "hours": None, "booking_url": None}})


def test_rule_faqs_merged_even_when_llm_misses_them():
    docs = [PageDocument(url="https://acme.com/faq", title="FAQ", markdown="",
                         category="faq")]
    ex = _empty_extraction("https://acme.com/faq", "faq")  # LLM found no FAQs
    rf = [RuleFacts(url="https://acme.com/faq", faq_pairs=[
        {"question": "Do you offer financing?", "answer": "Yes, 0% for 12 months."},
        {"question": "Are you licensed?", "answer": "Yes, fully licensed."}])]
    profile = build_profile(docs, [ex], rf)
    questions = {f["value"] for f in profile["faqs"]}
    assert "Do you offer financing?" in questions
    assert "Are you licensed?" in questions


def test_structured_data_signal_from_schema_org():
    docs = [PageDocument(url="https://acme.com/", title="Home", markdown="",
                         category="home")]
    ex = _empty_extraction("https://acme.com/", "home")
    rf = [RuleFacts(url="https://acme.com/", schema_org={
        "name": "Acme HVAC", "telephone": "704-357-0484",
        "address": "1 Main St, Charlotte, NC",
        "faqs": [{"question": "Licensed?",
                  "answer": "Yes, we are fully licensed and insured."}]})]
    profile = build_profile(docs, [ex], rf)
    sd = profile["structured_data"]
    assert sd["schema_org_detected"] is True
    assert sd["has_business"] is True
    assert sd["has_faq_schema"] is True
    # The schema FAQ should also seed the FAQ list (schema source is trusted,
    # but a substantive answer is still required — Pillar 1).
    assert any(f["value"] == "Licensed?" for f in profile["faqs"])


def test_no_structured_data_when_no_schema():
    docs = [PageDocument(url="https://acme.com/", title="Home", markdown="",
                         category="home")]
    profile = build_profile(docs, [_empty_extraction("https://acme.com/", "home")],
                            [RuleFacts(url="https://acme.com/")])
    assert profile["structured_data"]["schema_org_detected"] is False


# ---- FAQ validity gate (Goal 03D, Pillar 1) --------------------------------

def test_has_faq_context():
    # FAQ page by classification; homepage with an FAQ heading; plain page.
    faq_page = _doc("https://x.com/help")
    faq_page.category = "faq"
    assert rule_extractor._has_faq_context(faq_page) is True
    assert rule_extractor._has_faq_context(
        _doc("https://x.com/", headings=["Frequently Asked Questions"])) is True
    plain = PageDocument(url="https://x.com/", title="Home",
                         markdown="Book a call to grow your business.",
                         category="home")
    assert rule_extractor._has_faq_context(plain) is False


PROPLAN_FAKE_PAIRS = [
    {"question": "something real?",
     "answer": "Book a free strategy call. We'll map your biggest bottleneck."},
    {"question": "your business?",
     "answer": "Stop wasting time on manual processes. Let's build automation."},
    {"question": "Prefer to Talk First?",
     "answer": "Skip the form. Book a 15-minute intro call with our team."},
]


def test_build_profile_drops_markdown_fakes():
    # Marketing fragments that reached faq_pairs (markdown source) are filtered
    # out at the merge choke point (Layer B) — ProPlan's 5 fakes -> 0.
    docs = [PageDocument(url="https://x.com/", title="Home", markdown="",
                         category="home")]
    ex = _empty_extraction("https://x.com/", "home")
    rf = [RuleFacts(url="https://x.com/", faq_pairs=PROPLAN_FAKE_PAIRS)]
    profile = build_profile(docs, [ex], rf)
    assert profile["faqs"] == []


def test_build_profile_keeps_real_schema_faq():
    docs = [PageDocument(url="https://x.com/", title="Home", markdown="",
                         category="home")]
    ex = _empty_extraction("https://x.com/", "home")
    rf = [RuleFacts(url="https://x.com/", schema_org={
        "faqs": [{"question": "Do you offer financing?",
                  "answer": "Yes, we offer 0% financing for 12 months on "
                            "qualifying systems."}]})]
    profile = build_profile(docs, [ex], rf)
    assert any(f["value"] == "Do you offer financing?" for f in profile["faqs"])


# ---- extraction hygiene / provenance partition (Goal 03E) ------------------

def _svc_extraction(url, category, services):
    ex = _empty_extraction(url, category)
    ex.data["services"] = [{"value": s, "evidence": f"{s} content",
                            "confidence": 0.7} for s in services]
    return ex


def test_blog_only_service_partitioned_out_losslessly():
    # A blog page contributes an example automation; a product page contributes
    # the real feature. The blog example leaves services[] for blog_examples[],
    # and nothing is lost (services + blog_examples == all services).
    docs = [
        PageDocument(url="https://x.com/", title="Home", markdown="",
                     category="home"),
        PageDocument(url="https://x.com/blog/post", title="Post", markdown="",
                     category="blog"),
    ]
    exts = [
        _svc_extraction("https://x.com/", "home", ["AI Lead Scoring"]),
        _svc_extraction("https://x.com/blog/post", "blog",
                        ["Returns Processing Automation"]),
    ]
    rf = [RuleFacts(url=d.url) for d in docs]
    profile = build_profile(docs, exts, rf)
    svc = {s["value"] for s in profile["services"]}
    blog = {b["value"] for b in profile["blog_examples"]}
    assert "AI Lead Scoring" in svc
    assert "Returns Processing Automation" in blog
    assert "Returns Processing Automation" not in svc
    # loss-less: every fact is labelled and routed, none dropped.
    assert all(s.get("provenance") == "first_party_service"
               for s in profile["services"])
    assert all(b.get("provenance") == "blog_example"
               for b in profile["blog_examples"])


def test_pure_hvac_profile_has_no_blog_examples():
    docs = [PageDocument(url="https://acme.com/services", title="Services",
                         markdown="", category="services")]
    exts = [_svc_extraction("https://acme.com/services", "services",
                            ["AC Repair", "Furnace Installation"])]
    profile = build_profile(docs, exts, [RuleFacts(url=docs[0].url)])
    assert profile["blog_examples"] == []
    assert len(profile["services"]) == 2
