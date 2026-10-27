# P6E20 — Real Chromium two-language / three-tier upload-download QA

Date: 2026-10-27 KST, development branch `feature/kmong-v1`.

## Why this work was necessary
P6E19 already provided API-level deterministic CSV encoding selection and synthetic native Windows/Linux tests for Japanese CP932. However a TestClient or an HTML select-option existence assertion cannot prove that the **real** customer browser form sends a CP932 value, makes the POST, receives a real commercial-shaped ZIP and preserves the originally uploaded Japanese header bytes. The user has already demonstrated local Windows app launch and indicated they are tired, so this change does not require further owner manual action.

## Narrow actual browser integration tests
- Extend `scripts/p6_browser_smoke.py` with **two** synthetic input sources: existing default UTF-8-SIG Korean CSV and a second generated Japanese CP932 CSV with actual Japanese column labels `日付,地域,訪問数,売上,費用,購入`. No real customer data.
- For **each** BASIC, STANDARD, PREMIUM: open actual localhost HTML in headless Chromium; set the `csv_encoding` select explicitly to `auto` or `cp932`; use Playwright's real file-picker API; set the training target to `구매` or `購入`; click the visible submit button; await an actual downloadable ZIP.
- Validate each ZIP structure and manifest using the existing shipping policy and verify its report PDF exists. For CP932 additionally inspect `summary.json` quality `column` values: exact 6 Japanese originals and 120 input rows; reject any mojibake even if a ZIP was produced.
- Exactly **6 real end-to-end browser flows per operating system**, rather than 3. No customer rows/models/font binaries are retained or uploaded. Existing local API, user interface, model and delivery format remain unchanged.
- Executable test commits [5590cb0](https://github.com/hibi89/AI_AutoML_Analyst/commit/5590cb008dae454c4a2478ff120b6bdbc6a2520c) (six flows) and [f6e6bc5](https://github.com/hibi89/AI_AutoML_Analyst/commit/f6e6bc51a70068220d1d9a382d7feba670c4a3e0) (assert Japanese original names in downloaded ZIP). Tests run on Ubuntu and native Windows Chromium Actions with existing pinned dependencies.

## CI evidence — authoritative exact executable SHA
- [Linux Chromium 40473298293](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40473298293), `5590cb0`, SUCCESS: six actual browser download flows, original Korean and selected Japanese CP932.
- [Linux Chromium 40473385942](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40473385942), `f6e6bc5`, SUCCESS: six actual download flows with additional explicit Japanese original header assertions.
- [Windows Chromium 40473385920](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40473385920), `f6e6bc5`, **IN PROGRESS at writing**, must read final conclusion/logs before claiming Windows PASS. Earlier [Windows 40473298323](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40473298323) also in progress; prefer final SHA.
- Earlier P6E19 native Windows [40472590303](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472590303): 93 PASS/9 warnings and Linux [40472590292](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40472590292): 150 PASS/3 Windows skips; these test upstream application code and packaged PREMIUM predictor.

## Scope / release boundary
- User's actual physical Windows P6E18 was 91 PASS and all 3 screens opened, but P6E20 is a **hosted CI** test, NOT the user downloading and manually inspecting these new ZIPs. The user has not accepted PDF aesthetics, visual layout, font/legal distribution nor commercial delivery.
- Strict release milestone progress remains **5/7 = 71%**, P1 manual GUI/PDF acceptance PARTIAL, P6 commercialization gate NOT ACCEPTED, all three SKUs **NO-GO**. `main` original remains untouched; no hosting, Vercel, customer data or sale listing.
- Next developer should check exact native Windows final browser workflow outcome and fix any real regression. No reason to ask the tired owner to repeat the bootstrap.
