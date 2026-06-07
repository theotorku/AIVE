"""End-to-end extraction pipeline orchestration.

    crawl -> clean -> markdown -> classify -> rule extract -> llm extract
          -> normalize + confidence + merge -> ABI evidence

Persists three artifacts under output/<domain>/:
  - page_documents.json  (rich crawl output; cached for fast re-runs)
  - profile.json         (the merged semantic profile + ABI evidence)
  - pipeline.json        (run metadata: tokens, page categories, errors)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from openai import OpenAI

from backend.crawler.crawl import _domain_slug, _normalize_url
from backend.app.schema import Heading, Link, PageDocument
from backend.app.services import page_classifier, rule_extractor
from backend.app.services.abi_evidence import build_abi_evidence
from backend.app.services.crawler import crawl_documents
from backend.app.services.llm_extractor import DEFAULT_MODEL, extract_page
from backend.app.services.semantic_profile import build_profile


@dataclass
class PipelineResult:
    domain: str
    profile: dict = field(default_factory=dict)
    abi_evidence: dict = field(default_factory=dict)
    pages: int = 0
    page_categories: dict = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    output_file: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.pages > 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def _doc_to_dict(doc: PageDocument) -> dict:
    return asdict(doc)


def _doc_from_dict(d: dict) -> PageDocument:
    return PageDocument(
        url=d["url"], title=d.get("title", ""), markdown=d.get("markdown", ""),
        headings=[Heading(**h) for h in d.get("headings", [])],
        links=[Link(**l) for l in d.get("links", [])],
        metadata=d.get("metadata", {}), category=d.get("category", "unknown"),
    )


def _load_cached_docs(site_dir: Path) -> list[PageDocument] | None:
    cache = site_dir / "page_documents.json"
    if not cache.exists():
        return None
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        return [_doc_from_dict(d) for d in data]
    except Exception:  # noqa: BLE001
        return None


def run_pipeline(
    target: str,
    *,
    output_root: str | Path = "output",
    max_pages: int = 6,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
    reuse_crawl: bool = True,
    reuse_profile: bool = False,
) -> PipelineResult:
    """Run the full pipeline for a URL (or a cached domain slug)."""
    from backend.app.schema import validate_profile

    url = _normalize_url(target)
    domain = _domain_slug(url)
    site_dir = Path(output_root) / domain
    site_dir.mkdir(parents=True, exist_ok=True)

    # Fast path: return a previously computed, schema-valid profile unchanged.
    profile_path = site_dir / "profile.json"
    if reuse_profile and profile_path.exists():
        try:
            cached = json.loads(profile_path.read_text(encoding="utf-8"))
            abi = cached.pop("abi_evidence", {})
            validate_profile(cached)
            cats: dict = {}
            for sp in cached.get("source_pages", []):
                cats[sp["category"]] = cats.get(sp["category"], 0) + 1
            return PipelineResult(
                domain=domain, profile=cached, abi_evidence=abi,
                pages=len(cached.get("source_pages", [])), page_categories=cats,
                output_file=str(profile_path))
        except Exception:  # noqa: BLE001 - fall through to a fresh run
            pass

    # Stage 1: crawl (or reuse cached rich crawl).
    docs = _load_cached_docs(site_dir) if reuse_crawl else None
    if not docs:
        docs = crawl_documents(url, max_pages=max_pages)
        if docs:
            (site_dir / "page_documents.json").write_text(
                json.dumps([_doc_to_dict(d) for d in docs], indent=2, ensure_ascii=False),
                encoding="utf-8")
    if not docs:
        return PipelineResult(domain=domain, error="no pages crawled")

    # Stage 2: classify.
    page_classifier.classify_documents(docs)

    # Stages 3-4: per-page rule facts + LLM extraction.
    client = client or OpenAI()
    rule_facts, extractions = [], []
    prompt_tokens = completion_tokens = 0
    for doc in docs:
        rf = rule_extractor.extract_rules(doc)
        rule_facts.append(rf)
        ex = extract_page(doc, rule_facts=rf, client=client, model=model)
        extractions.append(ex)
        prompt_tokens += ex.prompt_tokens
        completion_tokens += ex.completion_tokens

    # Stages 5-7: normalize + confidence + merge.
    profile = build_profile(docs, extractions, rule_facts)
    # Stage 8: ABI evidence.
    abi = build_abi_evidence(profile)

    output = {**profile, "abi_evidence": abi}
    out_file = site_dir / "profile.json"
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    categories = {}
    for d in docs:
        categories[d.category] = categories.get(d.category, 0) + 1

    result = PipelineResult(
        domain=domain, profile=profile, abi_evidence=abi, pages=len(docs),
        page_categories=categories, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, output_file=str(out_file),
    )
    (site_dir / "pipeline.json").write_text(json.dumps({
        "domain": domain, "pages": len(docs), "page_categories": categories,
        "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
        "page_errors": [{"url": e.url, "error": e.error} for e in extractions if e.error],
    }, indent=2), encoding="utf-8")
    return result
