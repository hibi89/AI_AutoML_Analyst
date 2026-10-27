# P6E32 — Independent visual inspection and SKU-consistent PDF wording

Date: 2026-10-27 KST
Repository: hibi89/AI_AutoML_Analyst / feature/kmong-v1

## Evidence and sample provenance
- Downloaded GitHub Actions artifact `basic-synthetic-pdf-review` (artifact ID 12733681023) from [Linux 40501689831](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501689831), on executable SHA `0afef7c15022486f33ad665716e08651eae420c8`. It contains BASIC/STANDARD/PREMIUM `report.pdf`, page PNG previews and three synthetic ZIPs, not real customer records.
- Directly reviewed contact sheets of 6 BASIC + 9 STANDARD + 11 PREMIUM pages; opened PREMIUM first page at native preview resolution. Used pypdf to extract and compare page text across all 26 pages; counted 6/9/11 pages and detected no `[U+]` placeholder on first pages. This is independent visual/static evidence on the *pre-fix* reports only, not client acceptance.
- ZIP member lists contained 10/13/20 entries respectively, including PDF/charts/summary and ML/predict artifacts only at applicable tiers. This does not certify licenses or privacy for arbitrary customer data.

## Confirmed customer-facing defect
The report's shared BASIC section was reused verbatim by `build_standard_zip` and `build_premium_zip`. Thus the **STANDARD and PREMIUM PDFs opened with the literal `BASIC / EXPLORATORY DATA REPORT`** and had `BASIC 데이터 진단 보고서` footers on their first six pages. The BASIC explanatory text said ML fitting was not included, without clarifying that the upper tier's ML assessment is appended. The later STANDARD/PREMIUM pages did contain real model evaluation, so the product's *technical* model function was not demonstrated to be absent; this was misleading tier copy.

## Design options and selected minimum change
- Option A: rewrite first-page PDF content streams after merging. Rejected: brittle against PDF font subsets, text coordinates and content streams; regression/maintenance cost is high.
- Option B **selected**: pass `report_tier` through the existing `build_basic_zip` → `build_basic_delivery` → `_pdf` path, defaulting to BASIC. STANDARD/PREMIUM use tier-specific cover and footers and say model evaluation is in subsequent pages. Retains one shared engine and preserves plain BASIC semantics.
- Source: `backend/app/services/basic_report.py`, `basic_p3.py`, `standard_delivery.py`, `premium_delivery.py`; regression tests added to `tests/test_p3_basic_delivery.py`, `test_p4_standard_delivery.py`, `test_p5_premium.py`. Final patched test-inclusive SHA: `2fb562144d50652014fdc50a6933b80abac572c2`.
- New CI and new output PDFs were **NOT YET VERIFIED** as of this note; successful previous runs at the old source SHA cannot validate the new label rendering. No release approval granted.

## Aesthetic observations and limits
- Both chart pages and model comparison pages are rendered in a consistent teal visual system, with no obvious missing Korean headings or overlapping blocks at the available raster scale. Significant whitespace remains on the BASIC quality page and some appended ML/handover pages. Do not pad reports with invented insights to fill whitespace.
- Sample synthetic distributions produce repetitive, simple diagrams and perfect correlation values; do not represent them as evidence of accuracy, generalization or buyer usefulness.
- Visual inspection here does not establish actual Windows client rendering, legal permission for each locally selected/embedded font, customer-source rights, or owner acceptance.

## Remaining gates
- Confirm the **new** SHA's full test suite and Linux/Windows browser smoke, plus a new generated actual STANDARD/PREMIUM PDF proving label fixes at the delivery artifact level.
- Owner P6E22: final delivered PDF/ZIP aesthetics, actual font provenance and license/source obligations, and explicit tier-by-tier sale approval. All three SKUs remain NO-GO; milestone gate is 5/7 (71%), not code completion percentage.
