"""Goal 03 ABI scoring validation harness.

Scores every cached `profile.json` under the output directory and checks the
Goal 03 acceptance bars:

  Goal 03A — Scoring Engine Validation (default):
    - score >= 20 validated semantic profiles,
    - every site gets an overall score + 5 component scores + rationale +
      evidence + recommendations (explainability),
    - scoring is repeatable (each profile scored twice → identical),
    - the score block is schema-valid.

  Goal 03B — Benchmark Validation:
    - >= 50 total sites; same checks, plus a benchmark distribution.

This harness does no crawling and no LLM calls — it scores existing profiles, so
it is free and instant. Crawling more sites to reach 50 is a separate batch
(`run_extraction_validation.py`), per the two-phase Goal 03 plan.

Usage (from repo root):
    python -m backend.run_abi_validation
    python -m backend.run_abi_validation --min 50      # Goal 03B bar
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.schema import validate_abi_score, validate_profile
from backend.app.services.abi_score import DIMENSION_LABELS, score_abi

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "output"
REPORT_DIR = HERE / "validation"


def _passed_domains() -> set[str] | None:
    """Domains that passed extraction (from the Goal 02/03B summary), if present.

    Lets the benchmark score exactly the *successful* sites and exclude profiles
    that crawled but failed extraction accuracy (sparse/near-empty content).
    """
    summary = REPORT_DIR / "extraction_validation_summary.json"
    if not summary.exists():
        return None
    try:
        data = json.loads(summary.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return {r["domain"] for r in data.get("results", []) if r.get("passed")}


def _load_profiles(output_root: Path, passed_only: bool) -> list[tuple[str, dict]]:
    """Return (domain, profile) for every cached, schema-valid profile.json."""
    allow = _passed_domains() if passed_only else None
    out: list[tuple[str, dict]] = []
    for path in sorted(output_root.glob("*/profile.json")):
        domain = path.parent.name
        if allow is not None and domain not in allow:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        data.pop("abi_evidence", None)
        data.pop("abi_score", None)
        try:
            validate_profile(data)
        except Exception:  # noqa: BLE001
            continue  # not a Goal 02-valid profile; skip
        out.append((domain, data))
    return out


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 1) if xs else None


def run(output_root: Path, minimum: int, passed_only: bool) -> int:
    profiles = _load_profiles(output_root, passed_only)
    rows: list[dict] = []
    explainable = repeatable = schema_ok = 0
    weakness_counter: dict[str, int] = {}

    for domain, profile in profiles:
        score = score_abi(profile)

        # Explainability: overall + 5 component scores + per-criterion rationale,
        # evidence, and at least one actionable recommendation.
        dims = score["dimensions"]
        has_components = set(dims) == set(DIMENSION_LABELS)
        has_rationale = all(c["rationale"] for d in dims.values() for c in d["criteria"])
        has_recs = bool(score["top_recommendations"])
        is_explainable = has_components and has_rationale and has_recs
        explainable += is_explainable

        # Repeatability: identical output on a second run.
        is_repeatable = score_abi(profile) == score
        repeatable += is_repeatable

        # Schema validity of the score block.
        try:
            validate_abi_score(score)
            is_schema_ok = True
        except Exception as exc:  # noqa: BLE001
            is_schema_ok = False
            print(f"  schema invalid for {domain}: {exc}", flush=True)
        schema_ok += is_schema_ok

        # Track common weaknesses = the top-priority recommended criterion.
        if score["top_recommendations"]:
            weak = score["top_recommendations"][0]["criterion"]
            weakness_counter[weak] = weakness_counter.get(weak, 0) + 1

        rows.append({
            "domain": domain,
            "overall": score["overall"],
            "grade": score["grade"],
            "grade_label": score["grade_label"],
            "components": {k: dims[k]["score"] for k in dims},
            "top_recommendation": (score["top_recommendations"][0]["recommendation"]
                                   if score["top_recommendations"] else None),
            "explainable": is_explainable,
            "repeatable": is_repeatable,
            "schema_valid": is_schema_ok,
        })
        print(f"  {domain:32s} ABI {score['overall']:5.1f} {score['grade']}  "
              f"({score['grade_label']})", flush=True)

    n = len(rows)
    overalls = [r["overall"] for r in rows]
    component_means = {
        k: _mean([r["components"][k] for r in rows]) for k in DIMENSION_LABELS
    } if rows else {}
    benchmark = {
        "sites_scored": n,
        "average_abi": _mean(overalls),
        "lowest_abi": (min(overalls) if overalls else None),
        "highest_abi": (max(overalls) if overalls else None),
        "component_averages": component_means,
        "grade_distribution": _grade_dist(rows),
        "common_weaknesses": sorted(weakness_counter.items(),
                                    key=lambda kv: kv[1], reverse=True),
    }
    summary = {
        "minimum": minimum,
        "sites_scored": n,
        "met_minimum": n >= minimum,
        "all_explainable": explainable == n and n > 0,
        "all_repeatable": repeatable == n and n > 0,
        "all_schema_valid": schema_ok == n and n > 0,
        "benchmark": benchmark,
        "results": sorted(rows, key=lambda r: r["overall"], reverse=True),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "abi_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    _write_report(summary, REPORT_DIR / "abi_validation_report.md")

    passed = (summary["met_minimum"] and summary["all_explainable"]
              and summary["all_repeatable"] and summary["all_schema_valid"])
    print(f"\nScored {n} profiles | avg ABI {benchmark['average_abi']} "
          f"(range {benchmark['lowest_abi']}-{benchmark['highest_abi']}) | "
          f"explainable {explainable}/{n} | repeatable {repeatable}/{n} | "
          f"schema {schema_ok}/{n} | "
          f"{'PASS' if passed else 'NEEDS WORK'} (min {minimum})")
    return 0 if passed else 1


def _grade_dist(rows: list[dict]) -> dict:
    dist: dict[str, int] = {}
    for r in rows:
        dist[r["grade"]] = dist.get(r["grade"], 0) + 1
    return dict(sorted(dist.items()))


def _write_report(summary: dict, path: Path) -> None:
    b = summary["benchmark"]
    lines = [
        "# Goal 03 — ABI Scoring Validation Report",
        "",
        f"- Sites scored: {summary['sites_scored']} (minimum {summary['minimum']})",
        f"- Minimum met: {'yes' if summary['met_minimum'] else 'no'}",
        f"- Explainable (overall + 5 components + rationale + recs): "
        f"{'all' if summary['all_explainable'] else 'NO'}",
        f"- Repeatable (identical on re-score): "
        f"{'all' if summary['all_repeatable'] else 'NO'}",
        f"- Score block schema-valid: "
        f"{'all' if summary['all_schema_valid'] else 'NO'}",
        "",
        "## Benchmark",
        "",
        f"- Average ABI: {b['average_abi']}",
        f"- Range: {b['lowest_abi']} – {b['highest_abi']}",
        f"- Grade distribution: "
        + ", ".join(f"{g}: {n}" for g, n in b["grade_distribution"].items()),
        "",
        "### Component averages",
        "",
        "| Dimension | Avg score |",
        "|-----------|-----------|",
    ]
    for key, label in DIMENSION_LABELS.items():
        lines.append(f"| {label} | {b['component_averages'].get(key)} |")
    lines += [
        "",
        "### Most common top weakness",
        "",
        "| Criterion | Sites |",
        "|-----------|-------|",
    ]
    for crit, count in b["common_weaknesses"]:
        lines.append(f"| {crit} | {count} |")

    lines += [
        "",
        "## Per-site scores",
        "",
        "| # | Domain | ABI | Grade | Underst. | Retr. | Recomm. | Agent | Auth. | Top fix |",
        "|---|--------|-----|-------|----------|-------|---------|-------|-------|---------|",
    ]
    for i, r in enumerate(summary["results"], 1):
        c = r["components"]
        fix = (r["top_recommendation"] or "")[:60]
        lines.append(
            f"| {i} | {r['domain']} | {r['overall']} | {r['grade']} "
            f"| {c['ai_understanding']} | {c['ai_retrieval']} "
            f"| {c['ai_recommendation']} | {c['agent_readiness']} "
            f"| {c['semantic_authority']} | {fix} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ABI scoring (Goal 03).")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Directory of <domain>/profile.json outputs")
    parser.add_argument("--min", type=int, default=20, dest="minimum",
                        help="Minimum profiles required (20 = 03A, 50 = 03B)")
    parser.add_argument("--passed-only", action="store_true",
                        help="Score only domains that passed extraction "
                        "(per extraction_validation_summary.json)")
    args = parser.parse_args(argv)
    return run(args.output, args.minimum, args.passed_only)


if __name__ == "__main__":
    sys.exit(main())
