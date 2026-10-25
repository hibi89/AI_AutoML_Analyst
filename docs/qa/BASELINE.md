# P0 original application baseline — 2026-10-25 KST

## Identity and immutable reference
Repository: `hibi89/AI_AutoML_Analyst`
Development branch: `feature/kmong-v1`
Original baseline: `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` (unchanged during P0).
Verified application/test commit: `00d8427499bd38b911e4df6f90240efe6bbb6c41`.
Workflow: https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199323100
GitHub Actions job: `121186916967`.

## Executed, not inferred
GitHub-hosted `ubuntu-latest`, Python **3.11**, using `requirements-ci.txt`.
Commands:
```sh
python -m pip install -r requirements-ci.txt
python -c "from backend.app.main import app; print('FastAPI original import OK', app.version)"
python -m pytest -q tests/test_original_smoke.py
```
Observed output:
- Original FastAPI import: `FastAPI original import OK 0.1.0`.
- Pytest: **6 passed, 3 warnings in 2.93s**. No failed tests.
- Covered: original classification and regression pipeline with 3-fold CV, missing target, constant classification target (old code returns failed model), HTTP `/health`, HTTP CSV upload + persisted JSON and report retrieval. No customer data used.
- GitHub Actions conclusion: **success** at 2026-10-25 13:49 UTC.

## Explicit limits
- Tests exercise a tiny, synthetic dataset, no production URL, no Windows runtime, no true PDF/ZIP, no model persistence or repeated predictions.
- CI used latest compatible dependency bounds, **not locked exact versions**. The observed job installed FastAPI 0.162.0, pandas 2.3.3, scikit-learn 1.9.1, pytest 9.1.1.
- Direct clone from ChatGPT's analysis container failed DNS for `github.com`. GitHub connector writes and GitHub-hosted CI worked. The container only had Python 3.13, which is outside the declared supported range; GitHub Actions Python 3.11 is authoritative.
- 3 warnings; inspect if they become failures or affect user output. The deprecated Node URL parse warning seen after test steps concerns runner action/tooling, not proof of app weakness.

## Static risks deferred to designated task
- `task_type=None` currently falls back to classification rather than robust target inference; constant target does not reliably produce early friendly rejection.
- StratifiedKFold fallback may leak invalid rare-class distributions; grouped/time data lacks proper split.
- Existing default selectors count Dummy within caps and may truncate appended HistGradientBoosting.
- Existing folder browser and path analysis accept arbitrary server paths; permissive CORS. **Never expose current server to the public Internet**.
- Markdown-only original reports; no Korean PDF, output ZIP, validated XLSX, trusted model bundle, or Windows prediction runner.

## P0 acceptance
Original app import: PASS. Original classification/regression execution: PASS. Original HTTP upload and report persistence: PASS. Reproducible CI: PASS. Branch-only commits: PASS. **P0 DONE**.

Next stage: `AUTO-KM-P1` — local MVP vertical slice. Avoid releasing or handling real sensitive customer data before security and product QA gates.
