# P6E25 — chronological cross-validation same-timestamp leakage repaired

Updated 2026-10-27 KST. Local-only project; no customer data, paid API or deployment.

## 1. Design gap vs frozen contract
`REQUIREMENTS.md` and `TARGET_DESIGN.md` demand leakage-aware chronological CV for time-ordered customer ML. Previous `run_standard(..., split_policy="time")` sorted chronological train/holdout and correctly rejected coincident timestamps at the **holdout** boundary, but then ran `TimeSeriesSplit(n_splits=folds)` directly on **rows within the training portion**. TimeSeriesSplit has no concept of timestamp grouping. Repeated records at one timestamp could cross a train/CV validation boundary. Because STANDARD and PREMIUM share `run_standard`, both tiers were affected.

**Confirmed reproduction:** 90 training rows with 30 distinct chronological timestamps repeated exactly 3 times; `TimeSeriesSplit(n_splits=3)` produced 3 folds, 2 with equal max training and min validation timestamp (the conventional row-based split crossed identical date groups). Tested locally against installed sklearn 1.8.0 for failure demonstration. The hosted CI pinned sklearn 1.9.1 for application regression.

## 2. Compared designs and selected change
- A. Reject any repeated timestamps or treat repeated rows as invalid: fast but unnecessarily rejects legitimate repeated business records; **rejected**.
- B. **Selected:** time order is preserved, `TimeSeriesSplit` operates over strictly sorted **unique timestamp groups** and then expands each train/validation group membership back to full observation indices. Verify training's latest timestamp is strictly earlier than validation's earliest. No future data in fitting, no shuffle, no same-timestamp overlap; fail closed if fewer than 3 distinct training timestamps. Existing independent holdout boundary policy remains unchanged.
- C. GroupKFold on timestamps: breaks forward chronology; rejected.
The implementation maintains one shared evaluator for STANDARD/PREMIUM and existing 3/5 challenger budgets, tuning/search and Dummy baseline. Split sizes may differ from row-based folds; CV scores may change and must not be advertised as comparable to historical row-based results.

## 3. Source and test references
- Source: `backend/app/services/standard_engine.py`, new `_chronological_timestamp_cv`, used for split_policy=time; code commit [50e7ff9](https://github.com/hibi89/AI_AutoML_Analyst/commit/50e7ff901da6491fbdad0a2116341cc09f9fd63f).
- Tests: `tests/test_p6e25_time_cv_groups.py`, commit [e524f66](https://github.com/hibi89/AI_AutoML_Analyst/commit/e524f66337b71a419b60fda765651676543fb5a2). Checks original unsafe two-fold overlap, newly grouped safety for every fold, unsorted/fewer than 3 group fail-close, and **actual STANDARD run_standard** with 120 synthetic rows, 40 repeated timestamps, a 90-row disjoint training partition, regression CV/holdout.
- [Linux full 40479812780](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40479812780), exact test-inclusive source SHA `e524f66337b71a419b60fda765651676543fb5a2`: **SUCCESS 170 passed, 3 Windows-only skipped, 45 warnings**, synthetic BASIC6/STANDARD9/PREMIUM11 PDFs and all ZIP manifests PASS.
- [Windows native 40479732000](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40479732000), source SHA `50e7ff901da6491fbdad0a2116341cc09f9fd63f`: **SUCCESS 94 passed, 24 warnings**, BASIC6/STANDARD9/PREMIUM11 PDF+manifest and synthetic shipped predict.cmd replay. Windows subset workflow did not include new P6E25 test file; it is covered by Linux full suite.
- [Linux Chromium 40479731955](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40479731955), [Windows Chromium 40479731949](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40479731949), executable source SHA `50e7ff9`: both SUCCESS. Each OS verified BASIC/STANDARD/PREMIUM real browser ZIP download with auto+CP932 = 6/6 successful per OS.

## 4. Limits, release and next
- This resolves **same-timestamp overlap across CV folds**, not every possible time-series leakage mode. Leakage due post-outcome features, row identifier encoding, target-derived transformations, fold-global feature selection, target time semantics and distribution shifts remains an owner/modeling concern.
- Existing **final holdout** still fails closed if the naive 75% row cutoff bisects a timestamp group. A separate future choice is whether to choose a nearby timestamp-safe boundary instead of a 400 rejection; avoid changing holdout denominator/semantics without tests.
- Current categorical/high-cardinality/date **feature inclusion choices** are learned from the full training partition before CV, although imputation/OHE/scaling is fitted within folds. This may result in optimistic CV estimates. Next independent engineering audit/fix should move fold-dependent decisions inside CV if practical, without breaking shipped exact-schema PREMIUM prediction.
- Despite passing synthetic CI, physical owner PDF appearance, complete customer ZIP manual opening, legal/distribution and explicit commercial approval are **not accepted**; three SKUs remain **NO-GO**. Strict P0–P6 accepted **5/7=71%**. Original `main@c80c874` unchanged. No Vercel/production, font binaries, customer datasets or model ZIP in GitHub.
