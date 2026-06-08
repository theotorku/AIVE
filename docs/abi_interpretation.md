# Interpreting AI Visibility Audit Scores

## Overall Score

The AI Visibility Audit is powered by ABI, a 0-100 score.

| Grade | Range | Label |
|---|---:|---|
| A | 90-100 | AI-Optimized |
| B | 75-89.9 | AI-Ready |
| C | 60-74.9 | Partially Visible |
| D | 40-59.9 | Low Visibility |
| F | 0-39.9 | Invisible to AI |

An A is intentionally difficult. A high score requires clear services,
retrievable content, trustworthy proof, actionability, and machine-readable
authority.

## Five Dimensions

### AI Understanding — 25%

Can AI tell what this business is and what it does?

Common signals:

- business name,
- industry/category,
- services,
- service clarity,
- location/address signals.

### AI Retrieval — 25%

Can AI find and retrieve useful answers from the website?

Common signals:

- FAQ coverage,
- FAQ answer quality,
- heading structure,
- service area specificity,
- content breadth.

### AI Recommendation — 20%

Would AI have enough proof to recommend the business?

Common signals:

- trust signals,
- reputation diversity,
- offers/incentives,
- confidence of trust evidence.

### Agent Readiness — 15%

Can an AI assistant help a user contact, book, or act on the business?

Common signals:

- phone,
- email,
- address,
- hours,
- online booking tier,
- calls to action.

Online booking tiers:

| Tier | Meaning | Points |
|---|---|---:|
| T3 | Deep-linkable scheduler or machine-readable action | 20 |
| T2 | Fillable booking/quote form | 12 |
| T1 | Booking/contact intent only | 6 |
| T0 | No actionability signal | 0 |

### Semantic Authority — 15%

Does the website provide enough structured, corroborated, authoritative
information for AI to trust it?

Common signals:

- schema.org structured data,
- service depth,
- geographic authority,
- FAQ depth,
- cross-page corroboration.

## Recommendations

Recommendations are ranked by **ABI impact**:

```text
points left on criterion x dimension weight
```

The top recommendation is the highest-leverage fix according to the frozen ABI
v0.1.1 model.

## Confidence

Extracted facts carry confidence scores. ABI v0.1.1 uses confidence-aware
scoring so weak evidence contributes less than strong evidence.

Examples:

- a service in headings and repeated across pages counts more,
- a one-off low-confidence city mention counts less,
- schema.org-supported facts are stronger.

## Crawl Coverage

Low crawl coverage means the report may be incomplete. A low score from a
blocked or shallow crawl should be interpreted carefully.

Coverage diagnostics live in:

```text
backend/output/<domain>/crawl_coverage.json
```
