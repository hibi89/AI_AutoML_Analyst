# P6E14 — PREMIUM inference original CSV header fidelity

Date: 2026-10-27 KST. Repository `hibi89/AI_AutoML_Analyst`, development branch `feature/kmong-v1`.

## Grounded defect
The shipped PREMIUM repeat-prediction script `backend/app/services/premium_predict.py::_load_input` previously parsed CSV via `pd.read_csv` before validating its column list against `model_schema.json`. Pandas silently mangles duplicate source names `a,a` into `a,a.1`; if the legitimate model schema was `a,a.1`, an incorrect source CSV could have been accepted. Existing `raw.columns.duplicated()` cannot see that source duplication. This is the same class of input mutation already corrected at API upload in P6E13, but it remained independently present in the *delivered* customer predictor.

## Narrow implementation / alternative
- **Selected:** use built-in `csv.reader` to read just the source's first logical header record under the same UTF-8-SIG/UTF-8/CP949 decoding fallback already supported by PREMIUM. Reject duplicates or empty/whitespace header cells before pandas normalizes them. Preserve the valid explicit `a,a.1` case, BOM support, row and size limits, skops safety, output no-overwrite and Python compatibility. No new dependencies, no customer data.
- **Rejected:** blanket rejection of dotted suffix columns would block legitimate schemas, and changing encoding auto-detection or replacing the inference engine was unnecessary.

## Commits and observations
- `backend/app/services/premium_predict.py` modified: [7071e59](https://github.com/hibi89/AI_AutoML_Analyst/commit/7071e5939c840683f5c1aee9f933def8858208b3).
- `tests/test_p6_windows_compat.py` adds synthetic attack case and accepted valid explicit dotted header, blank-name rejection, UTF-8-BOM/Korean path valid case: [fb69da8](https://github.com/hibi89/AI_AutoML_Analyst/commit/fb69da8f2e3a8a8adcd600b8c38b1c19d9d9b385).
- New code+test CI runs [Windows 40465571058](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40465571058), [Linux 40465571117](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40465571117): **IN PROGRESS at first record**. Previous parser-only Linux real Chromium [40465500670](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40465500670) SUCCESS, but on code without new tests. Do not claim final PASS until CI observed.

## Release status
- Strict milestones **5/7=71%**, P1 physical Windows owner acceptance PARTIAL and P6 sale gate NOT ACCEPTED; BASIC/STANDARD/PREMIUM **NO-GO** until real owner machine test and explicit commercial approval.
- Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` unchanged. No public service, Vercel, secrets, customer datasets, model artifacts, font binaries or paid APIs.
- Next stage remains one physical Windows owner run described in `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`, not a new artificial completion milestone.
