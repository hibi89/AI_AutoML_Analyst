# AI AutoML Analyst commercialization — STATUS
Updated: 2026-10-25 KST
Repository: `hibi89/AI_AutoML_Analyst`
Development branch: `feature/kmong-v1`; preserved original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d`
Entry: `WORKER_START_HERE.md`
Next: `docs/dispatch/ACTIVE_TASK.md` (AUTO-KM-P6B READY; P6 release still IN PROGRESS).

## LOCKED products and method
One existing local-first Python/FastAPI/scikit-learn engine; original `main` untouched. BASIC **60,000 KRW** (quality/KPI/chart/insight/PDF/ZIP), STANDARD **150,000 KRW** (+ 3 non-Dummy models + Dummy baseline), PREMIUM **300,000 KRW** (+ 5 challengers, trusted model, same-schema repeat prediction). Frozen details in `REQUIREMENTS.md` and `docs/product/SKU_MATRIX.md`. MVP first, fill spec gaps, final QA; 2026-10-26 to 2026-10-28 is TARGET not guarantee. No actual paid sales or external hosting before release gates.

## Acceptance-based work tracking (P0–P6)
| Item | Status | Exact evidence / remaining gap |
|---|---|---|
| SETUP | DONE | Branch documentation, roadmap, handoff committed on dev branch |
| P0 original execution | **DONE** | Python 3.11 GitHub Actions run [40199323100](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199323100): original app import and **6 passed / 3 warnings**. `docs/qa/BASELINE.md`. |
| P1 horizontal MVP | **PARTIAL — API TESTED** | `/basic-mvp` + `/api/basic-report`; ZIP of Markdown/CSV/JSON/PNG, guards. Run [40199782514](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199782514): **13 passed / 3 warnings**; subsequent frontend/workflow commit run [40199903389](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199903389): **13 passed / 3 warnings**. Real browser JS/download not run; PDF not yet included. `docs/qa/MVP_P1.md`. |
| P2 ML validity | **DONE** | Auto target semantics / class rejection, Dummy outside 3/5 budget, CV guards, model warnings; [CI 40200745818](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200745818): **36 passed / 6 warnings**; `docs/qa/ML_P2.md`. |
| P3 BASIC report/ZIP | **DONE — implementation gate** | Korean searchable PDF **6 pages** on rich synthetic input, **5 meaningful charts**, summary CSV/JSON, integrity-manifest ZIP; GitHub Actions [40202695270](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40202695270) **42 tests PASS**; all six rendered pages visually reviewed, no obvious clipping. Windows/client sale QA belongs to P6. `docs/qa/BASIC_P3.md`. |
| P4 STANDARD | **DONE — implementation gate** | 3 non-Dummy + Dummy, train-only CV, independent holdout, random/group/time split, Korean 9-page PDF, ML scores CSV, ZIP. GitHub Actions [40204087390](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40204087390): **55 PASS**, 16 warnings, all 9 page previews reviewed. Windows/security release QA pending. |
| P5 PREMIUM | **DONE — implementation gate** | 5 challengers + Dummy, top-two CV tuning, trusted skops model, exact-schema CSV repeat runner, 11-page Korean PDF and 20-file ZIP. Python 3.11 [CI 40205977563](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40205977563): **59 PASS, 19 warnings**, all 11-page synthetic previews reviewed. Windows native run + release safety pending. `docs/qa/PREMIUM_P5.md`. |
| P6 release | **IN PROGRESS — NOT ACCEPTED** | Shared branded Korean graph engine/KPI PDF, localhost/Origin/Host and legacy-path lockdown, bounded CSV/XLSX, Windows QA script prepared. [CI 40207446007](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40207446007): **70 PASS / 25 warnings**. Real Windows/browser/predict.cmd, font rights, high-volume benchmark and final visual density still NOT VERIFIED; see `docs/qa/P6_RELEASE.md`. |
| P7 listing | OPTIONAL FUTURE | Kmong sample/listing after sellable tier passes. |

**Accepted implementation milestones:** **5 / 7 (71%)** P0, P2, P3, P4, P5. P1 HTTP/API implementation passes but real browser interaction is pending and P1 is not counted fully accepted. This is not the percentage of total source code written. **Sale-ready:** BASIC NO, STANDARD NO, PREMIUM NO.

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
