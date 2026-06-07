# Blockers

Active blockers and notable issues. Resolved items kept for history.

## Open

### Goal 01 — `hortonservices.com` did not render (non-blocking)
- 2026-06-06: Homepage fetch returned no usable HTML (timeout / likely bot
  protection); 0 pages crawled.
- Impact: none on Goal 01 completion — validation target (10 sites) was met
  using spare sites in `backend/validation/hvac_sites.txt`.
- Follow-up (future, not required for Goal 01): consider retry/backoff and a
  stealthier fetch profile if specific customer sites block the crawler.

## Resolved

(none yet)
