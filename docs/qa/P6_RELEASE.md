# P6 release QA — partial, NON-SELLABLE (2026-10-26 KST)

## Commercial go/no-go
**NO-GO BASIC, STANDARD, PREMIUM** until real Windows/browser, dependency/font rights, actual client-style ZIP extraction and repeat predictions, performance and final QA evidence pass. This document is not a release approval.

## P6 progress already implemented
1. `backend/app/services/chart_design.py` is the new shared BASIC/STANDARD/PREMIUM graph designer, with a real Korean font, branded navy/teal/gold palette, 155-dpi PNG, units not invented (labeled original-unit), numeric median label, missingness percentage annotations, real named correlation matrix (not anonymous N1), privacy-anonymized category names with explained mapping, quartile view and optional dated trend. Charts remain **data-dependent**, not automatically filled.
2. `backend/app/services/basic_p3.py` now uses those charts, KPI cards on page one, colored footer/top accent, expanded honest data-quality interpretation, and two appropriately sized chart panels per page. Existing PDF/ZIP generator and four tier tests retained. `standard_delivery.py` ML comparison scorecard previously improved. The user explicitly asked for commercial-quality, rather than stock Matplotlib, graphics; this addresses the chart look but further PDF whitespace/layout polish remains.
3. Retrieved synthetic P6 visual artifact from CI [40206740506](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40206740506). **59 PASS; 11 PREMIUM pages rendered** by Poppler. Reviewed all 11-page contact sheet and individual first chart: Korean glyphs rendered, the axes and annotated median are legible, no obvious clipping. Page 2 and 7+ still sparse; PDF is not yet approved as production design.
4. New **local-only HTTP middleware** in `backend/app/main.py`: denies unknown Host, non-loopback peers and Origin not matching local URL/port, even on legacy jobs, and shuts off deprecated arbitrary-path `/api/folders/browse`, `/api/folder/scan`, `/api/analyze-path` for all clients. Removed wildcard CORS, capped legacy `/api/analyze` upload size/rows/columns, preserves 413 as 413 rather than converting to 500. Original safe CSV upload tests still work. **Do not publicly expose** even with this guard; localhost first and future auth/pen-test pending.
5. New `backend/app/services/tabular_input.py` provides **CSV/XLSX** for all 3 commercial report routes. XLSX reads first worksheet only in read-only, `data_only=True` mode (formulas not evaluated), bounds compressed and total uncompressed ZIP sizes, max 20k rows/50 cols, duplicate/blank headers and macro binary parts. Uses `openpyxl` in app runtime, installed via `requirements-ci.txt`. Generated customer report never embeds original full XLSX/CSV rows. Browser file accept filters and input prompts updated.
6. `scripts/windows_release_qa.ps1`: owner-executable Windows 3.11 preflight for Nanum font, dependencies, non-GUI regression suite, optional opening of local BASIC/STANDARD/PREMIUM browser URLs. **It was authored, not run in real Windows**; manual download, CMD prediction, portable fonts still remain blocked.

## Executed CI evidence and specific mistakes fixed
- `40206952327`: 63 tests passed, one failed — legacy 413 converted into 500 by broad except; fixed.
- `40207319483`: 67 tests passed, 3 failed — XLSX iterator padded to 51 columns causing spurious header `None`; fixed to actual worksheet width.
- [GitHub Actions 40207446007](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40207446007): executable SHA `7bee655575b060a32a2dea1a4d69283343b3f267`, **70 PASSED, 0 FAILED, 25 WARNINGS**, Python 3.11 Linux. Includes P0–P5 suites + P6 security/XLSX; generated PDF artifacts for BASIC, STANDARD and PREMIUM. UI text-only commits after this are not code-engine changes and have their own subsequent CI runs. Use live GitHub runs for latest final UI commit.
- Tests added: `tests/test_p6_security.py` remote Host/Origin and legacy path lockout, 413 and column bounds; `tests/test_p6_xlsx.py` BASIC and STANDARD actual XLSX upload, formula non-execution, zip/archive rejection, max 50-column cap, local Host check.
- All data in Actions and download preview is **synthetic**. No customer data or secrets pushed.

## Open release blockers — do NOT claim done
- Real Windows-native Python3.11 run, font present/license and PDF rendering, Edge/Chrome upload/button/actual ZIP download, fresh CSV repeat predict.cmd, schema/tamper/error checks. Programmatically unverified here; do not infer from Linux GitHub Actions.
- Native Windows/office Excel XLSX edge cases, heavy/ragged datasets, performance/timeout and peak memory at the advertised **20k rows / 50 cols / 30 MiB**. Multipart body may be spooled before handler rejects content.
- Dependency lock/pins, `NanumGothic` font embedding/redistribution rights, `skops` safety review, final artifact provenance/manifest and user instructions, page-density/accessibility review. SHA-256 is integrity only, not source authentication. P6's local-only middleware is NOT authorization for public deployment.
- Feature leakage beyond literal duplicates; CV group/time split depends on correctly specified metadata, tune-on-CV optimism, customer-data bias; no performance guarantees.
- Windows helper does not verify GUI actions by itself. P1 remains PARTIAL until actual browser testing.
- Final finished PDF sample needs better information density on sparse pages; the graph styling is substantially improved but report is not a final client-approved template.

## Next focused P6 subtask
Run / automate Windows non-GUI checks, inspect actual fresh client-like inputs, stabilize PDF spacing and detailed chart accessibility, benchmark large bounded dataset, pin versions/audit font and model trust, independently verify actual ZIP and CMD runner. Then update STATUS/HANDOFF/ACTIVE_TASK, compute evidence-backed tier-specific GO/NO-GO. Do not start P7 sale/listing or merge main while blockers remain.
