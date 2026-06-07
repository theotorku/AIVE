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
| 2026-06-06 | Goal 02 | Build | ~300k (est.) | claude-opus-4-8 | single session | ~$6–9 (est.) | v1 single-pass extractor (superseded). Token figure estimated, not metered. |
| 2026-06-06 | Goal 02 v1 | Runtime (validation) | 137,095 | gpt-4o-mini | ~8 min wall | ~$0.025 | v1 full run (superseded by the staged pipeline below). |
| 2026-06-06 | Goal 02 (pipeline) | Build | ~600k (est.) | claude-opus-4-8 | single session | ~$12–16 (est.) | Staged pipeline redesign (10 services modules, schema, tests, validation). Token figure estimated, not metered. |
| 2026-06-06 | Goal 02 (pipeline) | Runtime (validation) | 288,277 (218,035 in + 70,242 out) | gpt-4o-mini | ~25 min wall (21 sites, full rich re-crawl + ~120 per-page LLM calls) | ~$0.075 | Per-page extraction with evidence/confidence. Re-runs reuse cached crawl/profile (~$0). |
| 2026-06-06 | Goal 02 (pipeline) | E2E processing | ~13,700 tokens/site avg | gpt-4o-mini | ~90 s/site (rich crawl + ~6 page LLM calls) | ~$0.0036 / site | Richer than v1 (~$0.0012); adds evidence, confidence, normalization, ABI evidence. |

## Notes

- **Build cost** = agent time to design/implement/validate. Token counts are
  estimates (the session is not metered here); refine if exact usage is needed.
- **Runtime / E2E cost** for Goal 01 is effectively $0 in external spend — the
  crawler uses no paid APIs. Per-website monetary cost begins in Goal 02 when
  LLM-based extraction is introduced.
- Goal 01 processing time is dominated by network settle, ~49 s/site average
  over 6 pages each (range ~25–88 s depending on site weight).
