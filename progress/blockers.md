# Blockers

Active blockers and notable issues. Resolved items kept for history.

## Open

### Goal 02 — some sites are crawl-blocked (non-blocking)
- 2026-06-06: `hellerphc.com`, `jacksonsfourseasons.com`,
  `haukeheatingandair.com`, `comfortexperts.com`, `estesservices.com` returned
  no rendered markdown (bot protection / failed navigation), so extraction had
  no input. `reliablehomecomfort.com` crawled but yielded near-empty content.
- Impact: none on Goal 02 — validation target (20 sites) met with spares, and
  schema was stable across all 21 successfully-crawled sites.
- Root cause is upstream (Goal 01 crawler), not extraction. Follow-up: shared
  with the existing crawler retry/anti-bot item below.

### Goal 01 — `hortonservices.com` did not render (non-blocking)
- 2026-06-06: Homepage fetch returned no usable HTML (timeout / likely bot
  protection); 0 pages crawled.
- Impact: none on Goal 01 completion — validation target (10 sites) was met
  using spare sites in `backend/validation/hvac_sites.txt`.
- Follow-up (future, not required for Goal 01): consider retry/backoff and a
  stealthier fetch profile if specific customer sites block the crawler.

## Resolved

(none yet)
