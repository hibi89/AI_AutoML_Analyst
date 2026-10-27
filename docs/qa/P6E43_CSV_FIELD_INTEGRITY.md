# P6E43 — CSV field integrity and prediction schema safety

Date: 2026-10-28 KST. Development branch: `feature/kmong-v1`. Test data: synthetic only.

## Reproduced correctness failure
A CSV header with two columns and three values per row (`amount,area\n1,A,extra\n2,B,extra`) may be loaded by pandas with the first data value treated as an implicit index. This silently moves the other values into the named columns. It can corrupt BASIC descriptive statistics, STANDARD/PREMIUM model input and the trusted PREMIUM repeat-prediction input without an explicit parser failure.

A naive `index_col=False` workaround silently discards surplus values with only a warning, which is unacceptable for customer data fidelity.

## Chosen repair vs rejected alternative
- **Chosen:** Stream logical CSV records through Python's strict `csv.reader` using the requested/fallback encoding before calling pandas. Reject records with **more fields than the header**, with a redacted actionable ValueError. Check at most the first 20,001 records; pandas already enforces the 20,000-row cap. Works with quoted commas and multiline quoted cells.
- **Rejected:** Require exactly equal field count on all records. Though simple, that breaks the preexisting supported behavior where a missing trailing value is represented as `NaN` and may be imputed. Also reject using `index_col=False` alone because pandas can truncate extra data without failing.

Code: `backend/app/main.py`, `backend/app/services/premium_predict.py`. Regression tests: `tests/test_p6e43_csv_field_integrity.py`.

## Execution evidence
- Local isolated pandas 2.2.3 reproduction: surplus first data field becomes implicit index; strict field-width preflight rejects it. Short trailing-missing row remains two-column `NaN`. Valid quoted comma/newline remains two columns. This is not a full local original-application execution.
- GitHub Linux full [40538932576](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40538932576), exact regression-test SHA `7dec46667877a76ffcda244fa7d1688c3f709e4d`: **SUCCESS, 237 passed / 3 skipped / 68 warnings**. Full synthetic preview generation and downstream benchmark/inventory steps SUCCESS; 6/9/11 PDF pages BASIC/STANDARD/PREMIUM.
- Hosted Windows native [40538855018](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40538855018), source SHA `a499c1c4ca830cfc12dd6fbcee44f904bf9c1a4b`: **SUCCESS, 99 passed / 9 warnings**.
- Windows real Chromium [40538854981](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40538854981), Linux real Chromium [40538855332](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40538855332), Docker local-only [40538855073](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40538855073): **SUCCESS** on application SHA `a499c1c4` (new final test-only revisions do not change application code).
- Early intermediate Linux [40538855026](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40538855026) **FAILED, 5 failed / 233 passed / 3 skipped** because an earlier test draft expected exact-width rejection and obsolete `field count` error text. Tests were aligned with the intentional missing-value compatibility contract at `618caed2` / `7dec4666`, with final 237-pass run above. Failure is preserved, not described as a final product regression.

## Remaining gates
This is synthetic CI evidence, not physical owner Windows signoff or customer-data QA. No `main` merge, external deployment, customer data, paid tools, or model artifact changes. Commercial approval remains P6E22: owner PDF/ZIP visual quality, installed fonts and source/dependency licenses/NOTICE, independent BASIC/STANDARD/PREMIUM sale GO decisions. Formal acceptance P0–P6 **5/7 (71%)**; P1 partial, P6 not accepted; all tiers SALE NO-GO.
