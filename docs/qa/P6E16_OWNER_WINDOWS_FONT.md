# P6E16 — Physical owner Windows missing Nanum Gothic, project-local QA bootstrap

Observed: 2026-10-27 KST. Dev `feature/kmong-v1`. Actual first owner retry after P6E15 fix:
- Owner successfully ran `git pull --ff-only origin feature/kmong-v1`; direct Python 3.11 and project QA virtualenv stage no longer triggered prior Python interactive `>>>`/missing venv interpreter failure.
- `scripts/windows_release_qa.ps1 -OpenBrowser` **failed at line 132** with "Install a properly licensed NanumGothic.ttf, then rerun. Do not bundle Microsoft fonts." This is an **observed physical owner machine**, NOT a hypothetical CI failure, and is not actual owner UI/PDF approval.

## Confirmed open license and distribution
- NAVER official Nanum font legal guide: https://help.naver.com/service/11029/contents/18088?lang=ko&osType=PC — font is free for corporate and individual users, commercial use possible under terms.
- Google Fonts original Nanum Gothic family METADATA: https://github.com/google/fonts/blob/main/ofl/nanumgothic/METADATA.pb — style regular, licensed OFL.
- Original OFL notice: https://github.com/google/fonts/blob/main/ofl/nanumgothic/OFL.txt.
- Exact upstream public QA font URL: https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf.
- SHA256 from observed native GitHub Windows original bytes, not a guess: `76F45EF4A6BCFF344C837C95A7DCC26E017E38B5846D5AE0CDCB5B86BE2E2D31`.

## Implementation
- Source [c2f67a9](https://github.com/hibi89/AI_AutoML_Analyst/commit/c2f67a90307421a8d98d2820fa8b9338a250ceae): use existing properly licensed installed Nanum font if detected (`NanumGothic.ttf` or `NanumGothic-Regular.ttf`, system or user). When missing, one-time HTTPS fetch **only** into project-ignored `.venv-automl-qa/qa-assets/NanumGothic-Regular.ttf`. No Windows global font installation, repository font commits, bundled fonts, customer model ZIP/font binaries, paid services, or customer data.
- Source [cd5527d](https://github.com/hibi89/AI_AutoML_Analyst/commit/cd5527de24e895208ab0e85beab798e6689ce9a8): require exact Google Fonts SHA256 for both new download and cached local QA copy, and basic TrueType structure/size. If mismatched or offline and missing, fail closed with actionable message, preserve existing files; no insecure fallback to unknown fonts.
- New `-FontProbeOnly` test mode returns only after venv and local QA font readiness; it does not install pip, start the server, or produce customer data.
- CI [8a58626](https://github.com/hibi89/AI_AutoML_Analyst/commit/8a5862661fd8a8ebeb3ac3e3a4b76bd558892753): native Windows PowerShell 5.1 real font download to temporary path-with-spaces and second cached run, no font committed, runner temp cleaned.
- Original local-only Python 3.11, 3-tier offline-first workflow and Windows `127.0.0.1` unchanged. Font download requires network only when locally missing (same as existing pip bootstrap); subsequent runs reuse cached file.

## Proof boundary
- [Native Windows source/CI 40468062866](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40468062866) **SUCCESS** at pre-hash-pin workflow SHA `8a5862661fd8a8ebeb3ac3e3a4b76bd558892753`: real font downloaded + subsequent local reuse, **77 PASS/9 warnings**, hash from logs matches expected above.
- **Final hash-pinned executable** [Actions 40468311430](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40468311430), SHA `cd5527de24e895208ab0e85beab798e6689ce9a8`: **IN PROGRESS at first document creation**. Do not claim final PASS before logs inspected.
- Physical owner second retry after latest hash-pinned source: **NOT RUN**. Actual Chrome/Edge click/upload, 3 tier PDF visual quality, customer-style private PREMIUM repeat prediction, provenance/font/third-party legal final signoff and explicit commercial sale approval still NOT RUN.
- Strict accepted stages P0–P6 **5/7=71%**; P1 PARTIAL, P6 NOT ACCEPTED, BASIC/STANDARD/PREMIUM sale **NO-GO**. Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` unchanged.

## Owner next step
Existing clone in `E:\AI AutoML Analyst`; no need to clone, delete venv, install global fonts or reinstall Python:
```powershell
cd "E:\AI AutoML Analyst"
git pull --ff-only origin feature/kmong-v1
powershell -ExecutionPolicy Bypass -File .\scripts\windows_release_qa.ps1 -OpenBrowser
```
Only the owner machine's redacted terminal result can confirm the new font path resolved that person's particular setup.


## FINAL exact-version Windows CI — 2026-10-27 KST
- [Windows 40468311430](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40468311430) **SUCCESS**, tested hash-pinned script commit `cd5527de24e895208ab0e85beab798e6689ce9a8`: actual PowerShell 5.1 synthetic-first-create venv in a path with spaces, Google Fonts OFL original exact checksum, and subsequent cached font reuse PASS; native **77 PASS /9 warnings**, zero CI errors. No font binary attached/committed or included in commercial ZIP.
- Owner has not re-executed new source on their own machine; no three-tier real browser or PDF aesthetic/commercial approval. Strict milestones 5/7=71%, all sales NO-GO. Owner can pull existing clone and run one command again, no global font installation or Python reinstall.
