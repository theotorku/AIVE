"""Agent-actionability detection (Goal 03D, Pillar 3).

Agent Readiness's *Online booking* criterion used to read exactly one field,
`contact_information.booking_url`, set on ~6% of sites while a booking
affordance is actually present on ~76% — a ~90% false-negative rate. This
module detects booking actionability from signals that are *already crawled*:
the outbound link graph (scheduler hosts / booking paths), schema.org
`potentialAction`, the booking CTAs, and `contact_information`.

It produces a structured, evidence-bearing block kept OUT of the extraction
contract (like `structured_data`), tiered by how directly an agent can execute:

    T3 Direct   deep-linkable scheduler / potentialAction / booking_url   -> 20
    T2 Form     a booking/quote/contact form an agent can fill            -> 12
    T1 Intent   booking-intent CTA or phone-to-book, no resolvable link   ->  6
    T0 None                                                               ->  0

The scoring (graduated criterion) lives in abi_score; this module only detects.
"""

from __future__ import annotations

from urllib.parse import urlparse

# Deep-linkable scheduler hosts (host or subdomain match — never substring, so
# "local.company" can't masquerade as "cal.com").
SCHEDULER_HOSTS = (
    "calendly.com", "cal.com", "meetings.hubspot.com", "acuityscheduling.com",
    "app.acuityscheduling.com", "setmore.com", "schedulicity.com",
    "youcanbook.me", "book.housecallpro.com", "squareup.com", "simplybook.me",
    "10to8.com", "appointlet.com", "tidycal.com", "savvycal.com",
)

# Booking/quote *action* form paths on the site's own domain (T2 — a fillable
# form whose path itself signals booking/quote intent). NOTE: a bare "/contact"
# is deliberately NOT here — a generic contact page is weak intent (T1), not a
# booking form, and crediting it T2 over-states actionability.
BOOKING_PATHS = (
    "/book", "/book-online", "/booking", "/schedule", "/appointment",
    "/request-service", "/request-estimate", "/request-a-quote", "/get-a-quote",
    "/free-estimate", "/request-appointment",
)

# Generic contact paths — reachable channel but not a booking/quote form: T1.
CONTACT_PATHS = ("/contact", "/contact-us")

# schema.org actions that imply a bookable/orderable surface.
ACTION_TYPES = {"reserveaction", "scheduleaction", "orderaction",
                "appointmentaction"}

# CTA text/type signalling booking intent (T1 when no link resolves).
BOOKING_INTENT = ("book", "schedule", "appointment", "consult", "reserve",
                  "request a quote", "request service", "free estimate")

_TIER_RANK = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}


def _host_matches(host: str, suffix: str) -> bool:
    return host == suffix or host.endswith("." + suffix)


def _scheduler_in(href: str) -> str | None:
    host = urlparse(href).netloc.lower()
    for s in SCHEDULER_HOSTS:
        if _host_matches(host, s):
            return s
    return None


def _path_matches(href: str, paths: tuple[str, ...]) -> bool:
    path = urlparse(href).path.lower().rstrip("/")
    return any(path == p or path.startswith(p + "/") or path.endswith(p)
               for p in paths)


def _is_booking_path(href: str) -> bool:
    return _path_matches(href, BOOKING_PATHS)


def _is_contact_path(href: str) -> bool:
    return _path_matches(href, CONTACT_PATHS)


def _potential_action(docs) -> str | None:
    """Return an evidence URL/type if any page declares a booking potentialAction."""
    for d in docs:
        for block in (d.metadata or {}).get("json_ld", []) or []:
            if not isinstance(block, dict):
                continue
            actions = block.get("potentialAction")
            if not actions:
                continue
            for act in (actions if isinstance(actions, list) else [actions]):
                if not isinstance(act, dict):
                    continue
                a_type = act.get("@type", "")
                a_types = {a_type.lower()} if isinstance(a_type, str) else {
                    str(t).lower() for t in (a_type or [])}
                if a_types & ACTION_TYPES:
                    target = act.get("target")
                    if isinstance(target, dict):
                        target = target.get("urlTemplate") or target.get("url")
                    return str(target) if target else f"potentialAction:{a_type}"
    return None


def _better(current: dict, tier: str, mechanism: str, evidence: str) -> dict:
    if _TIER_RANK[tier] > _TIER_RANK[current["tier"]]:
        return {"tier": tier, "mechanism": mechanism, "evidence": evidence}
    return current


def detect_actionability(docs, profile: dict) -> dict:
    """Detect the strongest booking affordance across all signals.

    Returns ``{"booking": {"tier", "mechanism", "evidence"}}``. Precedence is by
    tier (highest wins); every non-T0 credit names its evidence so the score
    stays explainable.
    """
    contact = profile.get("contact_information", {}) or {}
    ctas = profile.get("ctas", []) or []
    booking = {"tier": "T0", "mechanism": None, "evidence": None}

    # T3 — explicit machine-readable action.
    pa = _potential_action(docs)
    if pa:
        booking = _better(booking, "T3", "schema_potential_action", pa)

    # T3 — explicit booking_url the LLM lifted into contact_information.
    if contact.get("booking_url"):
        booking = _better(booking, "T3", "booking_url", contact["booking_url"])

    # Outbound link graph: scheduler host (T3) > booking/quote form path (T2) >
    # generic contact path (T1 intent — reachable, but not a booking form).
    for d in docs:
        for link in d.links:
            sched = _scheduler_in(link.href)
            if sched:
                booking = _better(booking, "T3", sched, link.href)
            elif _is_booking_path(link.href):
                booking = _better(booking, "T2", "form", link.href)
            elif _is_contact_path(link.href):
                booking = _better(booking, "T1", "contact", link.href)

    # T1 — booking-intent CTA (text proves intent; no resolvable destination).
    for c in ctas:
        cta_type = str(c.get("cta_type", "")).lower()
        value = str(c.get("value", "")).lower()
        if cta_type == "book" or any(k in value or k in cta_type
                                     for k in BOOKING_INTENT):
            booking = _better(booking, "T1", "cta_intent", c.get("value", ""))
            break

    # T1 — phone present with a booking-intent CTA is at best phone-to-book.
    if booking["tier"] == "T0" and contact.get("phone"):
        # A bare phone is human contact, not agent booking; leave T0 unless a
        # booking intent was seen above. (No upgrade here by design.)
        pass

    return {"booking": booking}
