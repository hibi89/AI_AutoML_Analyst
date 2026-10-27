# AI AutoML Analyst — 새 채팅 / 새 작업자 진입점
Updated: 2026-10-25 KST
Repository: https://github.com/hibi89/AI_AutoML_Analyst
Development branch: `feature/kmong-v1`
Preserved original: `main`

## One-line wake-up command
**[AI AutoML Analyst 깃헙 레포지토리 보고 작업이어가셈]**

When a new chat receives that sentence, act as the **single lead engineer/project owner for this repository**, use the connected GitHub repository to reconstruct state, and **proceed to the next actionable task without asking the user to restate decisions**. The phrase is authorization to continue ordinary repository development in the approved development branch, **not** authorization to expose private data, deploy production services, spend money, merge into main, or change GitHub visibility.

### Mandatory startup sequence
1. Confirm repository `hibi89/AI_AutoML_Analyst`, list branches, and read the **latest remote** version on `feature/kmong-v1` of:
   - `WORKER_START_HERE.md` (this file)
   - `AGENTS.md`
   - `REQUIREMENTS.md`
   - `docs/product/SKU_MATRIX.md`
   - `docs/architecture/TARGET_DESIGN.md`
   - `docs/dispatch/ROADMAP.md`
   - `STATUS.md`
   - `HANDOFF.md`
   - `docs/dispatch/ACTIVE_TASK.md`
   - most recent code/tests and recent Git commits
2. Confirm the latest branch SHA. Treat `STATUS.md` and `HANDOFF.md` as summaries; actual code, test logs, and remote commits are authoritative if they disagree. Reconcile discrepancies.
3. Select the one READY task in `docs/dispatch/ACTIVE_TASK.md` (or the next unblocked task in the roadmap). **Implement** it, not just plan it.
4. Work only on `feature/kmong-v1` by default. Execute runnable tests, record honest evidence, commit code/docs, and update the status, handoff, and next READY task. Avoid claiming success without executed verification.
5. Report: completed work, tests actually run, failed/blocked items, branch + commit SHA, overall project progress (completed acceptance criteria / total, no invented percentages), remaining effort estimate, next task. User shorthand `ㄱ` means continue immediately following the same routine.

### Approved decisions — DO NOT renegotiate without material necessity
- Keep the existing GitHub repository. Preserve current `main` (original application); no wholesale rewrite, new repository, or automatic merge to main.
- Product: **local/offline-first paid data-analysis deliverables on Kmong**, not hosted SaaS. Three prices: BASIC **60,000 KRW**, STANDARD **150,000 KRW**, PREMIUM **300,000 KRW**.
- Build plan: **working end-to-end MVP first → compare to frozen specification and fill gaps → final comprehensive security/stability QA**. Maintain basic protective boundaries from the first step (synthetic/non-sensitive data, localhost only, input validation, no unsafe file exposure).
- Target: **3-day sprint** starting Oct 26, 2026 (KST), with 10/28 as aspirational release-candidate checkpoint, **not a guarantee**. Ship only verified tiers. No untested PREMIUM sales.
- Technology: reuse current Python/FastAPI/pandas/scikit-learn and single HTML UI initially; one development branch; avoid unnecessary React, PostgreSQL, SaaS, paid AI/ML API, elaborate branch graph.
- Baseline models: existing `model_selector.py` registers **10 classification + 12 regression candidates**, of which 2 are Dummy baselines, not 22 distinct algorithms; test/fix actual selector before adding CatBoost. No blanket "AI-written report" claims; current explanations are rule-based.
- Tiers: BASIC substantial diagnostics/visuals/insights/PDF; STANDARD adds up to 3 non-Dummy ML models; PREMIUM up to 5 + trained-model artifact and repeat predictions on same schema. Dummy baseline is not counted against paid model caps. Scope details: `docs/product/SKU_MATRIX.md`.
- Do not commit real user/customer CSV/SQLite/files or credentials. Earlier standalone scikit-learn tests on two SQLite files are **not** original GitHub application end-to-end tests. The original has **NOT** been executed successfully in the analysis container as of this handoff.

### Environment / execution unblock
- Direct GitHub network from prior analysis container was blocked, but the **connected GitHub app** reads/writes repository files. Use app actions for GitHub work; do not conflate download/network failure with app failure.
- Prefer a reproducible repository **GitHub Actions CI smoke test** as an alternative to unavailable local git clone, or uploaded source archive if available. If Actions is unavailable, record the blocker and continue with code/tests and an executable validation workflow. Never fabricate passing CI.
- Initial READY task: see `docs/dispatch/ACTIVE_TASK.md`. Do not wait for an additional prompt beyond the one-line wake-up command.

### Updated records required at every work boundary
- `STATUS.md`: acceptance-driven task status, actual tests, blockers, percentage basis, effort remaining.
- `HANDOFF.md`: exact last verified commit SHA, files changed, previous outcome, next step, environment constraints.
- `docs/dispatch/ACTIVE_TASK.md`: next precise READY task with success criteria.
- Commit docs alongside each working increment. If tool operations cannot finish, record precisely what was actually completed.

## Current-next override (2026-10-27 KST)
Before following a stale `HANDOFF.md` / `STATUS.md` P6E7 task, read `docs/qa/P6E7_RELEASE.md` for the latest verified P6E7 outcome: Chromium all three tier ZIP downloads with shipping allowlist/hash PASS on `27d97b4`; Windows native **66 PASS /9 warnings** on `78f811b`. These are completed CI checks, not the owner's physical Windows/browser/design signoff. Current READY task is **AUTO-KM-P6E8**: physical Windows + release-gate evidence, or other unblocked QA. Sale state stays NO-GO, completion 5/7 (71%). The original `main` remains unchanged. The large historical `HANDOFF.md` and `STATUS.md` were deliberately not overwritten after a remote content-update safety block; the scoped P6E7 QA document and this pointer preserve the newer verified facts.

## Latest NEXT pointer (2026-10-27 KST) — supersedes prior P6E7 entry
- **P6E8 CLOSED on tested CI**. Read `docs/qa/P6E8_RELEASE.md` and final `HANDOFF.md`/ `STATUS.md` entries. Combined executable SHA `45c6272b2007cc41130ae6cf85ba48998146de6a`; Windows 67 PASS [40458277827](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277827), Linux 125 PASS/2 Windows-only SKIP [40458277791](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277791), Chromium 3 tiers PASS [40458238868](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458238868) at preceding application SHA. Native Windows Unicode-path prediction and command output encoding issue fixed and tested; prior failures retained in P6E8 QA document.
- **Next READY `AUTO-KM-P6E9`** is at bottom of `docs/dispatch/ACTIVE_TASK.md`. Work independently on remaining non-owner release checks; don't ask the owner to perform repeated local tasks. Actual physical Windows UI/PDF aesthetic/legal/commercial approval still NOT GIVEN. Official strict acceptance remains 5/7 (71%), all three SKUs NO-GO. Original `main` untouched, Vercel N/A.

## Latest P6E9 CI checkpoint / next task (2026-10-27 KST)
- P6E9 Python 3.11 launcher selection/fallback verified on GitHub Windows Actions [40459036865](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459036865) at code/workflow SHA `d5fa54b489a30c808bfe7bd4df27f1f5742167c3`: **67 PASS /9 warnings**, broken `py.cmd` shim fallback step succeeded. See `docs/qa/P6E9_RELEASE.md`, final STATUS/HANDOFF entries.
- **NEXT READY AUTO-KM-P6E10**, most recent section at end of `docs/dispatch/ACTIVE_TASK.md`. Physical owner's Windows first installation/browser/PDF/design/license and commercial approval NOT RUN. Official 5/7=71%, BASIC/STANDARD/PREMIUM NO-GO. `main` unchanged and no Vercel production.


## Latest P6E10 confirmed result and next P6E11 — 2026-10-27 KST
P6E10 Windows local-port safety guard tested [Windows Actions 40459966750](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459966750) at code/workflow SHA `2b314653241a2bbf527476841b4a78ed0a882e28`: occupied-port reject and freed-port permit both PASS; 67 Windows native regressions PASS/9 warnings; original main unchanged. See `docs/qa/P6E10_RELEASE.md`. New source/CI is tested; further documentation commits are not new executable CI.
**NEXT READY: P6E11** from bottom of `docs/dispatch/ACTIVE_TASK.md`. Physical owner Windows/browser/Korean-PDF design/legal launch signoff still NOT RUN. P1 PARTIAL, P6 not accepted; strictly 5/7=71%, BASIC/STANDARD/PREMIUM sale NO-GO. Local-only, no Vercel/production.


## Latest P6E11 verified Windows API identity / Next P6E12 (2026-10-27 KST)
- P6E11 `scripts/windows_release_qa.ps1` now requires expected AutoML root API JSON, `/health` and living child before opening browsers, on the previously verified unoccupied localhost port. CI [40461091189](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461091189) code/workflow SHA `5a7e56679a14a658586f18010449bee242f77fa2` **67 PASS /9 warnings**, real local app accepted and unrelated HTTP server refused. Detailed `docs/qa/P6E11_RELEASE.md`.
- **NEXT READY P6E12 owner-machine release gate** at end of `docs/dispatch/ACTIVE_TASK.md`. One future physical Windows review guide in `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`. Don't repeat CI, invent final user approval or change frozen scope for activity's sake. P1 PARTIAL/P6 IN PROGRESS, strict 5/7=71%, all SKU sales NO-GO, main unchanged. No Vercel/production.

## Latest P6E12 PASS / P6E13 owner acceptance (2026-10-27 KST)
P6E12 verified code/workflow SHA `539ba3baa985b16567cf20cfe9cb8338467304fd`, [native Windows Chromium CI 40462203822](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40462203822) SUCCESS. Real Playwright Windows Chromium uploads synthetic CSV to BASIC/STANDARD/PREMIUM, receives valid ZIPs BASIC 461,960B / STANDARD 603,718B / PREMIUM 689,449B; strict shipping/manifest and PDF header PASS. Disposable OFL Nanum font used only in runner temp, never committed or distributed. Existing backend/model code unchanged. This is hosted Windows runner, NOT physical owner Windows/Chrome/Edge GUI or PDF design approval. Official P0-P6 5/7=71%; P1 partial/P6 not accepted; all three SKU commercial NO-GO, main untouched, Vercel/production N/A.
Read `docs/qa/P6E12_RELEASE.md` and final `HANDOFF.md`, then owner one-command `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`. **NEXT P6E13 requires owner's real PC**; don't misreport hosted CI as physical approval, don't invent more code work. User action in one coordinated session only, 3 SKUs remain NO-GO.


## Latest P6E13 parser accuracy verification / actual owner gate (2026-10-27 KST)
Fix CSV original duplicated/blank header before pandas silent mangling; native Windows [40464753900](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464753900) **74 PASS/9 warnings** at code+test/workflow SHA `ba3287108dcc41eed46659c2db84cdd9733faeca`; full Linux [40464733521](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464733521) **132 PASS/2 SKIP/41 warnings**, native Windows/Linux Chromium 3 SKU ZIP PASS on earlier parser SHA. `docs/qa/P6E13_CSV_HEADER.md` captures evidence; repo latest HEAD may be docs-only.
**P6E13 OWNER MACHINE GATE BLOCKED** until actual owner runs `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md` and returns redacted actual output/visual decision. Generic user `ㄱ` means continue independently feasible work but **is not physical Windows signoff**. Product P0–P6 5/7=71%, P1 PARTIAL/P6 NOT ACCEPTED; all three SKU sales NO-GO; main untouched, no production.


## Latest P6E14 accepted code / still-blocked owner gate (2026-10-27 KST)
Trusted packaged PREMIUM predictor now rejects original duplicate CSV headers rather than pandas-mangling them into a valid literal dotted schema. Verified source+tests SHA `fb69da8f2e3a8a8adcd600b8c38b1c19d9d9b385`; native [Windows CI 40465571058](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40465571058) **77 PASS/9 warnings**, [Linux full 40465571117](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40465571117) **135 PASS/2 SKIP/41 warnings**; Chromium 3 SKU downloads PASS in Windows/Linux on immediately previous predictor source SHA. See `docs/qa/P6E14_PREMIUM_HEADERS.md`, `STATUS.md`, `HANDOFF.md`.
**NEXT is still P6E13 PHYSICAL OWNER MACHINE gate**, NOT executed; require actual owner-run command output/quality approval per `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`, not merely a `ㄱ`. Strict milestone 5/7=71%, BASIC/STANDARD/PREMIUM sale NO-GO, original main untouched, Vercel N/A.


## P6E15 owner real Windows first-install failure and CI-verified repair (2026-10-27 KST)
User's actual clone in `E:\AI AutoML Analyst` ran `scripts/windows_release_qa.ps1 -OpenBrowser`, unexpectedly entered Python 3.11.9 `>>>`; after `exit()` no `.venv-automl-qa\Scripts\python.exe` existed, so REAL OWNER FIRST INSTALL FAILED. Fixed owner script to invoke verified direct Python 3.11 binary, require venv Python existence, remove stale launcher arg prefix. CI [40467176162](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40467176162) SUCCESS at exact executable SHA `4245f7b7020719a000c147a5d3279ad4bcd9e23e`: native Windows PowerShell 5.1 first venv create + second reuse in spaced `AI AutoML Analyst` temp path PASS, 77 regression PASS/9 warnings. Full evidence `docs/qa/P6E15_OWNER_WINDOWS_VENV.md`. **Next:** owner on same PC runs `git pull --ff-only origin feature/kmong-v1` and original QA `-OpenBrowser`, returns redacted live output; do not infer success until then. Strict P0–P6 5/7=71%, all SKU sales NO-GO, main unchanged.
