"""Offline unit tests for the staged pipeline (no network / no LLM).

Covers the deterministic stages: classification, rule extraction, entity
normalization, confidence scoring, and profile merging.
"""

from backend.app.schema import Heading, Link, PageDocument
from backend.app.services import normalizer, page_classifier, rule_extractor
from backend.app.services.confidence import Signals, score
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
    md = ("Call us at (704) 357-0484 or email info@acme-hvac.com.\n"
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
