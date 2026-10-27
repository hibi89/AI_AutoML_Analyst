# P6E17 — Owner Windows PREMIUM shipped CMD replay failure

Date: 2026-10-27 KST. Branch `feature/kmong-v1`.

## Real owner report and precise scope
The owner successfully pulled commit `6bbda85`, downloaded the OFL Nanum Gothic project font, installed pinned Python 3.11 dependencies, and advanced into synthetic report generation. The terminal then showed scikit-learn `UndefinedMetricWarning` and Matplotlib missing NanumGothic *bold weight* fallback; **these are warnings and not the thrown exception**. The full stack trace originates in `scripts/p6e5_windows_demo.py` at the native Windows exact `predict.cmd` subprocess replay:
`RuntimeError: Windows predict.cmd synthetic replay failed.`
Then PowerShell correctly stopped with `Synthetic tier review pack failed; do not approve sale.`

The direct `predict_csv()` call before the Windows CMD branch had returned three predictions, otherwise execution would not have entered the later batch check. The basic/standard/premium ZIP builders also returned data that passed earlier structural checks. Nonetheless, the owner has NOT completed acceptance of all generated outputs nor real browser/PDF inspection. **Specific batch exit cause is still unknown** because original code intentionally discarded stderr; no owner-level model traceback or error code was captured.

## Independent cross-platform evidence and remaining difference
- Native Windows [40469761652](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40469761652) on old demo code and workflow integration commit `8ea4f1546d4d3186c3492a22052e6ec1307d9fca`: **SUCCESS**, actually running `python -m scripts.p6e5_windows_demo` under an output root containing spaces and requiring the shipped Windows CMD replay, model/ZIP manifests and PDF checks. This is a hosted runner, not owner PC. Therefore the owner-only failure cannot be called universally reproducible or conclusively a batch quoting bug.
- Existing `tests/test_p6_windows_compat.py` previously passed simple hand-authored model batch tests; those do not by themselves replace owner full synthetic SKU replay.

## Corrective change under verification
- [`81bdcd3`](https://github.com/hibi89/AI_AutoML_Analyst/commit/81bdcd3bf48c1ff2e66943b4daf809eb780b3ec1) in `scripts/p6e5_windows_demo.py`: run the documented customer-mode call from `premium/trusted_demo`: `predict.cmd new_data.csv cmd_predictions.csv`, using **relative file names** instead of two absolute owner path-with-spaces arguments. Captured cmd stdout/stderr is NOT directly emitted (protect user paths/model data); on failure emit bounded batch return code, safe predefined failure category, whether `python` on PATH resolves to current QA interpreter, and whether result file was created. Do not mark CMD PASS just because direct Python succeeds.
- [`16fb36e`](https://github.com/hibi89/AI_AutoML_Analyst/commit/16fb36e67b5cb1acabfad23ce5764317c25fcf98) adds synthetic-only tests for pathless output categorization. Same frozen product contract, no extra dependencies, no customer-model uploads, no main merge, no global Windows settings changes.
- CI at this document entry: [Windows 40470153374](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40470153374) and [Linux 40470153375](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40470153375) triggered on exact source+tests SHA `16fb36e` and **IN PROGRESS**. Must check final conclusion and actual Windows synthetic review stage before asserting PASS. This patch is a targeted hypothesis-based reliability improvement, not confirmed owner root-cause removal.

## Next owner action (after CI success)
Owner keeps the same local `E:\AI AutoML Analyst` clone and dedicated QA venv. No re-clone, deleting QA outputs or system font/venv installation. Execute:
```powershell
cd "E:\AI AutoML Analyst"
git pull --ff-only origin feature/kmong-v1
powershell -ExecutionPolicy Bypass -File .\scripts\windows_release_qa.ps1 -OpenBrowser
```
If batch still fails, the new sanitized `exit/category/python_matches_qa_venv/output_created` indicators will guide next correction without asking for raw dataset or private model contents. Fresh previews are created under a separate gitignored QA run directory and no older folder is deleted by this QA tool.

P0-P6 milestone contract remains **5/7 = 71%** accepted: P1 physical first install/GUI PARTIAL; P6 commercial release NOT ACCEPTED; BASIC/STANDARD/PREMIUM sales **NO-GO**. Owner must still inspect actual local Chrome/Edge download/ZIP/PDF Korean design, trusted PREMIUM model, and explicit legal/quality sale decision. `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` stays unchanged.


## FINAL CI evidence and owner gate — 2026-10-27 KST
- [Native Windows 40470153374](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40470153374), exact code+test SHA `16fb36e67b5cb1acabfad23ce5764317c25fcf98`: SUCCESS, **78 PASS /9 warnings**, real 3 tier synthetic PDF/ZIP BASIC6/STD9/PREM11 pages/manifest PASS, actual shipped `predict.cmd` replay PASS under spaced output path, `sale_gate=NO_GO`.
- [Linux 40470153375](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40470153375), same code+test SHA: SUCCESS, **136 PASS /2 Windows-only SKIP/41 warnings**, all three tier PDF ZIP/matrix checks PASS.
- Hosted runs **DO NOT** prove the exact owner's failed batch issue was fixed; next physical owner rerun and explicit actual browser/PDF/commercial gates remain NOT RUN. No customer rows, font binary or ZIP uploaded.
