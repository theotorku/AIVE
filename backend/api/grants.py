"""Access grants — the link a paying customer uses to see their full report.

File-based, consistent with the rest of the API (see store.py). A grant is
minted when Stripe confirms payment and binds an opaque token to one domain.
Tokens live under output/_grants/ so they survive redeploys on the Railway
volume alongside the audit artifacts they unlock.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.api import store

GRANTS_DIR = store.OUTPUT_DIR / "_grants"

# A buyer-less, read-only grant for the public "View sample" report.
SAMPLE_TOKEN = "sample"


def _grant_path(token: str) -> Path:
    # Tokens are uuid4 hex (or the literal "sample"); reject anything that could
    # escape the grants directory.
    if not token.isalnum():
        return GRANTS_DIR / "__invalid__"
    return GRANTS_DIR / f"{token}.json"


def mint(domain: str, session_id: str | None = None) -> str:
    """Create (or reuse) a grant for a domain. Idempotent per Stripe session."""
    GRANTS_DIR.mkdir(parents=True, exist_ok=True)
    if session_id:
        existing = find_by_session(session_id)
        if existing:
            return existing
    token = uuid.uuid4().hex
    payload = {
        "token": token,
        "domain": domain,
        "session_id": session_id,
        "created": datetime.now(timezone.utc).isoformat(),
    }
    _grant_path(token).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return token


def resolve(token: str, sample_domain: str | None = None) -> str | None:
    """Return the domain a token unlocks, or None if the token is unknown."""
    if token == SAMPLE_TOKEN:
        return sample_domain
    path = _grant_path(token)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("domain")
    except Exception:  # noqa: BLE001
        return None


def find_by_session(session_id: str) -> str | None:
    """Find an already-minted token for a Stripe session (idempotency)."""
    if not GRANTS_DIR.exists():
        return None
    for path in GRANTS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if data.get("session_id") == session_id:
            return data.get("token")
    return None
