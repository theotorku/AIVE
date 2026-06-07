"""Command-line entrypoint for Goal 02 extraction.

Usage (run from repo root):
    # crawl + extract a fresh URL
    python -m backend.extract_cli https://example-hvac.com

    # extract from an already-crawled domain under output/
    python -m backend.extract_cli --domain morrisjenkins.com
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.extraction import crawl_and_extract, extract_site_from_output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a business profile.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("url", nargs="?", help="Website URL to crawl + extract")
    src.add_argument("--domain", help="Extract from an already-crawled domain")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parent / "output"),
                        help="Crawl/extraction output root")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model")
    parser.add_argument("--max-pages", type=int, default=6, help="Pages to crawl")
    args = parser.parse_args(argv)

    if args.domain:
        site = extract_site_from_output(args.domain, output_root=args.output,
                                        model=args.model)
    else:
        site = crawl_and_extract(args.url, output_root=args.output,
                                 max_pages=args.max_pages, model=args.model)

    r = site.result
    print(f"Domain:          {site.domain}")
    print(f"Extraction file: {site.extraction_file}")
    print(f"Model:           {r.model}")
    print(f"Tokens:          {r.total_tokens} (prompt={r.prompt_tokens}, "
          f"completion={r.completion_tokens})")
    if r.error:
        print(f"ERROR:           {r.error}")
        return 1

    d = site.result.data
    print(f"Business name:   {d.get('business_name')}")
    print(f"Services:        {len(d.get('services', []))}")
    print(f"Locations:       {len(d.get('locations', []))}")
    print(f"Service areas:   {len(d.get('service_areas', []))}")
    print(f"FAQs:            {len(d.get('faqs', []))}")
    print(f"Offers:          {len(d.get('offers', []))}")
    print("\n--- extraction.json ---")
    print(json.dumps(d, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
