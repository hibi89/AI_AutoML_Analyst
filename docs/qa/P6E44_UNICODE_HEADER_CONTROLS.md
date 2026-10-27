# P6E44 — Unicode column-header display integrity

Updated: 2026-10-28 01:32 KST. Repository: `hibi89/AI_AutoML_Analyst`; branch: `feature/kmong-v1`.

## Confirmed source gap
Shared `validate_basic_frame` rejected header characters with Unicode code points below U+0020, but allowed DEL/U+007F, C1 Unicode control characters, and bidirectional format marks (such as U+202E and U+2066). As a result, a customer-supplied header might display in a different visual order than its actual column identity in the PDF/UI or be difficult to audit. This is a display and schema-identity integrity risk, **not** an assertion that an attack occurred.

## Minimal implementation
- `backend/app/services/basic_report.py`: reject any Unicode `Cc` control and explicit directional marks U+061C, U+200E, U+200F, U+202A..U+202E, U+2066..U+2069 before reports/model fitting. Preserve the exact original field name for accepted columns. Keep Unicode Korean/Japanese titles and standard punctuation valid; preserve the 160-character ceiling.
- Alternative considered: stripping/replacing invisible characters. Rejected because normalization might silently merge two distinct source headers or break exact PREMIUM prediction schema mapping; explicit 400 is more reliable for customer data.
- Preserve existing error contract including `control characters` substring for older consumers/tests; append directional-formatting detail.
- `tests/test_p6e44_unicode_header_controls.py`: parameterized code points U+202E, U+2066, U+200F, U+061C, U+007F, U+0085; accept Korean/Japanese ordinary labels; synthetic CSV and XLSX HTTP uploads checked against all three SKU endpoints for 400 without echoing the header.
- This narrowly covers these control classes; it does not claim to detect every visually confusable Unicode letter or malicious-looking ordinary text.

## Verified CI and failure reconciliation
- Earlier [Linux 40541116061](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40541116061) at test SHA `38b23ddfd84a3516915d4c0d239b83043336130b` **FAIL: 1 failed, 249 passed, 3 skipped**. Existing `tests/test_p6_chart_policy.py` expected substring `control characters`; initial new message used `control or bidirectional formatting characters`. This was a backwards-compatibility regression of the error text, not a bypass of the new validation.
- Final code SHA `d668c70ba7913304e2ab936546daa1824e6ab714` keeps the old phrase and adds the new rationale; test SHA `940b9c725d890c3e0c74cc624179edc003322375` validates the new wording.
- Final [Linux full 40541507030](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40541507030): **COMPLETED SUCCESS: 250 passed, 3 skipped, 68 warnings**, 6/9/11-page synthetic PDF preview and remaining original CI steps successful.
- [Windows native 40541497611](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40541497611): **COMPLETED SUCCESS: 99 passed / 9 warnings** on final application code.
- [Windows Chromium 40541497521](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40541497521), [Linux Chromium 40541497729](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40541497729), [Docker local 40541497619](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40541497619): all **COMPLETED SUCCESS** on final application code. These hosted runs use synthetic data; actual owner Windows GUI and customer-license approvals were not performed.

## Release state
Original `main` remains SHA `c80c874476f8d5deb4bf611761d89c6d72ca0a2d`; code changed on `feature/kmong-v1` only. No public deployment/Vercel, payments, customer data or third-party upload. Formal P0–P6 acceptance remains **5/7 (71%)**, P1 partial, P6 owner approval pending. BASIC / STANDARD / PREMIUM each remain **commercial NO-GO**, awaiting actual owner ZIP/PDF visual quality, selected font/software rights/NOTICE assessment and explicit independent per-SKU GO. 
