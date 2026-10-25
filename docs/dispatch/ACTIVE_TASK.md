# ACTIVE TASK — authoritative next work item
Updated: 2026-10-25 KST
status: READY
task_id: AUTO-KM-P0
target_branch: feature/kmong-v1
role: lead-engineer-and-implementer
predecessor: Documentation setup committed; **NO commercial code task completed**.
next_after_success: AUTO-KM-P1 in docs/dispatch/ROADMAP.md

## Task — establish exact ORIGINAL application baseline
Purpose: make the existing `main` FastAPI + AutoML run reproducibly and identify any real failures before the MVP feature slice.

### Do now — ordered steps
1. Read `WORKER_START_HERE.md`, `AGENTS.md`, `REQUIREMENTS.md`, `STATUS.md`, `HANDOFF.md`, `docs/architecture/TARGET_DESIGN.md` and source: `backend/app/main.py`, `backend/app/services/{automl_runner,model_selector,task_detector,preprocessor,trainer,evaluator,report_generator,storage}.py`, `frontend/index.html`, `pyproject.toml`.
2. Using connected GitHub, inspect all *current* source/testing files and latest remote development SHA, not past chat summaries. Base edits on that source and preserve existing routes.
3. Add practical reproducible Python 3.11 dependency install and a **small synthetic-data original-code pytest**: one classification, one regression, missing/constant target, plus FastAPI `/health` and upload path if readily achievable.
4. Execute original tests. Since the prior container could not resolve github.com, try a committed GitHub Actions workflow (Python 3.11) and inspect the **actual workflow run result** using connected GitHub actions. If Actions access is missing, mark tests NOT RUN and code changes as unverified, rather than claiming pass.
5. Record exact failures and environment evidence in `docs/qa/BASELINE.md`; only fix critical execution blockers within scope. Continue toward MVP if blocked but with clear test constraints.
6. Update `STATUS.md`, `HANDOFF.md`, this file to next READY ID, and commit all changes to `feature/kmong-v1`. Provide actual commit SHA.

### Acceptance (P0 is DONE only if ALL met)
- Original FastAPI app import/start and a sample original `run_automl_experiment` invocation successfully executed in a trusted environment (not a standalone mimic).
- At least one reproducible synthetic classification/regression test reports actual status and output; test constraints documented.
- Source and test modifications committed to `feature/kmong-v1`; original `main` unchanged.
- `docs/qa/BASELINE.md` records real results with environment and reproducible commands.
- If blocked, mark BLOCKED, not DONE. Proceed with separately scoped P1 work if safe and feasible, but do not quietly count P0 as finished.

### Non-goals
- No mass refactoring, React, external hosting, extra CatBoost dependency, customer data uploads, real credentials or private API access.
- No unapproved merge to main.
