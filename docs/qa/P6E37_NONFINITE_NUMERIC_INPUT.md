# P6E37 — non-finite numeric input gate, independently verified

Date: 2026-10-27 KST. Repository: `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`. Only synthetic samples were used.

## Actual defect
`chart_design.create_charts` selects a numeric series and passes `dropna()` output to Matplotlib histogram and box plots. `dropna()` does not remove `+inf`/`-inf`. Reproduced Matplotlib `ValueError: supplied range of [1.0, inf] is not finite`. The old shared `validate_basic_frame` checked dimensions, missing/duplicate headers and length, but did not reject infinity. A CSV containing `Infinity` or `-Infinity` in a numeric column could fail before delivering a usable report. ML estimators also cannot interpret such numbers as finite observations.

## Minimal repair
- Exact executable SHA [`c90dbaed53e11fac100a00a8f41b4c8bf52a22d1`](https://github.com/hibi89/AI_AutoML_Analyst/commit/c90dbaed53e11fac100a00a8f41b4c8bf52a22d1).
- In `backend/app/services/basic_report.py`, the already-shared `validate_basic_frame` rejects `+/-Infinity` in pandas numeric columns with an actionable `ValueError`. This is intentionally fail-closed, not silent data cleaning or misleading statistical reporting. True missing `NaN` remains allowed.
- In `tests/test_p3_basic_delivery.py`, two parametric +/-Infinity scenarios verify direct validation and HTTP 400 error responses from all three real FastAPI endpoints `/api/basic-report`, `/api/standard-report`, and `/api/premium-report`. A third test confirms missing NaN is not rejected.
- Scope excludes non-numeric object columns with literal "inf" text; those values remain strings, not numeric infinity. The original input is never committed.

## New source test result — all five CI workflows SUCCESS
| Environment | GitHub Actions run | Verified result |
| --- | --- | --- |
| Linux full suite / PDF preview | [40524775993](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40524775993) | SUCCESS; **216 passed, 3 skipped, 68 warnings** |
| Windows Python 3.11 native | [40524776014](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40524776014) | SUCCESS; **96 passed, 9 warnings** |
| Linux Chromium actual ZIP download | [40524776016](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40524776016) | SUCCESS |
| Windows Chromium actual ZIP download | [40524776048](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40524776048) | SUCCESS |
| Docker localhost compatibility | [40524776120](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40524776120) | SUCCESS |

The Linux full-suite log explicitly includes the new two `test_infinite_numeric_csv_is_rejected_consistently_before_all_sku_reports` parametrizations and final 216-pass summary. It emits two test-setup-only Pandas `FutureWarning` notices due to assigning a floating infinity into an int64 `방문수` fixture; these are not an application failure.

## Immutable owner release boundary
This engineering regression is **closed**. Formal owner-accepted P0–P6 milestones remain **5/7 = 71%**. P1 = PARTIAL, P6 = NOT ACCEPTED. P6E22 still requires actual owner's physical Windows/browser and PDF/ZIP quality review, exact font/software license notice review, and explicit commercial GO per tier. BASIC/STANDARD/PREMIUM all **NO-GO**, original `main` untouched, no public deployment, listing or customer data processing.
