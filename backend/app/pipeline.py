"""End-to-end extraction pipeline orchestration.

    crawl -> clean -> markdown -> classify -> rule extract -> llm extract
          -> normalize + confidence + merge -> ABI evidence -> ABI score

Persists under output/<domain>/:
  - page_documents.json  (rich crawl output; cached for fast re-runs)
  - extractions.json     (per-page LLM outputs; cached so the merge+score stages
                          can be re-run without paying for the LLM again)
  - profile.json         (the merged semantic profile + ABI evidence + ABI score)
  - pipeline.json        (run metadata: tokens, page categories, errors, ABI)
  - confidence.json      (Extraction Confidence Score)
  - abi_score.json       (standalone ABI score block)

Three reuse levers control how much is recomputed:
  - reuse_profile     : re-score the final profile only (cheapest; cannot apply
                        merge-stage changes since it has no per-page facts).
  - reuse_extraction  : rebuild merge + score from cached crawl + cached LLM
                        outputs (no LLM, no crawl) — applies merge-stage changes
                        for free.
  - reuse_crawl       : skip Playwright, re-run the LLM over the cached crawl.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from openai import OpenAI

from backend.crawler.crawl import _domain_slug, _normalize_url
from backend.app.schema import ABI_VERSION, Heading, Link, PageDocument
from backend.app.services import page_classifier, rule_extractor
from backend.app.services.abi_evidence import build_abi_evidence
from backend.app.services.abi_score import score_abi
from backend.app.services.confidence import average_confidence
from backend.app.services.crawler import crawl_documents
from backend.app.services.llm_extractor import (
    DEFAULT_MODEL, PageExtraction, extract_page)
from backend.app.services.semantic_profile import build_profile


@dataclass
class PipelineResult:
    domain: str
    profile: dict = field(default_factory=dict)
    abi_evidence: dict = field(default_factory=dict)
    abi_score: dict = field(default_factory=dict)
    pages: int = 0
    page_categories: dict = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    average_confidence: float | None = None  # Extraction Confidence Score
    crawl_coverage: dict = field(default_factory=dict)
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


def _load_cached_coverage(site_dir: Path) -> dict | None:
    cache = site_dir / "crawl_coverage.json"
    if not cache.exists():
        return None
    try:
        return json.loads(cache.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _coverage_from_docs(docs: list[PageDocument]) -> dict:
    """Minimal coverage for crawls cached before diagnostics existed."""
    n = len(docs)
    low = n < 3
    return {
        "final_page_count": n, "meaningful_pages_found": n,
        "crawled_urls": [{"url": d.url, "ok": True} for d in docs],
        "discovered_urls": [{"url": d.url} for d in docs],
        "skipped_urls": [], "low_coverage": low,
        "warning": (f"Low Crawl Coverage Warning: This report may be incomplete "
                    f"because only {n} pages were crawled." if low else None),
        "note": "synthesized (crawl predates coverage diagnostics)",
    }


def _ex_to_dict(ex: PageExtraction) -> dict:
    return {"url": ex.url, "category": ex.category, "data": ex.data,
            "prompt_tokens": ex.prompt_tokens,
            "completion_tokens": ex.completion_tokens, "error": ex.error}


def _ex_from_dict(d: dict) -> PageExtraction:
    return PageExtraction(
        url=d["url"], category=d.get("category", "unknown"),
        data=d.get("data") or {}, prompt_tokens=d.get("prompt_tokens", 0),
        completion_tokens=d.get("completion_tokens", 0), error=d.get("error"))


def _load_cached_extractions(site_dir: Path) -> list[PageExtraction] | None:
    cache = site_dir / "extractions.json"
    if not cache.exists():
        return None
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        return [_ex_from_dict(d) for d in data]
    except Exception:  # noqa: BLE001
        return None


def _persist(site_dir: Path, domain: str, profile: dict, abi: dict,
             abi_score: dict, categories: dict, prompt_tokens: int,
             completion_tokens: int, avg_conf: float | None,
             page_errors: list[dict], coverage: dict | None = None) -> PipelineResult:
    """Write every per-site artifact from a finished profile + score. Shared by
    every code path so files on disk always match the returned result.

    `coverage` (crawl diagnostics) is kept OUT of profile.json — it is not part
    of the extraction contract — and written to its own crawl_coverage.json.
    """
    coverage = coverage or {}
    output = {**profile, "abi_evidence": abi, "abi_score": abi_score}
    (site_dir / "profile.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    (site_dir / "pipeline.json").write_text(json.dumps({
        "domain": domain, "abi_version": ABI_VERSION,
        "pages": sum(categories.values()),
        "page_categories": categories,
        "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
        "average_confidence": avg_conf,
        "abi_overall": abi_score["overall"], "abi_grade": abi_score["grade"],
        "crawl_final_page_count": coverage.get("final_page_count"),
        "crawl_low_coverage": coverage.get("low_coverage"),
        "page_errors": page_errors,
    }, indent=2), encoding="utf-8")
    (site_dir / "confidence.json").write_text(json.dumps({
        "site": domain, "average_confidence": avg_conf,
    }, indent=2), encoding="utf-8")
    # Stamp the frozen ABI version on the standalone score artifact for
    # traceability (the score block itself is unchanged — version is metadata).
    (site_dir / "abi_score.json").write_text(json.dumps({
        "site": domain, "abi_version": ABI_VERSION, **abi_score,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    if coverage:
        (site_dir / "crawl_coverage.json").write_text(
            json.dumps({"site": domain, **coverage}, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return PipelineResult(
        domain=domain, profile=profile, abi_evidence=abi, abi_score=abi_score,
        pages=sum(categories.values()), page_categories=categories,
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        average_confidence=avg_conf, crawl_coverage=coverage,
        output_file=str(site_dir / "profile.json"))


def _finalize(site_dir: Path, domain: str, docs: list[PageDocument],
              extractions: list[PageExtraction], rule_facts: list,
              prompt_tokens: int, completion_tokens: int,
              coverage: dict | None = None) -> PipelineResult:
    """Merge + ABI evidence + ABI score from page-level facts, then persist."""
    profile = build_profile(docs, extractions, rule_facts)
    abi = build_abi_evidence(profile)
    abi_score = score_abi(profile)
    categories: dict = {}
    for d in docs:
        categories[d.category] = categories.get(d.category, 0) + 1
    page_errors = [{"url": e.url, "error": e.error} for e in extractions if e.error]
    if coverage is None:
        coverage = _load_cached_coverage(site_dir) or _coverage_from_docs(docs)
    return _persist(site_dir, domain, profile, abi, abi_score, categories,
                    prompt_tokens, completion_tokens,
                    average_confidence(profile), page_errors, coverage)


def run_pipeline(
    target: str,
    *,
    output_root: str | Path = "output",
    max_pages: int = 12,
    max_depth: int = 2,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
    reuse_crawl: bool = True,
    reuse_profile: bool = False,
    reuse_extraction: bool = False,
    progress: Callable[[str], None] | None = None,
) -> PipelineResult:
    """Run the full pipeline for a URL (or a cached domain slug).

    `progress`, if given, is called with coarse stage names ("crawling",
    "extracting", "scoring") so a UI can show live run status. It is purely
    observational — it does not affect outputs or contracts.
    """
    from backend.app.schema import validate_profile

    def emit(stage: str) -> None:
        if progress:
            progress(stage)

    url = _normalize_url(target)
    domain = _domain_slug(url)
    site_dir = Path(output_root) / domain
    site_dir.mkdir(parents=True, exist_ok=True)

    # Fast path: re-score the final profile only. Cannot apply merge-stage
    # changes (no per-page facts here), but refreshes the score artifacts so
    # files on disk match the recomputed scores after a formula change.
    profile_path = site_dir / "profile.json"
    if reuse_profile and profile_path.exists():
        try:
            cached = json.loads(profile_path.read_text(encoding="utf-8"))
            cached.pop("abi_evidence", None)
            cached.pop("abi_score", None)  # recomputed deterministically below
            validate_profile(cached)
            cats: dict = {}
            for sp in cached.get("source_pages", []):
                cats[sp["category"]] = cats.get(sp["category"], 0) + 1
            abi = build_abi_evidence(cached)
            abi_score = score_abi(cached)
            emit("scoring")
            cov = _load_cached_coverage(site_dir)
            return _persist(site_dir, domain, cached, abi, abi_score, cats,
                            0, 0, average_confidence(cached), [], cov)
        except Exception:  # noqa: BLE001 - fall through to a fresh run
            pass

    # Re-merge path: rebuild profile + score from cached crawl + cached LLM
    # outputs. No LLM, no crawl — applies merge-stage fixes for free.
    if reuse_extraction:
        docs = _load_cached_docs(site_dir)
        extractions = _load_cached_extractions(site_dir)
        if docs and extractions:
            page_classifier.classify_documents(docs)
            rule_facts = [rule_extractor.extract_rules(d) for d in docs]
            emit("scoring")
            return _finalize(site_dir, domain, docs, extractions, rule_facts, 0, 0)

    # Stage 1: crawl (or reuse cached rich crawl).
    emit("crawling")
    docs = _load_cached_docs(site_dir) if reuse_crawl else None
    coverage = _load_cached_coverage(site_dir) if docs else None
    if not docs:
        bundle = crawl_documents(url, max_pages=max_pages, max_depth=max_depth)
        docs = bundle.documents
        coverage = bundle.coverage
        if docs:
            (site_dir / "page_documents.json").write_text(
                json.dumps([_doc_to_dict(d) for d in docs], indent=2, ensure_ascii=False),
                encoding="utf-8")
            (site_dir / "crawl_coverage.json").write_text(
                json.dumps({"site": domain, **coverage}, indent=2, ensure_ascii=False),
                encoding="utf-8")
    if not docs:
        return PipelineResult(domain=domain, crawl_coverage=coverage or {},
                              error=(coverage or {}).get("error") or "no pages crawled")
    if coverage is None:
        coverage = _coverage_from_docs(docs)

    # Stage 2: classify.
    page_classifier.classify_documents(docs)

    # Stages 3-4: per-page rule facts + LLM extraction.
    emit("extracting")
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

    # Cache per-page LLM outputs so merge + score can be re-run for free.
    (site_dir / "extractions.json").write_text(
        json.dumps([_ex_to_dict(e) for e in extractions], indent=2, ensure_ascii=False),
        encoding="utf-8")

    # Stages 5-9: normalize + confidence + merge + ABI evidence + ABI score.
    emit("scoring")
    return _finalize(site_dir, domain, docs, extractions, rule_facts,
                     prompt_tokens, completion_tokens, coverage)
