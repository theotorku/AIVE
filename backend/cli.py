"""Command-line entrypoint for the Goal 01 crawler.

Usage:
    python -m backend.cli https://example-hvac.com
    python -m backend.cli example-hvac.com --max-pages 5 --output output
"""

from __future__ import annotations

import argparse
import sys

from backend.crawler import crawl_site


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crawl a website to clean markdown.")
    parser.add_argument("url", help="Website URL to crawl")
    parser.add_argument("--max-pages", type=int, default=8,
                        help="Maximum pages to crawl (default: 8)")
    parser.add_argument("--output", default="output",
                        help="Output root directory (default: output)")
    parser.add_argument("--timeout", type=int, default=30000,
                        help="Per-page navigation timeout in ms (default: 30000)")
    args = parser.parse_args(argv)

    result = crawl_site(
        args.url,
        output_root=args.output,
        max_pages=args.max_pages,
        timeout_ms=args.timeout,
    )

    print(f"Domain:        {result.domain}")
    print(f"Output dir:    {result.output_dir}")
    print(f"Pages crawled: {result.pages_crawled}")
    print(f"Pages OK:      {result.pages_ok}")
    print(f"Markdown chars:{result.total_markdown_chars}")
    for page in result.pages:
        flag = "OK " if page.ok else "ERR"
        detail = page.error if page.error else f"{page.markdown_chars} chars"
        print(f"  [{flag}] {page.url} -> {detail}")

    return 0 if not result.has_critical_error else 1


if __name__ == "__main__":
    sys.exit(main())
