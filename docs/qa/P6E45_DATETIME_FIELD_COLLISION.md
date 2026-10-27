# P6E45 — Datetime-derived feature collision (data-fidelity fix)

Date: 2026-10-28 KST. Repo `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`. Synthetic inputs only.

## Reproduced correctness defect
Before the patch, `backend/app/services/preprocessor.py::_expand_datetime_features` assigned `X[f"{col}__year"] = parsed.dt.year` and analogous month/day/dayofweek/hour fields without checking whether the generated column already existed in the customer's original frame. An input carrying both `sale_date` and a genuine numeric column `sale_date__year` silently loses its original values. Minimal pandas reproduction: values `[901, 902]` are replaced by `[2026, 2026]`. The same helper is used by train-only preprocessing, fold-local CV, STANDARD holdout fitting and PREMIUM final refit; field mutation would undermine model explainability, reproducible schema, and report accuracy. This is a real data-alignment problem, not proof of customer exposure.

## Fix and alternatives
- Source SHA `e204fe9a335a8132196540aa08aefa21e0043ca8`, `backend/app/services/preprocessor.py`: precompute the set of `__year`, `__month`, `__day`, `__dayofweek`, `__hour` names for detected datetime features, and reject any colliding existing column or duplicate generated field before modifying the frame. Return a controlled generic ValueError advising a source-column rename. No values or customer headers are echoed.
- Rejected alternative: silently suffix generated column names or overwrite/ignore original fields. This changes trained feature schema or discards customer data without authorizing a transformation and risks breaking PREMIUM exact-schema reuse. Rejecting is deterministic and honest.
- Regression test SHA `646c0d2342056525b7c41b298f6551c34d10a60b`, `tests/test_p6e45_datetime_feature_collision.py`: five suffix permutations, original input immutable, valid date expansion unaffected, train/preprocessor fail-fast, and real STANDARD/PREMIUM HTTP 400 with no row value exposed. BASIC never trains a predictive model so it is not changed.

## CI evidence and release boundary
- Docker local-only [40543676847](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40543676847): **SUCCESS** on fixed application SHA.
- Windows native [40543677019](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40543677019): **SUCCESS** on fixed application SHA.
- Windows Chromium [40543676827](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40543676827): **SUCCESS** on fixed application SHA.
- Linux Chromium [40543676895](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40543676895): **SUCCESS** on fixed application SHA.
- Full Linux and new regression [40543817771](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40543817771), source SHA `646c0d2342056525b7c41b298f6551c34d10a60b`: **COMPLETED SUCCESS — 259 passed / 3 skipped / 68 warnings in 68.33s**. All workflow steps succeeded, including original AutoML/API smoke, BASIC/STANDARD/PREMIUM synthetic PDF previews (6/9/11 pages), ZIP/owner review artifacts, BASIC 20k×50 budget benchmark, ML CV/holdout benchmark and resolved dependency inventory. No actual owner's Windows interactive commercial acceptance is implied.

## Unchanged conditions
Only `feature/kmong-v1` modified. Original `main` `c80c874476f8d5deb4bf611761d89c6d72ca0a2d` remains protected. No customer data, keys, font binaries or model assets committed; no public deployment, Vercel or paid APIs. Formal P0–P6 acceptance remains 5/7 (71%), P1 partial, P6 owner signoff pending. All tiers remain **commercial NO-GO** until owner reviews actual Windows PDF/ZIP, fonts/software license notices and grants independent SKU approval.