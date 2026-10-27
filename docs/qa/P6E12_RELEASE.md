# P6E12 — Windows real-browser cross-platform delivery gate

Date: 2026-10-27 KST. `hibi89/AI_AutoML_Analyst`, `feature/kmong-v1`.

## Why this adds value beyond P6E11
Prior Chromium UI upload → ZIP download → strict shipping policy was proven on a **Linux** runner only. Windows runs tested Python, packaged `predict.cmd`, launcher safety and API identity, but not actual Chromium browser file chooser and output download on a Windows host. This is a concrete previously untested cross-platform combination. It does not replace physical owner inspection of Korean PDF design.

## Implemented
- Commit [539ba3b](https://github.com/hibi89/AI_AutoML_Analyst/commit/539ba3baa985b16567cf20cfe9cb8338467304fd) adds `.github/workflows/windows-browser-smoke.yml` on the *development branch only*. It reuses the original `scripts/p6_browser_smoke.py` and existing pinned app requirements; real Playwright Chromium opens BASIC/STANDARD/PREMIUM localhost pages, chooses synthetic CSV, sets ML target, submits, downloads actual ZIPs, checks PDF header, tier files, manifest and fail-closed distribution policy (no bundled fonts/wheels, SHA hashes).
- A NanumGothic font from the [Google Fonts source repository](https://github.com/google/fonts/blob/main/ofl/nanumgothic/NanumGothic-Regular.ttf) with OFL licensing is placed **only in a temporary Windows CI runner folder** and supplied via `AUTOML_KOREAN_FONT_PATH`. No font is committed, retained as artifact, attached or sent to a customer. Test dataset is generated synthetically within a temporary folder. No hosted service or external customer file access.
- Avoided changing application/business logic or adding installer and dependencies to shipped products. CI can run on code/UI modifications or manual workflow dispatch; no user physical intervention needed for this automation.

## Evidence status at creation
- [Windows Chromium run 40462203822](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40462203822), exact workflow code SHA `539ba3baa985b16567cf20cfe9cb8338467304fd`: **IN PROGRESS** at creation; no pass claim yet.
- Previous Windows native [40461091189](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461091189) 67 PASS/9 warnings; previous Linux full [40458277791](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277791) 125 PASS/2 Windows-only skips; Linux browser Chromium [40458238868](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458238868) three tiers PASS, all on earlier code snapshots.

## Unresolved physical gate
- Exact **owner's Windows PC** setup, installed/distributable NanumGothic, actual Chrome/Edge usage, PDF layout/render appearance and quality approval, real extracted PREMIUM `predict.cmd`, font and license/NOTICE terms, explicit per-SKU commercial approval: **NOT RUN**, no claim of owner inspection.
- Strict accepted P0–P6 milestones **5/7 (71%)**, P1 physical acceptance PARTIAL, P6 release IN PROGRESS. BASIC ₩60k, STANDARD ₩150k, PREMIUM ₩300k all **NO-GO**. No change to original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d`; no paid services/Vercel/production URL.
- Next: verify exact Windows Chromium CI logs, address any observed failure before owner session, then guide owner through **one** physical session using `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md` when ready. No need for repetitive owner tests.
