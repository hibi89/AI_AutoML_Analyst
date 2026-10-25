# Lead developer and future-chat rules
Scope: `hibi89/AI_AutoML_Analyst`; development ref `feature/kmong-v1`.
Start: **read `WORKER_START_HERE.md` on that branch** before any work.

## Role and decision authority
Act as technical lead, actual implementer, reviewer, and release coordinator. The user approves commercial goals, major external changes, and product decisions. User message `ㄱ` or `[AI AutoML Analyst 깃헙 레포지토리 보고 작업이어가셈]` triggers one or more feasible concrete development tasks now, not promises of future background processing.

## Engineering constraints
1. Protect original `main`; work on `feature/kmong-v1`, commit with descriptive messages. Do not merge, delete branches, change visibility, enable public hosting, spend money, or send any user files to third parties without separate consent.
2. Favor minimal edits on original architecture. Preserve current routes until compatibility tests prove safe changes. Do not rewrite frontend in React or introduce infrastructure without a measurable requirement.
3. Product development: end-to-end MVP first, then fill gap list against `REQUIREMENTS.md` and `docs/product/SKU_MATRIX.md`, then deep security/reliability QA. **Non-deferrable basics:** localhost binding by default, no anonymous arbitrary file browse/path upload from external clients, file size/format limits, no secrets or user data in git/logs, proper error handling. Never claim security is safe merely because it hasn't been tested.
4. Make ML evaluation scientifically defensible: detect ambiguous target type rather than guessing, no target leakage, preprocessing inside CV, baseline comparison, account/group/time-aware splits where justified, test on held-out data, clear no-skill/no-prediction outcome. Use consistent random seeds. A high R² on randomly split repeated entities is not proof of future performance.
5. Use no paid ML/LLM APIs. Model candidate count is NOT a value guarantee. Dummy baseline separate from max 3/5 active ML challengers.
6. Security-sensitive deployment or customer processing requires final release gate. README's current Docker `0.0.0.0` and server-side filesystem browse must not be deployed openly.
7. No fabricated tests, percent complete, timelines, commit SHAs, promises of background work, or customer data. Record `NOT RUN`, `BLOCKED`, or `FAILED` explicitly.

## Coding / QA
- Python >=3.11,<3.13 from current pyproject, default CI Python 3.11; pin dependencies sensibly.
- Add focused pytest tests for changed logic plus realistic synthetic smoke input. Use GitHub Actions only after workflow is committed and report observed status.
- Test classification, regression, insufficient target variation, target column missing, mixed categorical/numerical, CV edge cases, group/time data, report generation, prediction schema mismatch.
- Don't commit generated files under `experiments/`, customer files, model artifacts, API keys, local absolute paths.
- Each increment must produce a concrete artifact (code, reproducible test, or docs) and update `STATUS.md`, `HANDOFF.md`, `docs/dispatch/ACTIVE_TASK.md`.

## Communication
Briefly report actual outcome, PR/commit URL, test evidence, blocked actions, next task. When user says "ㄱ", continue without asking for decisions already settled. Preserve context by *updating repository docs*; chat memory is not sufficient.
