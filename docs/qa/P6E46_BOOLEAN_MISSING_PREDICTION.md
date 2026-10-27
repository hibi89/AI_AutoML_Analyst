# P6E46 — Missing boolean values in trusted PREMIUM repeat prediction

2026-10-28 KST. Repository: `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`. All cases are synthetic.

## Reproduced defect
The exported PREMIUM `model_schema.json` lists true training-side boolean input features in `boolean_raw_columns`. For a new CSV `flag,amount\nTrue,1\n,2\nFalse,3\n`, pandas 2.2.3 reasonably reads `flag` as object containing `[True, NaN, False]`, not pure bool. `_load_input` previously rejected every non-bool dtype before the shipped `_prepare` could convert the boolean column to float and pass the missing value to the already-trained numeric imputer. Therefore routine missing prediction cells failed despite the product's documented missing-value policy.

## Narrow change and alternatives
- **Source commit:** `e5858b949f12a0007ace9000f1aa241d00e0ca0b`, `backend/app/services/premium_predict.py`.
- Keep ordinary pandas boolean dtype accepted.
- When the raw boolean feature is wholly missing, permit it for the existing trained imputer; no alternate feature-value claims.
- Permit pandas object series with non-null values that are genuinely `bool` or `numpy.bool_` (e.g. True, NaN, False). Continue to reject `yes/no`, `0/1`, arbitrary text, mixed numeric/boolean entries. No coercion via `astype(bool)` (would incorrectly treat `"False"` as truthy).
- `_prepare` already converts accepted bool/NaN values to 1.0/0.0/NaN, matching trained feature schema, with no model change or metadata edit.
- **Regression commit:** `da765d4fbd0dd14d27ec08f7a60e582e9227e70b`, `tests/test_p6e46_boolean_prediction_missing.py`: valid boolean with blanks, all blank, no blank, 7 invalid literals, real `predict_csv` output order with a synthetic recording estimator (mocked `_model_and_schema`; no trusted serialized model run in this focused test), CSV header/output and overwrite prohibition. Existing PREMIUM end-to-end serialized pipeline tests continue in full CI.

## Verification
- Local pandas 2.2.3 isolated reproduction: `True,,False` with a blank returns object `[True, NaN, False]`, and new predicate preserves bool/NaN; strings `yes` or `0` mixed with other booleans do not qualify.
- GitHub Docker [40546704907](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40546704907): **SUCCESS** on application SHA.
- GitHub Windows Chromium [40546705041](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40546705041): **SUCCESS** on application SHA.
- GitHub Windows native [40546704996](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40546704996): **SUCCESS** on application SHA.
- Full Linux + new regression [40546766710](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40546766710) on exact test SHA `da765d4f`: **IN PROGRESS at this document's first write**. Do not mark P6E46 final verified until its completed result and test count are checked; preserve any failures.
- Linux Chromium [40546704889](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40546704889): **IN PROGRESS at this document's first write**.

## Boundary
Original `main` SHA `c80c874476f8d5deb4bf611761d89c6d72ca0a2d` protected. No external/customer CSV, paid API, model archive or physical font file committed. No Vercel/public hosting. Physical owner Windows PDF/ZIP and font/software-rights/NOTICE validation and explicit per-SKU commercial acceptance remain outside automated CI. Formal P0–P6 acceptance: **5/7 = 71%**, P1 partial, P6 owner approval pending; BASIC/STANDARD/PREMIUM **SALE NO-GO**.
