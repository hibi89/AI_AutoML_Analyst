# P6E24 — BASIC ML feasibility gap against frozen design

Updated 2026-10-27 KST. Development branch: `feature/kmong-v1`. Original `main@c80c874` preserved.

## 1. Product/spec comparison
Frozen `REQUIREMENTS.md` BASIC requires: **ML feasibility report, potential target columns, ambiguities, constraints, and recommended additional data**; no ML fitting or auto-classifier/regressor assertion. `docs/product/SKU_MATRIX.md` includes target feasibility guidance.
Before P6E24: BASIC report had generalized caveats, a compact numeric summary, and no column-specific target ambiguity/inspection metadata. Existing MVP PDF/ZIP/manifest, 5 selected charts, quality figures and production of 6-page rich reports already worked.

## 2. Design options and choice
- Option A: add actual sklearn target-selection/ML fitting to BASIC. Broader compute and leakage/price-tier risk, conflicts with contract; **rejected**.
- Option B: implement **pure, bounded, rules-only feature-column review**. Zero external API/model fits. Present at most three **unconfirmed inspection prompts** sorted by explicit outcome-name hints then lowest missingness, flag low-cardinality numerical columns as ambiguous rather than infer classification. Exclude obvious identifier/date columns and constant/empty columns. Output candidate name/type/non-null count/unique/missing %, high-level cautions, conditions and requested client information. No raw category values/record rows. **Chosen** for cost/speed/contract adherence.

## 3. Files and reproducible QA
- New `backend/app/services/ml_feasibility.py`: `inspect_ml_feasibility(df)`, no ML import or fitting, no row values in result.
- Modified `backend/app/services/basic_p3.py`: add `ml_feasibility` to `summary.json`, show only compact client-review candidates and limitation statement on BASIC final PDF page. ZIP, manifest and existing report page scope remain.
- New `tests/test_p6e24_basic_ml_feasibility.py`: candidate metadata, numeric classification-vs-regression ambiguity, identifier/date exclusions, sparse/constant data, text/bool review-only, no customer-like synthetic raw row contents leaking to PDF/JSON/CSV, actual BASIC PDF/ZIP.
- Initial test-inclusive CI [40478697812](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40478697812) **FAILED 1 test/166 passed/3 skipped** because sparse-data diagnostic text omitted the word "추가" expected by test. Not an ML fit failure. Fixed explanatory text in source SHA [b3a102c](https://github.com/hibi89/AI_AutoML_Analyst/commit/b3a102cc90d1c23972a56fd0349752c1b54fa26d).
- Verified FINAL source SHA `b3a102cc90d1c23972a56fd0349752c1b54fa26d`: [Linux full 40478917054](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40478917054) **SUCCESS 167 PASSED, 3 Windows-only SKIPPED, 45 warnings** including true BASIC/STANDARD/PREMIUM PDFs 6/9/11 pages, full ZIP manifests, dependency check. [Windows Chromium 40478917327](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40478917327) **SUCCESS** for BASIC/STANDARD/PREMIUM auto/CP932 actual file upload/form/ZIP download, **6/6 flows**.
- Native Windows and Linux Chromium `b3a102c` jobs are separate runs; verify and record their final conclusions separately (do not infer from Linux or Windows Chromium). Physical owner Windows/new design not tested.

## 4. Design contract reconciliation
| Frozen requirement | Status after P6E24 | Evidence / limitation |
|---|---|---|
| BASIC PDF/ZIP/Charts/KPI | implemented/tested | Real 6 page, ZIP manifest and 5 meaningful charts rich fixture; sparse no filler |
| BASIC ML candidate and ambiguity guidance | **implemented/tested** | Up to three unconfirmed candidates; numeric <=20 unique explicitly ambiguous, no automated classifier choice |
| BASIC additional-data constraints | **implemented/tested** | `summary.json` structured constraints and extra-information requests, short PDF caveat |
| STANDARD 3 challengers + Dummy | regression preserved | CI synthetic; not independently reviewed real customer evidence |
| PREMIUM 5 challengers + repeat prediction | regression preserved | CI synthetic; model retained only in trusted local ZIP |
| Independent preprocessing within every CV fold | **partial known methodological limitation** | Current feature *selection* is derived from entire TRAIN before CV; sklearn imputers/scalers/OHE fit within fold but column inclusion rules are outside CV; review before commercial scientific guarantee |
| Real owner PDF visuals/legal/privacy/go-live | **NOT ACCEPTED** | Existing owner first install/3 forms P6E18 PASS but new report not owner-signed |
| Japanese PDF glyph coverage | **partial** | Linux CP932 graph warnings showed missing certain Japanese glyphs with Korean NanumGothic, despite 200/ZIP/browser functional passes; cannot claim native Japanese PDF typography perfect |

## 5. Release status and next
- Current strict milestone P0..P6: **5/7 = 71%** (P0/P2/P3/P4/P5 accepted; P1 owner visual review PARTIAL, P6 sale gate NOT ACCEPTED). This ratio deliberately measures acceptance gates, not implementation volume.
- Sale decision BASIC/STANDARD/PREMIUM **NO-GO** until physical customer-like ZIP/PDF/legal approval; no production deployment, main merge, font binaries or customer files.
- Next independent engineering focus: verify/fix CV methodology where time-group boundaries may overlap (`TimeSeriesSplit` does not itself group identical timestamps), avoid leaking future labels; evaluate safe split designs with tests. Subsequently Japanese glyph coverage and dependency/resource gate. No need to make owner repeat already-passed setup.
