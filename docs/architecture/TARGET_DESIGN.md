# Commercial MVP technical architecture & gap audit
Last reviewed: 2026-10-27 KST
`main` is legacy original; `feature/kmong-v1` is development ref.

## Current implementation reconciliation — 2026-10-27

The static design review below records the source state seen on 2026-10-25. It is retained as a historical baseline and **must not be used as the current open-gap list**. Current acceptance limits and owner gates are tracked in [`FINAL_ACCEPTANCE_CROSSWALK.md`](../qa/FINAL_ACCEPTANCE_CROSSWALK.md), [`STATUS.md`](../../STATUS.md), and [`ACTIVE_TASK.md`](../dispatch/ACTIVE_TASK.md).

| 2026-10-25 observation | Current implementation evidence | Current status / limit |
|---|---|---|
| Task detector was not called; ambiguous numeric targets risked classification by default. | `automl_runner.py` and `standard_engine.py` call `task_detector.detect_task`; BASIC emits rules-only target-feasibility and ambiguity cues. | Resolved for the implemented flows. Ambiguous targets require explicit semantics; BASIC does not fit a model. |
| Histogram gradient boosting could be truncated before the challenger cap. | `model_selector.py` prioritizes eligible HistGradientBoosting candidates before applying the challenger limit; Dummy remains outside the 3/5 challenger budget. | Resolved in selector policy; candidate counts do not promise model quality. |
| Random CV could mix groups/times; an independent holdout was not established. | STANDARD/PREMIUM `standard_engine.py` supports random, group, and chronological holdout/CV; chronological folds split distinct timestamps. Model selection and tuning use training CV, then evaluate once on untouched holdout. | Automated synthetic cases pass. The owner must still confirm the split matches a real use case; no future-performance claim is approved. |
| Feature inclusion/type decisions could be learned before CV folds. | `FoldLocalPreprocessor` learns preprocessing and feature inclusion within each CV training fold; shipped final pipelines keep the supported prediction schema. | Automated synthetic regressions pass; this does not validate a customer-specific data-generating process. |
| End-to-end reports, packages, and repeat prediction were unverified. | BASIC/STANDARD/PREMIUM build tiered PDF/ZIP manifests; PREMIUM includes a trusted local artifact and same-schema CSV prediction runner. Windows and hosted Chromium synthetic flows are recorded in the crosswalk. | Synthetic implementation gate passes. Owner visual, client-machine, font-rights, and commercial approval remain open (P6E22). |
| Public exposure risk from filesystem browsing, upload limits, and bind settings. | Legacy arbitrary-path browse/scan routes are disabled; local Host/client/Origin checks and bounded CSV/XLSX parsing protect the local workflow. | Partial release/security evidence only. Docker's `0.0.0.0` bind and remaining deployment configuration are not approved for public hosting; no penetration or full source-security audit is claimed. |
| Repository ownership and dependency/font licensing were unsettled. | Dependency, font attribution, embedding metadata, and distribution choices are documented in `docs/qa/`. | No root project license or qualified legal/commercial clearance is recorded. Owner review remains required. |

Implementation and test references are summarized in [`docs/qa/FINAL_ACCEPTANCE_CROSSWALK.md`](../qa/FINAL_ACCEPTANCE_CROSSWALK.md) and `docs/qa/P6E24_*` through `P6E29_*`. Those checks use synthetic data and do not replace owner acceptance.

## Historical static baseline — 2026-10-25 (superseded for current status)

## Existing source layout (verified via connected GitHub file reads)
- `backend/app/main.py`: FastAPI endpoints for upload analysis, browsing/scanning CSV folders, on-server path analysis, saved results and report download.
- `backend/app/services/automl_runner.py`: preprocessing > model selection > CV > ranking; presently task type defaults to classification when unset.
- `backend/app/services/model_selector.py`: **10 classifier candidates + 12 regressor candidates** (2 Dummy baselines). Dynamic selection currently capped at 7/6/5 depending on dataset size, Dummy included.
- `backend/app/services/task_detector.py`: auto-detection defined but NOT invoked by `automl_runner.py`. Numeric <=20 unique currently assumed classification; misleading for discrete-valued regression.
- `backend/app/services/trainer.py`: sklearn Pipeline + cross_validate; StratifiedKFold for classification, shuffled KFold for regression. Does NOT consider account/group/time by default.
- `backend/app/services/preprocessor.py`: mixed numeric/categorical transform existing.
- `backend/app/services/report_generator.py`: Markdown reporting (not validated end-to-end).
- `frontend/index.html`: plain JS with hard-coded 127.0.0.1 API URL.
- `Dockerfile`: runs uvicorn on `0.0.0.0`; `docker-compose.yml` contains developer-specific absolute mount. Not acceptable as open production hosting.
- `pyproject.toml`: Python >=3.11,<3.13; dependencies not comprehensively locked.
- Source licensing: no root LICENSE/Licence.md file found in previous review; check ownership and all dependency licenses prior to commercialization.

## Main observed design issues (static; NOT evidence of failures during execution)
1. Auto classifier/regressor selection bug: task detector unused; ambiguous targets.
2. `HistGradientBoosting*` candidates appended at tail then truncated at max_models (often never selected).
3. Candidate register duplicated between `backend/app/models/registry.py` and services/model_selector.py.
4. Group/time/entity leakage possible due random CV; external holdout not clearly present.
5. Arbitrary local/server path browsing without auth if exposed publicly; permissive CORS; upload limits and server bind need hardening.
6. No verified reusable final fitted model, CSV prediction inference, PDF packaging / SKU gating.
7. Original GitHub code **not yet** actually executed in previous analysis container. Standalone test on two converted SQLite datasets demonstrated sklearn feasibility, NOT original backend compatibility.

## Target pipeline — MVP then fill
1. Input: CSV and XLSX, format/size/type checks, CSV encoding, basic privacy/sensitive-column warnings. App only listens on localhost for regular use.
2. Profiling: row/column schema, quality stats, KPI suggestion, suitable visualizations, grounded findings and qualified suggestions.
3. If Standard+: explicit target semantics or cautious detector, choose classification or regression; reject unsupported constant/rare targets.
4. Leak-aware dataset split: choose stratified, grouped, or chronological based on data/context. Fit all preprocessors inside training split/CV only.
5. Model selector: Dummy baseline separate from caps; model diversity (linear, trees, boosting) with compute budget; fair metrics and holdout evidence. Do not blindly run all 20 non-Dummy options.
6. Results: model comparison, uncertainty/caveats, readable HTML dashboard, Korean PDF (e.g. HTML-to-PDF if available), graph PNG and CSV export.
7. SKU packager: single engine, BASIC/ STANDARD/ PREMIUM output manifest, validate outputs, ZIP delivery.
8. Premium: refit chosen preprocessor+estimator only on correct training scope; persist trusted local pipeline and predict on schema-matching CSV. Strict trusted artifacts; no user-uploaded pickle loading.
9. Tests: synthetic fixtures, controlled input/negative cases, actual original API smoke & file result verification; Windows repeat predictions and Korean PDF render check before release.

## Speed controls / explicitly deferred beyond the 3-day candidate
- No React rewrite, no hosted SaaS, no PostgreSQL, no cloud billing, no unbounded data science model catalog.
- No speculative CatBoost/XGBoost dependency until baseline proven. Candidate addition only if feature earns its maintenance/testing cost.
- No complex time-series forecasting, unsupervised clustering, image/text NLP in advertised product.
- No complicated GUI installer in v1. Premium may start with a reproducible Windows launch script only if actually tested.
- Safety floors are immediate; broad penetration/perf audit may be scheduled late, **but never skipped for go-live**.

## MVP gate
User can open local app, submit a synthetic CSV, obtain quality summary and BASIC report, run up to three valid classifiers/regressors + separate baseline, view results and download a ZIP. Log errors, do not silently claim completed reports. This first vertical slice precedes extensive refactoring.

## Licensing
All commercial components must have redistribution-friendly licenses and pinned versions. User ownership of repository does not automatically grant permission to relicense third-party code. Avoid distributing trained models containing customer raw data without explicit consent.
