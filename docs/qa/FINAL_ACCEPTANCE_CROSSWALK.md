# Final product acceptance crosswalk — 2026-10-27 KST

Repository: `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`. This crosswalk compares the frozen [`REQUIREMENTS.md`](../../REQUIREMENTS.md) and [`SKU_MATRIX.md`](../product/SKU_MATRIX.md) with evidence available after P6E29 and the local Windows verification on source commit `12189482177c8efb415972fcab75f1cfe2bdd4f2`.

## Status meanings

- **PASS (synthetic/automated):** the stated automated or synthetic check passed. This is not customer acceptance.
- **PARTIAL:** implementation or limited verification exists, but a material release requirement remains open.
- **NOT TESTED:** there is no evidence for the named human, customer-data, legal, or production condition.
- **FAIL:** a check actually failed. No currently known product behavior failure is hidden by this status table; the Windows suite's initial font-family expectation was corrected and the resulting tests pass.

## Requirement and evidence crosswalk

| Requirement / area | Status | Verified evidence | Remaining limit |
|---|---|---|---|
| CSV/XLSX input, encoding, duplicate/header checks, row/column/file bounds | PASS (synthetic/automated) | Regression suites cover CSV/XLSX parsing, Korean/Japanese encodings, ambiguous/duplicate headers, malformed input and bounded dimensions; P6E13–14 evidence is in `docs/qa/`. | No customer dataset has been processed or accepted. The chosen file and target still require customer authorization and human review. |
| BASIC profiling, KPIs, charts, PDF and ZIP | PASS (synthetic/automated); PARTIAL (acceptance) | Latest local synthetic pack created BASIC PDF (6 pages), chart PNGs and ZIP; manifest/checksum verified. PDF pages were rendered and text-extracted; all pages were reviewed in contact sheets, with representative pages inspected at full resolution. | A human product owner has not approved the latest full report aesthetics or whether each result is useful for a real buyer. Findings and suggestions are rules-based and data-dependent. |
| BASIC ML feasibility, with no model fitting | PASS (synthetic/automated) | P6E24 adds per-column feasibility cues and target ambiguity warnings without fitting a model. | Human suitability advice for any actual business target is NOT TESTED. |
| STANDARD target selection, classification/regression, candidate cap and baseline | PASS (synthetic/automated) | Target ambiguity/variation, classification and regression paths, Dummy baseline separation, up-to-three non-Dummy challengers, scoring schema and failure cases are covered by engine tests and current Windows suite. | No customer-approved target or customer performance result exists. |
| STANDARD/PREMIUM preprocessing, CV, group/time-aware splits, leakage and holdout | PASS (synthetic/automated) | Fold-local preprocessing and chronological equal-timestamp separation have dedicated regressions (P6E25–26); CV/holdout and comparison are exercised on synthetic data. | These checks do not establish that a chosen split matches a specific customer's deployment or future-data process. No real-world generalization claim is approved. |
| PREMIUM tuning, trusted artifact and repeat prediction | PASS (synthetic/automated) | Top-model tuning, same-schema validation and prediction output are exercised. Latest synthetic pack generated three direct Python predictions and three Windows `predict.cmd` predictions; rows and values matched exactly. | This supports only the generated trusted synthetic artifact. Never load customer-supplied serialized models or claim support for a changed schema. |
| Korean/Japanese PDF fonts and ZIP font disclosure | PASS (technical evidence); PARTIAL (rights) | P6E29 checks actual PDF font descriptor streams and README claims; Windows selected/embedded-font tests pass. The latest Windows sample used installed MS Gothic as a Japanese fallback. | Embedded-font evidence and metadata are not a commercial license opinion. The product owner must confirm each selected font's source and terms for the intended delivery. |
| Deliverable integrity and package content by tier | PASS (synthetic/automated) | Latest ZIP manifest/checksum checks passed: BASIC 10 members, STANDARD 13, PREMIUM 20. PDFs were 6/9/11 pages, within frozen target ranges. ZIPs contained no standalone font file; sample pack is synthetic-only. | Real browser downloads, customer unzip experience, and client-machine PDF rendering for this exact source revision are NOT TESTED. |
| Web form, browser selection and actual downloaded ZIP | PARTIAL | Earlier hosted Chromium CI passed 6/6 tier/encoding download cases on Windows and Linux (P6E29 source revision). P6E18 owner machine opened pages and launched the local server. | No current-revision physical owner form-submit/download-and-open session was completed. CI evidence is not owner-machine acceptance. |
| Localhost and file/security guardrails | PARTIAL | Existing automated tests cover localhost/Origin handling, disabled arbitrary filesystem browsing, upload bounds, parser error handling, ZIP contents and trusted artifact boundaries. No public service or customer processing was used. | This is not a penetration test or full dependency/source security audit. Public deployment and anonymous external access remain prohibited. Customer-data privacy behavior is NOT TESTED. |
| Clear no-skill/no-prediction outcomes and truthful claims | PASS (synthetic/automated) | Insufficient/constant target, unsupported cases, model errors and absent valid importance are covered by focused regression tests; BASIC copy does not promise fitting. | A human has not reviewed all buyer-facing wording or accepted the reports as commercially clear. No model accuracy guarantee is made. |
| No paid API, no customer data/model/font committed, main preserved | PASS (repository/process evidence) | Work used local synthetic samples and source-only commits. Original `main` remains `c80c874476f8d5deb4bf611761d89c6d72ca0a2d`; local QA outputs and font cache are ignored. | This does not authorize a sale, production deployment, public listing, or merge. |
| Commercial font, dependency and overall legal clearance | NOT TESTED / NOT CERTIFIED | Technical metadata and current dependency checks are recorded in P6E3/P6E28/P6E29. | No qualified legal review or owner commercial clearance was recorded. Metadata/CVE scans are not legal certification. |
| Owner visual, service-boundary and sale approval | NOT TESTED | No explicit current owner approval is recorded for the latest ZIP/PDFs or any SKU. | Required P6E22 owner decision remains open. |

## Local verification for this revision

- Focused tier/font regression: **13 passed, 16 warnings**.
- Windows release test subset (same ten test modules selected by the wrapper): **93 passed, 25 warnings**. Exact command:

  ```powershell
  .\.venv-automl-qa\Scripts\python.exe -m pytest -q tests/test_original_smoke.py tests/test_basic_mvp.py tests/test_p2_ml_validity.py tests/test_p4_standard_delivery.py tests/test_p5_premium.py tests/test_p6_security.py tests/test_p6_xlsx.py tests/test_p6_windows_compat.py tests/test_p6_chart_policy.py tests/test_p6e6_delivery_policy.py
  ```

  The first attempt to run the wrapper inside the managed sandbox stalled in Windows asyncio `socket.socketpair()` while Starlette TestClient created its portal. The focused endpoint test and the complete 93-test subset passed in the normal local process context. The wrapper's `-OpenBrowser` path was **not** completed in this run.
- Latest generated review pack: `qa-preview/p6e5-20261027T105043Z/` (ignored local synthetic output; not a repository artifact). BASIC/STANDARD/PREMIUM: 6/9/11 PDF pages; ZIP manifests passed; premium direct Python and shipped `predict.cmd` returned equal three-row outputs.
- GitHub CI before this source-only fix: P6E29 Linux [40486435539](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40486435539) 200 passed / 3 skipped; Windows native [40486340777](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40486340777) 94 passed; Windows and Linux Chromium [40486340841](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40486340841) / [40486340785](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40486340785) 6/6 each. Those runs precede commit `1218948`; current-revision remote CI must be checked separately after push.

Warnings were observed and retained in the counts; they include TestClient deprecation, sklearn undefined-metric warnings on synthetic fixtures and pandas date-inference warnings. Warnings are not recorded as zero.

## Per-SKU release decision

| SKU | Implementation/sample gate | Owner visual + font/legal gate | Sale |
|---|---|---|---|
| BASIC ₩60,000 | Synthetic 6-page PDF and manifest PASS | NOT GIVEN | **NO-GO** |
| STANDARD ₩150,000 | Synthetic 9-page PDF, model outputs and manifest PASS | NOT GIVEN | **NO-GO** |
| PREMIUM ₩300,000 | Synthetic 11-page PDF, trusted local prediction replay and manifest PASS | NOT GIVEN | **NO-GO** |

Frozen progress remains **5/7 = 71%** accepted implementation milestones. P1 remains partial; P6 release is not accepted. P6E22 is owner-only: review actual local tier ZIP/PDFs, verify font and service terms, and explicitly decide whether any specific SKU may be sold. No SKU is currently approved for sale. No deployment, listing, paid service, or merge to `main` is authorized by this technical verification.
