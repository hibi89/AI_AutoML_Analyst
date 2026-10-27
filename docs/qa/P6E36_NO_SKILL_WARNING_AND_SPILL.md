# P6E36 — conditional no-skill warning and independent PDF spill regression (2026-10-27 KST)

Repository `hibi89/AI_AutoML_Analyst`; working branch `feature/kmong-v1`. All test data is synthetic. This is engineering evidence, **not sale acceptance**.

## Verified follow-up — release image/page regression closed (2026-10-27 KST)

- Current implementation source `a8c102c0bf13c718bf48c97e44632bc4c59cbf61`, deterministic CI visual gate `d6dade5317ba3630cf495b0bdf0419a88d72ced0`.
- Script-inclusive full Linux CI [40518329515](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40518329515): **SUCCESS, 213 passed / 3 skipped / 66 warnings**.
- Independently downloaded **actual artifact 12741525131** (not a prior revision). PDF pages BASIC **6**, STANDARD **9**, PREMIUM **11**. Paid tier ML appendix exactly **3 pages each**, no extra `ML 4` spill.
- Both STANDARD and PREMIUM were `holdout_beats_dummy=false`, and **both printed** `예측 성능 우위가 입증되지 않았습니다.` in the ML PDF. The previously missing PREMIUM warning is now unambiguously present.
- All three deliverable ZIP CRC and manifest file SHA-256 validations PASS; externally rendered PDF bytes equal the PDF inside corresponding ZIP; no unsupported `[U+HEX]` placeholders or text spans outside page rectangles in **26 total pages**.
- Source `a8c102c0` Windows native [40517973675](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973675) **96 passed/9 warnings**, Windows Chromium [40517973790](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973790) SUCCESS, Docker [40517973754](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973754) SUCCESS; source Linux integration [40517973833](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973833) 213 PASS /3 SKIP. Linux Chromium [40517973806](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973806) still IN PROGRESS at capture; **do not call 5/5 complete** until verified.
- Product milestones **remain 5/7=71%**, P1 PARTIAL / P6 NOT ACCEPTED; visual approval on owner's physical Windows machine, installed font/source-rights and component notices, and explicit individual SKU commercialization decisions remain OPEN. No public hosting, main merge, customer processing or sale.

**Remaining next step:** check outstanding Linux Chromium status (single check, no rerun), then P6E22 owner-only manual acceptance. Do not reopen P6E36 engineering unless a new reproducible failure appears.



## Reproduced defect: sales-critical warning silently omitted
- Actual 150-row synthetic PREMIUM deliverable from GitHub Actions [40511166451](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40511166451) at tested source `dce23b6847316d3b4b4568145faabf7a7b6aba2b` gave independent holdout `f1_weighted` selected **0.2841**, Dummy **0.3333**, `holdout_beats_dummy=false`.
- The PREMIUM `premium_summary.json` has seven warnings, including `비교 모델이 Dummy 기준선을 넘지 못했습니다. 유효한 예측 신호가 있다고 주장할 수 없습니다.` as warning 7. Shared PDF builder `backend/app/services/standard_delivery.py` rendered only `analysis["warnings"][:6]`, silently omitting that release-critical warning in PREMIUM PDF (STANDARD had six and displayed it).
- This is a real output/communication defect even though the underlying ML metrics were correctly reported. A buyer must not mistake the delivered reusable model for established predictive improvement.

## First repair — discarded after independent artifact inspection
- Commit [`feb61a59`](https://github.com/hibi89/AI_AutoML_Analyst/commit/feb61a59fe1aab3444f40212a0e3d3ed2bfbb254) added a conditional standalone warning and conditional assertions in STANDARD/PREMIUM PDF tests.
- **All five hosted CI workflows completed SUCCESS** at `feb61a59`: Linux [40517044807](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517044807), Windows native [40517044339](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517044339), Linux Chromium [40517044288](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517044288), Windows Chromium [40517044737](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517044737), Docker [40517044631](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517044631).
- However, independently downloaded **actual PDF review artifact 12738494377** from Linux CI: STANDARD remained 9 pages but PREMIUM grew from 11 to **12 pages**, with a nearly empty `ML 4` page containing only a concluding disclaimer. This quality regression was **not detected** by the previously broad 10–15-page acceptance range. Automated test success is not human-quality acceptance.
- Do **not** reuse or reinstate the extra-paragraph repair.

## Revised repair, source `a8c102c0`
- [`a8c102c0`](https://github.com/hibi89/AI_AutoML_Analyst/commit/a8c102c0bf13c718bf48c97e44632bc4c59cbf61) replaces an *existing* small explanatory paragraph conditionally rather than inserting another paragraph: when `holdout_beats_dummy=false`, show `중요: 독립 검증에서 Dummy 대비 예측 성능 우위가 입증되지 않았습니다.`. When true, retain the earlier qualification about statistical significance and generalization. Model logic and PDF layout geometry remain otherwise untouched.
- This avoids adding text flow blocks, but **new PDF page count and visible warning must still be independently checked on the revised-source CI artifact**. Do not infer success from source inspection or older artifacts.
- Existing two SKU tests check the conditional text when holdout falls below Dummy.

## Added reproducible CI visual gate, script `d6dade53`
- [`d6dade53`](https://github.com/hibi89/AI_AutoML_Analyst/commit/d6dade5317ba3630cf495b0bdf0419a88d72ced0) adds `_check_ml_review_pdf` to `scripts/create_basic_preview.py`. The exact realistic 150-row synthetic STANDARD/PREMIUM review cases must now show **exactly three appendix ML pages**, and if holdout is not better than Dummy, the PDF ML section must visibly contain the no-skill warning.
- This gate directly detects BOTH old failures: source `dce23b68` = PREMIUM 11 pages / 3 ML pages / **warning absent**; source `feb61a59` = PREMIUM 12 pages / 4 ML pages / warning present.
- Latest source-level CI for `a8c102c0`: Linux [40517973833](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973833), Windows [40517973675](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973675), Linux browser [40517973806](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973806), Windows browser [40517973790](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973790), Docker [40517973754](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40517973754); check LIVE statuses before asserting success.
- Script-gate CI for `d6dade53`: Linux [40518329515](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40518329515); status **PENDING verification** at documentation creation.

## Independent pre-repair package audit (source `dce23b68`)
Local analysis of artifact 12736797946 confirmed: BASIC 6 / STANDARD 9 / PREMIUM 11 PDF pages; ZIP members 10 / 13 / 20, with exactly 9 / 12 / 19 hashed manifest files; all actual ZIP member names/sizes/SHA-256 hashes, CRC, identical extracted `report.pdf`, no `[U+HEX]` text placeholders, no text spans extending outside A4 PDF bounds; extracted PDF font sizes at least 8 pt (chart-image font is separately out of scope). This **does not** certify the post-repair PDF, private category metadata, actual hardware print rendering, or legal rights.

## Font reference and remaining owner-only acceptance
- NAVER official Nanum font license: https://help.naver.com/service/11029/contents/18088?lang=ko&osType=PC — commercial font use other than selling the font itself permitted under OFL 1.1, subject to specific terms.
- Microsoft Windows-supplied font document embedding rights depend on the actual font embedding flags and conditions: https://learn.microsoft.com/en-us/typography/fonts/font-faq .
- Actual owner's installed font provenance and licensing, dependency NOTICE triage, final customer PDF/ZIP inspection, and explicit SKU-by-SKU commercial approval remain **OWNER ACTION REQUIRED**.
- Accepted implementation milestones **5/7 = 71%**, P1 PARTIAL, P6 NOT ACCEPTED; all BASIC/STANDARD/PREMIUM **NO-GO**. Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` preserved. Localhost-only app; Vercel/Production URL NOT APPLICABLE. No public listing, charge, main merge, paid API or customer data use.

## Exact next ㄱ continuation
1. Read live `feature/kmong-v1` HEAD. Check the five `a8c102c0` workflows and `d6dade53` visual-gate run, including logs; distinguish checked pass/fail/pending.
2. Download **revised actual** `basic-synthetic-pdf-review` artifact from source `a8c102c0` or the new script-gate run. Verify 6/9/11 page counts; exactly three ML appendix pages, no `ML 4` spill, clearly visible no-skill warning in PREMIUM and STANDARD when not beating Dummy, ZIP checksums and tier labels. Do not assume GitHub runner PASS proves aesthetic acceptance.
3. If that fails: inspect exact root cause; fix minimal source or gate, avoid repeating the extra-paragraph approach. If it passes: update `STATUS.md`, `HANDOFF.md`, `ACTIVE_TASK.md` with verified SHA/status, avoid needless changes.
4. Only the user can complete P6E22 physical Windows/license/commercial acceptance. No sale authorization inferred from ㄱ.

Last document evidence cut: 2026-10-27 KST. Source/test HEAD before docs: `d6dade5317ba3630cf495b0bdf0419a88d72ced0`.
