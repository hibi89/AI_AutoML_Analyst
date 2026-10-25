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
