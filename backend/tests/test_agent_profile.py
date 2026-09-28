"""The additive agent profile exposes claims and sources without guessing."""

from backend.app.schema import Link, PageDocument
from backend.app.services.agent_profile import build_agent_profile
from backend.app.services.llm_extractor import PageExtraction
from backend.app.services.rule_extractor import RuleFacts
from backend.app.services.semantic_profile import build_profile


def test_agent_profile_captures_actionable_claims_and_sources():
    doc = PageDocument(
        url="https://acme.example/pricing", title="Pricing", category="pricing",
        markdown=("Call (312) 555-1234\n"
                  "Same-day emergency service by appointment.\n"
                  "Service visits start at $89 plus tax.\n"
                  "Cancellation requires 24 hours notice.\n"),
        links=[Link("Book a visit", "https://calendly.com/acme/visit"),
               Link("Request a quote", "https://acme.example/request-a-quote")],
    )
    profile = {
        "services": [{"value": "AC Repair", "confidence": .9,
                      "evidence": "AC Repair", "source_url": doc.url}],
        "service_areas": [], "trust_signals": [], "offers": [],
        "pricing_tiers": [],
        "contact_information": {"phone": "(312) 555-1234", "hours": None,
                                "email": None, "address": None,
                                "booking_url": None},
    }
    agent = build_agent_profile([doc], profile)
    assert agent["version"] == "1.0"
    assert agent["canonical_services"][0]["source_url"] == doc.url
    assert agent["availability"][0]["live_slots"] is False
    assert agent["pricing"][0]["amounts"] == ["$89"]
    assert "plus tax" in agent["pricing"][0]["qualifiers"]
    assert agent["policies"][0]["kind"] == "cancellation"
    assert {x["tier"] for x in agent["booking_endpoints"]} == {"T2", "T3"}
    assert all(x["verified"] is False for x in agent["booking_endpoints"])
    assert agent["contact_information"]["phone"]["source_url"] == doc.url
    assert agent["live_availability_checked"] is False


def test_missing_facts_remain_empty_and_unattributed_contact_is_explicit():
    doc = PageDocument(url="https://acme.example", title="Home", markdown="Welcome")
    agent = build_agent_profile([doc], {
        "services": [], "service_areas": [], "trust_signals": [],
        "offers": [], "pricing_tiers": [],
        "contact_information": {"hours": "Monday to Friday 9–5"},
    })
    assert agent["pricing"] == agent["policies"] == agent["booking_endpoints"] == []
    assert agent["contact_information"]["hours"]["source_type"] == "unattributed"
    assert agent["contact_information"]["hours"]["confidence"] == 0.0


def test_merged_evidence_url_matches_selected_quote_and_agent_profile_present():
    docs = [
        PageDocument(url="https://acme.example/a", title="A", markdown="AC repair",
                     category="services"),
        PageDocument(url="https://acme.example/z", title="Z", markdown="AC repair",
                     category="services"),
    ]
    exts = []
    for doc, confidence in zip(docs, (0.5, 0.95)):
        exts.append(PageExtraction(url=doc.url, category=doc.category,
                                   data={"services": [{"value": "AC Repair",
                                                       "evidence": f"quote from {doc.url}",
                                                       "confidence": confidence}]}))
    profile = build_profile(docs, exts, [RuleFacts(url=d.url) for d in docs])
    service = profile["services"][0]
    assert service["source_url"] == docs[1].url
    assert service["evidence"] == f"quote from {docs[1].url}"
    assert profile["agent_profile"]["canonical_services"][0]["source_url"] == docs[1].url
