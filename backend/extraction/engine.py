"""Extraction orchestration: crawl output (markdown) -> extraction.json.

Bridges Goal 01 and Goal 02. Reads the combined `_site.md` a crawl produced
for a domain (crawling first if needed), runs LLM extraction, and writes a
schema-valid `extraction.json` next to the markdown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from backend.crawler import crawl_site
from backend.crawler.crawl import _domain_slug, _normalize_url

from .extract import DEFAULT_MODEL, ExtractionResult, extract_from_markdown
from .schema import empty_extraction, validate_extraction


@dataclass
class SiteExtraction:
    domain: str
    source_markdown: str | None
    extraction_file: str | None
    result: ExtractionResult

    @property
    def ok(self) -> bool:
        return self.result.ok


def _load_site_markdown(site_dir: Path) -> str | None:
    combined = site_dir / "_site.md"
    if combined.exists():
        return combined.read_text(encoding="utf-8")
    # Fall back to concatenating individual page files (excluding meta files).
    pages = sorted(p for p in site_dir.glob("*.md") if not p.name.startswith("_"))
    if not pages:
        return None
    return "\n\n---\n\n".join(p.read_text(encoding="utf-8") for p in pages)


def extract_site_from_output(
    domain: str,
    *,
    output_root: str | Path = "output",
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
    reuse: bool = False,
) -> SiteExtraction:
    """Extract from already-crawled markdown for a domain under output_root.

    With reuse=True, a previously written, schema-valid extraction.json is
    returned without calling the API (keeps re-runs fast and cheap).
    A crawl failure (no markdown) yields a schema-valid empty payload with an
    error set, so schema stability is never confused with crawl coverage.
    """
    site_dir = Path(output_root) / domain
    out_file = site_dir / "extraction.json"

    if reuse and out_file.exists():
        try:
            cached = validate_extraction(json.loads(out_file.read_text(encoding="utf-8")))
            return SiteExtraction(
                domain=domain, source_markdown=str(site_dir / "_site.md"),
                extraction_file=str(out_file),
                result=ExtractionResult(
                    data=cached, model=f"{model} (cached)", prompt_tokens=0,
                    completion_tokens=0, input_chars=0, truncated=False),
            )
        except Exception:  # noqa: BLE001 - fall through to a fresh extraction
            pass

    markdown = _load_site_markdown(site_dir)
    if not markdown:
        return SiteExtraction(
            domain=domain, source_markdown=None, extraction_file=None,
            result=ExtractionResult(
                data=empty_extraction(), model=model, prompt_tokens=0,
                completion_tokens=0, input_chars=0, truncated=False,
                error="no crawl markdown found"),
        )

    result = extract_from_markdown(markdown, client=client, model=model,
                                   source_url=f"https://{domain}")
    out_file = site_dir / "extraction.json"
    out_file.write_text(json.dumps(result.data, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return SiteExtraction(
        domain=domain, source_markdown=str(site_dir / "_site.md"),
        extraction_file=str(out_file), result=result,
    )


def crawl_and_extract(
    url: str,
    *,
    output_root: str | Path = "output",
    max_pages: int = 6,
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
) -> SiteExtraction:
    """Crawl a URL (Goal 01) then extract (Goal 02) in one call."""
    url = _normalize_url(url)
    domain = _domain_slug(url)
    crawl_site(url, output_root=output_root, max_pages=max_pages)
    return extract_site_from_output(domain, output_root=output_root,
                                    client=client, model=model)
