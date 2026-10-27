# P6E27 — Japanese CP932 PDF/PNG glyph integrity

**Verified 2026-10-27 KST** against `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`. Synthetic fixture only. Frozen prices/requirements unchanged.

## Verified pre-existing defect
Previous P6E19/P6E20 workflows proved accurate CP932 table decoding and BASIC/STANDARD/PREMIUM form-upload/ZIP download, **not PDF/PNG glyph readability**. Linux NanumGothic is a good Korean font but lacks characters used in Japanese business headers (notably U+58F2 `売` and U+6570 `数`), so Matplotlib emitted `Glyph ... missing from font` warnings. ReportLab could also silently substitute an unsupported glyph. Encoding success and ZIP integrity do not prove readable graphs.

## Implemented solution
- New `backend/app/services/font_coverage.py` uses ReportLab TrueType cmap checks on local installed fonts. Primary selection is the existing licensed Korean font, optional Japanese fallback `AUTOML_JAPANESE_FONT_PATH` or common **locally installed** TTC/TTF paths; without coverage it fails with an actionable `ValueError` (HTTP 400 for user-facing upload) **rather than silently emitting missing customer column glyphs**. Fallback font must be embeddable TrueType; unsupported CFF/OTF fonts fail clearly. No network call in the application, fonts never committed or copied into repository.
- BASIC chart designer now supplies a Matplotlib family fallback list chosen for actual input column glyphs. BASIC PDF uses safe per-character ReportLab `<font name="...">` markup for unsupported primary glyphs; input is XML-escaped and column names verified before rendering. Same PDF fallback for STANDARD and PREMIUM. Pure user-authored decorative/report symbols that neither licensed font supports are made explicit as `[U+XXXX]` so a report does not fail on a decorative glyph; customer **column names** remain strict glyph-check inputs.
- Test: `tests/test_p6e27_japanese_glyphs.py` validates actual Japanese fonts `売`/`数`, fail-closed when fallback absent, safe escaping, real PDF Unicode text extraction, ZIP contents, and zero missing-glyph Matplotlib warnings in a 120-row synthetic Japanese business table.
- On ephemeral Linux GitHub Actions runners only, CI installs Ubuntu packages `fonts-nanum` + `fonts-arphic-uming`; package includes `/usr/share/fonts/truetype/arphic/uming.ttc` and its ARPHIC license document. Ubuntu source/package reference: https://packages.ubuntu.com/noble/fonts-arphic-uming and https://packages.ubuntu.com/questing/all/fonts-arphic-uming/filelist . Existing Windows runner uses locally installed CJK font paths without adding remote fonts. No standalone font binary is part of source or delivery ZIP.

## Exact commits and CI verification
- Source: `1baa3de` font coverage module, `efa89f9` chart font family, `61e2862` BASIC PDF fallback, `220aa58` STANDARD PDF fallback, `6d822f4` PREMIUM PDF fallback.
- CI font provisioning: `9bc1fea` Linux baseline, `ce12296` Linux Chromium.
- Regression: `b0ab1c9` new four tests.
- Initial CI exposed a secondary defect: the first strict markup implementation rejected glyphs in report-authored decorative text and broke otherwise valid STANDARD/PREMIUM PDF. This was a **real observed CI failure** (e.g. Linux 40483350412 and Windows 40483205411 from earlier source), not hidden. Source `5c923f8` changed fallback of unsupported non-column symbols to explicit `[U+XXXX]` while preserving strict source-column verification.
- **Final test-inclusive [Linux full 40483496600](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40483496600)** at source SHA `5c923f8c823033d522bfae98de8bd4aa20c30f7e`: **SUCCESS, 179 passed / 3 skipped / 42 warnings**, real synthetic PDF 6/9/11 pages and ZIP manifests PASS; dependency consistency PASS.
- **[Windows native 40483496602](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40483496602)** at same source SHA: **SUCCESS 94 passed/9 warnings**, BASIC6/STANDARD9/PREMIUM11 PDFs/ZIP manifests PASS. Windows native fixed subset does not execute new P6E27 test file; Linux full does.
- **[Linux Chromium 40483496583](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40483496583)** and **[Windows Chromium 40483496634](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40483496634)**: each **SUCCESS 6/6**, real file chooser/upload/download for 3 tiers × default and explicit CP932 encoding, ZIP integrity PASS.
- **Not** an actual owner-machine/manual PDF signoff. Synthetic Japanese PDF tests verified text extraction and glyph warning absence, not every font style, word break and cross-device visual aesthetic.

## Commercial/licensing boundaries
- The installed fallback fonts have independent licenses. Ubuntu `fonts-arphic-uming` ships under the ARPHIC Public License, **not SIL OFL**. Font embedding, attribution, license notice and any customer redistribution need checking against the specific installed font license before commercial delivery. Do not claim a blanket redistribution authorization because GitHub Actions or a PDF font subset succeeded.
- Normal deployment remains offline/localhost, no new paid service, no font binary distribution. Customer must have an acceptable licensed Korean font and—for non-covered Japanese characters—a licensed compatible fallback installed locally.
- Original main remains untouched. Strict accepted P0–P6 milestone **5/7=71%**, P1 owner visual review PARTIAL and P6 release NOT ACCEPTED; BASIC/STANDARD/PREMIUM **NO-GO** until owner manually reviews an actual customer-like ZIP/PDF and clears font/legal/commercial requirements.

## Next practical independent work
Perform targeted packaged-PDF font license/source attribution review and end-user instructions for locally installed CJK fallback (do not embed an unverified/undocumented license claim). Then owner-dependent P6E22 one-session PDF/ZIP/visual/legal approval, with no repeated setup requested of the tired owner.
