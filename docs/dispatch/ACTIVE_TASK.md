# ACTIVE TASK — authoritative next work item
Updated: 2026-10-25 KST
status: READY
task_id: AUTO-KM-P2
target_branch: feature/kmong-v1
role: lead-engineer-and-implementer
predecessor: P0 verified (6/6 CI), P1 BASIC MVP code/API verified (13/13 CI); browser UI interaction remains NOT VERIFIED.
next_after_success: AUTO-KM-P3 in docs/dispatch/ROADMAP.md

## Task — ML correctness before commercial tier wiring
Make the existing trainer/model_selector/runner produce defensible classification/regression selection and baseline comparison, without breaking P0/P1.

### Scope, ordered
1. Re-fetch live HEAD, source, STATUS, HANDOFF, REQUIREMENTS and `docs/qa/{BASELINE,MVP_P1}.md`; check newest CI for HEAD.
2. Add explicit target validation: missing/constant/too-rare classes; numeric <=20-unique can be ambiguous — prompt the caller to select classification vs regression rather than silently defaulting classification. Preserve explicit `task_type` choices. Avoid auto-inference with unverifiable semantics.
3. Separate Dummy baseline from non-Dummy challenger budget and preserve a diverse challenger set; eliminate the HistGradientBoosting append-then-truncate issue with deterministic, documented policy. Check existing registry vs selector to avoid diverging definitions.
4. Reject invalid StratifiedKFold conditions with readable error; no silently misleading KFold fallback for rare classes. Evaluate preprocessing inside CV as currently implemented. If group/time split remains unsupported, visibly warn; leave full group/time/holdout support to P4.
5. Add P2 synthetic tests: binary/multiclass, numeric ambiguous target, rare class, regression, 3/5 challenger caps independent of Dummy; no paid APIs or real customer data.
6. Execute Python 3.11 GitHub Actions test suite, inspect job logs and commit SHA. Record failure counts, warnings and limitations. Minimal edits only.
7. Update `STATUS.md`, `HANDOFF.md`, this task and QA results; commit. Preserve `main` untouched.

## Acceptance
- No numeric target is silently mislabeled as classification when ambiguous.
- Constant, missing and insufficiently populated target cases are explicitly rejected or clearly reported as infeasible.
- DEFAULT and selected SKU candidate lists distinguish Dummy baseline from up to 3/5 non-Dummy challengers; regression/classification behavior tested.
- Actual original FastAPI+AutoML P0 and BASIC MVP P1 tests remain green.
- CI job output and branch SHA recorded. P2 only DONE if the above are observed, never based on static review alone.

## P1 follow-up, tracked separately
Headless tests verify HTTP GET, upload, ZIP artifacts and PNG. JS behavior in actual Windows browser, UI click/download, and client-level PDF are NOT VERIFIED. Do not mark BASIC sellable before P3+P6.
