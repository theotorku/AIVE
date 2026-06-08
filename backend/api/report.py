"""Self-contained HTML ABI report.

Renders one styled, dependency-free .html file from a site's real artifacts —
openable anywhere, and the browser's Print -> Save as PDF covers PDF. No data is
invented; every number comes from the profile's `abi_score`.
"""

from __future__ import annotations

import html
from datetime import date

GRADE_COLOR = {"A": "#1a7f37", "B": "#2da44e", "C": "#bf8700",
               "D": "#cf5500", "F": "#cf222e"}


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _bar(score: float, color: str) -> str:
    pct = max(0.0, min(100.0, float(score or 0)))
    return (f'<div class="bar"><div class="fill" '
            f'style="width:{pct:.0f}%;background:{color}"></div></div>')


def _coverage_section(coverage: dict) -> str:
    """Crawl coverage section + a prominent low-coverage warning banner."""
    if not coverage:
        return ""
    crawled = coverage.get("crawled_urls") or []
    ok_pages = [c for c in crawled if c.get("ok")]
    final = coverage.get("final_page_count", len(ok_pages))
    found = coverage.get("meaningful_pages_found")
    warning = coverage.get("warning")
    skipped = coverage.get("skipped_urls") or []

    banner = (f"<div class='warn'>&#9888; {_esc(warning)}</div>" if warning else "")

    rows = "".join(
        f"<tr><td>{_esc(c.get('url'))}</td><td>{_esc(c.get('link_source','—'))}</td>"
        f"<td>{_esc(c.get('depth','—'))}</td>"
        f"<td>{'ok' if c.get('ok') else _esc(c.get('error','failed'))}</td></tr>"
        for c in crawled)

    skip_rows = "".join(
        f"<tr><td>{_esc(s.get('url'))}</td><td>{_esc(s.get('reason'))}</td></tr>"
        for s in skipped[:30])
    skip_html = (f"<h3>Skipped ({len(skipped)})</h3>"
                 f"<table class='cov'><tr><th>URL</th><th>reason</th></tr>"
                 f"{skip_rows}</table>") if skipped else ""

    facts = []
    facts.append(f"pages crawled: <strong>{_esc(final)}</strong>")
    if found is not None:
        facts.append(f"public pages found: <strong>{_esc(found)}</strong>")
    if coverage.get("sitemap_url_count") is not None:
        facts.append(f"sitemap URLs: {_esc(coverage.get('sitemap_url_count'))}")
    if coverage.get("canonical_host"):
        facts.append(f"canonical host: {_esc(coverage.get('canonical_host'))}")

    return f"""
  {banner}
  <h2>Crawl coverage</h2>
  <p class='muted'>{' &middot; '.join(facts)}</p>
  <table class='cov'><tr><th>Crawled URL</th><th>source</th><th>depth</th><th>status</th></tr>
  {rows}</table>
  {skip_html}"""


def render_report(site: dict) -> str:
    domain = site["domain"]
    profile = site.get("profile") or {}
    score = site.get("abi_score") or {}
    coverage = site.get("coverage") or {}
    if not score:
        return f"<html><body><h1>No ABI score for {_esc(domain)}</h1></body></html>"

    name = profile.get("business_name") or domain
    overall = score.get("overall")
    grade = score.get("grade", "?")
    label = score.get("grade_label", "")
    gcolor = GRADE_COLOR.get(grade, "#57606a")
    dims = score.get("dimensions", {})
    recs = score.get("top_recommendations", [])

    dim_rows = []
    for key, dim in dims.items():
        dcolor = GRADE_COLOR.get(dim.get("grade", ""), "#57606a")
        crit_items = []
        for c in dim.get("criteria", []):
            ev = c.get("evidence") or []
            ev_html = ("<ul class='ev'>" + "".join(
                f"<li>{_esc(e)}</li>" for e in ev) + "</ul>") if ev else ""
            rec = c.get("recommendation")
            rec_html = (f"<div class='rec'>&#9656; {_esc(rec)}</div>"
                        if rec else "")
            crit_items.append(
                f"<div class='crit'><div class='crit-head'>"
                f"<span>{_esc(c.get('name'))}</span>"
                f"<span class='pts'>{c.get('earned')}/{c.get('max')}</span></div>"
                f"<div class='rationale'>{_esc(c.get('rationale'))}</div>"
                f"{ev_html}{rec_html}</div>")
        dim_rows.append(
            f"<section class='dim'><div class='dim-head'>"
            f"<h3>{_esc(dim.get('label'))}</h3>"
            f"<span class='dim-score' style='color:{dcolor}'>"
            f"{dim.get('score')} <small>/100 &middot; {int(dim.get('weight',0)*100)}% weight"
            f" &middot; {_esc(dim.get('grade'))}</small></span></div>"
            f"{_bar(dim.get('score'), dcolor)}"
            f"<div class='crits'>{''.join(crit_items)}</div></section>")

    rec_rows = "".join(
        f"<li><span class='pri'>{r.get('priority')}</span>"
        f"<div><strong>{_esc(r.get('dimension_label'))} &middot; {_esc(r.get('criterion'))}</strong>"
        f"<div>{_esc(r.get('recommendation'))}</div>"
        f"<span class='impact'>ABI impact +{r.get('impact')}</span></div></li>"
        for r in recs) or "<li>No high-impact gaps remain.</li>"

    contact = profile.get("contact_information") or {}
    contact_bits = [f"{k}: {_esc(v)}" for k, v in contact.items() if v]
    contact_line = " &middot; ".join(contact_bits) if contact_bits else "&mdash;"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>ABI Report — {_esc(name)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         color: #1f2328; margin: 0; background: #f6f8fa; }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 32px; }}
  header {{ display: flex; justify-content: space-between; align-items: center; gap: 24px; }}
  h1 {{ font-size: 26px; margin: 0 0 4px; }}
  .muted {{ color: #57606a; font-size: 14px; }}
  .grade-badge {{ text-align: center; min-width: 132px; padding: 16px;
                 border-radius: 14px; color: #fff; background: {gcolor}; }}
  .grade-badge .g {{ font-size: 46px; font-weight: 800; line-height: 1; }}
  .grade-badge .o {{ font-size: 14px; opacity: .92; margin-top: 6px; }}
  .summary {{ background: #fff; border: 1px solid #d0d7de; border-radius: 12px;
             padding: 16px 20px; margin: 20px 0; font-size: 15px; }}
  .bar {{ height: 8px; background: #eaeef2; border-radius: 6px; overflow: hidden; margin: 8px 0 14px; }}
  .fill {{ height: 100%; }}
  section.dim {{ background: #fff; border: 1px solid #d0d7de; border-radius: 12px;
                padding: 18px 20px; margin: 14px 0; }}
  .dim-head {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .dim-head h3 {{ margin: 0; font-size: 17px; }}
  .dim-score {{ font-weight: 700; font-size: 18px; }}
  .dim-score small {{ color: #57606a; font-weight: 500; font-size: 12px; }}
  .crit {{ border-top: 1px solid #eaeef2; padding: 10px 0; }}
  .crit-head {{ display: flex; justify-content: space-between; font-weight: 600; font-size: 14px; }}
  .pts {{ color: #57606a; font-variant-numeric: tabular-nums; }}
  .rationale {{ font-size: 13px; color: #424a53; margin: 3px 0; }}
  ul.ev {{ margin: 4px 0; padding-left: 18px; font-size: 12px; color: #57606a; }}
  .rec {{ font-size: 13px; color: #0550ae; margin-top: 4px; }}
  ol.recs {{ list-style: none; padding: 0; margin: 0; }}
  ol.recs li {{ display: flex; gap: 12px; background: #fff; border: 1px solid #d0d7de;
               border-radius: 10px; padding: 12px 14px; margin: 8px 0; font-size: 14px; }}
  .pri {{ flex: 0 0 28px; height: 28px; border-radius: 50%; background: #0969da; color: #fff;
         display: flex; align-items: center; justify-content: center; font-weight: 700; }}
  .impact {{ color: #1a7f37; font-size: 12px; font-weight: 600; }}
  h2 {{ font-size: 18px; margin: 26px 0 6px; }}
  h3 {{ font-size: 15px; margin: 16px 0 4px; }}
  .warn {{ background: #fff3cd; border: 1px solid #e0c84e; color: #6b5900;
          border-radius: 10px; padding: 12px 16px; margin: 16px 0; font-weight: 600; }}
  table.cov {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 6px 0; }}
  table.cov th, table.cov td {{ text-align: left; padding: 4px 8px;
          border-bottom: 1px solid #eaeef2; word-break: break-all; }}
  table.cov th {{ color: #57606a; font-weight: 600; }}
  footer {{ color: #8c959f; font-size: 12px; margin-top: 28px; text-align: center; }}
</style></head>
<body><div class="wrap">
  <header>
    <div>
      <h1>{_esc(name)}</h1>
      <div class="muted">{_esc(domain)} &middot; {_esc(profile.get('industry') or 'industry n/a')}</div>
      <div class="muted">Contact: {contact_line}</div>
    </div>
    <div class="grade-badge"><div class="g">{_esc(grade)}</div>
      <div class="o">ABI {_esc(overall)} / 100</div>
      <div class="o">{_esc(label)}</div></div>
  </header>

  <div class="summary">{_esc(score.get('summary'))}</div>

  <h2>Priority recommendations</h2>
  <ol class="recs">{rec_rows}</ol>

  <h2>Dimensions &amp; evidence</h2>
  {''.join(dim_rows)}

  {_coverage_section(coverage)}

  <footer>Agent Business Index — generated {date.today().isoformat()} from
  ProPlan AI Visibility Platform. Scores are deterministic and reproducible.</footer>
</div></body></html>"""
