# P6E6 — licensed-delivery boundary and ten-package legal-obligation review
As of 2026-10-26 KST. All files on `feature/kmong-v1`; main original preserved.

## Scoped engineering change
- Added `scripts/p6e6_delivery_policy.py` to check the **actual generated customer ZIP**. Allowlist per tier and chart artifact type; reject unexpected members, duplicated entries, path traversal, wheel/raw-font/native executable/bundled Python source or binary, a lower-tier fitted model, missing deliverables and ZIP manifest hash/size mismatch. This is a *shipping-artifact-only* guard, not a safe parser for arbitrary external ZIP uploads.
- Integrated `verify_shipping_zip(payload, tier)` into the existing `scripts/p6e5_windows_demo.py` local/CI three-tier synthetic pack generation, **before writing each ZIP to disk**. Review JSON now records that vendor wheels, loose fonts, native EXEs are absent; the PDF-embedded font's license remains a separate question.
- Added `tests/test_p6e6_delivery_policy.py`: clean all three tiers, forbidden wheels/font/vendor file/path traversal/new unauthorized chart, cross-tier model exclusion, missing font notice, manifest tampering and required-member deletion.
- Updated three tier `README.txt` outputs using shared `NANUM_FONT_CREDIT` (basic_p3.py, standard_delivery.py, premium_delivery.py). Citation to the official Naver NanumGothic SIL Open Font License 1.1, copyright statement and origin. Added policy requirement that every shipped ZIP's README retain the credit. This does not redistribute original TTF files or certify the embedded subset's conditions by itself.
- Added `docs/qa/P6E6_LICENSE_DISTRIBUTION.md`: exact installed name+version license evidence of 10 previously flagged packages and the distribution choice (customer separately installs Python packages; no Python wheel/venv installer bundled). Future frozen-EXE/third-party-wheel font bundle would require a **new legal audit**.

## Previously accepted factual evidence
- P6E5 full Linux [40216846990](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216846990), source SHA `a0741885e481d32914b039e92e729775073be1e1`: **111 PASS / 1 Windows-only SKIP, 41 warnings**, BASIC 6 / STANDARD 9 / PREMIUM 11 PDF/ZIP, 3-row PREMIUM Python replay.
- Windows native [40216847015](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216847015), same SHA: **52 PASS** with PowerShell source parse and native prediction; NOT owner's computer.
- [P6E5 license/security 40216690129](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216690129): 52 installed Linux packages have license/NOTICE-file metadata and hashes, 10 flagged license complexities; **0 known vulnerabilities reported at scan time**. The 10 were review flags, not proof of license violations.
- P6E6 **newest code CI must be checked at test SHA** before claiming success; previous P6E5 green run does not test this new shipping policy.

## Owner / legal blockers not automatically closed
- Physical owner's Windows/Chrome/Edge first-use, unzip, PDF visual inspection and PREMIUM `predict.cmd` on actual machine: **NOT RUN**. Existing owner runbook `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`; human design signoff still NOT APPROVED.
- The chosen ZIP + customer's own pip install significantly narrows source/binary redistributions, but font embed license conditions and any *future* installer/binary packaging remain compliance questions. The 10 package obligations are cataloged, not individually lawyer-certified.
- The report and model are rule-generated and supplied only to authorized client; model may retain private categorical metadata.
- 6–8/8–12/10–15 page targets remain. Leave deliberately sparse instruction pages alone rather than fabricate results.
- No customer files, font binaries, proprietary model files or paid secrets committed. No main merge, external deployment, visibility change, spending, or sales listing approved. Vercel production = NOT APPLICABLE (localhost deliverable).
- Strict `P0–P6` acceptance **5/7=71%**, P1 PARTIAL physical Windows, P6 IN PROGRESS, **all three SKU sales NO-GO**.

## Next READY AUTO-KM-P6E7
1. Verify final Linux regression, Windows native and Chromium browser on the **latest shipping-policy + font-license-credit code SHA**, not earlier snapshots; fix any failing regression and inspect representative output artifact content.
2. Prepare a concise owner release gate evidence/feedback schema with no user data; physical owner must actually run `scripts/windows_release_qa.ps1 -OpenBrowser` and review PDF/ZIP. Distinguish launcher automatically generated evidence from manual approval.
3. Confirm future customer artifact composition stays allowlisted and source license notices are preserved. Only modify design where observable clipping, bad text, or misleading claim exists, never filler.
4. Release only tiers explicitly approved after remaining gates. Do **not** auto-merge, launch a Kmong listing, publish a public service or move model/customer files to GitHub.

Full package/source review: `docs/qa/P6E6_LICENSE_DISTRIBUTION.md`.
