# Product Improvements Before Launch

Scope discipline: everything here serves selling and delivering audits. No new
ABI dimensions (spec frozen), no roadmap items. P0 blocks launch; P1 within 30
days; P2 nice-to-have.

## P0 — blocks public launch (Week 1–2)

1. **Gate `/api/runs`** (DEPLOYMENT.md §4): rate limit per IP, email-verified
   free grades, per-domain result cache (24h), max pages/crawl cap. Protects
   cost and queue (risk #7).
2. **Teaser-grade output mode:** grade + top gap only (blurred dimension bars),
   distinct from the paid full report. The free/paid line must exist in the
   product, not in manual redaction.
3. **Payment path:** Stripe payment links for $399/$749/$2,500 + checkout link
   on the teaser result page. No invoicing dance for a founding buyer.
4. **Report branding + shareability:** ProPlan logo, date, ABI version stamp,
   plain-language dimension explanations, printable/PDF-friendly HTML. The
   report gets forwarded to webmasters and partners — it *is* the marketing.
5. **Batch pre-audit CLI hardening:** run 100 URLs unattended (retries, failure
   log, CSV in → grades CSV out). The outbound engine depends on it.

## P1 — within 30 days

6. **Email capture + delivery pipeline:** grade result emailed automatically;
   graded-prospect list exportable (feeds sequence + FB custom audiences).
7. **Owner-language pass on recommendations:** every finding renders a
   "why this costs you customers" sentence (sales calls read the report aloud;
   fix-list wording = close rate).
8. **Re-audit compare view:** before/after score + per-dimension delta on one
   page (`reuse_extraction` re-score). This is the proof asset for rungs 3–4.
9. **Crawl robustness for slow sites:** cap heavy-site latency (goettl.com
   ~88s in validation); a prospect watching a spinner for 90s abandons.
10. **Basic analytics events:** grade_run, email_captured, checkout_click,
    purchase — or the KPI sheet (13) can't be filled honestly.

## P2 — nice-to-have (only if idle)

11. White-label report skin (logo swap) for agency resellers.
12. Benchmark percentile line in the report ("you're in the bottom 31% of HVAC
    sites") — auto-generated from the benchmark dataset.
13. Monitoring MVP: scheduled monthly re-score + email diff (cron + compare
    view is enough; no dashboard needed for the first 10 retainers).

## Explicitly not now

ABI Profiles (SaaS/agency weights), ATS anything, MCP/agent integrations,
multi-user accounts, subscriptions self-serve portal. Revisit after 10 paying
customers.
