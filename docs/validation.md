# Validation Workflow

## Test Layers

### Offline Unit Tests

Run:

```powershell
python -m pytest backend/tests -q
```

These tests cover deterministic crawler helpers, extraction merge logic,
confidence scoring, FAQ validation, provenance routing, actionability detection,
ABI scoring, and freeze guards.

### ABI Benchmark Validation

Run:

```powershell
python -m backend.run_abi_validation --min 50
```

This scores cached profiles for free. It verifies:

- minimum site count,
- explainability,
- repeatability,
- ABI schema validity,
- benchmark distribution.

Generated outputs:

```text
backend/validation/abi_validation_report.md
backend/validation/abi_validation_summary.json
```

Use the generated outputs as the benchmark source of truth.

### Extraction Validation

Run:

```powershell
python -m backend.run_extraction_validation --target 20 --max-pages 6
```

This can call the crawler and LLM unless cached modes are used. It validates:

- crawl success,
- profile schema stability,
- field coverage,
- confidence,
- token usage.

Generated outputs:

```text
backend/validation/extraction_validation_report.md
backend/validation/extraction_validation_summary.json
```

## E2E Smoke Flow

Manual smoke flow:

1. Start backend API on port 8000.
2. Start frontend on port 5173.
3. Open the dashboard.
4. Confirm the benchmark panel loads.
5. Select a scored site.
6. Confirm the ABI score, dimensions, recommendations, and evidence panel load.
7. Click a dimension card and confirm the proof panel updates.
8. Download the HTML report.

Known verified smoke path:

- selected `proplansolutions.io`,
- verified ABI 39 / F,
- verified actionability proof shows Calendly booking at 20/20,
- downloaded `abi-report-proplansolutions.io.html`.

## Freeze Validation

ABI v0.1.1 is frozen. The freeze guard should fail if frozen contracts drift:

```text
backend/tests/test_abi_freeze.py
```

Do not change:

- dimension IDs,
- weights,
- criteria names,
- grade bands,
- profile contract,
- provenance label set,
- ABI version,

without following the change policy in `abi_spec_v0.1.1.md`.

## Investigation Reports

Current calibration/review documents:

- `abi_calibration_review.md`
- `faq_validation_plan.md`
- `extraction_hygiene_plan.md`
- `impact_estimates.md`
- `single_page_bias_review.md`

These are useful for reasoning and product calibration, but generated validation
artifacts remain the source of truth for current benchmark numbers.
