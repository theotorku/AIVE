"""Entity normalization (stage 5).

Different pages name the same thing differently ("AC Repair", "Air
Conditioning Repair", "Emergency Cooling Repair"). This stage collapses
variants into canonical entities with an `aliases` list, for both services and
locations/areas. Deterministic: a curated map for common HVAC/home-service
terms, plus a generic token-based grouping for everything else.
"""

from __future__ import annotations

import re

# Canonical service -> regex of alias indicators (matched on lowercased text).
_SERVICE_CANON: list[tuple[str, re.Pattern]] = [
    ("AC Repair", re.compile(r"\b(a/?c|air[- ]?condition\w*|cooling)\b.*\brepair|emergency cooling")),
    ("AC Installation", re.compile(r"\b(a/?c|air[- ]?condition\w*|cooling)\b.*\b(install\w*|replace\w*)")),
    ("AC Maintenance", re.compile(r"\b(a/?c|air[- ]?condition\w*|cooling)\b.*\b(maintenance|tune[- ]?up)")),
    ("Heating Repair", re.compile(r"\b(heating|furnace|heat[- ]?pump)\b.*\brepair")),
    ("Heating Installation", re.compile(r"\b(heating|furnace|heat[- ]?pump)\b.*\b(install\w*|replace\w*)")),
    ("Heating Maintenance", re.compile(r"\b(heating|furnace|heat[- ]?pump)\b.*\b(maintenance|tune[- ]?up)")),
    ("Furnace Services", re.compile(r"\bfurnace\b")),
    ("Heat Pump Services", re.compile(r"\bheat[- ]?pump\b")),
    ("Duct Services", re.compile(r"\b(duct|ductwork|air duct)\b")),
    ("Thermostat Services", re.compile(r"\bthermostat\b")),
    ("Indoor Air Quality", re.compile(r"\b(indoor air quality|iaq|air purif\w*|air filtration)\b")),
    ("Drain Cleaning", re.compile(r"\bdrain\b.*\b(clean\w*|clog)")),
    ("Water Heater Services", re.compile(r"\bwater heater|tankless\b")),
    ("Plumbing Repair", re.compile(r"\bplumb\w*\b.*\brepair|leak repair")),
    ("Plumbing Services", re.compile(r"\bplumb\w*\b")),
    ("Electrical Services", re.compile(r"\belectric\w*\b")),
]

# Canonical metro -> alias indicators.
_AREA_CANON: list[tuple[str, re.Pattern]] = [
    ("Dallas-Fort Worth", re.compile(r"\b(dfw|dallas[- ]?fort[- ]?worth|dallas metroplex|north texas|metroplex)\b")),
    ("San Francisco Bay Area", re.compile(r"\b(bay area|sf bay|san francisco bay)\b")),
    ("Greater Phoenix", re.compile(r"\b(phoenix metro|valley of the sun|greater phoenix)\b")),
]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).strip(" -–—|·•")


def _canonical_for(text: str, table: list[tuple[str, re.Pattern]]) -> str | None:
    low = text.lower()
    for canonical, pattern in table:
        if pattern.search(low):
            return canonical
    return None


def _token_key(text: str) -> str:
    """Order-independent key for generic grouping (drops filler words)."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"the", "and", "of", "a", "an", "for", "your", "our", "services", "service"}
    core = sorted(w.rstrip("s") for w in words if w not in stop)
    return " ".join(core) or text.lower()


def _group(values: list[str], table: list[tuple[str, re.Pattern]]) -> list[dict]:
    """Return [{canonical, aliases:[...]}] preserving first-seen order."""
    groups: dict[str, dict] = {}
    order: list[str] = []
    for raw in values:
        name = _clean(raw)
        if not name:
            continue
        canonical = _canonical_for(name, table)
        key = canonical.lower() if canonical else _token_key(name)
        if key not in groups:
            groups[key] = {"canonical": canonical or name, "aliases": []}
            order.append(key)
        grp = groups[key]
        if name.lower() != grp["canonical"].lower() and name not in grp["aliases"]:
            grp["aliases"].append(name)
    return [groups[k] for k in order]


def normalize_services(values: list[str]) -> list[dict]:
    return _group(values, _SERVICE_CANON)


def normalize_areas(values: list[str]) -> list[dict]:
    return _group(values, _AREA_CANON)


def normalize_simple(values: list[str]) -> list[str]:
    """Case-insensitive dedupe for free-text lists (trust signals, CTAs)."""
    seen, out = set(), []
    for v in values:
        name = _clean(v)
        low = name.lower()
        if name and low not in seen:
            seen.add(low)
            out.append(name)
    return out
