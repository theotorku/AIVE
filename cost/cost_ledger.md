# Cost Ledger

Every goal completion must update this ledger.

Track: build cost, runtime cost, E2E processing cost.
Per entry: tokens, model, duration, estimated spend.

---

| Date | Goal | Type | Tokens | Model | Duration | Est. Spend | Notes |
|------|------|------|--------|-------|----------|------------|-------|
| 2026-06-06 | Goal 01 | Build | ~250k (est.) | claude-opus-4-8 | single session | ~$5–8 (est.) | Crawler design, implementation, tests, validation. Token figure estimated, not metered. |
| 2026-06-06 | Goal 01 | Runtime (validation) | n/a | n/a (local) | ~8.2 min wall (11 sites) | ~$0.00 | Playwright + trafilatura run locally; no paid API. Compute/bandwidth only. |
| 2026-06-06 | Goal 01 | E2E processing | n/a | n/a (local) | ~49 s/site avg | ~$0.00 / site | Goal 01 (crawl + markdown) has no LLM cost. Extraction/scoring costs arrive in Goal 02/03. |
| 2026-06-06 | Goal 02 | Build | ~300k (est.) | claude-opus-4-8 | single session | ~$6–9 (est.) | Extraction engine design, schema, tests, two validation runs. Token figure estimated, not metered. |
| 2026-06-06 | Goal 02 | Runtime (validation) | 137,095 (full run: 127,421 in + 9,674 out) | gpt-4o-mini | ~8 min wall (20 extracted; crawl reused) | ~$0.025 | First full run extracting 20 sites. Re-run with cache reuse cost ~$0.0014. |
| 2026-06-06 | Goal 02 | E2E processing | ~6,855 tokens/site avg | gpt-4o-mini | ~6 s/site extract (crawl extra) | ~$0.0012 / site | LLM extraction only; crawl cost from Goal 01 (~$0). Combined crawl+extract ≈ $0.0012/site. |

## Notes

- **Build cost** = agent time to design/implement/validate. Token counts are
  estimates (the session is not metered here); refine if exact usage is needed.
- **Runtime / E2E cost** for Goal 01 is effectively $0 in external spend — the
  crawler uses no paid APIs. Per-website monetary cost begins in Goal 02 when
  LLM-based extraction is introduced.
- Goal 01 processing time is dominated by network settle, ~49 s/site average
  over 6 pages each (range ~25–88 s depending on site weight).
