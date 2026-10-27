# P6E5 — one-command physical Windows owner review

**State: PREPARED, NOT EXECUTED on the owner's Windows PC (2026-10-26 KST).**

This is a local ZIP/PDF product, not a Vercel or public web service. Do not send real client files to GitHub, CI, public web tools or chats.

## The only local launch command

After obtaining the latest approved feature/kmong-v1 code, open PowerShell in the project root and run:

    powershell -ExecutionPolicy Bypass -File .\scripts\windows_release_qa.ps1 -OpenBrowser

The launcher verifies Python **3.11** and an installed, properly licensed NanumGothic.ttf. It creates/reuses the project-only, gitignored **.venv-automl-qa** and never installs packages into global Python. It runs Python QA, generates an isolated synthetic **qa-preview/p6e5-...** run folder without overwriting earlier runs, and verifies the three tiers' ZIP manifest/hash and PDF page counts.

The generated folder contains BASIC and ML input CSVs, three tier ZIPs/PDFs, and a PREMIUM trusted_demo folder. The generator replays **three synthetic rows** using Python. On actual Windows it additionally launches the **exact shipped predict.cmd**, checking its output. Failure aborts the preflight.

With -OpenBrowser, the helper starts a localhost-only server at 127.0.0.1:8000, checks health and opens the three tier pages. The server PID is printed. Stop it with the printed number using: Stop-Process -Id <printed PID>.

## Remaining real-human approval (NEVER assumed from CI)

Use **basic_input.csv** on the BASIC page and **ml_input.csv**, target **구매**, on STANDARD and PREMIUM. Download each tier's ZIP in the actual Windows browser; open every PDF, verify Korean text/charts/page breaks and decide whether remaining whitespace is acceptable. Confirm the fresh PREMIUM ZIP and guide reflect the intended delivery.

Mark each actual gate PASS/FAIL or leave NOT RUN. A successful script does NOT constitute human aesthetic/functional approval. Store redacted errors if a step fails. Review the tier-specific acceptance list in P6E4_TIER_RELEASE_GATE.md and detailed checklist in P6E3_WINDOWS_RELEASE_CHECKLIST.md.

The new run contains **P6E5_REVIEW_EVIDENCE.json** with only synthetic counts, package hashes and explicit NOT_RUN manual fields. This summary may be shared back for release triage. Never send the ZIP, skops model, authentic client CSV, credentials or personal data.

## Release gate

BASIC: actual Windows font/PDF quality and upload/download/extraction. STANDARD: those checks plus selection validity, CV/holdout interpretation and warnings. PREMIUM: actual repeated prediction with same schema, safe rejection of tampering and output collision, and private model delivery. Check appropriate third-party notice/font usage rules.

Commercial approval is separate for all three products. This guide alone does not approve sale. No user-machine action was executed while authoring it.


## P6E11 confirmed runner evidence and single physical-owner acceptance round (2026-10-27 KST)

Before running, download or check out a trusted `feature/kmong-v1` revision that **includes** P6E11 changes (tested source/CI SHA `5a7e56679a14a658586f18010449bee242f77fa2`, with possible later documentation-only commits). No instruction here grants permission to merge into `main`, publish product files, or sell.

**One physical session only when the owner is ready:**
1. Launch the existing PowerShell command above from the repository root after checking Python 3.11, licensed NanumGothic and downloaded dependencies. Script refuses occupied port 8000 before starting; optional `-Port 8001` is available if the owner has explicitly selected a free non-default port. Never kill existing services automatically.
2. Startup now checks **both** `/health` and the known AutoML root API identity before browser tabs open. This does not prove that a local service is cryptographically authentic; the purpose is to prevent an unrelated ordinary server from being mistaken for the application. The PID is displayed for later cleanup.
3. On the three pages, use the **generated synthetic** `basic_input.csv` (BASIC) and `ml_input.csv` (STANDARD/PREMIUM). Confirm actual file picker, upload, ZIP download, archive extraction and each full PDF. Check Korean glyphs, charts, overflow, clipping, page breaks and usefulness/visual design. Verify the downloaded ZIP belongs to its tier, not a previous file.
4. In the **extracted, trusted and disposable PREMIUM folder**, run `predict.cmd` with a correctly ordered synthetic CSV and new output filename, verify header and row count; rerun against an existing output and a wrongly ordered schema to confirm failure without overwrite. Model tampering must be checked only on a separate throwaway copy, never the original.
5. Record only Windows version, Python version, browser/version, repo SHA, hashes, gate statuses (**PASS / FAIL / NOT RUN**) and **redacted** error messages in a private log. Do not send CSV rows, category metadata, model artifacts, ZIP, passwords or personal information.
6. Decide separately per tier: business suitability of the deliverable, font/NOTICE distribution terms, and explicit sale consent. Neither an all-green script nor runner CI authorizes a sale.

**P6E11 evidence:** [GitHub Windows 40461091189](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461091189) on source+CI SHA `5a7e56679a14a658586f18010449bee242f77fa2`: real local AutoML identity PASS, unrelated HTTP server identity REFUSED, PowerShell parse PASS, port collision check PASS, native regression **67 PASS /9 warnings**. Prior Linux and Chromium success remains on earlier unchanged application/backend code. This is **NOT** evidence of this PC's physical GUI, browser, PDF or aesthetic approval.

**At this writing: OWNER PHYSICAL ACCEPTANCE NOT RUN; BASIC / STANDARD / PREMIUM NO-GO.** P0–P6 strict accepted milestones remain **5/7 (71%)**; P1 partially accepted, P6 release pending.

## P6E12 Windows Chromium CI / narrowed manual gate (2026-10-27 KST)
P6E12 verified code/workflow SHA `539ba3baa985b16567cf20cfe9cb8338467304fd`, [native Windows Chromium CI 40462203822](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40462203822) SUCCESS. Real Playwright Windows Chromium uploads synthetic CSV to BASIC/STANDARD/PREMIUM, receives valid ZIPs BASIC 461,960B / STANDARD 603,718B / PREMIUM 689,449B; strict shipping/manifest and PDF header PASS. Disposable OFL Nanum font used only in runner temp, never committed or distributed. Existing backend/model code unchanged. This is hosted Windows runner, NOT physical owner Windows/Chrome/Edge GUI or PDF design approval. Official P0-P6 5/7=71%; P1 partial/P6 not accepted; all three SKU commercial NO-GO, main untouched, Vercel/production N/A.
The one owner command at the top of this document remains current. Now the only remaining approval is actual physical Windows first-install, genuine Chrome/Edge interaction, output ZIP extraction and Korean PDF aesthetics, trusted PREMIUM extracted CMD replay, and explicit product/license consent. Record PASS/FAIL/NOT RUN with redacted errors; never upload raw data/model/ZIP to GitHub. Do not equate the hosted Windows Chromium CI to these manual checks.

## P6E15 first real owner run and repaired launcher — 2026-10-27 KST
- Owner confirmed original clone in a Windows directory with spaces and working direct Python 3.11.9. First `-OpenBrowser` unexpectedly entered `>>>` Python interactive mode; after `exit()` virtualenv `Scripts\python.exe` missing. **First owner install: FAIL**. Browser/PDF/manual acceptance has NOT occurred.
- Owner QA script updated to run the verified Python 3.11 executable directly instead of forwarding through the `py` launcher, and to verify virtualenv Python exists after creation. [Windows GitHub CI 40467176162](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40467176162) **SUCCESS** with native PowerShell 5.1 first-create and second reuse in project path containing spaces, 77 tests passed. This is runner proof, not proof of user's PC repair.
- On **existing clone**, don't re-clone or delete anything. Execute `git pull --ff-only origin feature/kmong-v1` and run this guide's original `-OpenBrowser` command once. If a partial venv or missing licensed font blocks setup, report the sanitized exact error rather than removing files or modifying other Python installations. Commercial release remains all tiers NO-GO and 5/7 milestones accepted.
