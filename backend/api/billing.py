"""Stripe checkout for the Pilot Audit ($399).

Flow:
  1. POST /api/checkout {domain}  -> create a Checkout Session, return its URL.
  2. Customer pays on Stripe's hosted page.
  3. success_url returns them to the app with ?session_id=...
  4. GET /api/checkout/{session_id} verifies payment and mints a report grant.
  5. (backup) the webhook mints the grant too, in case the redirect is lost.

Stripe keys come from the environment; nothing here is hardcoded. If
STRIPE_SECRET_KEY is unset the endpoints return a clear 503 instead of crashing,
so the rest of the API still runs locally without payments configured.
"""

from __future__ import annotations

import os

from backend.api import grants

# Pilot Audit price (sales/offer.md rung 1) — $399 founding price, first 10
# clients (standard $749). Cents; override with a Stripe Price.
PILOT_PRICE_CENTS = int(os.getenv("PILOT_PRICE_CENTS", "39900"))
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")  # optional; takes precedence
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5173")


def _stripe():
    """Return a configured stripe module, or None if billing isn't set up."""
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        return None
    import stripe  # imported lazily so the API runs without the dependency

    stripe.api_key = key
    return stripe


def is_configured() -> bool:
    return _stripe() is not None


def create_checkout(domain: str) -> str:
    """Create a Checkout Session for one domain; return the hosted payment URL."""
    stripe = _stripe()
    if stripe is None:
        raise RuntimeError("billing_unconfigured")

    if STRIPE_PRICE_ID:
        line_item = {"price": STRIPE_PRICE_ID, "quantity": 1}
    else:
        line_item = {
            "price_data": {
                "currency": "usd",
                "unit_amount": PILOT_PRICE_CENTS,
                "product_data": {
                    "name": "AI Visibility Audit — Pilot",
                    "description": f"Full AI Visibility report for {domain}",
                },
            },
            "quantity": 1,
        }

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[line_item],
        metadata={"domain": domain},
        success_url=f"{PUBLIC_BASE_URL}/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{PUBLIC_BASE_URL}/?checkout=cancelled",
    )
    return session.url


def grant_for_session(session_id: str) -> tuple[str, str] | None:
    """Verify a paid session and mint its report grant. Returns (token, domain)."""
    stripe = _stripe()
    if stripe is None:
        raise RuntimeError("billing_unconfigured")
    session = stripe.checkout.Session.retrieve(session_id)
    if session.get("payment_status") != "paid":
        return None
    domain = (session.get("metadata") or {}).get("domain")
    if not domain:
        return None
    token = grants.mint(domain, session_id=session_id)
    return token, domain


def handle_webhook(payload: bytes, sig_header: str | None) -> None:
    """Verify and process a Stripe webhook (backup grant minting)."""
    stripe = _stripe()
    if stripe is None:
        raise RuntimeError("billing_unconfigured")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if secret and sig_header:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    else:
        import json

        event = json.loads(payload)

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("payment_status") == "paid":
            domain = (session.get("metadata") or {}).get("domain")
            if domain:
                grants.mint(domain, session_id=session.get("id"))
