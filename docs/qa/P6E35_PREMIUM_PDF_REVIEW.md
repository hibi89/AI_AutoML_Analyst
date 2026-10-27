# P6E35 — verified PREMIUM PDF ML section labeling and unsupported glyph repair

Date: 2026-10-27 KST
Working branch: `feature/kmong-v1`
Source SHA: `dce23b6847316d3b4b4568145faabf7a7b6aba2b`

## First-hand pre-fix evidence
Downloaded actual synthetic report artifact `basic-synthetic-pdf-review` **12736318685** from Linux [CI 40509856749](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40509856749), source SHA `6cd7c39ef9cf622d22ae76c3e66aebca79368838`.

PDF page counts: BASIC 6, STANDARD 9, PREMIUM 11. Extracted text and directly inspected the rendered image of PREMIUM page 9.

1. PREMIUM **pages 7–9** showed the text **`AI AutoML Analyst | STANDARD 모델 검증`** in all three footers; the appended ML-section title on page 7 also said **`STANDARD — 모델 학습 및 검증`**. The five-model PREMIUM computation and model handover pages existed; defect was in the *shared section's output labeling*, not evidence of wrong model selection.
2. Both STANDARD and PREMIUM page 9 displayed literal **`[U+2212]`** in the scorecard sentence `선택 모델 [U+2212] Dummy 차이`. This was visually confirmed in the PNG, not merely text-extraction encoding noise.
3. Across all 26 pre-fix report pages, those two page-nine placeholders were the only `[U+HEX]` occurrences found.

## Selected minimal repair
- `backend/app/services/standard_delivery.py`: add keyword-only `report_tier` to shared `_append_ml_pdf`, require one of STANDARD/PREMIUM; include the chosen tier in footer, ML section title and PDF document metadata. Default STANDARD retains the existing STANDARD call behavior.
- `backend/app/services/premium_delivery.py`: pass `report_tier="PREMIUM"` at the shared ML appendix call.
- Replace unsupported U+2212 mathematical minus glyph in the human-facing score-difference sentence with safe, readable ASCII `-`; retain the **actual metric arithmetic and sign unchanged**.
- `tests/test_p4_standard_delivery.py` and `tests/test_p5_premium.py`: assert the respective merged-PDF text and guard against the reappearance of `[U+2212]` and STANDARD labeling in PREMIUM ML pages. No impact on the BASIC report path.

## Hosted full CI on source SHA dce23b68
- Linux integration [40511166451](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40511166451): **213 passed, 3 skipped, 66 warnings**. BASIC 6, STANDARD 9 and PREMIUM 11 PDF pages; tier ZIP manifests PASS.
- Windows native [40511166279](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40511166279): **96 passed, 9 warnings**, all 3 tier PDF/ZIP delivery checks PASS.
- Windows three-tier Chromium [40511166377](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40511166377): **SUCCESS**.
- Linux real Chromium [40511166238](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40511166238): **SUCCESS**.
- Docker localhost [40511166378](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40511166378): **SUCCESS**.

## Independent fixed-output validation
Downloaded the **new** Linux build PDF review artifact **12736797946** from run 40511166451. Independently opened/extracted all **26 pages** using a PDF renderer. All report pages showed **zero literal `[U+...]` placeholders**. The STANDARD ML appendix retained the STANDARD title and three STANDARD footers; the PREMIUM ML appendix had three PREMIUM footers and a PREMIUM ML section title with **no STANDARD model-validation text**. Both had a readable ASCII model-minus-Dummy difference sentence. No real customer files were involved.

## Still out of scope / sale decision
- This is a verified *synthetic report* rendering/text integrity repair, not a substitute for actual customer-machine PDF aesthetic inspection or real-data business interpretation.
- Installed font provenance, applicable SIL OFL/third-party attribution and customer source rights, complete release/legal approval, Windows physical owner acceptance remain distinct, owner-only gates. **BASIC, STANDARD and PREMIUM are all NO-GO for sale**; formal acceptance remains **5/7 (71%)**.
- Original `main` protected. No public web deployment, no user/client records, models or font binaries committed.
