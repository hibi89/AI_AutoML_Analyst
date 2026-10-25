# P6C release-depth QA — current evidence, NOT SALE-READY
Updated 2026-10-26 KST. Source `feature/kmong-v1`, original `main` intentionally unchanged.
This is an implementation QA record, **not** a go-live signoff.

## Verified native Chromium GUI, real ZIP download
- GitHub Linux Chromium [40209289729](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209289729): PASS for **all three** local browser pages. The Playwright script `scripts/p6_browser_smoke.py` launches actual localhost uvicorn (127.0.0.1), opens page, uses real file chooser, chooses classification target for ML, clicks the real submit button, awaits browser download, saves the ZIP and validates PDF magic, manifest and tier-specific contents.
- Actual ZIP bytes recorded: BASIC **479,695**, STANDARD **626,494**, PREMIUM **722,198**. These use only synthetic 120-row CSVs. Later Chromium CI [40209395821](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209395821) also passed after PDF/header changes. This is **Linux headless Chromium**, not actual owner's Windows Chrome/Edge. P1 owner's Windows interaction still pending.
- Source: `.github/workflows/browser-smoke.yml`, `requirements-browser.txt`. Runs are temporary CI, not deployment or customer data exposure.

## Real model CPU performance — CV/holdout/tuning included
- Synthetic benchmark `scripts/p6c_model_benchmark.py` exercises `run_standard` with random train/holdout, 3-fold CV, 7 input columns and fixed-seed synthetic labels. Tests both STANDARD Dummy+3 challengers and PREMIUM Dummy+5 challengers with actual top-two CV tuning. No raw actual customer data.
- [Linux CI 40209531361](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209531361), all previous code tests 78 PASS/1 Windows-only SKIP:
  | Rows | STANDARD, s | PREMIUM, s |
  | ---: | ---: | ---: |
  | 120 | 0.851 | 2.570 |
  | 400 | 0.896 | 2.590 |
  | 2,000 | 1.503 | 4.370 |
  Numbers are observed for one runner & 7 features, NOT estimates for 20,000 rows × 50 columns or for user PC. This does not establish all-size ML safety or all target/data types. A newer CI run on updated dependencies varies slightly; check latest logs.

## PDF + input correctness
- Expanded STANDARD ML methodology page with a data-grounded CV/holdout selection card and actual holdout-vs-Dummy difference, still clearly not a significance or future accuracy guarantee.
- Added shared column header validation (maximum 160 characters; no control characters) to prevent unreadable PDF/plots. Initial new test `tests/test_p6_chart_policy.py` accidentally used a *literal* backslash-n rather than a real newline and failed three intermediate CI runs. Corrected test in commit `47a6c2099edba00580e215bc5c9bc8e90016b627`; [Linux CI 40209531361](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209531361) 78/78 other tests passed, no application issue. Do not misrepresent the failed runs as successful.
- Downloaded final PDF preview artifact from [40209596783](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209596783). Visually inspected the 11-page PREMIUM raster montage: Korean text and updated charts visible, STANDARD methodology card appears; some BASIC/ML/PREMIUM pages still have unused whitespace. The PDF is **not** yet approved by the owner for sale.

## Exact installed Python dependencies + licensing inventory
- `scripts/p6c_environment_audit.py`: validates `python -m pip check` (no broken requirements found), captures 14 direct package versions + license metadata and `pip freeze` for Linux Python 3.11. [CI 40209596783](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209596783) passed; artifact `p6c-verified-dependency-versions` contains metadata + exact freeze.
- Direct versions: FastAPI 0.162.0, Uvicorn 0.54.0, pandas 2.3.3, numpy 2.4.6, scikit-learn 1.9.1, python-multipart 0.0.32, httpx 0.28.1, pytest 9.1.1, matplotlib 3.11.2, reportlab 4.5.1, pypdf 6.21.2, Pillow 12.3.0, skops 0.16.0, openpyxl 3.1.5. No direct dependency lacked license metadata, but **transitive package licensing, security vulnerabilities and cross-platform wheel availability remain review items**.
- Added `requirements-verified-py311.txt` with these exact versions, switched Linux CI, Windows native CI, Chromium CI and owner's PowerShell QA installer to it. Pinned cross-platform CI results should be read and logged before accepting. Do not ship a Linux-only `pip freeze` as a universal Windows lock.
- Font metadata: official NAVER Nanum font use recorded in `docs/qa/FONT_LICENSE_REVIEW.md`; no standalone TTF bundled to customers.

## Windows run and known limits
- Windows-native [40208598494](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208598494) proved real `cmd.exe` `predict.cmd` output and safe output-file collision for a trusted synthetic model (39 PASS). Future pinned Windows CI updates will confirm exact versions.
- `scripts/windows_release_qa.ps1` updated: `-OpenBrowser` now actually starts the local uvicorn server in a child process, checks `/health`, and opens the three tier interfaces, logging the local server PID for cleanup. This script was **not run on the owner's physical machine**; the owner must still verify Windows font availability, browser download, ZIP extraction and repeat prediction.
- Still unverified: full 20k×50 ML capacity, worst-case high-cardinality categorical growth, Windows full PDF/font graphics, abnormal Excel/CSV, first-run with actual customer-like data, package vulnerability scan, final product report design signoff, accessibility/print output, real user-account data privacy flow.

## Release gate
**BASIC NO-GO, STANDARD NO-GO, PREMIUM NO-GO.** P0/P2/P3/P4/P5 implementation accepted, P1 partly accepted (Linux Chromium browser works, owner Windows GUI pending), P6 partial; strict milestones **5/7=71%**. No merge to main, public hosting, real customer data upload, price/listing publication.
