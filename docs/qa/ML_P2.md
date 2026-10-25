# AUTO-KM-P2 ML correctness — executed evidence and limitations
Checked 2026-10-25 KST, GitHub branch `feature/kmong-v1`.

## Implementation and review
- `backend/app/services/task_detector.py`: detect_task now checks missing/constant/too-few/rare class targets, numeric low-cardinality ambiguity (<=20 unique values) and explicit task semantics. It rejects non-numeric regression labels. The caller chooses classification vs regression if the value meaning is ambiguous.
- `backend/app/services/automl_runner.py`: actual AutoML pipeline calls detect_task before preprocessing, supports `max_challengers=3` default (5 can be requested from Python; API/SKU-specific route remains P4), reports task semantics, Dummy baseline and comparison `beats_dummy_baseline`. Best recommended model cannot be Dummy.
- `backend/app/services/model_selector.py`: Dummy baseline always separate from 1–5 challenger budget; model diversity and HistGradientBoosting numeric eligibility are prioritized before truncation. Legacy model pools preserved; no CatBoost/XGBoost or paid dependencies.
- `backend/app/services/trainer.py`: insufficient rare-class CV fails rather than silently using nonstratified KFold; regression n_splits bounded to assure >=2 holdout observations per fold for R².
- `backend/app/services/report_generator.py`: baseline comparison and group/time-unaware CV warning surfaced in Markdown.
- `tests/test_p2_ml_validity.py`: 23 additional cases; baseline test updated to expect constant-target failure.

## Actual CI results
- Initial iterative CI run https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200601358 on SHA `5aa09d4f7955a29aab887e2adfb3350b130b69f5` **FAIL: 31 passed / 5 failed / 4 warnings**. Proven defect: regression priority code accidentally inserted into classification selector, leaving no challengers; corrected by following commit.
- Corrected smoke https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200682075 SHA `cf25dfbaa1aa78fc5fd5409fea46c0d16d6e4ccd`: **36 passed, 0 failed, 6 warnings in 3.64 s**. Existing original FastAPI + P1 BASIC API tests retained.
- Report-warning addition https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200721568 SHA `fdb4234706188d7d0852243d075e6adae44bd1d7`: **GitHub Actions success**, confirming the report-format addition.
- Latest markdown escaping fix is in SHA `8e38ce1c998ccc0da4a4f111313aebedeb52d7b3`; check its specific CI https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200745818 before declaring this final code revision fully verified.

## Risks / not claimed
- Repeated entities, grouped and chronological data **not** evaluated by group/time-aware CV or independently held out. That scientific validity gap is tracked for P4; `policy.warnings` and generated reports explicitly disclose it.
- Target features may leak derived targets or after-outcome observations; P4 must add leakage review and holdout. The positive `beats_dummy_baseline` check is **only cross-validation evidence**, not a production skill guarantee.
- Existing `main.py` permissive CORS and generic filesystem scanning routes still unsafe on a public interface. Binding to localhost required until P6 security gate.
- No end-user Windows browser interaction, customer PDF, repeated CSV prediction or Vercel Production validation was performed.
- CI is Python 3.11 GitHub runner with synthetic examples, not an end-to-end commercial acceptance.
