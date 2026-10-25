# Kmong SKU matrix — FROZEN v1.0
Date: 2026-10-25 KST. Applies to this repository's commercial `feature/kmong-v1`.
ONE shared analysis engine, SKU-specific deliverables. Prices in KRW; no paid API.

| Deliverable | BASIC 60,000 | STANDARD 150,000 | PREMIUM 300,000 |
|---|---|---|---|
| Files | 1 CSV/XLSX | same | same |
| Diagnosis (shape, types, missing, dupes, outlier indication) | YES | YES | YES |
| Suitable descriptive KPIs | 5–10 when available | YES | YES |
| Meaningful visualizations | ~5 | 6–8 | >=8 if warranted |
| Grounded findings | 3–5 if warranted | YES | YES |
| Qualified practical suggestions | up to 3 | YES | YES |
| ML feasibility / target guidance | YES | YES | YES |
| ML fitting / classifier-regressor selection | NO | YES | YES |
| Non-Dummy model challengers | 0 | up to 3 | up to 5 |
| Dummy baseline | feasibility only | run separately | run separately |
| CV / leakage / independent holdout | no fitting | YES | YES |
| Basic feature importance, if valid | NO | YES | YES |
| Limited extra tuning | NO | NO | top 1–2 models |
| Final trained pipeline artifact | NO | NO | YES |
| Repeat prediction on matching CSV schema | NO | NO | YES |
| Korean PDF pages (target) | 6–8 | 8–12 | 10–15 |
| Result tables | diagnostic CSV or XLSX | + model scoring CSV | + new predictions CSV |
| Visual artifacts | graph PNGs | + ML plots | + prediction/output plots if warranted |
| User guide | short reading guide | findings/method guide | + local repeat-prediction guide |
| Delivery | single ZIP | single ZIP | ZIP + trusted local predict utility |
| Corrections | 1 | 1 | 2 |

## Commercial boundaries
- Delivery is tailored **analysis and reports**, not custom web development.
- One target / dataset per order, with one data dictionary or schema description as needed.
- Guidance guardrail for initial listing: <=20,000 rows, <=50 columns, <=30MB. Confirm actual capacity with benchmark.
- Correction means genuine analytical/report inaccuracies within original dataset + target; replacing the dataset or prediction target is a new scope.
- Customer data must be approved, lawful, deidentified; do not upload into GitHub or third-party tools. Only local processing until separately approved.
- No model performance guarantees; if data unsuitable, deliver honest feasibility/limitation findings and clarify customer expectation before work proceeds.
- No guaranteed chart count or insight count when data cannot support meaningful material.
- Excel optional dependency / licensing and PDF Korean font embedding must be actually tested before advertising XLSX/PDF support.

## Acceptance artifacts per tier
- BASIC: `report.pdf`, `summary.csv` or `summary.xlsx`, `charts/*.png`, `README.txt` zipped; report 6–8 pages in appropriate sample dataset.
- STANDARD: BASIC artifacts + `model_scores.csv`, suitable model comparison graphics and validity warnings.
- PREMIUM: STANDARD artifacts + `model_pipeline` trusted serialized bundle with pinned versions, `predict.py` or equivalent local runner, `sample_input.csv`, `sample_predictions.csv`, user-guide and schema tests.
- Before go-live validate every ZIP against declared SKU; no BASIC-only items silently missing; never ship fabricated ML scores.

## Pricing and internal labor target (aspirational, not measured)
BASIC <60min, STANDARD <120min, PREMIUM <240min internal operations once mature; record actual observed time and do not assume targets achieved.
