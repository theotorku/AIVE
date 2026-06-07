"""Goal 01 validation harness.

Crawls a list of HVAC websites and checks the Goal 01 success criteria:
  - the URL is crawled,
  - JS-rendered content is captured,
  - clean, readable markdown is produced,
  - no critical errors (every accepted site yields readable markdown).

Writes a human-readable report and a machine-readable summary, and exits
non-zero if fewer than --target sites pass so CI / the operator can tell.

Usage:
    python -m backend.run_validation
    python -m backend.run_validation --target 10 --max-pages 6
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from backend.crawler import crawl_site

HERE = Path(__file__).resolve().parent
DEFAULT_SITES = HERE / "validation" / "hvac_sites.txt"
REPORT_DIR = HERE / "validation"

# Heuristic: a site "passes" if its markdown is long enough to be useful and
# at least one page rendered cleanly. Tuned to flag empty/blocked sites.
MIN_READABLE_CHARS = 600


def load_sites(path: Path) -> list[str]:
    sites: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            sites.append(line)
    return sites


def run(target: int, max_pages: int, sites_file: Path, output_root: Path) -> int:
    sites = load_sites(sites_file)
    rows = []
    passed = 0

    for i, url in enumerate(sites, 1):
        print(f"[{i}/{len(sites)}] crawling {url} ...", flush=True)
        t0 = time.monotonic()
        try:
            result = crawl_site(url, output_root=str(output_root), max_pages=max_pages)
            elapsed = time.monotonic() - t0
            readable = (not result.has_critical_error
                        and result.total_markdown_chars >= MIN_READABLE_CHARS)
            rows.append({
                "url": url,
                "domain": result.domain,
                "pages_crawled": result.pages_crawled,
                "pages_ok": result.pages_ok,
                "markdown_chars": result.total_markdown_chars,
                "elapsed_s": round(elapsed, 1),
                "passed": readable,
                "error": None if readable else "insufficient readable markdown",
            })
            if readable:
                passed += 1
            status = "PASS" if readable else "FAIL"
            print(f"    {status}  pages_ok={result.pages_ok}/{result.pages_crawled}"
                  f"  chars={result.total_markdown_chars}  {elapsed:.1f}s", flush=True)
        except Exception as exc:  # noqa: BLE001 - never let one site abort the run
            elapsed = time.monotonic() - t0
            rows.append({
                "url": url, "domain": None, "pages_crawled": 0, "pages_ok": 0,
                "markdown_chars": 0, "elapsed_s": round(elapsed, 1),
                "passed": False, "error": f"{type(exc).__name__}: {exc}",
            })
            print(f"    ERROR {exc}", flush=True)

        if passed >= target:
            # Stop once the target is met to keep the run short.
            break

    summary = {
        "target": target,
        "attempted": len(rows),
        "passed": passed,
        "met_target": passed >= target,
        "min_readable_chars": MIN_READABLE_CHARS,
        "results": rows,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    _write_markdown_report(summary, REPORT_DIR / "validation_report.md")

    print(f"\nResult: {passed}/{target} sites passed "
          f"({'TARGET MET' if summary['met_target'] else 'TARGET NOT MET'})")
    return 0 if summary["met_target"] else 1


def _write_markdown_report(summary: dict, path: Path) -> None:
    lines = [
        "# Goal 01 — Crawler Validation Report",
        "",
        f"- Target: {summary['target']} HVAC websites",
        f"- Attempted: {summary['attempted']}",
        f"- Passed: {summary['passed']}",
        f"- Target met: {'yes' if summary['met_target'] else 'no'}",
        f"- Readable threshold: {summary['min_readable_chars']} markdown chars",
        "",
        "| # | Site | Pages OK | MD chars | Time (s) | Result |",
        "|---|------|----------|----------|----------|--------|",
    ]
    for i, r in enumerate(summary["results"], 1):
        result = "PASS" if r["passed"] else f"FAIL ({r['error']})"
        lines.append(
            f"| {i} | {r['url']} | {r['pages_ok']}/{r['pages_crawled']} "
            f"| {r['markdown_chars']} | {r['elapsed_s']} | {result} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Goal 01 crawler validation.")
    parser.add_argument("--target", type=int, default=10,
                        help="Number of sites that must pass (default: 10)")
    parser.add_argument("--max-pages", type=int, default=6,
                        help="Max pages per site (default: 6)")
    parser.add_argument("--sites", type=Path, default=DEFAULT_SITES,
                        help="Path to the site list file")
    parser.add_argument("--output", type=Path, default=HERE / "output",
                        help="Output root directory")
    args = parser.parse_args(argv)
    return run(args.target, args.max_pages, args.sites, args.output)


if __name__ == "__main__":
    sys.exit(main())
