# P6E19 — Explicit Japanese CP932 import and PREMIUM repeat prediction

Date: 2026-10-27 KST. Only `feature/kmong-v1`; no `main` merge, product publication, paid APIs, customer data uploads, or changes to the physical owner's existing Windows installation.

## Grounded requirement gap
The frozen `REQUIREMENTS.md` explicitly requires Japanese/Korean encoding. Shared `_read_csv_from_bytes` previously tried UTF-8, CP949, EUC-KR, then Latin-1; Japanese Windows `CP932` CSV was not directly supported. Some Shift-JIS bytes can be decoded as CP949 but yield different glyphs, so blind detection could silently corrupt column labels or values. A new optional encoding select provides a deterministic route without changing the historical auto order.

PREMIUM's shipped `predict.py` also supported only automatic UTF-8/CP949 for repeat prediction. A Japanese CP932 training dataset would lack a documented way to replay CP932 predictions. Allow explicit CP932 in the local shipped model runner as well.

## Implemented without changing default behavior
- Shared ingestion `backend/app/main.py::_read_csv_from_bytes(content, encoding='auto')`: unchanged `auto` candidates; strict allowlist and explicit `cp932`, retains duplicate source-header fail-closed and row limit checks.
- `backend/app/services/tabular_input.py::read_uploaded_table(..., csv_encoding='auto')` forwards selected codec for CSV; XLSX is parsed independently as workbook and selection is irrelevant.
- Three local FastAPI report routes accept a form field `csv_encoding`, default `auto`; all three `frontend/*_mvp.html` show Auto/UTF-8/CP949/CP932 with Japanese-encoding caveat. No JavaScript dependency, no extra service, and no change to original legacy API.
- Shipped PREMIUM `predict.py`: optional `--csv-encoding cp932` in trusted local CLI. Shipped Windows `predict.cmd` adds an optional *third* parameter, e.g. `predict.cmd new_data.csv predicted.csv cp932`. Existing two-parameter command remains the default. PREMIUM report handover and ZIP README explain the optional third argument.
- Tests with synthetic CP932 Japanese column/value strings verify exact glyph integrity, train/report endpoint propagation, explicit rejection of unsupported encodings and duplicate headers, normal Korean CP949/UTF-8 operation, and Windows optional third-argument prediction.
- Source commits: `c458133`, `8f3cab1`, `852ed02`/`923074b`/`5d9c052`, `af3db2a`/`b09af25`, `d7f48ca`/`d50283a`/`b2dc86b`. New `tests/test_p6e19_csv_encoding.py` included in native Windows workflow.
- CP932 is **explicit**, not promised as universally auto-detected. Reading arbitrary Latin-1 in default auto mode remains a documented preexisting limitation; unknown source encoding requires customer confirmation, not AI guessing. User has not manually approved new form layout, and direct owner device has not run new code.

## QA references (check conclusions before reporting)
- Windows native source+predictor regression [40472590303](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472590303), Linux full [40472590292](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472590292) at final executable/test SHA `b2dc86bd589f667b110dc4146562c40bcc9089e0`: **IN PROGRESS at document creation**.
- Windows 3 SKU Chromium browser [40472529164](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472529164) and Linux 3 SKU browser [40472529272](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472529272), at `d50283a` source SHA. Linux browser **SUCCESS**, Windows browser initially IN PROGRESS. These synthetic browser runs do not replace owner's PDF aesthetic and commercial judgment.
- Original 2026-10-27 physical owner Windows run established 91 PASS, 3 SKUs’ PDF/ZIP manifests and trusted `predict.cmd`, visible BASIC/STANDARD/PREMIUM local pages; this latest P6E19 code has **NOT** been pulled on owner PC.
- Official frozen P0-P6 milestone count remains **5/7 = 71%**, P1 final user GUI/PDF judgment PARTIAL and P6 sales NO-GO; no new sale signoff claimed.

## Next
Verify latest CI and exact new tests. Document any failing test and repair before calling complete. Keep owner's private machine untouched until they elect to inspect visual/design/legal/release gates. All changes and test data remain in GitHub branch; no customer model or files committed.

## FINAL CI evidence (2026-10-27 KST)
- Exact latest executable+tests SHA `b2dc86bd589f667b110dc4146562c40bcc9089e0`:
  - [Windows native 40472590303](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472590303) **SUCCESS: 93 PASS / 9 warnings**, including Japanese CP932 cross-tier synthetic encoding tests, delivered Windows `predict.cmd` optional CP932 third argument and full Windows 3-tier synthetic report/ZIP/model replay in path with spaces. No failed steps.
  - [Linux full 40472590292](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472590292) **SUCCESS: 150 PASS /3 Windows-only SKIP /41 warnings**. Generated synthetic BASIC PDF **6 pages**, STANDARD **9**, PREMIUM **11**; all manifests PASS.
  - Browser regression on executable source `d50283a4883375620a3b9ed47c7b9e0afa15c164` (only additional regression tests/docs since): [Windows Chromium three-tier 40472529164](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472529164) **SUCCESS**, [Linux Chromium three-tier 40472529272](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472529272) **SUCCESS**.
- CP932 is **explicit**, NOT promised as reliable automatic inference; all three MVP UI pages retain historical `auto` default. Shipped Windows PREMIUM CLI supports optional `predict.cmd new_data.csv predicted.csv cp932`; previous two-parameter invocation continues to pass native tests. End-to-end source accuracy under selected codec verified in synthetic tests, not a real customer's dataset.
- Actual owner Windows test from P6E18 happened on earlier code, NOT on this new branch head. No owner's new actual browser clicking/PDF aesthetic/legal/per-tier sale signoff. Strict P0–P6 **5/7=71%** accepted, all SKU commercial **NO-GO**; no main merge, global font updates or production hosting. 
