# ONTOINSIGHT AX P50 exact-source evidence — 2026-11-13 KST

## Basis and architecture
- Final blueprint (private): hibi89/Freelancer branch product/ontoinsight-ax-data-analytics, docs/FINAL_BLUEPRINT.md; phase acceptance in docs/ACCEPTANCE_AND_ROADMAP.md.
- Reuse original AutoML bounded CSV parser, add independent local-only data dictionary + review-only ontology role candidates. Reject external LLM data upload (privacy/cost) and unchanged standalone AutoML (no customer meaning approval).
- Source paths: backend/app/services/ontoinsight_p50.py; scripts/ontoinsight_p50_review.py; tests/test_ontoinsight_p50.py. Executable SHA: 8da6ae98e308f68b52af159a662fe58c20f5bc74.

## Exact-source verification
- [GitHub Actions #43375766099](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/43375766099) SUCCESS, Ubuntu24.04 11 PASS/0 FAIL/0 SKIP, Windows Server2025 11 PASS/0 FAIL/0 SKIP; both compileall PASS.
- Existing original AutoML CSV reader exercised on actual repo by focused tests; no uploaded customer CSV. Synthetic KPI totals: gross 350.00, refund 20.00, net 330.00, 3 unique orders, AOV 110.00; independently reconciled original CSV vs parsed dataframe with Decimal.
- All candidate mappings remain REVIEW_HOLD; actual customer KPI NOT_COMPUTED, ML_NOT_SUITABLE. Source SHA256 invalidates change. No raw row values written to JSON review.
- Local isolated stub harness also 11 PASS (not exact original integration evidence); GitHub CI is authoritative.

## Trace and limits
| Final-design area | Evidence | Classification |
|---|---|---|
| P50 original one-CSV intake | Original bounded read_uploaded_table invoked | SYNTHETIC VERIFIED |
| P50 dictionary + meaning role candidate | column dtype, missing, unique, sensitivity, inferred role | SYNTHETIC VERIFIED / REVIEW_HOLD |
| P50 SHA/source integrity | SHA256 + mismatch rejection | SYNTHETIC VERIFIED |
| P50 >=4 exact KPI test | five synthetic KPI with raw-vs-parsed audit | SYNTHETIC VERIFIED |
| Mapping owner approval / XLSX / joins / real financial report | Not implemented | P70+ PENDING |
| Leakage-safe ML / HTML-Excel-PDF / buyer Windows10/11 | Not implemented/NOT RUN | P85+ PENDING |
| Whole final-blueprint percentage | No owner-approved 100-point weights | OFFICIAL UNASSESSED |

Full original regression, CLI invoked on buyer file, actual customer data/right-to-use, customer mapping approval, buyer Windows10/11, external rights/legal, browser and production are NOT VERIFIED. Vercel N/A. All sale gates RELEASE HOLD.

## Recover, usage and next
- Parent source commit a3ddd8b9d20fee591ad246becab2b4adc89b56d8 remains available as non-destructive recovery base. Original main, original AutoML analysis behavior and customer records unchanged.
- Local review CLI: python -m scripts.ontoinsight_p50_review AUTHORIZED.csv --output FRESH.json. Writes metadata-only new file; buyer runtime NOT VERIFIED.
- P70 next: source-bound owner-signed mapping consent, safe multi-CSV/XLSX intake, cardinality-safe join and independent reconciliation. P85 ML leakage/time/group gating. No final completion rate until all full-blueprint requirements are traced with approved weights.
