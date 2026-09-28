---
name: audit-led-outreach
description: Run the audit-led outbound workflow for AIVE — build a prospect list, batch pre-audit sites, generate personalized grade-hook emails from real ABI findings, and track the sequence. Use when the user wants to prospect, do outreach, send cold emails, build a target list, or launch a metro/vertical batch.
---

# Audit-Led Outreach

The core AIVE growth motion (sales/strategy.md §2): **never send a cold email
without the prospect's real grade.** COGS ≈ $0.004/audit — grade the whole list
first, then personalize from actual findings.

## Workflow

### 1. Build the list (ICP: gtm/01_icp.md)

50–100 prospects per metro batch. Required fields (Pipeline sheet of
gtm/AIVE_kpi_tracker.xlsx): business, website, metro, contact name, verified
email, phone. Qualify: real multi-page site, defined service area, marketing
spend signals (ads, SEO agency, redesign). Disqualify per anti-ICP.

### 2. Batch pre-audit

Run each site through the pipeline (backend CLI; see backend/cli.py and
run_validation harness patterns). Capture per prospect:

- ABI score + grade
- Top gap in plain language (the #1 lowest-scoring, highest-weight finding)
- One evidence snippet (quote from their own site)
- Number of actionable findings
- Optional: a named competitor's grade in the same metro

QA rule: spot-check 1 in 10 reports by hand before any email references them.

### 3. Generate the sequence

Use gtm/09_cold_email_sequence.md templates (5 touches / 21 days). Fill
{{grade}}, {{score}}, {{top_gap_plain}}, {{evidence_snippet}},
{{specific_finding}}, {{competitor_name}}/{{competitor_grade}} (only if a
genuinely higher-graded competitor exists — never fabricate).

**Hard rule: no finding → no send.** If extraction failed or findings are
generic, re-run or skip the prospect.

### 4. Send + track

- 20/day cap, Tue–Thu 7–9am prospect-local, stop-on-reply
- CAN-SPAM footer; hand-built lists only
- LinkedIn warm-up connect 2–3 days before email 1 (gtm/10)
- Log every touch in the Pipeline sheet; weekly funnel row every Friday
  (gtm/13_kpi_dashboard.md)

### 5. Reply handling

- "send it" → teaser (grade + top gap + blurred bars), NOT the full report,
  plus booking link
- Booked call → gtm/08_sales_script.md
- Negative → mark Lost/Nurture with reason (feeds messaging iteration)

## Quality bars

- Reply rate target ≥15%; <8% after 50 sends → stop and rewrite email 1
- Every email contains ≥1 site-specific fact a competitor's email couldn't
- Never promise rankings, mentions, or leads (sales/offer.md "What Not To Sell")
