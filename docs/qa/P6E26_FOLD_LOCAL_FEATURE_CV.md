# P6E26 — fold-local feature inclusion for STANDARD/PREMIUM CV

**Verified 2026-10-27 KST.** Scope: local-first Kmong v1 feature branch `feature/kmong-v1`, no public deploy or customer data.

## 1. Frozen design gap / previous behavior
`REQUIREMENTS.md` and `docs/architecture/TARGET_DESIGN.md` demand leak-aware cross-validation, with all train-dependent preprocessing learned on each CV training fold only. Before P6E26, `run_standard()` called `build_preprocessing_pipeline()` on the complete outer training partition and supplied `prep.X` plus `clone(prep.preprocessor)` to sklearn CV. The numerical imputer/scaler and categorical encoder were fitted inside folds; **however the following inclusion decisions were already learned using the CV validation rows**:
- all-missing and constant-column removal,
- high-cardinality string column exclusion,
- date-string recognition and date-derived schema,
- boolean/column type mapping.
This may change candidate features and CV metrics without truly causal value leakage; the issue is an information leak from CV validation feature distribution. Crucially, it is **not** leakage from the untouched final holdout (the previous code used only the outer TRAIN for the decisions).

## 2. Deterministic synthetic reproduction
- 24 rows, categorical `region`: first 12 rows alternate "A"/"B", final 12 are 12 fresh synthetic category strings. Numeric `amount`. With threshold=5 and ratio=0.5, original full-partition filtering sees 14 unique names /24 and drops `region`, despite the first fold's 12 **training-only** rows containing only 2 categories. Hence CV validation distribution can decide feature inclusion.
- `event_date` 12 parseable training timestamps, 12 unparseable later validation strings: global parse success 50% marks it text; fold-training-only parse success 100% marks it datetime. This is a separate concrete inclusion decision influenced by validation rows.
- No customer data, no private labels, no fitting for BASIC.

## 3. Implemented least-disruptive solution
`FoldLocalPreprocessor(TransformerMixin, BaseEstimator)` in `backend/app/services/preprocessor.py`: on `fit(X)`, create a unique internal non-null dummy target to reuse existing **same** `build_preprocessing_pipeline` inclusion logic on only the current CV training fold. Record fixed selected columns and datetime/boolean conversion contract; fit the cloned original sklearn `ColumnTransformer` only on fold data. On `transform(X)`, enforce fitted raw columns, apply only the **fitted** datetime and boolean rules, select original training-fold column order, run fitted imputer/onehot/scaler. Unknown validation categories handled by existing `handle_unknown='ignore'`. This estimator is sklearn-cloneable, lightweight and only appears in CV/tuning, not in final serialized PREMIUM model.
`backend/app/services/standard_engine.py`: `cv_raw_features` holds raw outer TRAIN features; train/test split, all model CV and PREMIUM `GridSearchCV` now take raw features with `FoldLocalPreprocessor` on each fold, rather than globally processed `prep.X`. Existing outer-TRAIN-derived schema and `ColumnTransformer` remain used for final untampered holdout evaluation and full labeled refit. Thus **no serialized new custom type**, no `skops` trust expansion, same PREMIUM CSV headers and `predict.py` interface, same BASIC output and frozen prices.
- Code [6e4dec28](https://github.com/hibi89/AI_AutoML_Analyst/commit/6e4dec28890f515010a77ad06ffac87756d279be), [8c5886f1](https://github.com/hibi89/AI_AutoML_Analyst/commit/8c5886f1f5e0f250e499e6519e75bbf93068cbd4).
- Test `tests/test_p6e26_fold_local_features.py` commits [24656f4b](https://github.com/hibi89/AI_AutoML_Analyst/commit/24656f4bd285f7542dcbca8dd2be7f6c807e0136), [af6dfaee](https://github.com/hibi89/AI_AutoML_Analyst/commit/af6dfaeeef7dcceb36d8c6407447452460a3a82e). Covers high-card categorical validation leakage, date parse validation leakage, dense/sparse compatibility, sklearn clone + CV, real STANDARD random and time split 3 challenger/Dummy use of raw feature input and fold-local selector.

## 4. Actual CI (not owner-PC acceptance)
- **New-test-inclusive** [Linux full 40481374009](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40481374009), test HEAD `af6dfaeeef7dcceb36d8c6407447452460a3a82e`: **SUCCESS, 175 PASS / 3 SKIP / 46 WARNINGS**. Existing PDF/ZIP/manifest BASIC6 / STANDARD9 / PREMIUM11 pages PASS, dependency consistency PASS. The skipped tests are Windows-only, not missing the P6E26 unit/integration suite.
- [Linux full source 40481202329](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40481202329), source SHA `8c5886f1`: **170 PASS / 3 SKIP /45 warnings**, 3 PDFs and manifest PASS.
- [Windows native 40481202457](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40481202457), source SHA `8c5886f1`: **SUCCESS 94 PASS /24 warnings**, 6/9/11 PDF pages and ZIP manifests; Windows-native workflow has a fixed subset and did not execute the new P6E26 test file, which was covered by Linux full.
- [Windows actual Chromium 40481202333](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40481202333), [Linux actual Chromium 40481202425](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40481202425): both **SUCCESS**; original client-browser BASIC/STANDARD/PREMIUM upload and ZIP download **6/6 flows per OS** (auto and CP932 encoding).
- The additional earlier source-only runs at SHAs `6e4dec28` and `24656f4b` are not the final test-inclusive evidence.

## 5. Residual scientific and sale gates
- Corrected: CV **feature inclusion & fitting** learned inside CV train folds, and P6E25 repeated timestamps stay grouped across forward CV. Untouched final holdout still protected from model selection.
- Not asserted: perfect causal inference, fair treatment of target-derived features defined by business context, stationarity, group/time choice or unbiased performance after hyperparameter selection. Outer-TRAIN global *model-candidate family budget* and candidate subset still uses outer TRAIN metadata; no untouched holdout leakage. Selection/tuning CV has known optimistic bias and warning; holdout is the decision reference.
- Local-only; synthetic testing cannot approve PDF typography or real-buyer suitability. P6E22 physical one-session ZIP/PDF/legal/commercial signoff still PENDING; all three SKUs **NO-GO**. Frozen P0–P6 acceptance **5/7 = 71%**, P1 owner visual PARTIAL, P6 release NOT ACCEPTED. Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` unchanged; no Vercel or public deployment.
- Next independent engineering priority: Japanese CP932 column **PDF glyph coverage** (NanumGothic CI font lacks some Japanese characters despite correct CSV decoding and 6/6 browser PASS). Verify font fallback or fail-closed export behavior without adding unlicensed fonts or uploading binaries. Keep commercial release and legal authorization explicitly separate.
