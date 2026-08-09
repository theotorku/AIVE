# KPI Dashboard

Weekly-updated single source of truth. Tracker: [AIVE_kpi_tracker.xlsx](AIVE_kpi_tracker.xlsx)
(Weekly Funnel + Pipeline + Unit Economics sheets, targets and variance built in).

## North star

**ABI adoption** = paid audits delivered + sites verifiably improved (re-audit lift).

## Funnel KPIs (weekly)

| Stage | Metric | Target | Red flag |
|---|---|---|---|
| List | new qualified prospects added | 25/wk | list quality < 90% email-verified |
| Pre-audit | prospects graded before touch | 100% | any un-graded outreach |
| Outreach | emails sent (touch 1) | 20/day | — |
| | reply rate | ≥15% | <8% after 50 sends |
| | call booking rate (of replies) | ≥50% | <30% |
| Sales | demo→audit close rate | ≥25% | <15% after 10 calls |
| | paid audits (cumulative) | 10 by day 70 | <3 by day 45 |
| Expansion | audit→fix attach | ≥30% | <15% |
| | fix→monitoring conversion | ≥40% | — |
| Proof | avg ABI lift after fix | +15 pts | <+8 |
| Inbound | free grades run/wk | 25 by day 60 | — |
| | free grade→paid audit | ≥5% | <2% |

## Revenue KPIs (weekly)

- Cash collected (wk / cumulative) — day-90 target $8–12k
- MRR (monitoring) — day-90 target $600+
- Avg revenue per customer; fix attach revenue share

## Unit economics (monthly)

- COGS/audit (LLM + crawl; cost_ledger.md) — keep <$0.05
- Gross margin ≥98% · CAC (paid) <$500 · CAC (outbound) = time-cost only
- LTV proxy: audit + attach × fix + months × monitoring → target LTV:CAC >5:1

## Channel KPIs (weekly)

- Email: opens, replies, positive-reply %, per-email-variant performance
- LinkedIn: grades attributed, agency convos opened, warmed-prospect reply lift
- Facebook: group grade-thread site drops, paid CPL (<$15), retarget CTR
- Referral: % of new customers from referral (target 20%+ by day 90)

## Review ritual (Friday, 30 min)

1. Fill the week's row in the xlsx (all counts from CRM/inbox — no estimates)
2. Compare to targets; every red cell gets one decision: kill / fix / double
3. Update progress/progress.md with the decision log
