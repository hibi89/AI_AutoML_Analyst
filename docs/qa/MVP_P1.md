# P1 BASIC horizontal MVP — audit snapshot (2026-10-25 KST)

## Delivered code (development branch only)
- `backend/app/services/basic_report.py`: bounded CSV frame validation; row, column, dtype, unique, missing and duplicate summaries; evidence-backed findings; up to 3 checks; dynamically selected histogram / missingness / anonymized category PNG; in-memory ZIP; Excel formula-safe summary.csv.
- `backend/app/main.py`: `GET /basic-mvp` and `POST /api/basic-report`. New routes reject remote clients and foreign browser origins, non-CSV extensions and oversized uploads; pre-existing routes unchanged.
- `frontend/basic_mvp.html`: plain local browser upload and ZIP download UI; no CDN/API billing.
- `requirements-ci.txt`: matplotlib added.
- `tests/test_basic_mvp.py`: seven synthetic tests covering page, full report archive/PNG, extension, size, origin, column limits, formula prefixes.
- `.github/workflows/baseline-smoke.yml`: legacy and BASIC tests on Python 3.11; frontend edits retrigger CI.

## Executed evidence
- Original P0 CI: https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199323100 — **6 pass, 3 warnings**.
- P1 integration CI: https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40199782514 — **13 pass, 3 warnings in 3.76s**, original import OK. Commit `8921c0df3a445f1daee127aa66f26dd2ce925193`.
- HTML delayed object-URL release and frontend CI triggers were subsequently committed; check newer workflow run at branch HEAD for final verification.
- API and HTTP page were exercised by FastAPI TestClient, not by an actual Windows browser. No Production deployment exists, and none was requested.

## Known limitations and release block
- This ZIP has `report.md`, `summary.csv`, `summary.json`, `README.txt`, and a PNG if meaningful. **No PDF**, XLSX, 5 charts, polished client-level layout, ML comparison scores, holdout, trained pipeline, model reuse, Windows packaging.
- The original application still has unsafe generic folder/path endpoints and broad CORS; local-only checks apply to the **new MVP routes** only. NEVER host the whole server to the public Internet.
- Currently binary chart rendering and plain Markdown output do not include a Korean PDF font/typography QA. More chart diversity and factual insights are required by P3.
- No customer data was used or committed. Frontend JS interaction and actual ZIP download by real browser remain **NOT VERIFIED**.
- Baseline CI dependencies have ranges rather than frozen exact versions; release needs lock/compatibility testing.

## Status / next
- P0: DONE with GitHub-hosted runtime evidence.
- P1: Core horizontal MVP implementation + API tests PASS; **browser execution remains unverified**, so final acceptance PARTIAL until actual UI interaction checked (or explicitly accept HTTP smoke as MVP scope). Neither the BASIC SKU nor other SKUs is sellable.
- Next engineering item: P2 model selection / target semantics / evaluation validity. Before release: P3/P4/P5 and P6 acceptance.
