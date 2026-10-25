# AI AutoML Analyst — frozen commercial requirements v1.0
Baseline: existing `main` application (FastAPI + pandas + scikit-learn + HTML/JS)
Owner-approved strategy as of 2026-10-25 KST. Authoritative tier details: `docs/product/SKU_MATRIX.md`.

## Product and buyer promise
Local-first **customer-supplied CSV/XLSX** analysis and deliverables. Not a hosted SaaS, not an unconditional accuracy guarantee, and not a general software development service. Use no paid API. Only analyze customer-authorized, de-identified data. Customer files and generated models never enter public GitHub.

### BASIC — KRW 60,000
- One dataset; data shape, types, missingness, duplicates, simple outlier signal and basic descriptive stats.
- Relevant key figures (up to 5-10, when computable); **around five meaningful charts** chosen based on schema; avoid meaningless filler charts.
- Data-grounded **3-5 findings** and up to 3 actionable suggestions (qualify suggestions and avoid causation claims).
- ML feasibility report: potential targets, target ambiguities, constraints and recommended additional data. **No ML fitting/comparison promised in BASIC.**
- Delivery: well-designed Korean PDF around **6-8 pages**, summary CSV or XLSX, graph PNGs, concise guidance, ZIP.

### STANDARD — KRW 150,000
- BASIC plus user-approved target and classification/regression analysis; **up to 3 distinct non-Dummy candidate estimators** (+ baseline, not counted).
- Cross-validation appropriate for dataset, holdout verification where viable, meaningful primary/secondary metrics, comparison chart, basic feature importance where technically valid, leakage warning.
- PDF around **8-12 pages**, model evaluation CSV, charts, ZIP; **no reusable model package** promised.

### PREMIUM — KRW 300,000
- STANDARD plus **up to 5 distinct non-Dummy models** (+ baseline), limited extra tuning for best 1-2 models.
- Final fitted preprocessing+model pipeline stored with compatible versions; **new CSV with identical schema** can be predicted using local tool/script; output CSV + instructions. No custom website, server integration, perpetual maintenance or arbitrary schema support.
- PDF around **10-15 pages**, report/plots/comparison/serialized pipeline/reuse script in ZIP.
- Do NOT launch/sell before Windows compatibility, dependency/license, security, schema validation, and actual repeat-prediction tests pass. Serialized sklearn models are untrusted code-execution inputs: only load locally generated trusted artifacts; do not accept untrusted pickles.

## Shared constraints
- One file / one target by default; multi-file DB joins, large data, complex forecasting, spatial/NLP/image analysis and custom integrations excluded or separately priced.
- Current proposed standard upper guardrails: 20,000 rows, 50 columns, 30 MB; test and adjust before listing. Graceful failure rather than silently sampling or losing records.
- Unknown target semantics require user choice; do not infer that a low-cardinality numeric revenue is classification. Reject constant targets and targets with insufficient support.
- Missing data / insufficient rows / no predictive signal => honest diagnostics, no invented ML scores or insights.
- All tier packaging comes from **one shared engine** and one SKU configuration, not three divergent forks.
- Japanese/Korean encoding, time-type parsing, CSV/XLSX ingestion, safe output paths and human-readable errors require tests.
- User-facing copy must accurately describe report generation; current rules-based explanations are not LLM-generated.

## Frozen engineering/release strategy
1. 3-day **target** (Oct 26–28, 2026 KST; aspirational, NOT guaranteed): MVP end-to-end → gap-fill vs original spec → comprehensive QA/release.
2. Minimal security from start; postpone broad regression/performance/security audit to final day. Never ship before release gate.
3. Separate release gates: BASIC and STANDARD may become sellable before PREMIUM if PREMIUM prediction packaging is blocked.
4. Definition of done per tier: real original FastAPI/API + web interaction run, reproducible tests, actual PDF/file packaging, synthetic and de-identified customer-like datasets, documented Windows validation, clear caveats.
5. New code only on `feature/kmong-v1` until verified and explicitly authorized to merge. Status must separate implementation, tests, and sale readiness.
