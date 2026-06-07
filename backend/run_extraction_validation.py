"""Goal 02 validation harness.

Crawls (if needed) and extracts a list of HVAC sites, then checks the Goal 02
criteria:
  - run against 20 websites,
  - JSON schema is stable (every output validates against the stable schema),
  - outputs are accurate (measured via field coverage + spot-checkable dumps).

Writes a human-readable report and a machine-readable summary, and exits
non-zero if fewer than --target sites pass.

Usage (from repo root):
    python -m backend.run_extraction_validation
    python -m backend.run_extraction_validation --target 20 --max-pages 6
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from openai import OpenAI

from backend.crawler import crawl_site
from backend.crawler.crawl import _domain_slug, _normalize_url
from backend.extraction import extract_site_from_output, validate_extraction

HERE = Path(__file__).resolve().parent
DEFAULT_SITES = HERE / "validation" / "extraction_sites.txt"
REPORT_DIR = HERE / "validation"


def load_sites(path: Path) -> list[str]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def _has_crawl(output_root: Path, domain: str) -> bool:
    site_dir = output_root / domain
    return (site_dir / "_site.md").exists() or any(
        p for p in site_dir.glob("*.md") if not p.name.startswith("_")
    ) if site_dir.exists() else False


def _coverage(data: dict) -> dict:
    contact = data.get("contact_information", {})
    return {
        "services": len(data.get("services", [])),
        "locations": len(data.get("locations", [])),
        "service_areas": len(data.get("service_areas", [])),
        "faqs": len(data.get("faqs", [])),
        "offers": len(data.get("offers", [])),
        "has_phone": bool(contact.get("phone")),
        "has_address": bool(contact.get("address") or contact.get("hours")),
        "business_name": bool(data.get("business_name")),
    }


def run(target: int, max_pages: int, model: str, sites_file: Path,
        output_root: Path) -> int:
    sites = load_sites(sites_file)
    client = OpenAI()
    rows = []
    passed = 0
    total_prompt = total_completion = 0

    for i, url in enumerate(sites, 1):
        url = _normalize_url(url)
        domain = _domain_slug(url)
        print(f"[{i}/{len(sites)}] {domain}", flush=True)
        t0 = time.monotonic()
        try:
            if not _has_crawl(output_root, domain):
                print("    crawling ...", flush=True)
                crawl_site(url, output_root=str(output_root), max_pages=max_pages)

            site = extract_site_from_output(domain, output_root=str(output_root),
                                            client=client, model=model)
            r = site.result
            elapsed = time.monotonic() - t0

            schema_valid = False
            schema_err = None
            try:
                validate_extraction(r.data)
                schema_valid = True
            except Exception as exc:  # noqa: BLE001
                schema_err = str(exc)

            cov = _coverage(r.data) if schema_valid else {}
            # Accuracy signal: a real HVAC site should yield services and/or a
            # phone number. Schema validity is the hard requirement.
            accurate = bool(cov) and (cov["services"] > 0 or cov["has_phone"])
            ok = (r.error is None) and schema_valid and accurate

            total_prompt += r.prompt_tokens
            total_completion += r.completion_tokens
            rows.append({
                "url": url, "domain": domain, "schema_valid": schema_valid,
                "accurate": accurate, "passed": ok,
                "coverage": cov,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "truncated": r.truncated, "elapsed_s": round(elapsed, 1),
                "error": r.error or schema_err,
            })
            if ok:
                passed += 1
            status = "PASS" if ok else "FAIL"
            print(f"    {status}  schema={'ok' if schema_valid else 'BAD'}  "
                  f"services={cov.get('services','-')} faqs={cov.get('faqs','-')} "
                  f"phone={cov.get('has_phone','-')} tokens={r.total_tokens} "
                  f"{elapsed:.1f}s", flush=True)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - t0
            rows.append({
                "url": url, "domain": domain, "schema_valid": False,
                "accurate": False, "passed": False, "coverage": {},
                "prompt_tokens": 0, "completion_tokens": 0, "truncated": False,
                "elapsed_s": round(elapsed, 1),
                "error": f"{type(exc).__name__}: {exc}",
            })
            print(f"    ERROR {exc}", flush=True)

        if passed >= target:
            break

    schema_valid_count = sum(1 for r in rows if r["schema_valid"])
    summary = {
        "target": target,
        "model": model,
        "attempted": len(rows),
        "passed": passed,
        "schema_valid": schema_valid_count,
        "schema_stable": schema_valid_count == len(rows),
        "met_target": passed >= target,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "results": rows,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "extraction_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    _write_report(summary, REPORT_DIR / "extraction_validation_report.md")

    print(f"\nResult: {passed}/{target} passed | "
          f"schema valid {schema_valid_count}/{len(rows)} | "
          f"tokens {total_prompt + total_completion} | "
          f"{'TARGET MET' if summary['met_target'] else 'TARGET NOT MET'}")
    return 0 if summary["met_target"] else 1


def _write_report(summary: dict, path: Path) -> None:
    # gpt-4o-mini pricing (USD per 1M tokens) for a rough cost estimate.
    in_rate, out_rate = 0.15, 0.60
    est_cost = (summary["total_prompt_tokens"] / 1e6 * in_rate
                + summary["total_completion_tokens"] / 1e6 * out_rate)

    lines = [
        "# Goal 02 — Extraction Validation Report",
        "",
        f"- Model: {summary['model']}",
        f"- Target: {summary['target']} websites",
        f"- Attempted: {summary['attempted']}",
        f"- Passed: {summary['passed']}",
        f"- Schema valid: {summary['schema_valid']}/{summary['attempted']} "
        f"({'STABLE' if summary['schema_stable'] else 'UNSTABLE'})",
        f"- Target met: {'yes' if summary['met_target'] else 'no'}",
        f"- Tokens: {summary['total_prompt_tokens']} prompt + "
        f"{summary['total_completion_tokens']} completion",
        f"- Est. cost: ${est_cost:.4f}",
        "",
        "| # | Domain | Schema | Svc | Loc | FAQ | Off | Phone | Result |",
        "|---|--------|--------|-----|-----|-----|-----|-------|--------|",
    ]
    for i, r in enumerate(summary["results"], 1):
        c = r.get("coverage") or {}
        result = "PASS" if r["passed"] else f"FAIL ({r.get('error') or 'low coverage'})"
        lines.append(
            f"| {i} | {r['domain']} | {'ok' if r['schema_valid'] else 'BAD'} "
            f"| {c.get('services','-')} | {c.get('locations','-')} "
            f"| {c.get('faqs','-')} | {c.get('offers','-')} "
            f"| {'Y' if c.get('has_phone') else '-'} | {result} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Goal 02 extraction validation.")
    parser.add_argument("--target", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=6)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--sites", type=Path, default=DEFAULT_SITES)
    parser.add_argument("--output", type=Path, default=HERE / "output")
    args = parser.parse_args(argv)
    return run(args.target, args.max_pages, args.model, args.sites, args.output)


if __name__ == "__main__":
    sys.exit(main())
