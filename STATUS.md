# AI AutoML Analyst commercialization — STATUS
Updated: 2026-10-26 KST
Repository: `hibi89/AI_AutoML_Analyst`
Development branch: `feature/kmong-v1`; preserved original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d`
Entry: `WORKER_START_HERE.md`
Next: `docs/dispatch/ACTIVE_TASK.md` (AUTO-KM-P6D READY; P6 release still IN PROGRESS).

## LOCKED products and method
One existing local-first Python/FastAPI/scikit-learn engine; original `main` untouched. BASIC **60,000 KRW** (quality/KPI/chart/insight/PDF/ZIP), STANDARD **150,000 KRW** (+ 3 non-Dummy models + Dummy baseline), PREMIUM **300,000 KRW** (+ 5 challengers, trusted model, same-schema repeat prediction). Frozen details in `REQUIREMENTS.md` and `docs/product/SKU_MATRIX.md`. MVP first, fill spec gaps, final QA; 2026-10-26 to 2026-10-28 is TARGET not guarantee. No actual paid sales or external hosting before release gates.

## Acceptance-based work tracking (P0–P6)
| Item | Status | Exact evidence / remaining gap |
|---|---|---|
| SETUP | DONE | Branch documentation, roadmap, handoff committed on dev branch |
| P0 original execution | **DONE** | Python 3.11 GitHub Actions run [40199323100](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199323100): original app import and **6 passed / 3 warnings**. `docs/qa/BASELINE.md`. |
| P1 horizontal MVP | **PARTIAL — LINUX CHROMIUM GUI TESTED** | Actual Linux Chromium native file chooser/ZIP download **ALL 3 SKUs PASS** [CI 40210012769](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210012769). Korean PDF + ZIP generated; Windows owner's Chrome/Edge install/GUI flow still NOT tested. See `docs/qa/P6C_RELEASE.md`. |
| P2 ML validity | **DONE** | Auto target semantics / class rejection, Dummy outside 3/5 budget, CV guards, model warnings; [CI 40200745818](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200745818): **36 passed / 6 warnings**; `docs/qa/ML_P2.md`. |
| P3 BASIC report/ZIP | **DONE — implementation gate** | Korean searchable PDF **6 pages** on rich synthetic input, **5 meaningful charts**, summary CSV/JSON, integrity-manifest ZIP; GitHub Actions [40202695270](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40202695270) **42 tests PASS**; all six rendered pages visually reviewed, no obvious clipping. Windows/client sale QA belongs to P6. `docs/qa/BASIC_P3.md`. |
| P4 STANDARD | **DONE — implementation gate** | 3 non-Dummy + Dummy, train-only CV, independent holdout, random/group/time split, Korean 9-page PDF, ML scores CSV, ZIP. GitHub Actions [40204087390](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40204087390): **55 PASS**, 16 warnings, all 9 page previews reviewed. Windows/security release QA pending. |
| P5 PREMIUM | **DONE — implementation gate** | 5 challengers + Dummy, top-two CV tuning, trusted skops model, exact-schema CSV repeat runner, 11-page Korean PDF and 20-file ZIP. Python 3.11 [CI 40205977563](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40205977563): **59 PASS, 19 warnings**, all 11-page synthetic previews reviewed. Windows native run + release safety pending. `docs/qa/PREMIUM_P5.md`. |
| P6 release | **IN PROGRESS — NOT ACCEPTED** | P6C real Linux Chromium 3/3 success, pinned direct Python 3.11 versions, Windows native skops/CMD 39 PASS, Linux full suite 78 PASS/1 Windows-only SKIP; [Linux 40210003500](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210003500), [Windows 40210007786](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210007786), [Chromium 40210012769](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210012769). Real ML CV+holdout+tuning performance measured up to 2000 rows/7 predictors. Owner Windows GUI, large-scale 20k×50 ML, PDF design signoff, full compliance and privacy QA pending. |
| P7 listing | OPTIONAL FUTURE | Kmong sample/listing after sellable tier passes. |

**Accepted implementation milestones:** **5 / 7 (71%)** P0, P2, P3, P4, P5. P1 HTTP/API + real Linux Chromium interactions pass, but owner's Windows native browser/first-install remains unverified and P1 is not counted fully accepted. This is not the percentage of total source code written. **Sale-ready:** BASIC NO, STANDARD NO, PREMIUM NO.

## Changed code / verified execution
- New `backend/app/services/basic_report.py` aggregates diagnostics and builds an in-memory archive. Upload limits 30MiB / 20k rows / 50 cols on new route.
- New `frontend/basic_mvp.html`; existing `backend/app/main.py` appended routes; original paths maintained. New local client / Origin guards are NOT a general security audit.
- New tests `tests/test_original_smoke.py` (6) and `tests/test_basic_mvp.py` (7); `requirements-ci.txt`, `.github/workflows/baseline-smoke.yml`.
- Latest tested executable SHA: `ef134ecafe345c7cb8585dbb4d4dce1f48f37349`; [Actions 40204087390](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40204087390) **55 PASS / 0 FAIL / 16 warnings in 12.30s**. STANDARD synthetic artifact `12603068030`: 9 A4 pages, embedded Korean font, all 9 preview images manually reviewed, without obvious clipping. Docs commits after this do not modify code.
- P5 last verified executable commit `f975364a8f1b13d0a7d0074b8932fb9f1ebcd712`; [CI 40205977563](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40205977563): **59 passed, 0 failed, 19 warnings**, with 11-page Korean synthetic PREMIUM report & ZIP. Model, exact schema prediction, SHA tamper guards, CV-only top-two tuning tested. Original `main` remains unchanged.
- Premium generated synthetic `premium_synthetic_demo.zip` includes 20 files incl. `model_pipeline.skops`, schema, `predict.py`, `predict.cmd`, exact requirements, comparison charts, PDF, output templates and manifest. Final selected model `ridge_classifier` alpha 0.5 and second tuned model logistic C 1.6 in this synthetic run; not customer evidence.
- The remote HEAD must be fetched each turn; the doc is not a self-updating reference.

## P6 security and design partial implementation (2026-10-26 KST)
- New shared `chart_design.py` (Korean descriptions, visual scorecard and high-resolution real aggregate charts) used in BASIC + downstream tiers; KPI card layout and expanded quality cautions. **11-page PREMIUM synthetic PDF rendered and visually inspected**; chart better than default Matplotlib, overall report whitespace still being refined.
- Legacy absolute-path browse/scan/analyze APIs blocked globally; no wildcard CORS, local Host/IP/Origin enforcement; old direct CSV upload now bounded. This is a localhost boundary, **not production web security approval**.
- New `tabular_input.py`: CSV and **first-sheet XLSX**, bounded ZIP expansion, read-only, cached formula values, 50-column and 20k-row limits. HTML upload copy updated.
- `scripts/windows_release_qa.ps1` prepared but NOT executed on Windows. Real Windows native Python/Chrome/Edge/predict.cmd gate remains.
- Verified application-code SHA `7bee655575b060a32a2dea1a4d69283343b3f267` via [70 PASS CI 40207446007](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40207446007) (25 warnings); only UI text and documentation commits follow. Live HEAD and latest Actions run always override this snapshot. Details: `docs/qa/P6_RELEASE.md`.
- **P6 not accepted, sale-ready BASIC / STANDARD / PREMIUM all NO, strict milestone progress remains 5/7=71%.** Next task: AUTO-KM-P6B practical Windows/render/benchmark/licensing and release QA.

## Risks, limitations, action
- Pre-existing folder/path APIs and broad CORS are unsafe on open networks; **NEVER host externally** until hardened. Current local route restrictions do not resolve legacy exposure.
- P4 implements train-only CV with separate holdout, random/group/time splits, direct target-copy checks and 3+Dummy evaluation. Unknown derived-target, grouping and post-outcome proxy leakage still needs expert review; randomized split is unsuitable for entity/time-related records unless the split policy is explicitly adapted.
- P3 now generates actual six-page Korean PDF for rich synthetic data, five suitable charts, summary CSV/JSON and SHA-256 ZIP manifest. No Excel XLSX reader yet (CSV UTF-8/CP949 verified); final Windows visual/print/font-license inspection and polished client usability remain release gates. Trusted model/predict package remains P5.
- No original customer records were used; no data/API secrets pushed. Clone via container failed due GitHub DNS; connected GitHub + GitHub Actions used instead.
- Python 3.11 validated in CI; real local Windows launch, browser click and ZIP save, Docker/Production URL remain **NOT VERIFIED** or **NOT APPLICABLE**.
- Immediate next: **AUTO-KM-P6**. Critical business requirement: current BASIC plots are not commercial graphic quality; user explicitly requires substantially better visual hierarchy, Korean axis/units and useful density. P6 task addresses report design FIRST, then all existing legacy CORS/file-path security exposures, CSV/XLSX support gap, Windows browser and actual batch prediction, pin/license checks, performance and final go/no-go. **No SKU is sale ready until P6.**

Latest UI-inclusive verification: [GitHub Actions 40207617902](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40207617902), executable/UI SHA `d883a3d655ea8328c61a7ba006159608ca54b096`, **70 PASS / 25 warnings**, PREMIUM 11 rendered pages; only docs changes afterwards. P6 remains IN PROGRESS and no tier sellable.

## P6B completed work / still blocked
- Code winner: dev SHA `7eb13ab31866902e1e2f24d31c4e3037d1cbf222` (latest production-relevant executable change). Windows **39/39 PASS** (6 warnings) explicitly includes real `cmd.exe` `predict.cmd` usage and output collision. First real batch test found a quoted-folder-backslash bug; fixed `"%~dp0"` -> `"%~dp0."`. Additional Windows owner-preflight script update followed; fetch live HEAD before further writes.
- Linux **77 PASS /1 SKIP/25 warnings**, [40208598555](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208598555), with 11-page PREMIUM synthetic PDF/ZIP and actual 20,000 x 50 BASIC processing benchmark (**1.00 s**, **177,312 KiB RSS**). This is one CI-run synthetic BASIC measurement, not a response-time promise.
- Dates now prioritize a real calendar chart rather than fifth redundant box diagram; fallback box for no date. Tested additional 3 chart scenarios.
- Official NAVER OFL 1.1 font commercial PDF use reviewed and recorded in `docs/qa/FONT_LICENSE_REVIEW.md`. Do not send font files with user artifacts.
- **P6 remains blocked** by owner Windows browser/ZIP flow, first-install fonts, actual local environment, STANDARD/PREMIUM max-load/cancel safeguards, output design density review and cross-platform dependency pin/license reproducibility. All product tiers NO-GO until verified.

## P6C latest verification (2026-10-26 KST)
- **True Linux Chromium GUI** `scripts/p6_browser_smoke.py`: file chooser, form submission, actual ZIP download, PDF/manifest/artifact inspection for BASIC, STANDARD and PREMIUM. [Pinned package CI 40210012769](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210012769) SUCCESS; this does **not** represent owner's Windows desktop browser.
- **Native Windows skops + real cmd.exe** [40210007786](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210007786): **39 PASS, 6 warnings** with direct library versions pinned in `requirements-verified-py311.txt`.
- **Linux 3.11 full suite** [40210003500](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210003500): **78 passed, 1 Windows-only skipped, 25 warnings** with exact verified direct dependencies and `pip check` no broken requirements; all three synthetic PDF artifacts generated. PDF pages visually reviewed in full: 6 BASIC, 9 STANDARD, 11 PREMIUM, Hangul/font/chart legible but density still has unused space.
- **Real synthetic ML benchmark**: 2,000 rows / 7 predictors STANDARD 1.976 s and PREMIUM 5.664 s (one pinned Linux runner, 3CV + Dummy, PREMIUM top-two tuning), NOT customer SLA and NOT 20k×50. Measurements and risks in `docs/qa/P6C_RELEASE.md`.
- Python direct dependency/version/license metadata inventory captured via GitHub CI (14 packages, no missing direct license metadata; transitive security/license risk still not fully certified). Pinned `requirements-verified-py311.txt` used for CI and Windows owner's first run.
- `scripts/windows_release_qa.ps1 -OpenBrowser` now boots uvicorn on localhost, checks health and opens three pages; **script itself not executed on owner's PC**. Owner physical Windows GUI + ZIP extraction + model replay signoff remains a release blocker.
- **STRICT PROGRESS 5/7 (71%)**, P6 NOT ACCEPTED, all tiers NOT SELLABLE. Next P6D: stress/performance at near-guardrail dataset, graphical first-run Windows owner verification, final report layout/accessibility/packaging/licensing and go/no-go. `main` unchanged.
