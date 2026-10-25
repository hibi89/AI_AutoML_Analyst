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
