# ACTIVE TASK — authoritative next work item
Updated: 2026-10-25 KST
status: READY
task_id: AUTO-KM-P4
target_branch: feature/kmong-v1
role: lead-engineer-and-implementer
predecessor: P0 done, P1 API MVP passed (real Windows browser pending), P2 done (36/36), P3 BASIC PDF/ZIP implementation passed 42/42 CI (manual PDF visual/font+Windows sale QA pending).
next_after_success: AUTO-KM-P5 (PREMIUM model serialization and same-schema predictions)

## Objective — STANDARD (₩150,000) end-to-end
Extend the existing FastAPI local workflow with a **STANDARD** package using the same data engine:
BASIC quality report and charts + user-approved target + **at most 3 non-Dummy** ML challengers + independent Dummy baseline, defensive cross-validation / holdout and a single PDF 8–12 pages + ML comparison table/plot/ZIP. Do not manufacture scores if infeasible.

## Ordered implementation
1. Read live HEAD, HANDOFF, STATUS, AGENTS, REQUIREMENTS, SKU_MATRIX, source and P0/P1/P2/P3 QA. Ensure GitHub Actions latest P3 tests still PASS; also note the temporary synthetic PDF preview artifact.
2. Design and implement explicit classifier/regressor & target selection, retain existing model_selector and P2 guards. **No unconditional auto guessing** for ambiguous numeric targets. Budget max 3 non-Dummy for STANDARD, Dummy distinct.
3. Split before fit; use train subset for cross-validation and held-out subset for independent final evaluation where viable. Choose random stratified for classification by default, and require user context or explicit policy for group/time-ordered data rather than false future-generalization claims. Add warnings/no-score when leak-safe split is impossible.
4. Preprocessing must remain inside sklearn Pipeline fitted within train/CV only. Evaluate same metrics fairly and distinguish CV metrics vs holdout metrics, baseline comparisons, uncertainty/limits. **Do not select on holdout**. Expose no-skill outcome transparently.
5. Reuse BASIC P3 ZIP/PDF/chart code for shared delivery. Add true ML score CSV, comparison chart, Korean result interpretation, target leakage warnings, and STANDARD report 8–12 pages when data supports it. Preserve existing routes; add local-only endpoint/UI without exposing dangerous legacy folder path API. No model serialization in STANDARD.
6. Add synthetic tests including normal classification/regression, ambiguous target 400, constant/rare class 400, group/time future leakage warnings, row/feature/size controls, baseline exactly once, CV/holdout separation, ZIP/PDF extractability, Korean glyphs and client errors. Avoid customer data and paid APIs.
7. Execute GitHub Actions Python 3.11 full suite, inspect logs, capture actual SHA and artifact manifest, record failures honestly, fix minimal bugs. Update STATUS/HANDOFF/ACTIVE_TASK.

## Acceptance
- Functional local API/upload -> genuine STANDARD ZIP with BASIC + ML comparison, honest scores, corresponding Korean PDF, and all required source controls.
- Python 3.11 all existing **42 P0/P1/P2/P3 tests** plus new P4 tests PASS and actual HTTP/PDF/ZIP tests PASS.
- Group/time leakage either properly handled or explicitly prohibited/caveated. No false holdout-based model selection.
- No real customer files or secrets in GitHub. main intact. Windows/browser/security QA remain release gate P6; **STANDARD NOT SALE READY** until verified.

## Explicit future
P5 PREMIUM: up to 5 challengers, trusted serialized pipeline and identical-schema CSV repeat prediction with Windows script, no unsafe pickle from customers.
P6 final gates: Windows real browser, Korean PDF visual review/page overflow, dependency licenses, CORS/filesystem/path hardening, sizing/performance, artifact verification.
