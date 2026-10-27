# P6E34 — pre-parser multipart request-envelope budget

**2026-10-27 KST — VERIFIED**
- Repository: `hibi89/AI_AutoML_Analyst`
- Branch: `feature/kmong-v1`
- Source/test SHA: `6cd7c39ef9cf622d22ae76c3e66aebca79368838`

## Confirmed resource-boundary gap
All four POST endpoints (`/api/analyze`, `/api/basic-report`, `/api/standard-report`, `/api/premium-report`) capped the uploaded `UploadFile` through `await file.read(MAX_UPLOAD_BYTES + 1)`. This is required but runs **after** Starlette processes the multipart HTTP request, which can already spool oversized content into temporary storage. Therefore the endpoint limit alone did not bound multipart receipt/temporary-file use. This is a resource-consumption risk, not evidence of a confirmed exploit in a deployed public service.

## Minimum architecture change
- Created `backend/app/upload_guard.py` pure-ASGI middleware and registered it in `backend/app/main.py` before the app's existing localhost access boundary in the effective middleware stack. The existing outer localhost boundary remains in place; the new upload body guard runs before FastAPI's route-level multipart parser.
- Enforced a fixed full HTTP upload envelope budget of **30 MiB + 128 KiB** (for multipart framing/form fields). Existing per-file **30 MiB** check remains unchanged.
- Normal requests with `Content-Length` above budget fail **413 before body read**. Missing `Content-Length` or chunked requests are measured incrementally and fail **413 upon crossing budget**. Malformed/duplicate `Content-Length` headers fail **400**. Only designated upload POST paths are scoped; GET health/UI routes and other traffic pass through.
- A private exception marker is caught only when the entire exception (possibly Starlette's nested `ExceptionGroup`) consists of the upload-size abort. Unrelated server errors are not treated as 413.
- No change to customer report/PDF/ZIP formats, original `main`, public deployment, or pricing.

## Automated evidence
- Five new synthetic tests in `tests/test_p6e34_upload_envelope.py`: small valid multipart passes, oversized Content-Length 413, no-length chunked body exceeds budget 413, duplicate/invalid length 400, non-upload route unaffected.
- Prototype of the middleware passed **5/5** isolated local tests under an installed FastAPI/Starlette environment. This is preliminary only; authoritative repository CI is below.
- [Full Linux suite 40509856749](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40509856749): **213 PASS / 3 SKIP / 66 warnings**, 0 failures, source SHA `6cd7c39`. The synthetic shipping output generated BASIC 6, STANDARD 9, PREMIUM 11 PDF pages and passed the ZIP manifest checks.
- [Windows native 40509856743](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40509856743): **96 PASS / 9 warnings**. PDF/ZIP synthetic delivery checks passed, including the customer's existing Windows prediction tooling.
- [Windows real Chromium 40509856757](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40509856757): SUCCESS; [Linux real Chromium 40509857436](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40509857436): SUCCESS; [Docker loopback 40509856730](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40509856730): SUCCESS. All runs target the updated code SHA.
- Tests and CI used synthetic datasets only. No real customer files, model ZIPs or license font binaries were committed.

## Residual caveats and acceptance
- This bounds **HTTP body bytes**, not request concurrency, slow-client duration, all CPU complexity, PDF layout, font-source legal terms or anything beyond the local server. The 128 KiB multipart overhead allowance is a release policy constant; it may reject unusually large extra form fields even if the file is below 30 MiB. This is intentional fail-closed behavior.
- Codex had reported uncommitted upload security edits on the owner's separate Windows disk. Those local edits were not remotely accessible, not examined and not overwritten. Review before attempting to apply them to this now-tested GitHub branch.
- All SKU sale gates remain **NO-GO** pending P6E22 owner physical Windows ZIP/PDF visual inspection, licensed font/source review, and explicit commercial authorization. Strict P0–P6 accepted milestones remain **5/7 = 71%**. No merge or public hosting is authorized.
