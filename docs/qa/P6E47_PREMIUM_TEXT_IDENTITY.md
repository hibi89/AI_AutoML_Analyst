# P6E47 — PREMIUM prediction preserves text identity across batches

Updated 2026-10-28 KST. Repo `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`; synthetic inputs only.

## Observed correctness defect
The shipped trusted repeat-prediction script previously called `pd.read_csv` without type hints, even though the model schema already distinguishes original numeric/boolean features from textual/categorical/date ones. A customer training CSV containing mixed textual category labels `001` and `A` fits an encoder with literal string category `001`. But a new batch containing only `001` and `002` silently loads as integers 1 and 2. A fitted OneHotEncoder treats integer 1 as an unknown category, silently producing all-zero encoding; the input header still matches exactly, so the old schema guard does not detect the semantic corruption. Independent pandas 2.2.3/sklearn reproduction confirmed conversion and string-vs-int encoded mismatch.

## Narrow fix
- Code commit `aa2ffb19f31073feddd5b8dfeebedb5be68ef7be`, `backend/app/services/premium_predict.py`: compute set of originally numeric and boolean feature names from *existing trusted schema* `numeric_raw_columns` and `boolean_raw_columns`. Parse all other raw columns with explicit `dtype={name: str}`; this preserves leading zero codes, text dates and Korean/Japanese categories across inference batches. Numeric and strict boolean validation from P6E41/P6E46 remain untouched. No schema version migration, model archive regeneration, hidden type conversion or arbitrary dtype coercion.
- Targeted regression commit `6c376aceae1d571d68d42b325fcdaa177fc5dfd4`, `tests/test_p6e47_prediction_text_identity.py`: exact string identity `001`/`002`, OneHotEncoder known-vs-unknown match, YYYYMMDD date text and derived year/day, unchanged numeric and boolean types, mixed strings and missing values, and legacy schema without extra fields.
- Alternative rejected: silently cast every new category to numeric (loses `001` identity) or add a new mandatory schema field (breaks trusted existing shipped bundles without need). The already-delivered raw feature schema is sufficient.

## Verification (checked run statuses, no inferred successes)
- [Docker 40548672267](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548672267) **COMPLETED SUCCESS** on exact application SHA `aa2ffb19`.
- [Full Linux 40548766131](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548766131) on exact regression SHA `6c376ace`: IN PROGRESS at initial documentation. Confirm final count and artifact steps before calling P6E47 complete.
- [Windows native 40548671991](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548671991), [Windows Chromium 40548671949](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548671949), [Linux Chromium 40548672179](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548672179): IN PROGRESS at initial documentation; verify completed status.

## Release boundaries
Only `feature/kmong-v1` changed. Original `main` remained `c80c874476f8d5deb4bf611761d89c6d72ca0a2d`. No customer data, credentials or model/font binaries committed and no public SaaS deployment. Strict P0–P6 commercial acceptance remains 5/7 (71%), P1 partial, P6 owner physical Windows PDF/ZIP quality, font/software rights/NOTICE and independent GO per tier still unapproved. All three SKUs **SALE NO-GO**. CI on synthetic cases is not owner physical signoff.
