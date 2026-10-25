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

## Latest UI-inclusive CI confirmation
- [Actions 40207617902](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40207617902) on commit `d883a3d655ea8328c61a7ba006159608ca54b096`: **70 passed, 0 failed, 25 warnings in 11.11s**, PREMIUM 11-page synthetic PDF preview generated. Changes since earlier code SHA were upload page copy/accept filters. Docs-only commits afterward do not affect code.

## P6B follow-through — measured evidence, 2026-10-26 KST

### Native Windows Python and actual CMD delivery
- [Windows Actions 40208130115](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208130115): **38 PASS / 6 warnings**, Python 3.11, without GUI/font; direct trusted skops model serialization and reload, strict schema, integrity and version validation, legacy HTTP tests.
- Added a **real cmd.exe** test for the exact shipped `predict.cmd`. First execution [40208475083](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208475083) failed **1 / 39**: Windows path `"%~dp0"` has a trailing backslash before the closing quote; subsequent CLI flags became part of the model folder argument. Fixed the batch template to `"%~dp0."`, centralizing `windows_predict_command()` in `premium_delivery.py` and testing those precise bytes.
- [Windows Actions 40208598494](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208598494), executable SHA `7eb13ab31866902e1e2f24d31c4e3037d1cbf222`: **39 PASS / 6 warnings**, includes real `cmd.exe` running `predict.cmd` against a trusted locally generated skops model, output file content and failure to overwrite an existing output. Test platform is Windows GitHub runner, **not the user's PC or interactive Edge/Chrome**.

### Maximum supported BASIC dataset benchmark
- `scripts/p6_benchmark.py` generates **synthetic 20,000 rows × 50 columns**, invokes the actual full BASIC PDF/chart/ZIP generator and records elapsed and peak process RSS.
- [Linux Actions 40208598555](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208598555): full suite **77 PASS / 1 SKIP (Windows-only CMD test) / 25 warnings**, Python 3.11. Max-size BASIC processing **1.00s**, **177,312 KiB ~173.2 MiB process peak RSS**, output ZIP **486,955 bytes**, five charts. These are one synthetic Linux runner execution, NOT performance or memory guarantees on Windows or customer datasets, and NOT a PREMIUM/ STANDARD fit benchmark.
- Similar previous [40208195474](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208195474) achieved 74/74 Linux and 1.54s / 176,920 KiB before P6B-specific tests and time-chart priority.

### Visual design changes and observed PDF
- `chart_design.py` now prioritizes a **valid monthly trend** over a redundant box plot when 5 chart slots would otherwise fill; a box remains for no-date datasets. Added `tests/test_p6_chart_policy.py` (time trend, fallback and sparse no-filler). Chart data are actual month-group means; no filled area implying misleading baseline.
- Retrieved final rendered synthetic ZIP from Linux Actions 40208598555. Examined actual `charts/05_trend.png` and full PREMIUM 11-page raster montage. The Korean time labels, graph lines, axes and source-unit notice display without obvious clipping, and the PDF remains 11 pages. Other PDF pages remain sparse; design remains commercially unapproved.
- `scripts/windows_release_qa.ps1` now includes P6B Windows model command and chart policy tests for owner-local preflight; this script has NOT run on the owner's physical machine.

### Font-use source and compliance
- NAVER's official terms: https://help.naver.com/service/30016/contents/18088?lang=ko&osType=PC . NAVER says Nanum fonts may be used commercially and are OFL 1.1; embedding in generated PDF is permitted, font sold separately prohibited, and font-program redistribution with software requires notices/conditions. Full specific review `docs/qa/FONT_LICENSE_REVIEW.md`.
- We **do not distribute standalone font files** to customers. Remaining release requirements include transitive Python package licenses/pins and Windows font installation validation. This is an engineering source review, not a legal certification.

### Honest release gate
P6B is advanced but NOT accepted. **BASIC/STANDARD/PREMIUM remain NOT SELLABLE** until actual GUI upload/download (preferably owner's Windows Chrome/Edge), first-install/local font test, full commercial PDF design review, full STANDARD/PREMIUM performance and resource bounds, dependency reproducibility and error cases pass. `main` unmodified; no external deployment or actual customer data used.

## P6C linked evidence and updated GO/NO-GO (2026-10-26)
Detailed record: **`docs/qa/P6C_RELEASE.md`**. Real Linux Chromium browser form/ZIP for all three tiers PASS; pinned Python3.11 dependencies Linux 78 PASS/1 Windows-only SKIP, Windows 39 PASS with actual `predict.cmd`, Chromium 3/3 real downloads, synthetic ML CPU + holdout + tuning benchmark at 120/400/2000 rows, pip consistency+declared license metadata inventory. Pinned verified direct dependencies `requirements-verified-py311.txt`; owner PowerShell script can launch localhost UI but actual owner's PC run unverified. All reports rendered and 11-page PREMIUM sample visually inspected; blank-space/design signoff not complete.

**NO-GO BASIC/STANDARD/PREMIUM** pending owner's Windows first-run GUI/zip, report final signoff, worst-case category & 20k×50 ML capacity, transitive licenses/vulnerability review, customer privacy/abuse stress. Strict accepted milestones remain 5/7=71%; no public hosting or main merge.

## P6D — row/encoded-matrix hard guards and actual capacity test (2026-10-26)
New resource-policy and implementation detail `docs/qa/P6D_RELEASE.md`: BASIC 20k descriptive cap remains; STANDARD supervised max 5k rows, 180 encoded columns, 600k train cells; PREMIUM supervised max 3k, 140 encoded, 360k cells. Original legacy model endpoint also row-guarded. Fail before fitting with customer-readable errors, never silently sample. Train-only encoded cardinality estimate and explicitly disclosed dropped identifier columns. Training-derived model importance (where valid) grouped by original column to avoid disclosing private OneHot category labels. Synthetic 50-column near-cap real fit GitHub [40211135507](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211135507) PASS; final regression [40211592836](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211592836) **90 PASS, 1 Windows-only SKIP, 34 warnings**. Native Windows and Chromium prior stage PASS, physical owner's browser not validated. PDF 11-page montage visually reviewed, excessive whitespace persists. P6E ready; **ALL TIERS STILL NO-GO**.


## P6E1 verified (2026-10-26 KST)
PREMIUM last two pages now use real model/CV/untouched-holdout/Dummy numbers and compact runbook, schema counts, ZIP inventory, privacy/provenance caveats; no invented customer scores. Added P6E Korean long-header/privacy/two-page layout regression. [Linux Actions 40212675598](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212675598) on code+test SHA `08dd90f244dc114f045284eb6d6f2b513d664b9b`: **91 PASS /1 Windows-only SKIP/34 warnings**, BASIC 6 / STANDARD 9 / PREMIUM 11 synthetic PDF pages generated. [Windows 40212557635](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212557635) and [Chromium 40212557611](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212557611) SUCCESS at executable SHA `38f68e9064acb3fc4d87193062748249a9026172`. PDF raster page creation verified; human visual signoff on these new pages NOT YET. Physical user's Windows Chrome/Edge/first-install/ZIP extraction still NOT TESTED. No external server deployment or customer data. P6E still IN PROGRESS; strict 5/7 (71%), all SKUs NO-GO. See `docs/qa/P6E_RELEASE.md`.

Remaining: customer-PC first run; full PDF visual signoff; malicious malformed/adversarial cases; dependency-license/security review; tier-specific sales gate. No P7 listing approval.
