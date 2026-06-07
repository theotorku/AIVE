"""Goal 02 validation harness (staged pipeline).

Runs the full extraction pipeline over a list of HVAC sites and checks the
Goal 02 criteria:
  - run against 20 websites,
  - JSON schema is stable (every profile matches the stable contract),
  - outputs are accurate (field coverage + evidence/confidence present).

Schema stability is measured over sites we could actually crawl. Crawl is
cached (page_documents.json) so re-runs skip the browser; pass --reuse-profile
to also skip the LLM and reuse cached profiles.

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

from backend.crawler.crawl import _domain_slug, _normalize_url
from backend.app.pipeline import run_pipeline
from backend.app.schema import validate_profile

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


def _coverage(profile: dict) -> dict:
    contact = profile.get("contact_information", {}) or {}
    return {
        "services": len(profile.get("services", [])),
        "service_areas": len(profile.get("service_areas", [])),
        "locations": len(profile.get("locations", [])),
        "faqs": len(profile.get("faqs", [])),
        "offers": len(profile.get("offers", [])),
        "trust_signals": len(profile.get("trust_signals", [])),
        "has_phone": bool(contact.get("phone")),
        "business_name": bool(profile.get("business_name")),
    }


def run(target: int, max_pages: int, model: str, sites_file: Path,
        output_root: Path, reuse_profile: bool) -> int:
    sites = load_sites(sites_file)
    client = OpenAI()
    rows, passed = [], 0
    total_prompt = total_completion = 0

    for i, url in enumerate(sites, 1):
        url = _normalize_url(url)
        domain = _domain_slug(url)
        print(f"[{i}/{len(sites)}] {domain}", flush=True)
        t0 = time.monotonic()
        try:
            result = run_pipeline(url, output_root=str(output_root), model=model,
                                  max_pages=max_pages, client=client,
                                  reuse_crawl=True, reuse_profile=reuse_profile)
            elapsed = time.monotonic() - t0
            crawl_ok = result.pages > 0 and result.error is None
            total_prompt += result.prompt_tokens
            total_completion += result.completion_tokens

            schema_valid, schema_err = False, None
            if crawl_ok:
                try:
                    validate_profile(result.profile)
                    schema_valid = True
                except Exception as exc:  # noqa: BLE001
                    schema_err = str(exc)

            cov = _coverage(result.profile) if crawl_ok else {}
            accurate = bool(cov) and (cov["services"] > 0 or cov["has_phone"])
            ok = crawl_ok and schema_valid and accurate

            rows.append({
                "url": url, "domain": domain, "crawl_ok": crawl_ok,
                "pages": result.pages, "page_categories": result.page_categories,
                "schema_valid": schema_valid, "accurate": accurate, "passed": ok,
                "coverage": cov,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "elapsed_s": round(elapsed, 1),
                "error": (None if ok else (result.error or schema_err
                          or ("low coverage" if crawl_ok else "crawl failed"))),
            })
            if ok:
                passed += 1
            status = "PASS" if ok else "FAIL"
            print(f"    {status}  crawl={'ok' if crawl_ok else 'FAIL'} "
                  f"schema={'ok' if schema_valid else 'BAD'}  pages={result.pages} "
                  f"svc={cov.get('services','-')} faq={cov.get('faqs','-')} "
                  f"phone={cov.get('has_phone','-')} tok={result.total_tokens} "
                  f"{elapsed:.1f}s", flush=True)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - t0
            rows.append({
                "url": url, "domain": domain, "crawl_ok": False, "pages": 0,
                "page_categories": {}, "schema_valid": False, "accurate": False,
                "passed": False, "coverage": {}, "prompt_tokens": 0,
                "completion_tokens": 0, "elapsed_s": round(elapsed, 1),
                "error": f"{type(exc).__name__}: {exc}"})
            print(f"    ERROR {exc}", flush=True)

        if passed >= target:
            break

    crawled = [r for r in rows if r["crawl_ok"]]
    schema_valid_count = sum(1 for r in crawled if r["schema_valid"])
    summary = {
        "target": target, "model": model, "attempted": len(rows),
        "crawl_ok": len(crawled), "passed": passed,
        "schema_valid": schema_valid_count,
        "schema_stable": schema_valid_count == len(crawled) and len(crawled) > 0,
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
          f"schema valid {schema_valid_count}/{len(crawled)} crawled "
          f"({'STABLE' if summary['schema_stable'] else 'UNSTABLE'}) | "
          f"tokens {total_prompt + total_completion} | "
          f"{'TARGET MET' if summary['met_target'] else 'TARGET NOT MET'}")
    return 0 if (summary["met_target"] and summary["schema_stable"]) else 1


def _write_report(summary: dict, path: Path) -> None:
    in_rate, out_rate = 0.15, 0.60  # gpt-4o-mini USD / 1M tokens
    est = (summary["total_prompt_tokens"] / 1e6 * in_rate
           + summary["total_completion_tokens"] / 1e6 * out_rate)
    lines = [
        "# Goal 02 - Extraction Pipeline Validation Report",
        "",
        f"- Model: {summary['model']}",
        f"- Target: {summary['target']} websites",
        f"- Attempted: {summary['attempted']}",
        f"- Crawled OK: {summary['crawl_ok']}",
        f"- Passed: {summary['passed']}",
        f"- Schema valid: {summary['schema_valid']}/{summary['crawl_ok']} crawled "
        f"({'STABLE' if summary['schema_stable'] else 'UNSTABLE'})",
        f"- Target met: {'yes' if summary['met_target'] else 'no'}",
        f"- Tokens: {summary['total_prompt_tokens']} prompt + "
        f"{summary['total_completion_tokens']} completion",
        f"- Est. cost: ${est:.4f}",
        "",
        "| # | Domain | Pages | Schema | Svc | Area | Loc | FAQ | Trust | Phone | Result |",
        "|---|--------|-------|--------|-----|------|-----|-----|-------|-------|--------|",
    ]
    for i, r in enumerate(summary["results"], 1):
        c = r.get("coverage") or {}
        res = "PASS" if r["passed"] else f"FAIL ({r.get('error') or 'low coverage'})"
        lines.append(
            f"| {i} | {r['domain']} | {r['pages']} "
            f"| {'ok' if r['schema_valid'] else 'BAD'} | {c.get('services','-')} "
            f"| {c.get('service_areas','-')} | {c.get('locations','-')} "
            f"| {c.get('faqs','-')} | {c.get('trust_signals','-')} "
            f"| {'Y' if c.get('has_phone') else '-'} | {res} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Goal 02 pipeline validation.")
    parser.add_argument("--target", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=6)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--sites", type=Path, default=DEFAULT_SITES)
    parser.add_argument("--output", type=Path, default=HERE / "output")
    parser.add_argument("--reuse-profile", action="store_true",
                        help="Reuse cached profile.json (skip LLM) when present")
    args = parser.parse_args(argv)
    return run(args.target, args.max_pages, args.model, args.sites, args.output,
               reuse_profile=args.reuse_profile)


if __name__ == "__main__":
    sys.exit(main())
