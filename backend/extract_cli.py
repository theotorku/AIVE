"""Command-line entrypoint for the Goal 02 extraction pipeline.

Runs the full staged pipeline (crawl -> classify -> rules -> LLM -> normalize
-> confidence -> merge -> ABI evidence) for one site.

Usage (from repo root):
    python -m backend.extract_cli https://example-hvac.com
    python -m backend.extract_cli --domain morrisjenkins.com   # reuse cached crawl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the semantic extraction pipeline.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("url", nargs="?", help="Website URL to crawl + extract")
    src.add_argument("--domain", help="Run against an already-crawled domain")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parent / "output"))
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--max-pages", type=int, default=6)
    parser.add_argument("--fresh", action="store_true", help="Re-crawl even if cached")
    args = parser.parse_args(argv)

    target = args.domain or args.url
    result = run_pipeline(target, output_root=args.output, model=args.model,
                          max_pages=args.max_pages, reuse_crawl=not args.fresh)

    print(f"Domain:        {result.domain}")
    print(f"Pages:         {result.pages}  {result.page_categories}")
    print(f"Tokens:        {result.total_tokens}")
    print(f"Output:        {result.output_file}")
    if result.error:
        print(f"ERROR:         {result.error}")
        return 1

    p = result.profile
    print(f"Business name: {p.get('business_name')}")
    print(f"Industry:      {p.get('industry')}")
    for fld in ("services", "service_areas", "locations", "faqs", "offers",
                "trust_signals", "ctas"):
        print(f"{fld:14} {len(p.get(fld, []))}")
    print("\n--- profile.json (truncated) ---")
    print(json.dumps({**p, "abi_evidence": result.abi_evidence}, indent=2,
                     ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
