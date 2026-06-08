# Single-Page Bias Review — ABI v0.1.1

**Date:** 2026-06-08  
**Scope:** Investigation only. No scoring or implementation changes.  
**Dataset:** 54 current scored profiles under `backend/output/`, matching the current `backend/validation/abi_validation_summary.json`.

## Executive conclusion

ABI v0.1.1 does **not** appear to over-reward single-page websites in the current benchmark. The opposite pattern appears:

- **Single-page sites average ABI 4.5** and are effectively invisible.
- **2-5 page sites average ABI 58.3**.
- **6+ page sites average ABI 66.4**.

The page-count correlation with ABI is positive in this corpus (`r ≈ 0.69`). Current scoring rewards enough structured, corroborated, multi-page evidence more than dense one-page extraction.

Important caveat: the single-page sample is tiny (`n=4`) and mostly consists of weak/failed crawls, not polished one-page businesses. This review is strong evidence against a current benchmark bias, but not proof that a high-quality one-page site could never be over-scored.

## Method

For each scored site, I read:

- `profile.json` for ABI score, dimensions, services, separated blog examples, and criterion details.
- `pipeline.json` for page count and page categories.
- `crawl_coverage.json` for crawl coverage diagnostics.
- `confidence.json` where present.

Groups:

- **single-page:** `pages == 1`
- **2-5 pages:** `2 <= pages <= 5`
- **6+ pages:** `pages >= 6`

`average crawl coverage` below is `pages crawled / meaningful pages found` when available. In this cached corpus it is `1.00` for every group, so the low-coverage flag is more informative than the ratio.

## Requested group comparison

| Group | Sites | Avg ABI | Avg Understanding | Avg Retrieval | Avg Recommendation | Avg Agent Readiness | Avg Semantic Authority | Avg services | Avg corroboration score | Avg crawl coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Single-page | 4 | 4.5 | 10.0 | 3.0 | 0.0 | 5.7 | 2.2 | 1.5 | 0.0 / 15 | 1.00 |
| 2-5 pages | 2 | 58.3 | 84.5 | 49.6 | 55.0 | 44.0 | 47.9 | 10.5 | 1.5 / 15 | 1.00 |
| 6+ pages | 48 | 66.4 | 86.4 | 57.7 | 67.4 | 52.2 | 60.3 | 19.5 | 3.4 / 15 | 1.00 |

## Diagnostic metrics

| Group | Avg pages | Avg facts/page | Avg services/page | Avg content breadth score | Avg blog examples | Avg blog pages | Low-coverage flagged |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-page | 1.0 | 1.8 | 1.5 | 3.0 / 15 | 0.0 | 0.0 | 2 / 4 |
| 2-5 pages | 5.0 | 6.8 | 2.1 | 15.0 / 15 | 0.0 | 0.0 | 0 / 2 |
| 6+ pages | 6.1 | 11.0 | 3.2 | 14.8 / 15 | 0.8 | 0.3 | 0 / 48 |

## Sites by group

### Single-page

| Domain | ABI | Services | Content breadth | Corroboration |
|---|---:|---:|---:|---:|
| goodberlet.com | 12.5 | 6 | 3.0 / 15 | 0.0 / 15 |
| cmcservice.com | 3.8 | 0 | 3.0 / 15 | 0.0 / 15 |
| johnmooreservices.com | 0.8 | 0 | 3.0 / 15 | 0.0 / 15 |
| reliablehomecomfort.com | 0.8 | 0 | 3.0 / 15 | 0.0 / 15 |

### 2-5 pages

| Domain | ABI | Pages | Services | Content breadth | Corroboration |
|---|---:|---:|---:|---:|---:|
| mistersparky.com | 68.5 | 5 | 13 | 15.0 / 15 | 0.0 / 15 |
| morrisjenkins.com | 48.0 | 5 | 8 | 15.0 / 15 | 3.0 / 15 |

### 6+ pages

48 sites. Top five:

| Domain | ABI | Pages | Services | Content breadth | Corroboration |
|---|---:|---:|---:|---:|---:|
| fhfurr.com | 85.7 | 6 | 28 | 15.0 / 15 | 2.5 / 15 |
| mauzy.com | 84.8 | 6 | 15 | 15.0 / 15 | 0.5 / 15 |
| servicechampions.com | 82.2 | 6 | 14 | 15.0 / 15 | 7.1 / 15 |
| snellheatingandair.com | 82.1 | 6 | 14 | 15.0 / 15 | 4.1 / 15 |
| fixmyhome.com | 82.0 | 6 | 32 | 15.0 / 15 | 4.4 / 15 |

## Cause analysis

### 1. Are single-page sites genuinely clearer?

**No, not in this corpus.**

The single-page group is not a set of elegant, dense one-page sites. It is mostly failed or near-empty extraction:

- Average Understanding is only **10.0**.
- Average services count is **1.5**.
- Average Recommendation is **0.0**.
- Corroboration is **0.0** because there are no cross-page signals.

`goodberlet.com` is the only single-page site with any service count, and it still scores only **12.5** ABI.

### 2. Does the scoring model reward density?

**Yes, some criteria reward extracted density, but it is not creating a single-page advantage.**

Count-based criteria such as service coverage, FAQ coverage, trust signals, offers, and CTAs can reward a dense page if the extracted facts are credible enough. However, in the current profile set:

- Single-page sites average only **1.8 facts/page**.
- 6+ page sites average **11.0 facts/page**.
- 6+ page sites also have higher average services/page (**3.2**) than single-page sites (**1.5**).

So density reward exists as a model property, but the benchmark evidence shows dense multi-page sites, not single-page sites, are receiving that benefit.

### 3. Do multi-page sites suffer from blog/content noise?

**Sometimes, but 03E hygiene is containing it, and it is not depressing the multi-page group below single-page sites.**

The 6+ group averages:

- **0.8 blog examples** separated out of scored services.
- **0.3 blog pages** crawled per site.

Most 6+ sites have no separated blog examples. The obvious outlier is `proplansolutions.io`, where **29 blog examples** were routed out of scored services after extraction hygiene. That site scores **39.0**, which is directionally correct after calibration.

Conclusion: blog/content noise remains a site-level risk, especially for non-HVAC content-heavy sites, but it is not causing a general multi-page penalty in the current corpus.

### 4. Is cross-page corroboration too strict?

**Possibly strict, but not a source of single-page over-reward.**

Average corroboration:

- Single-page: **0.0 / 15**
- 2-5 pages: **1.5 / 15**
- 6+ pages: **3.4 / 15**

Single-page sites cannot earn cross-page corroboration, and they do not get compensated elsewhere enough to overcome that. Multi-page sites earn more, but still often earn little relative to the 15-point criterion.

The stricter question is whether corroboration is under-crediting legitimate multi-page consistency. That needs separate spot-checking of repeated facts and `confidence_reason`, but it is not evidence of single-page bias.

### 5. Are content breadth criteria underweighting depth?

**Yes beyond five pages, but not in a way that over-rewards single-page sites.**

The `Content breadth` criterion saturates at five relevant pages:

- Single-page sites earn **3.0 / 15**.
- 2-5 page sites average **15.0 / 15**.
- 6+ page sites average **14.8 / 15**.

This means a 5-page site can receive the same content breadth credit as a 10-page site. So ABI v0.1.1 under-distinguishes 5-page depth from deeper sites. But single-page sites still receive only the minimum partial credit and score extremely low overall.

The practical risk is not “single-page sites are over-rewarded.” The risk is “5-page sites may be treated as breadth-complete too quickly.”

## Interpretation

Current benchmark ordering by page group:

1. **6+ pages:** highest ABI, highest services, highest authority, highest corroboration.
2. **2-5 pages:** viable when the site is compact but structured.
3. **Single-page:** very weak, often low-coverage or empty.

The model currently rewards:

- clear identity and services,
- enough non-blog content pages,
- credible fact extraction,
- FAQ content,
- trust signals,
- contact/actionability,
- schema.org,
- and some cross-page corroboration.

Single-page sites fail too many of those surfaces to score well.

## Recommendations for future calibration (no implementation changes here)

1. **Add a synthetic polished one-page fixture.** The current single-page group is mostly weak crawl output, so it does not test the true edge case: a deliberately dense, well-structured one-page site with schema, FAQ, services, CTAs, trust, and contact.

2. **Track page-count buckets in future validation summaries.** Add reporting for single-page / 2-5 / 6+ groups so this bias check becomes a recurring benchmark, not a one-off audit.

3. **Audit the 5-page saturation point later.** Content breadth maxes at five relevant pages. That is reasonable for MVP speed, but it may under-credit deeper sites once the crawler reliably reaches 10-12 pages.

4. **Spot-check corroboration reasons on strong multi-page sites.** If repeated facts are visibly present but not receiving `repeated across` confidence reasons, the issue is in merge/confidence evidence tracking rather than ABI scoring.

5. **Keep blog-example routing visible.** 03E appears to prevent blog noise from inflating services at the group level, but content-heavy non-local sites should remain a standing calibration witness.

## Final answer

ABI v0.1.1 does **not** over-reward single-page websites in the current 54-site benchmark. Single-page sites are scoring dramatically worse than multi-page sites. The only calibration concern surfaced here is that content breadth saturates at five pages, which may under-credit depth beyond five pages, not that one-page sites are being advantaged.
