# P6E23 — PREMIUM exact-schema sample CSV formula-header protection

Verified: 2026-10-27 KST. Branch `feature/kmong-v1`. No customer data.

## Confirmed source-level defect
`backend/app/services/premium_delivery.py` generated a customer-facing `sample_input.csv` by passing `raw_schema["raw_feature_columns"]` directly to `csv.writer`, without the `_csv_safe` protection already used for BASIC `summary.csv`. Spreadsheet software may interpret first-row cells beginning with `=`, `+`, `-`, or `@` as formulas. CSV quote characters alone do not neutralize spreadsheet formulas. A client-controlled malicious feature name could be retained verbatim in the ZIP template.

## Safe design choice
1. Escape/prefix feature headers in the shipped template: invalidates the exact-column contract enforced by `premium_predict._load_input`; unusable without renaming after Excel editing.
2. **Chosen:** fail closed *before* PREMIUM ML training when a required feature column's trimmed header starts with a formula prefix. Return a generic actionable 400 message without reflecting supplied names. Do not affect BASIC or STANDARD reports or non-feature target/group/time metadata. Existing legitimate names such as `gross-margin` or `sales@shop` are unchanged.
The user may rename dangerous source feature names locally and resubmit. No new infrastructure, paid API, external data or model changes.

## Change and tests
- Code: [2fa2448](https://github.com/hibi89/AI_AutoML_Analyst/commit/2fa2448ce32b01df0d70188b9cc2cf353e82b736) `backend/app/services/premium_delivery.py`.
- Test: [9cd74cc](https://github.com/hibi89/AI_AutoML_Analyst/commit/9cd74ccdb2c164efe2c59415c1227bc8317c64a5) `tests/test_p6e23_premium_csv_formula.py`. Includes five explicit unsafe prefixes, skip expensive model fitting assertion, no malicious header disclosure, safe business headers, exclusions and a legitimate schema.
- New test-inclusive [Linux full CI 40477711873](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40477711873): **SUCCESS, 163 PASSED, 3 SKIPPED, 45 WARNINGS** on SHA `9cd74ccdb2c164efe2c59415c1227bc8317c64a5`. This includes all eight new P6E23 tests plus pre-existing suite.
- Application-source [Windows native 40477642500](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40477642500): **SUCCESS, 94 PASSED, 24 WARNINGS**, PDF and manifest BASIC6 / STANDARD9 / PREMIUM11 pages. Existing Windows workflow selects a subset and does not independently execute the new P6E23 tests; the entire new test file ran in Linux full.
- Application-source [Windows Chromium 40477642604](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40477642604): **SUCCESS**, actual browser file chooser/upload/ZIP download BASIC/STD/PREM across default auto and explicit CP932 encodings, **6/6 PASS**. P6E23 adversarial inputs were unit/API tested under Linux, not native Windows browser.
- Any in-progress runs at documentation time must be checked for final conclusions before claiming success. No claims of customer physical Windows commercial signoff.

## Current gate and next action
Physical owner first install/3 screens was observed previously in P6E18. The owner has NOT approved design aesthetics, actual manually extracted client ZIP/PDF, third-party font/legal delivery, or commercial listing. All three SKUs **NO-GO**; frozen P0–P6 strict accepted 5/7 = **71%**, P1 PARTIAL, P6 NOT ACCEPTED. Original `main@c80c874` unmodified, no Vercel/production and no customer models/source CSV/font binaries committed.
Next owner-dependent P6E22 one-session review remains necessary when the owner chooses. Do not repeat prior successful first-install QA or claim sale readiness from CI.
