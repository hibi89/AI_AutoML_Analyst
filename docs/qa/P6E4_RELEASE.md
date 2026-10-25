# P6E4 — report density / exact skops license / tier release gates
Updated 2026-10-26 KST. Scope: `feature/kmong-v1`, synthetic test files only. Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` preserved.

## Changes and decisions
- `backend/app/services/basic_p3.py`: new `_numeric_profiles` computes observed-only quartiles and valid-row counts for at most four numeric columns. JSON summary exposes these aggregates. The final single-chart page now presents Q1/median/Q3, with no filler chart or individual records; final BASIC page adds observed column coverage/uniqueness/missingness as an ML-target **review aid, not a target recommendation**. Sparse datasets do not receive invented profiles.
- `backend/app/services/standard_delivery.py`: under-filled ML-methodology page adds the actual successful CV candidate count, the selected model's training CV score, and the Dummy baseline's training CV score, explicitly distinguished from independent holdout metrics. No new ML experiments or claims invented.
- Updated `tests/test_p3_basic_delivery.py` to compare serialized quartiles to source synthetic data and require both new PDF sections in the correct pages; `tests/test_p4_standard_delivery.py` requires the train-CV method table.
- Verified official `skops==0.16.0` source/LICENSE at PyPI release attested commit `bcc69da93df528e3c72993e5d623682dbfd1d443`: **MIT**, copyright (C) 2021 Hugging Face Inc., notice retention requirements. See `docs/qa/P6E4_SKOPS_LICENSE.md`. This resolves exact skops license identification, not all third-party commercial redistribution compliance.
- Created tier-specific `docs/qa/P6E4_TIER_RELEASE_GATE.md`: BASIC KRW 60k, STANDARD KRW 150k, PREMIUM KRW 300k, all explicit **NO-GO** pending actual physical owner Windows execution and final legal/design approval.

## CI progression — including failure and fix
- First STANDARD report layout commit `ec8d432ca6de379e2d1a668b81ea8d91286f0d3b` introduced a missing closing `)` on `story.extend([...])`. [Linux 40215234937](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215234937) **FAILED at test collection (3 errors)**. Root cause confirmed from runner source traceback at `standard_delivery.py:205`; fixed in commit `62e3bdc4c3afe584f77f6b06cfe43a3a8a72b185`. Do not repeat this patch pattern without static syntax review.
- Final full [Linux 40215434575](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215434575) on code SHA `62e3bdc4c3afe584f77f6b06cfe43a3a8a72b185`: **105 passed, 1 Windows-only skipped, 41 warnings**. Synthetic BASIC **6** / STANDARD **9** / PREMIUM **11** PDF pages generated and rasterized, upper-bound synthetic BASIC benchmark and ML comparison benchmarks completed.
- Final [Windows native 40215434541](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215434541) same executable SHA **50 passed, 9 warnings**, headless Windows runner (not owner's PC).
- Final [Chromium real download 40215434538](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215434538) same executable SHA **SUCCESS**, actual browser upload + button + verified ZIP bytes: BASIC **481,722**, STANDARD **636,345**, PREMIUM **729,592**. Synthetic CI only.
- Earlier [Linux dependency audit 40214119475](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214119475): 52 pinned installed Linux distributions, zero **known advisories at scan time**. Not continuously monitored nor a legal/commercial clearance.

## Actual visual review
- Retrieved GitHub Actions `basic-synthetic-pdf-review` from final Linux CI 40215434575 and reviewed BASIC 6, STANDARD 9, PREMIUM 11 rendered page montages. Pages 5/6/7 have visibly better grounded numerical density, with no obvious overlapping text, clipped tables, or broken Korean glyphs at montage resolution.
- **Remaining visual limitations:** first/basic quality page 2 and PREMIUM instruction pages 10/11 are intentionally still spacious. Aesthetic acceptability for paying customers has **not been approved by owner**; don't infer visual signoff from passing pdftoppm or text parsing. Run specific full-resolution final checks on owner Windows.

## Residual blockers / commercial truth
- Physical owner Windows first installation, licensed Korean font, Edge/Chrome input/download, full ZIP extraction, premium predict.cmd with NEW matching-schema CSV, tampering/wrong-schema/no-overwrite: **NOT RUN**; checklist `docs/qa/P6E3_WINDOWS_RELEASE_CHECKLIST.md`.
- Review full 52-package transitive license/NOTICE and chosen redistribution/install flow. MIT for skops verified; no assertion that every dependency is commercially cleared. OS/font notice obligations and supply-chain provenance must remain.
- Operational bounds remain: BASIC 20,000 descriptive rows/50 cols/30MiB, STANDARD supervised max 5,000 rows/180 encoded/600k cells, PREMIUM supervised 3,000/140 encoded/360k cells. No silent data sampling.
- No customer files/credentials/model artifacts committed. No public server, production Vercel (NOT APPLICABLE), merge to `main`, or paid service use.
- Overall strict milestone completion `P0–P6: 5/7 = 71%`. P1 PARTIAL, P6 IN PROGRESS, all 3 SKUs sale **NO-GO**.

## Next READY AUTO-KM-P6E5
1. Handle remaining sparse PDF areas 2/10/11 only if defensible (prefer deliberate whitespace to filler) and collect explicit owner visual signoff on actual samples.
2. Prepare targeted release evidence bundle and detailed physical Windows guide/feedback acceptance report. Await observed owner-machine results; do not simulate them.
3. Finish identifiable transitive license/NOTICE distribution audit for full 52-pkg set and confirm security/model provenance boundaries; do not label unreviewed as pass.
4. Verify exact tier-specific go/no-go, owner authorization, and launch conditions. Do not merge/deploy/sell without permission.
