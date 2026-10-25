# P6D — Resource, transparency and native delivery QA
Updated: 2026-10-26 KST. Branch `feature/kmong-v1`. All evidence synthetic. **Not a release go/no-go approval.**

## Engineering: separate descriptive and ML workloads
- BASIC analysis cap remains **20,000 rows / 50 columns / 30 MiB**, independent of supervised model-fitting budget.
- `backend/app/services/ml_workload_policy.py` introduces fail-fast conservative tiers:
  | Tier | Max total input rows | Estimated encoded features | Estimated training matrix cells |
  |---|---:|---:|---:|
  | STANDARD | 5,000 | 180 | 600,000 |
  | PREMIUM | 3,000 | 140 | 360,000 |
- Limits are **provisional customer-safe operating policies**, not universal performance claims; conditional on actual encoded dimension and dataset context. Deliberately leave 20k-row supervised datasets to a separately scoped/quoted assessment. No silent sampling, no inaccurate 20k × 50 ML guarantee.
- Row limit checked before task inference, CV or fitting. Encoded size estimated **only from TRAIN columns**, after train-only high-cardinality filtering and date preprocessing. A user-supplied 50-column input can expand dramatically through one-hot features; estimated footprint is checked before training, and errors are explicitly reported.
- Original `/api/analyze` (legacy ML route) also receives 5,000-row guard to prevent bypassing new commercial routes; BASIC remains unaffected.
- Dropped input features (e.g. high-cardinality identifier columns) are explicitly disclosed in results and warnings rather than silently disappearing. Exported ML `resource_budget` metadata states actual budget and estimated train cells. UI STANDARD/PREMIUM file labels now disclose respective row limits.

## Real near-cap stress benchmark
- [GitHub Actions 40211135507](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211135507) **SUCCESS**, synthetic 50-column binary classification with 44 numeric predictors, five categorical columns (5 categories each), and target. Dataset: 50 total columns, 69 estimated encoded features, CV 3 plus independent holdout, 3 or 5 non-Dummy candidates, PREMIUM top-two tuning.
- **STANDARD 5,000 rows: 10.33 s**, process peak RSS 205,852 KiB (~201 MiB).
- **PREMIUM 3,000 rows: 10.79 s**, process peak RSS 215,136 KiB (~210 MiB).
- These are peak RSS *of the Python benchmark process* on an Ubuntu CI runner, not incremental model-only RAM; second reading includes prior runs. This confirms **these exact synthetic conditions only**, not arbitrarily complex group/time datasets, large Excel rows, nonlinear targets, many labels, user PCs or fixed delivery times.
- Added `scripts/p6d_ml_stress.py` and `.github/workflows/p6d-ml-stress.yml`; run remains independent of full pytest for quick reproducibility.

## Improved report & privacy
- STANDARD/PREMIUM model report displays a training-derived model-specific importance ranking **only when estimator supports it**; tree impurity or absolute preprocessed coefficients are explicitly described, not claimed to be causal or comparable across model families.
- One-hot encoded category-level contributions are **aggregated to their original field header**, never serialized to `premium_summary.json` or public PDF as original private category names. Fallback omits ranking when attribution names or underlying estimator do not support it.
- Added summary of high-cardinality/constant features dropped from training; avoids implying every input field drove the prediction.
- QA `tests/test_p6d_importance.py` synthetic category marker `SECRET_CUSTOMER_CATEGORY_` checks that no raw private category value reaches rankings or PDF. The final fitted model bundle **necessarily encodes the training categories** for later predictions; this is customer-sensitive and should only be delivered directly to the authorized client using secure channels.
- Retrieved latest full synthetic 11-page PREMIUM PDF from [CI 40211407887](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211407887) (88 pass, one Windows-only skip); visual preview still has excess whitespace on pages 5, 7, 10, 11 and should not be represented as final signed-off commercial design.

## CI progression and checks
- First new high-card test [40211039507](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211039507) **86 PASS/1 FAIL/1 SKIP** because test fixture's 65 unique per 150-row column matched existing preprocessing discard rule; fixture corrected to 45 unique so estimated OHE guard is exercised. [40211063593](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211063593) **87 PASS/1 SKIP**.
- [40211407887](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211407887): **88 PASS /1 Windows-only SKIP /31 warnings**, Korean PDF produced with safe new model ranking.
- [40211572386](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211572386), plus [Windows 40211572333](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211572333) and [Chromium 40211572238](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211572238) PASS, after transparent dropped-feature code.
- Windows workflow now statically parses `scripts/windows_release_qa.ps1` and exercises ML row/encoding guards in native Windows Python3.11; it remains a CI runner, NOT owner's physical PC.
- Follow-up Linux CI [40211592836](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211592836) contains newly added transparent identifier-drop regression; consult live status/log before claiming it passed.

## Remaining final gate
**All three tiers NO-GO** pending user's physical Windows font, Chrome/Edge GUI/ZIP/model-reuse and first-install run, page-density/client design approval, adversarial privacy/security and transitive dependency vulnerability check, actual price/delivery terms. Accept P6 only on observed evidence; original `main` preserved. Next P6E should prioritize those remaining gates and tier-specific sale readiness, not expand arbitrary features.
