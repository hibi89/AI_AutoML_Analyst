# P6E13 engineering addendum — raw CSV header fidelity

Date: 2026-10-27 KST. Source repository `hibi89/AI_AutoML_Analyst`, development branch `feature/kmong-v1`. **P6E13 physical owner release acceptance remains NOT RUN.**

## Grounded defect
Before this correction, `backend/app/main.py::_read_csv_from_bytes` called `pd.read_csv` before checking raw CSV headers. Pandas disambiguates duplicate headers by adding suffixes (`amount,amount` => `amount,amount.1`). The later `validate_basic_frame(df)` duplicate check sees only unique names and silently accepts an altered schema, contrary to frozen requirements for reliable CSV/schema data and no unannounced shape changes. Pandas also creates placeholders for blank source header fields. This affects commercial BASIC/STANDARD/PREMIUM shared uploads and the legacy CSV analyzer.

## Narrow solution and rejected alternative
- **Implemented:** inspect first *logical* CSV header row using built-in `csv.reader` under the existing encoding-candidate sequence before passing the bytes into pandas. Reject actual repeated or whitespace-only column headers. Legitimate separate `sales,sales.1` columns remain valid; preserve all existing encoding order and row/column limits.
- **Deferred:** guess whether ambiguous legacy byte strings are Korean CP949 or Japanese CP932 based on scripts; Japanese CP932 text can be decoded as valid but incorrect CP949 Korean glyphs. Unsupported auto-guessing could silently corrupt data. A future explicit encoding choice could be designed separately if customer examples justify it.
- No external data, network, LLM, new dependency, architecture change, additional UI or client file upload.

## Change commits and evidence
1. [Parser code b55f362](https://github.com/hibi89/AI_AutoML_Analyst/commit/b55f36245c31fe24ecd9aa99eed5b75e41fff7a9): raw CSV header validation and consistent user-visible error before pandas renaming.
2. [Synthetic test c6181b0](https://github.com/hibi89/AI_AutoML_Analyst/commit/c6181b08c34d37cb217b97e80836449605453e78): duplicated ASCII, quoted comma, CP949 Korean and blank headers rejected; normal explicit `.1` and Korean UTF8 BOM names retained, including HTTP 400 tests.
3. [Windows test workflow ba32871](https://github.com/hibi89/AI_AutoML_Analyst/commit/ba3287108dcc41eed46659c2db84cdd9733faeca) invokes the new focused regression among all existing native tests.
4. [Windows 40464753900](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464753900), full code+test/workflow SHA `ba3287108dcc41eed46659c2db84cdd9733faeca`: **SUCCESS 74 PASS /9 warnings**, including 7 new tests.
5. [Windows Chromium 40464676684](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464676684) and [Linux Chromium 40464676692](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464676692) **SUCCESS** on prior parser-only code SHA `b55f362`: actual all three SKU ZIP downloads. [Linux full 40464676814](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464676814) **SUCCESS** on parser-only SHA. [Linux full 40464733521](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464733521) on test SHA **IN PROGRESS** at this entry; read final logs before claiming completion.

## Release boundary
- P0–P6 accepted **5/7=71%**, P1 physical Windows partial/P6 final sale pending. BASIC/STANDARD/PREMIUM **NO-GO**. No user's real Windows browser, Korean PDF visual aesthetic review, installed font license validation or private PREMIUM customer-style replay performed by owner; one physical owner session is still required from `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`.
- `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` not modified, all commits on dev branch; local-first product no Vercel/production URL, no payment or customer data.
- **Next:** reconcile final Linux test SHA, then leave P6E13 OWNER MACHINE gate explicitly BLOCKED until physical evidence instead of inventing further readiness.


## FINAL P6E13 CSV header regression evidence (2026-10-27 KST)
- [Linux full Actions 40464733521](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464733521) **SUCCESS**, exact parser+test SHA `c6181b08c34d37cb217b97e80836449605453e78`: **132 PASS, 2 Windows-only SKIP, 41 warnings**; BASIC PDF 6 pages and PREMIUM 11 pages manifest PASS.
- [Windows native 40464753900](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464753900) **SUCCESS** at source+test+workflow SHA `ba3287108dcc41eed46659c2db84cdd9733faeca`: **74 PASS, 9 warnings** (seven new parser tests). [Linux Chromium 40464676692](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464676692) and [Windows Chromium 40464676684](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40464676684) both SUCCESS on parser-only SHA `b55f362`; tested real three-tier ZIP downloads with synthetic data.
- No Windows physical owner machine/installed Korean font, browser visually inspected PDF, private extracted customer CMD, license clearance or tier signoff; accepted milestone **5/7=71%**, all tier sales NO-GO. Next physical **P6E13 OWNER MACHINE** step is still BLOCKED pending owner run. Do not inflate progress or merge main.
