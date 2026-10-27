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
- A verified feature increment needs code/test evidence and only the documentation that materially changed. Do NOT edit STATUS, HANDOFF, ACTIVE_TASK and README together by habit; keep STATUS for current truth, HANDOFF for recovery/blockers, README for users and AGENTS for durable policy.


## Development acceleration directive (owner, 2026-10-28; overrides inefficient process steps)
- Goal: shortest route to a working and verified product, not commit/test/doc counts. Sequence: MVP -> original specification gaps -> real integration -> security/accuracy/stability -> optional final visual polish; localhost/file bounds, data protection and licensing approval are never waived.
- Work as one coherent feature unit: inspect branch at start, edit related implementation and focused tests together, run focused checks where executable, commit atomically using Git tree or local Git, and run full regression at integration/release boundaries. Do not force-push or overwrite another owner. Recheck branch ref at commit with expected-SHA protection. Stop polling unchanged CI repeatedly.
- Single Windows owner check: from repo root run \`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\verify_local.ps1\`. It reuses \`scripts/windows_release_qa.ps1 -AllTests\`, produces synthetic BASIC/STANDARD/PREMIUM package review, and runs local Chromium 6-path download smoke by default; \`-Quick\` runs existing fast subset+synthetic demo without Chromium, \`-SkipBrowser\` isolates a failed browser-install environment. JSON + log are in ignored \`qa-preview/\`. Existing files/DB/ports remain untouched, no customer records or public deploy. Actual physical owner PDF/ZIP review and commercial approval are separate. Only claim a check after it actually ran.
- **Observed time sinks / basis**: (1) file-by-file GitHub writes/CI polls and four near-duplicate handoff docs after minor repairs (2026-10-28 P6E45–47 history; HANDOFF >580 lines) -> make one atomic feature commit + one short source-of-truth note; (2) Windows release helper only ran a fixed ~10-file pytest subset vs Linux full 273 PASS/3 SKIP (Linux run 40548766131) -> support opt-in \`-AllTests\`, single full verify root command; (3) costly remote CI environment/font/browser bootstrap, a previously recorded apt/font phase ~11 minutes, rather than test execution alone (Linux 273 tests ~64 seconds at run 40548766131) -> focused tests first, avoid duplicate CI and use one local owner check. Other timings are unmeasured; do not present estimates as timings.
- **Execution boundary:** assistant may edit repository, run available CI and inspect hosted logs; Windows GUI/installed-font/client PDF physical assessment requires owner or approved local Codex. Financial transactions, real customer data, public distribution/merge and license/GO require explicit owner approval; never equate automated synthetic passes with human acceptance.
- Next product outcome: confirm current Chromium source-linked CI, run one-click full Windows owner verifier, obtain font/software terms/NOTICE and per-SKU explicit GO, and fix only material remaining functional/security gaps. MVP BASIC/STANDARD/PREMIUM is working in synthetic tests; formal P0–P6 5/7 accepted (71%), P1 partial and P6 owner unaccepted; all tiers SALE NO-GO.

## Communication
Briefly report actual outcome, PR/commit URL, test evidence, blocked actions, next task. When user says "ㄱ", continue without asking for decisions already settled. Preserve context by *updating repository docs*; chat memory is not sufficient.
