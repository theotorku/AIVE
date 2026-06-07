"""HTML -> clean markdown (stage 1).

Thin wrapper over the Goal 01 converter so the pipeline has a single,
named conversion step (per the recommended architecture) without duplicating
the trafilatura/bs4 logic.
"""

from __future__ import annotations

from backend.crawler.clean import html_to_markdown


def to_markdown(html: str, *, url: str | None = None) -> str:
    return html_to_markdown(html, url=url)
