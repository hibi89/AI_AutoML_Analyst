# AI AutoML Analyst — cross-chat handoff
Updated: 2026-10-25 KST
State: STARTUP DOCUMENTATION RECORDED; DEVELOPMENT NOT YET STARTED

## Exact trigger in a new conversation
**[AI AutoML Analyst 깃헙 레포지토리 보고 작업이어가셈]**

Treat this as a request to READ the connected GitHub repo and WORK ON IT, not to ask for the user's prior messages. Project: `hibi89/AI_AutoML_Analyst`. Must explicitly fetch branch `feature/kmong-v1` because default repo branch `main` intentionally remains legacy. First read `WORKER_START_HERE.md` on **feature/kmong-v1**.

## Project identity and owner goals
Local/offline-first AutoML-assisted analytical deliverables for Kmong. Sell **KRW 60k BASIC, 150k STANDARD, 300k PREMIUM**. Shared engine. Original `main` remains unchanged for safe rollback. Aim for **MVP first**, compare to `REQUIREMENTS.md`, then enrich and finish thorough stability/security checks before sale. 3-day TARGET Oct 26–28, 2026, not guaranteed. User expects autonomous task selection, small commits with evidence, no repetitive questions, and new chat startup by one sentence only.

## File reading order
1. `WORKER_START_HERE.md`
2. `AGENTS.md`
3. `REQUIREMENTS.md`
4. `docs/product/SKU_MATRIX.md`
5. `docs/architecture/TARGET_DESIGN.md`
6. `docs/dispatch/ROADMAP.md`
7. `STATUS.md`
8. `HANDOFF.md`
9. `docs/dispatch/ACTIVE_TASK.md`
10. Actual source, tests and recent GitHub history

## Decisions not to re-open
- One existing repo, one dev branch (`feature/kmong-v1`), no new repo or parallel feature branches.
- No React rewrite, paid APIs, hosted app, PostgreSQL, fully custom software/installation.
- Business scope BASIC broad descriptive analytics & report; STANDARD 3 non-Dummy ML models with evidence; PREMIUM 5 non-Dummy + saved local model + future same-schema CSV inference.
- Existing repository models: 22 candidate entries including two Dummy; fix selection/detection and evaluate appropriately before speculative CatBoost.
- MVP horizontal integration first; do not strip minimal safe defaults. No sale before QA.

## Evidence and limits as of handoff
- GitHub repo confirmed public/default `main`; development branch `feature/kmong-v1` created through connected GitHub.
- Baseline main source commit observed previously: `c80c874476f8d5deb4bf611761d89c6d72ca0a2d` (verify exact HEAD on resume).
- Existing files examined via connected GitHub: `README.md`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `backend/app/services/automl_runner.py`, `model_selector.py`, `task_detector.py`, `trainer.py` and others.
- Prior uploaded SQLite independent validation: planner 959 records, raw 7,672 observations; external sklearn test 9/9 models succeeded; **not an execution test of this repository**.
- No real user/customer datasets committed. No original code changes in dev branch yet, only documentation.
- Current main's HTTP server allows unauthenticated filesystem paths/CORS; do not expose to Internet.
- Direct remote github.com networking failed in previous analysis container. GitHub connector reads/writes work. GitHub Actions may provide reproducible original-code tests; verify actual runs rather than assume.

## NEXT TASK — take action immediately
`docs/dispatch/ACTIVE_TASK.md`: **AUTO-KM-P0** READY.
- Reconstruct original app and test pipeline.
- Add reproducible Python 3.11 smoke test / CI if feasible.
- Run original backend, inspect evidence, fix only immediate breakages.
- Then build MVP and fill frozen SKU gaps with actual commits.

## Update protocol at every boundary
Before finishing, refresh `STATUS.md`, `HANDOFF.md`, `docs/dispatch/ACTIVE_TASK.md`; include exact ref and observed commit SHA from remote. If an unexpected failure prevents update, tell user clearly.

## Revision integrity
This file was authored during initial setup. Its own final commit SHA cannot be self-recorded recursively; **fetch the live remote branch HEAD** before development and never rely on SHA in this document as the latest branch tip.
