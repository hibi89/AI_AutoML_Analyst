# Commercial MVP technical architecture & gap audit
Last reviewed: 2026-10-25 KST
`main` is legacy original; `feature/kmong-v1` is development ref.

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
