"""Read-only access to the real pipeline artifacts on disk.

Every value the dashboard shows comes from here — straight from the JSON the
pipeline wrote. Nothing is synthesized.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BACKEND_DIR / "output"
VALIDATION_DIR = BACKEND_DIR / "validation"

# A domain slug is exactly what the crawler writes (see crawl._domain_slug):
# a hostname reduced to lowercase alphanumerics plus dot/hyphen/underscore.
# Anything else (slashes, "..", encoded traversal) must never reach the
# filesystem, so it is rejected here rather than joined onto OUTPUT_DIR.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def _valid_domain(domain: str) -> bool:
    return bool(domain) and ".." not in domain and _SLUG_RE.match(domain) is not None


def _read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def site_dir(domain: str) -> Path:
    if not _valid_domain(domain):
        raise ValueError(f"invalid domain slug: {domain!r}")
    return OUTPUT_DIR / domain


def has_profile(domain: str) -> bool:
    if not _valid_domain(domain):
        return False
    return (site_dir(domain) / "profile.json").exists()


def load_site(domain: str) -> dict | None:
    """Combined view for one domain: profile + its abi_score + run metadata.

    The profile already embeds `abi_evidence` and `abi_score`; we also surface
    the standalone artifacts so the shape is explicit for the UI.
    """
    if not _valid_domain(domain):
        return None
    profile = _read_json(site_dir(domain) / "profile.json")
    if not isinstance(profile, dict):
        return None
    abi_score = profile.get("abi_score") or _read_json(site_dir(domain) / "abi_score.json")
    pipeline = _read_json(site_dir(domain) / "pipeline.json") or {}
    confidence = _read_json(site_dir(domain) / "confidence.json") or {}
    coverage = _read_json(site_dir(domain) / "crawl_coverage.json") or {}
    return {
        "domain": domain,
        "profile": profile,
        "abi_score": abi_score,
        "pipeline": pipeline,
        "confidence": confidence,
        "coverage": coverage,
    }


# Plain-language grade meanings (mirrors frontend GRADE_MEANING in api.ts).
_GRADE_MEANING = {
    "A": "AI understands your business very well and is likely to surface it.",
    "B": "AI understands your business well, with a few gaps to close.",
    "C": "AI only partially understands your business.",
    "D": "AI struggles to understand your business — important details are missing.",
    "F": "AI can barely understand your business right now.",
}


def load_teaser(domain: str) -> dict | None:
    """Free teaser: headline grade + the single biggest gap, nothing more.

    Deliberately excludes the dimension/criteria/evidence breakdown so the paid
    deliverable is never sent to anonymous clients (sales/strategy.md §5, rung 0).
    """
    if not _valid_domain(domain):
        return None
    profile = _read_json(site_dir(domain) / "profile.json")
    if not isinstance(profile, dict):
        return None
    score = profile.get("abi_score") or _read_json(site_dir(domain) / "abi_score.json")
    if not isinstance(score, dict):
        return None
    grade = score.get("grade")
    recs = score.get("top_recommendations") or []
    top = recs[0] if recs else None
    top_gap = None
    if isinstance(top, dict):
        top_gap = {
            "title": top.get("dimension_label") or top.get("dimension"),
            "why": top.get("recommendation"),
        }
    return {
        "domain": domain,
        "business_name": profile.get("business_name"),
        "overall": score.get("overall"),
        "grade": grade,
        "grade_label": score.get("grade_label"),
        "grade_meaning": _GRADE_MEANING.get(grade or ""),
        "top_gap": top_gap,
    }


def list_sites() -> list[dict]:
    """Lightweight catalogue of every scored site (for the gallery)."""
    out: list[dict] = []
    if not OUTPUT_DIR.exists():
        return out
    for path in sorted(OUTPUT_DIR.glob("*/profile.json")):
        domain = path.parent.name
        profile = _read_json(path)
        if not isinstance(profile, dict):
            continue
        score = profile.get("abi_score") or {}
        out.append({
            "domain": domain,
            "business_name": profile.get("business_name"),
            "industry": profile.get("industry"),
            "overall": score.get("overall"),
            "grade": score.get("grade"),
            "grade_label": score.get("grade_label"),
        })
    out.sort(key=lambda s: (s["overall"] is None, -(s["overall"] or 0)))
    return out


def load_benchmark() -> dict | None:
    """The ABI benchmark summary (averages, distribution, weaknesses)."""
    summary = _read_json(VALIDATION_DIR / "abi_validation_summary.json")
    if not isinstance(summary, dict):
        return None
    return {
        "sites_scored": summary.get("sites_scored"),
        "benchmark": summary.get("benchmark"),
    }
