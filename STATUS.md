# AI AutoML Analyst commercialization — STATUS
Updated: 2026-10-25 KST
Repository: `hibi89/AI_AutoML_Analyst`
Development branch: `feature/kmong-v1`; preserved original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d`
Entry: `WORKER_START_HERE.md`
Next: `docs/dispatch/ACTIVE_TASK.md` (AUTO-KM-P2 READY).

## LOCKED products and method
One existing local-first Python/FastAPI/scikit-learn engine; original `main` untouched. BASIC **60,000 KRW** (quality/KPI/chart/insight/PDF/ZIP), STANDARD **150,000 KRW** (+ 3 non-Dummy models + Dummy baseline), PREMIUM **300,000 KRW** (+ 5 challengers, trusted model, same-schema repeat prediction). Frozen details in `REQUIREMENTS.md` and `docs/product/SKU_MATRIX.md`. MVP first, fill spec gaps, final QA; 2026-10-26 to 2026-10-28 is TARGET not guarantee. No actual paid sales or external hosting before release gates.

## Acceptance-based work tracking (P0–P6)
| Item | Status | Exact evidence / remaining gap |
|---|---|---|
| SETUP | DONE | Branch documentation, roadmap, handoff committed on dev branch |
| P0 original execution | **DONE** | Python 3.11 GitHub Actions run [40199323100](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199323100): original app import and **6 passed / 3 warnings**. `docs/qa/BASELINE.md`. |
| P1 horizontal MVP | **PARTIAL — API TESTED** | `/basic-mvp` + `/api/basic-report`; ZIP of Markdown/CSV/JSON/PNG, guards. Run [40199782514](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199782514): **13 passed / 3 warnings**; subsequent frontend/workflow commit run [40199903389](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199903389): **13 passed / 3 warnings**. Real browser JS/download not run; PDF not yet included. `docs/qa/MVP_P1.md`. |
| P2 ML validity | **READY** | Fix ambiguous task selection, rare target support, Dummy separation and candidate caps; test. |
| P3 BASIC paid report | NOT STARTED | Five suitable charts, Korean PDF 6–8 pages, final ZIP, XLSX/CSV and QA. |
| P4 STANDARD | NOT STARTED | Up to 3 non-Dummy, separate baseline, suitable CV/holdout/leakage and PDF ZIP. |
| P5 PREMIUM | NOT STARTED | Up to 5 non-Dummy, trusted stored pipeline, schema validation and Windows repeated predictions. |
| P6 release | NOT STARTED | Full safety, licensing, performance, fonts, Windows/browser and artifact QA. |
| P7 listing | OPTIONAL FUTURE | Kmong sample/listing after sellable tier passes. |

**Accepted milestones:** **1 / 7 (14%)** P0–P6. P1 implementation exists and HTTP tests pass, but browser execution is pending and thus P1 is not counted accepted. This is not the percentage of total source code written. **Sale-ready:** BASIC NO, STANDARD NO, PREMIUM NO.

## Changed code / verified execution
- New `backend/app/services/basic_report.py` aggregates diagnostics and builds an in-memory archive. Upload limits 30MiB / 20k rows / 50 cols on new route.
- New `frontend/basic_mvp.html`; existing `backend/app/main.py` appended routes; original paths maintained. New local client / Origin guards are NOT a general security audit.
- New tests `tests/test_original_smoke.py` (6) and `tests/test_basic_mvp.py` (7); `requirements-ci.txt`, `.github/workflows/baseline-smoke.yml`.
- Last tested code/workflow SHA: `368872970db656dde03a6361378b7a4ff8f56434`; run [40199903389](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199903389) PASS. Documentation-only commits after this point do not modify executable code.
- The remote HEAD must be fetched each turn; the doc is not a self-updating reference.

## Risks, limitations, action
- Pre-existing folder/path APIs and broad CORS are unsafe on open networks; **NEVER host externally** until hardened. Current local route restrictions do not resolve legacy exposure.
- Task type defaults to classification; rare/constant targets, CV group/time leakage, Dummy candidate caps await P2/P4.
- Missing client-ready PDF, XLSX, final Korean font verification and trusted model/predict package.
- No original customer records were used; no data/API secrets pushed. Clone via container failed due GitHub DNS; connected GitHub + GitHub Actions used instead.
- Python 3.11 validated in CI; real local Windows launch, browser click and ZIP save, Docker/Production URL remain **NOT VERIFIED** or **NOT APPLICABLE**.
- Immediate next: AUTO-KM-P2. Record exact run logs, branch SHA and changed files after implementation. Update STATUS/HANDOFF/ACTIVE_TASK every boundary.
