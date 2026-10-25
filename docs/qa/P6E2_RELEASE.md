# P6E2 — adverse input / private output validation (2026-10-26 KST)

## Measured execution, scope, and changed paths
- Code changes on `feature/kmong-v1`: `backend/app/main.py`, `backend/app/services/standard_engine.py`, `backend/app/services/tabular_input.py`.
- New regression suite: `tests/test_p6e_adversarial.py`; synthetic-only.
- Latest full [Linux CI 40213253212](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213253212), tested SHA `801c4ddad9db2644604c79b7fde8277fad53a085`: **100 passed, 1 Windows-only skipped, 41 warnings**. Executed BASIC/STD/PREMIUM PDF generator with **6/9/11 pages**. No failed tests.
- [Windows native 40213192384](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213192384) and [Linux Chromium native UI 40213192440](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213192440): **SUCCESS** at latest implementation SHA `76e60f256ff1c479dd815722b7aee58c1d26f913`, before addition of test-only suite.
- Existing original main `c80c874476f8d5deb4bf611761d89c6d72ca0a2d` was not modified.
  
## Actual mitigations
1. `_read_csv_from_bytes` now rejects NUL, attempts bounded `MAX_ROWS+1` parsing (over-limit rows **rejected**, not silently sampled), only retries encoding failures, returns generic parser details instead of potentially reflecting raw customer rows to client errors.
2. CV model-level failure metadata in `standard_engine.py` now contains only exception **class** and generic explanation, not raw `str(exc)` potentially embedding confidential row/category text; successful models remain evaluated and selection semantics unchanged.
3. XLSX ZIP parser now rejects case-insensitive VBA/macro markers, duplicated/case-colliding member names, and external-link workbook parts before openpyxl reads the workbook. Existing 30 MiB compressed /80 MiB inflated /20k rows /50 columns remain.
4. Synthetic confidentiality suite verifies BASIC/STANDARD ZIP manifest hashes, no raw categorical row labels in PDF text / CSV / JSON / README, original field metadata intentionally retained, formula-shaped summary CSV field begins with apostrophe, hostile CSV and XLSX yield safe errors, and private sklearn error strings do not escape into analysis JSON.
5. PREMIUM fitted `model_pipeline.skops` **necessarily contains learned category information** for repeat predictions. Never describe the PREMIUM ZIP as category-value-free; ship only to the authorized customer. Integrity SHA is not identity proof.

## Actual PDF review
- Downloaded fresh P6E1 `basic-synthetic-pdf-review` artifact from [Actions 40212675598](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212675598); visually examined all 11 PREMIUM pages in a montage, including new handover pages 10–11. **No obvious clipping or broken Korean glyphs at montage resolution**. Noticeable unused lower-page whitespace remains particularly on 5/6/7/10/11; owner has **not** approved the design. This sample predates P6E2 security-only changes; those changes do not intentionally change PDF layout.

## Dependency inventory and unverified gates
- Downloaded `p6c-verified-dependency-versions` artifact from CI 40213253212. `pip freeze` shows **46 resolved Python distributions** on Linux runner; recorded metadata covers 14 direct dependencies only. `skops==0.16.0` has no machine-readable license text in that particular metadata result (classifier reads "OSI Approved"); inspect upstream exact license and transitive license obligations before selling.
- **No automated CVE/vulnerability scanner executed.** Treat vulnerabilities as NOT CHECKED, and distribution/license suitability as PARTIAL, not green.
- Owner's Windows computer: first install, actual Edge/Chrome download/unzip, font, repeated PREMIUM predictions, file tamper/wrong schema: **NOT RUN**. Browser/Windows CI runner passing does not replace this gate.
- Multipart body spooling before application-level 30 MiB cap, large adversarial categorical workload, scheduler timeouts and termination, complex customer semantics are not fully certified.
- This local-only app has **no Vercel/Production deployment**. No customer CSV/ZIP/model uploaded to GitHub. No external public server or payment.

## Commercial readiness / next
**P1 PARTIAL**, **P6 IN PROGRESS**, strict P0–P6 milestones **5/7 = 71%**. BASIC=NO-GO, STANDARD=NO-GO, PREMIUM=NO-GO for sale.

Next READY: **AUTO-KM-P6E3** — safely run reproducible version-scoped vulnerability/transitive license report; address outstanding CVE findings rather than suppress; add realistic wide/ragged XLSX and CSV/multipart boundary tests; inspect PDF density and refine only from actual data; prepare concise owner Windows approval checklist. No main merge, Vercel or Kmong launch absent approval.
