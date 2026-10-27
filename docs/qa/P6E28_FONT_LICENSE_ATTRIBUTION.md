# P6E28 — font embedding flags and delivered ZIP notice integrity

**Completed and CI-verified: 2026-10-27 KST.** Scope: `feature/kmong-v1`, local-only BASIC/ STANDARD/ PREMIUM, no font binaries in GitHub or customer ZIP.

## 1. Specific defect versus frozen delivery contract
Prior P6E27 corrected Japanese glyph coverage, but BASIC, STANDARD and PREMIUM always appended `NANUM_FONT_CREDIT` to `README.txt`, **even when** a Japanese AR PL UMing fallback or non-Nanum Windows/custom primary could be selected. The legal/source claim was not grounded in the font actually registered for PDF embedding. A PDF with successful ReportLab generation alone cannot guarantee legal embedding permissions.

## 2. Source/licensing references and careful distinctions
- **NAVER NanumGothic**: included by Google Fonts as `OFL` with NAVER/NHN copyright; SIL Open Font License 1.1 allows embedding in documents including commercial documents. Font-file redistribution is a different act and may require notice/license with the file. Font family provenance should match embedded font metadata, not file name alone. Sources:
  - https://github.com/google/fonts/tree/main/ofl/nanumgothic
  - https://opensource.org/license/OFL-1.1
  - https://software.sil.org/oflt/ (notably sections 1.10–1.13: embedding vs redistribution)
- **AR PL UMing**: Debian font package `fonts-arphic-uming` is described as **Arphic Public License**, not Nanum's OFL; installed for synthetic Linux QA with `fonts-arphic-uming`. Do **not** claim OFL or automatic unlimited commercial sublicensing for ARPHIC. Preserve its own license in provenance and review actual deployed binary's package license before granting any final sale approval:
  - https://packages.debian.org/en/stable/fonts/fonts-arphic-uming
- **Windows-supplied fonts**: Microsoft distinguishes desktop/bitmap output, document embedding permissions, and forbidden standalone system-font redistribution. Document embedding depends on OpenType/TrueType `OS/2.fsType` flags and the creation/document format; no general entitlement to package Windows fonts with applications. Other non-Microsoft local fonts have their own license.
  - https://learn.microsoft.com/en-us/typography/fonts/font-faq
- This is an **engineering metadata gate and customer notice**, not legal advice or a certificate of commercial rights. The owner must still independently approve the actual font provenance/licensing and customer-ready PDF.

## 3. Implementation / choices
- `backend/app/services/font_coverage.py`:
  - Added `embedding_rights_flags(path)`, reading TrueType collection/font `OS/2.fsType` (index 0) via installed `fontTools.ttLib.TTFont`; rejects flags `0x0002` restricted embedding, `0x0100` no subsetting, and `0x0200` bitmap-only. `0x0004` preview/print remains technically eligible for this locked PDF output, but does **not** alone imply a broader commercial grant; arbitrary license terms still apply. Font registration invokes the check *before* ReportLab embeds a font subset.
  - Added `_installed_font_family` from **font internal name metadata**, not potentially misleading local filesystem name. `font_usage_notice(required_text)` resolves the same Korean/fallback fonts as the actual PDF/charts and writes only the family and known license/provenance pointers, not local paths, usernames, font binary or private CSV values.
  - Recognizes Nanum Gothic / OFL, AR PL UMing / Arphic Public License, common Windows fonts / conditional Windows embedding guidelines, and unknown installed fonts with explicit **license unverified** warning. Never mislabel unknown custom font as Nanum. Does not import/license unknown fonts automatically.
- `backend/app/services/basic_p3.py`, `standard_delivery.py`, `premium_delivery.py`: each generated `README.txt` now appends **dynamic font notice determined from that run's original input columns**, including supplementary Japanese font when actually selected. Every README is captured by existing cryptographic ZIP manifest. Old static `NANUM_FONT_CREDIT` is retained only for source/backward-reference compatibility, **not** inserted into new customer README.
- No external API, installer changes, font downloads by product, new font binary ZIP members, main merge, hosting, or payment.

## 4. Verified objective acceptance / tests
- Added `tests/test_p6e28_font_licenses.py` **12 tests**:
  - 3 SKUs x 2 languages (Korean only versus Japanese CJK synthetic input), verifying README matches chosen primary/fallback, known license names and warnings, contains no absolute system font path, includes no TTF/TTC/OTF asset, and has correct SHA-256 README in manifest.
  - Unknown local-family synthetic monkeypatch explicitly cannot falsely claim OFL.
  - Four denied OS/2 embedding/no-subset/bitmap flag values produce controlled exception.
  - Preview/print `0x0004` technical allowance is not interpreted as commercial license.
- Final test-inclusive [Linux GitHub Actions 40485064697](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40485064697), test SHA `8c65048636b8492e6efc8ed4a2830cf390d89555`: **SUCCESS, 191 passed, 3 Windows-only skipped, 54 warnings**, BASIC 6, STANDARD 9, PREMIUM 11 real synthetic PDFs, ZIP manifests and dependency consistency PASS.
- [Windows-native GitHub Actions 40485011199](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40485011199) at code SHA `7fdc82fd3e04da1f64c2d586c3e15bd82b4e5964`: **SUCCESS 94 passed, 9 warnings**, basic/standard/premium 6/9/11 PDF/manifest and bundled predict.cmd replay PASS. Windows job runs its existing fixed subset, **not** the 12 new tests; new tests ran Linux full.
- [Windows real Chromium 40485011187](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40485011187) and [Linux real Chromium 40485011165](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40485011165): both **SUCCESS** actual browser local uploads and ZIP downloads in 6/6 tier x auto/CP932 flows each, at production-app source SHA `7fdc82fd...`.
- Source commits `b4d61ca` (fsType+dynamic notice), `7fa9903` (actual README newlines), `8ef4bac` (BASIC), `c5c9deb` (STANDARD), `7fdc82f` (PREMIUM), new tests `8c65048`.

## 5. Remaining limitations / next
- Technical `OS/2.fsType` flags are **not the legal license itself**, and may not capture bespoke restrictions. Embedded subset legality and customer distribution of a PDF should be checked with licensed original font terms.
- No actual owner-machine PDF/XObject embedded-font inventory or human design/aesthetic signoff was performed in this iteration. No final legal decision for arbitrary Windows/custom fonts or ARPHIC customer licensing. Do not make a commercial warranty.
- Strict milestones P0–P6 accepted **5/7 = 71%**: P1 owner visual/real customer ZIP review PARTIAL; P6 commercial gate NOT ACCEPTED. BASIC/STANDARD/PREMIUM **NO-GO**. Main original `c80c874476f8d5deb4bf611761d89c6d72ca0a2d` preserved. No Vercel/public deployment/listing.
- Next independent work only if it advances evidence: verify **actual embedded PDF font resource identities** correspond to README without leaking paths in customer ZIP, and optionally add fail-closed unknown-font commercial policy if client owner requests it. Owner P6E22 one-session ZIP/PDF visual, explicit licensed font and sale approval is still necessary.
