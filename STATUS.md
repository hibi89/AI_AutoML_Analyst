# AI AutoML Analyst commercialization — STATUS
Last update: 2026-10-25 KST
Branch: `feature/kmong-v1`
Canonical entry point: `WORKER_START_HERE.md`
Immediate task: `docs/dispatch/ACTIVE_TASK.md` (AUTO-KM-P0 READY)

## Product decisions — LOCKED
- Existing public repository `hibi89/AI_AutoML_Analyst`, original `main` preserved.
- BASIC **KRW 60,000**, STANDARD **KRW 150,000**, PREMIUM **KRW 300,000**.
- BASIC: genuine diagnostics, suitable ~5 charts, grounded findings 3–5, action suggestions up to 3, ML feasibility, Korean PDF ~6–8p, CSV/XLSX/PNG ZIP.
- STANDARD: BASIC + up to 3 **non-Dummy** sklearn model comparisons, separate Dummy baseline, defensible CV/holdout/leakage notes, PDF 8–12p.
- PREMIUM: STANDARD + up to 5 non-Dummy models, trusted model+preprocessor persistence and same-schema CSV predictions, PDF 10–15p, Windows-tested local tool.
- MVP → specification gap-fill → final broad QA; keep minimal local security controls from start. 3-day sprint TARGET, not guaranteed deadline.

## Implementation status — acceptance-based
| ID | Stage | Status | Evidence |
|---|---|---|---|
| SETUP | GitHub branch, project instructions, specification, roadmap, handoff docs | DOCUMENTED | GitHub create-file commits in feature branch; verify remote files |
| P0 | Original app execution / reproducible tests | READY — NOT RUN | Only independent external sklearn prototype ran previously; original unverified |
| P1 | End-to-end commercial MVP | NOT STARTED | None |
| P2 | ML auto selection and evaluation quality | NOT STARTED | Static weaknesses identified |
| P3 | BASIC reports / plots / ZIP | NOT STARTED | Design mock only; not actual app output |
| P4 | STANDARD comparison / report / ZIP | NOT STARTED | None |
| P5 | PREMIUM trained pipeline / repeated predictions | NOT STARTED | None |
| P6 | Final QA/security/release evidence | NOT STARTED | None |
| P7 | Sales sample and listing material | OPTIONAL FUTURE | None |

### Progress
- Documentation/setup: created (verify remote read before claiming final).
- **Commercial implementation tasks P0–P6: 0 / 7 accepted (0%).** This is not the completion percentage of original source code or design; the existing software may already implement some pieces.
- **Sale-ready tiers: BASIC NO, STANDARD NO, PREMIUM NO.**
- ETA: Oct 26–28 three-day sprint target, confidence uncertain until original app runs; no time estimate treated as verified.

## Source review observations, NOT executed pass/fail
- Existing model selection pool: 10 classifiers / 12 regressors including 2 Dummy. Actual default selection caps 7/6/5, includes Dummy.
- No target auto-detection invocation seen in automl_runner; task defaults to classification if missing.
- Current CV shuffles KFold/StratifiedKFold, so potential account/time leakage.
- HistGradientBoosting candidate appended after limits list and often removed by truncation.
- Unauthenticated arbitrary server path endpoints + CORS permissiveness risk if deployed. Local-only protective bounds required.
- Existing HTML UI hardcoded local API, Markdown reports rather than verified PDF output.
- Direct github.com clone from previous analysis container blocked; connected GitHub actions work for file reads/writes.
- Prior sqlite tests (959 planner tasks and 7,672 post observations) ran with separate sklearn pipeline. **They do not prove the original application ran.**

## Current blockers
- No original-app runtime test evidence yet.
- Need confirm GitHub Actions availability or source archive for test environment.
- Windows execution and PDF rendering unverified.
- Do not expose real user data to public repo.

## Required update on every development turn
Date/time, source branch/remote SHA, ID and status, actual changed files, executed tests + outputs, report artifacts, blockers, exact next task. Update `HANDOFF.md` and `docs/dispatch/ACTIVE_TASK.md` together with this file.
