# AI AutoML Analyst — HANDOFF
Last reviewed: 2026-10-25 KST. Next chat wake-up:
**[AI AutoML Analyst 깃헙 레포지토리 보고 작업이어가셈]**

**IMPORTANT:** Read the *live* `feature/kmong-v1` branch in this order:
`WORKER_START_HERE.md` → `HANDOFF.md` → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → `docs/product/SKU_MATRIX.md` → `docs/dispatch/ACTIVE_TASK.md` → relevant source/tests.
The next READY item is `AUTO-KM-P3`. Never rely on the legacy `main` documentation for commercial work.

## 1. Goal, exact requirements, technology
Local-first customer-approved CSV/XLSX data-analysis deliverables for Kmong; BASIC ₩60k (diagnostics, ~5 charts, Korean PDF 6–8p and ZIP), STANDARD ₩150k (+ up to 3 non-Dummy ML + baseline and evaluation), PREMIUM ₩300k (+ up to 5, trustworthy persisted fitted pipeline and repeated same-schema CSV prediction). Tech is current FastAPI/pandas/scikit-learn/HTML UI; no paid API, SaaS, PostgreSQL, React rewrite, customer data in GitHub, or new project. Three-day Oct 26–28 aspirational target. MVP → fill frozen spec gaps → final release QA. `main` must remain unchanged.

## 2. Delivered functionality and rationale
P0 established real original app behavior in Python 3.11. Added reproducible baseline tests and Actions. P1 added `backend/app/services/basic_report.py` with bounded CSV diagnostics, report.md/summary.csv/summary.json/README.txt/in-memory ZIP and one meaningful PNG when supported; `/api/basic-report` and `/basic-mvp` local-only routes appended to existing `backend/app/main.py`; separate `frontend/basic_mvp.html`. This is a quick horizontal MVP; PDF and full SKU quality deliberately deferred to P3. Legacy routes were preserved. Added size 30MiB, row 20k, column 50, local client/host/origin restriction, export formula prefix guard. These restrictions protect new routes only.

## 3. Tests / pass-fail / unverified
- Original baseline: GitHub Actions [40199323100](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199323100), `python -m pytest -q tests/test_original_smoke.py` → **6 passed, 3 warnings in 2.93s**, app import OK.
- Integrated BASIC MVP: [40199782514](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199782514) → **13 passed, 3 warnings in 3.76s**.
- Latest tested code+CI trigger: [40199903389](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199903389), SHA `368872970db656dde03a6361378b7a4ff8f56434` → **13 passed, 3 warnings in 2.82s**.
- P2 final code: [40200745818](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200745818), SHA `8e38ce1c998ccc0da4a4f111313aebedeb52d7b3`, **36 passed / 0 failed / 6 warnings in 3.61s**. Tests exercise task semantics, rare CV, 3/5 non-Dummy + baseline, report integration, original P0 and P1. Initial P2 incremental run [40200601358](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200601358) failed 5/36 due mislocated regression candidate prioritization; corrected in `cf25dfbaa1aa78fc5fd5409fea46c0d16d6e4ccd` and rerun clean.
- Repro: GitHub Actions Python 3.11 or local `python -m pip install -r requirements-ci.txt && python -m pytest -q tests`. No customer data used.
- **NOT VERIFIED:** real Windows local launch, click/download behavior in a real browser, web Console/Network, PDF fonts/pagination, XLSX, full model eval, repeated predictions, public deployment (not planned).

## 4. Completed / in progress / ready / blocked
- P0 **DONE**.
- P1 **PARTIAL acceptance**: functionality and HTTP ZIP tests pass; real browser UI execution unverified. Do not count P1 as fully accepted or sale ready.
- P2 **DONE**: `detect_task` wired into AutoML; numeric ambiguous target requests explicit semantics; constant/rare labels rejected; model selection includes separate Dummy baseline outside default 3 and optional 5 challengers; CV prevents rare-class KFold fallback; regression fold size guard; group/time limits disclosed in report. Validation: 36/36 test PASS. See `docs/qa/ML_P2.md`.
- P3 BASIC Korean PDF charts/insights: **READY**, task fully specified in `docs/dispatch/ACTIVE_TASK.md`. P4 Standard: NOT STARTED; P5 Premium: NOT STARTED; P6 final security/release QA: NOT STARTED.
- Acceptance progress P0–P6: **2 / 7 = 29%** plus partial P1; BASIC, STANDARD, PREMIUM **NOT SELLABLE**.

## 5. Errors, evidence, failed attempts, forbidden retries, alternatives
Previous analysis-container `git ls-remote` of github.com failed DNS; direct clone cannot be assumed possible. No reason to blindly retry the same call. **Pivot succeeded**: connected GitHub file reads/writes and GitHub-hosted CI. Python 3.13 in analysis container is out of project compatibility (<3.13); Python 3.11 CI is authoritative. P2 was corrected after real 5-failure CI from accidental model priority insertion, using minimal targeted fix; latest full suite has 36 PASS, 6 warnings. **Still unresolved:** group/time-aware split and independent holdout, target-derived leakage, and generic filesystem routes/CORS unsafe on public networks. P2 addresses earlier ambiguous task guessing, rare KFold fallback and Dummy budget issues.

## 6. Repository, branch, checked code SHA, paths
`https://github.com/hibi89/AI_AutoML_Analyst`.
Branch `feature/kmong-v1`, main baseline `c80c874476f8d5deb4bf611761d89c6d72ca0a2d`.
Last **tested executable code/workflow commit** `8e38ce1c998ccc0da4a4f111313aebedeb52d7b3` (CI 40200745818, 36 PASS). Several docs-only commits follow; fetch actual live HEAD (including this update) before work. Key source:
`backend/app/main.py`, `backend/app/services/automl_runner.py`, `model_selector.py`, `trainer.py`, `preprocessor.py`, new `basic_report.py`, new `frontend/basic_mvp.html`, `tests/test_{original_smoke,basic_mvp}.py`, CI `.github/workflows/baseline-smoke.yml`.
QA: `docs/qa/BASELINE.md`, `docs/qa/MVP_P1.md`, `docs/qa/ML_P2.md`. New files modified for P2: `backend/app/services/{task_detector,automl_runner,model_selector,trainer,report_generator}.py`, `tests/test_p2_ml_validity.py`, and adjusted `tests/test_original_smoke.py`.
Future work from `docs/dispatch/ACTIVE_TASK.md` + `ROADMAP.md`.

## 7. Production, Vercel, commands, environment
**NO production service, Vercel project or Production URL (NOT APPLICABLE).** Local only, no external deployment approval.
Install `python -m pip install -r requirements-ci.txt`; serve `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`, then open `http://127.0.0.1:8000/basic-mvp`. Swagger `http://127.0.0.1:8000/docs`. Do not start on public interfaces. CI `python -m pytest -q tests`.

## 8. Originals, backup, data/authentication and edit bans
Keep `main` as immutable rollback source. Work only on `feature/kmong-v1` unless separately approved. No customer CSV/SQLite or trained models committed. Test data is synthetic and in-memory. Original HTML and prior API routes have been preserved; P1 adds separate UI/endpoint. Never commit API keys, credentials, `.env`, private data, model artifacts. No paid external services or unsafe pickle loading.

## 9. Next exact priority, steps, acceptance and approvals
Proceed immediately with **AUTO-KM-P3**: read current source/docs and P2 proof; extend current `basic_report.py` with approximately five suitable charts when a real schema supports them, defensible findings/KPI/suggestions, real Korean PDF 6–8p on representative synthetic dataset, `summary.csv`, chart PNGs, and validated single ZIP manifest. Render/inspect actual PDF including Korean glyphs and pagination, test HTTP upload and ZIP, keep legacy P0+P1+P2 green and protect customer privacy. Follow with P4 holdout/scoring/ML report, P5 trust-only pipeline reuse, P6 final QA. Do not silently claim P1 browser acceptance or sale readiness. No new approval required for normal dev-branch source/test changes. Explicit approval needed for merging to main, changing hosting/visibility, user data transmission, fees, or quality/scope reduction. P2 DONE only after actual CI and preserved legacy P0/P1 behavior.

## 10. Time, verification scope and document baseline
Checked 2026-10-25 KST against connected GitHub branch and Actions runs. Last tested executable SHA `8e38ce1c998ccc0da4a4f111313aebedeb52d7b3`; document revision HEAD must be re-fetched because this file's own SHA cannot be self-recorded. Observed verification: Linux GitHub Actions Python3.11, original FastAPI import, **36 synthetic unit/integration tests**, new HTTP endpoint and ZIP contents, P2 model selection/task constraints. **Not** a Windows/browser/manual or production verification. Current `STATUS.md` and `ACTIVE_TASK.md` are synchronized with this handoff.
