"""Best-effort abuse mitigation for the public live-audit endpoint.

A live audit crawls an arbitrary site and calls the paid LLM, so the open
endpoint is a cost vector. This caps runs per client IP and globally per day.

Defaults are a conservative launch posture (2/IP/hour, 5/IP/day, 25 globally/day)
sized to an OpenAI monthly budget alert of ~$25; raise them only after observing
real conversion and per-audit cost. This is a monitoring/throttle control, not a
dependable spend cap — it is in-memory and per-process, so counts reset on deploy
or restart, and it does not track dollars. For a real hard cap, move the quota to
persistent storage (Redis/Supabase/Postgres) with atomic reservation and pair it
with the OpenAI budget alert + Vercel WAF rules described in DEPLOYMENT.md §4.
"""

from __future__ import annotations

import os
import threading
import time

_PER_IP_HOUR = int(os.getenv("RUNS_PER_IP_HOUR", "2"))
_PER_IP_DAY = int(os.getenv("RUNS_PER_IP_DAY", "5"))
_GLOBAL_DAY = int(os.getenv("RUNS_GLOBAL_DAY", "25"))

_HOUR = 3600
_DAY = 86400

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}   # ip -> timestamps
_global: list[float] = []            # all timestamps


def _prune(stamps: list[float], window: float, now: float) -> list[float]:
    cutoff = now - window
    return [t for t in stamps if t >= cutoff]


def check(ip: str) -> tuple[bool, str | None]:
    """Return (allowed, reason). Records the hit when allowed."""
    now = time.time()
    with _lock:
        global _global
        _global = _prune(_global, _DAY, now)
        if len(_global) >= _GLOBAL_DAY:
            return False, "Daily audit capacity reached on this instance. Try again tomorrow."

        stamps = _prune(_hits.get(ip, []), _DAY, now)
        last_hour = [t for t in stamps if t >= now - _HOUR]
        if len(last_hour) >= _PER_IP_HOUR:
            return False, "Too many audits from your network. Please wait an hour."
        if len(stamps) >= _PER_IP_DAY:
            return False, "Daily audit limit reached for your network. Try again tomorrow."

        stamps.append(now)
        _hits[ip] = stamps
        _global.append(now)
        return True, None
