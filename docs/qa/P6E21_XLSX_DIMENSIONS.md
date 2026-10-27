# P6E21 — XLSX worksheet-dimension robustness (2026-10-27 KST)

## 1. Scope and root cause
While inspecting bounded commercial XLSX intake, identified a real incompatibility with valid XLSX workbooks lacking an `xl/worksheets/sheet1.xml` `<dimension>` element. `openpyxl` read-only mode exposes `sheet.max_row/max_column=None` in this case, and the prior `if sheet.max_column > MAX_COLUMNS` raises `TypeError` instead of importing or returning a controlled 400 response. A falsely small declared `dimension` could truncate rows/columns if `iter_rows` trusted that metadata.

The defect was reproduced in a disposable synthetic XLSX under openpyxl 3.1.5. No customer data, real workbook, font binary, or ML model was used.

## 2. Repair and alternatives
A) Reject all XLSX files missing `<dimension>`: smallest patch, but excludes legitimate third-party exports and leaves underreported-size truncation unless separately checked.
B) **Chosen**: preflight against oversized declared dimensions, reset untrusted read-only dimensions, stream the actual worksheet cells, enforce hard 20k-row/50-column bounds during streaming, and pad ragged records to the real header width. This preserves valid exports while rejecting oversized content without silent slicing.

Code: `backend/app/services/tabular_input.py` commit [7ec96ff](https://github.com/hibi89/AI_AutoML_Analyst/commit/7ec96ff5114dccbfbbffb236af333b2b751f2681).
Regression tests: `tests/test_p6e21_xlsx_dimensions.py` commit [a8bca18](https://github.com/hibi89/AI_AutoML_Analyst/commit/a8bca18524b8f1dc7398ecfed81388fa25aa2cdb), covering missing, underreported, hidden extra columns, oversized reported dimensions. Existing 50-column ragged, XLSX security, CSV and all-tier regression suites were retained.

## 3. Observed verification (not inferred)
- [Linux full pytest 40476509725](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40476509725) on **test-inclusive SHA `a8bca18524b8f1dc7398ecfed81388fa25aa2cdb`**, SUCCESS: **155 passed, 3 Windows-only skipped, 45 warnings**. 3-tier PDF/ZIP generation and existing benchmarks executed in same workflow.
- [Windows native 40476443963](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40476443963) on **application-source SHA `7ec96ff5114dccbfbbffb236af333b2b751f2681`**, SUCCESS: **94 passed, 24 warnings**; BASIC 6, STANDARD 9, PREMIUM 11 pages, all ZIP manifests PASS. This workflow excludes the new P6E21 test file by path filters but runs the changed XLSX implementation and pre-existing XLSX coverage.
- [Linux Chromium 40476443606](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40476443606) and [Windows Chromium 40476443797](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40476443797) on **application-source SHA `7ec96ff`** SUCCESS; each OS verified BASIC, STANDARD, PREMIUM real file-picker/submit/download for auto and explicit cp932, **6/6 flows per OS**.
- [Linux prior no-test commit workflow 40476443771](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40476443771) also SUCCESS. All recorded Actions conclusions checked after completion.

## 4. Limits and release decision
- Synthetic fixtures only: no independent real-world third-party XLSX corpus or corrupted XML fuzz campaign. ZIP inflate/input size limits remain as previously implemented; this change does not imply memory safety for arbitrary hostile workbooks or prove every Excel export compatible.
- Previous owner physical Windows P6E18 local setup 91 PASS and three forms opened, **not** the owner exercising this latest XLSX patch. Do not ask the fatigued owner to rerun installation solely to inflate test coverage.
- No original `main` edits, no external deployment, paid APIs or customer data. Vercel/Production N/A.
- Frozen acceptance **P0–P6: 5/7 = 71%**. P1 manual owner GUI/PDF acceptance still PARTIAL, P6 release gate NOT ACCEPTED. BASIC/STANDARD/PREMIUM **commercial NO-GO**.
- Next release blocker: customer-like manual ZIP opening, report layout/typography review, and explicit legal/commercial signoff by owner. Hosted CI or synthetic sample checks are not substitutes. No additional synthetic-only milestone is required without a new evidenced defect.
