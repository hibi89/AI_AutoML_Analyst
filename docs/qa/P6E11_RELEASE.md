# P6E11 — Confirm local API identity before Windows owner browser launch

Checked: 2026-10-27 KST. `hibi89/AI_AutoML_Analyst`, `feature/kmong-v1`.

## Source-grounded risk
The physical Windows release helper verified `/health` status 200 before opening three tier pages. P6E10 now preflights port availability, but a process can occupy a port during the launch/probe interval, and an unrelated service may also return 200 at `/health`. Therefore status-200 by itself is insufficient evidence that the requested AutoML server is serving the UI. This is a potential race from code inspection, **not an observed owner-machine incident**.

## Chosen approach, constraints
- Reuse the already-existing FastAPI public root contract from `backend/app/main.py`: `message == "AI AutoML Analyst API"`, `health == "/health"`, `analyze_upload == "/api/analyze"`. The owner script now checks that JSON on the **same localhost port**, as well as `/health` 200 and that the child process is still running, before opening the browser.
- Add `-IdentityProbeOnly -Port N`, a read-only control path that does not create a venv, install packages, inspect fonts, start a new server, or open tabs. This permits automated native-Windows positive and negative simulation.
- **Not selected:** random auth tokens/new HTTP routes, killing other programs on a shared port, changing the root API response, or broad server rewrite. Those would introduce avoidable compatibility changes. Root contract checking is identification of an expected service, **not cryptographic process attestation**; arbitrary process races/spoofing remain outside this bounded check.

## Actual changes (CI must confirm)
1. `scripts/windows_release_qa.ps1` at [a7a328f](https://github.com/hibi89/AI_AutoML_Analyst/commit/a7a328fa1f51c82c8cf1371a04fe5b1fe0359764): `Test-AutoMLServerIdentity` + read-only `-IdentityProbeOnly`; `-OpenBrowser` readiness now requires exact known API root, `/health` success and still-alive child.
2. `.github/workflows/windows-compat.yml` at [5a7e566](https://github.com/hibi89/AI_AutoML_Analyst/commit/5a7e56679a14a658586f18010449bee242f77fa2): on a disposable port, launch real AutoML `uvicorn` and demand identity PASS; then launch an unrelated stdlib `http.server` on that port and demand fail-closed. Both processes are stopped in `finally`; tests never bind outside `127.0.0.1`.
3. At document creation [Windows CI 40461040277](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461040277) (code-only) and [40461091189](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461091189) (combined script/CI) were **IN PROGRESS**. Do not report P6E11 PASS until actual job outcome and failing-step details checked.

## Frozen commercial/release scope
- Prior code+workflow [P6E10 Windows 40459966750](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459966750): 67 PASS /9 warnings; local occupied and freed port test passed. Linux full [40458277791](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277791) 125 PASS /2 Windows-only skips, Chromium [40458238868](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458238868) 3 tier ZIP browser downloads PASS on earlier app code. P6E11 changes owner launcher and Windows CI only; backend/report/model code unchanged.
- BASIC ₩60k, STANDARD ₩150k, PREMIUM ₩300k; no paid API, credentials, client data, customer-trained model files, font binaries or Vercel deployments committed. Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` unchanged.
- Strict accepted milestone count **P0–P6 5/7 = 71%**, P1 physical owner desktop PARTIAL and P6 release NOT ACCEPTED, all SKUs commercial **NO-GO**.
- Physical Windows owner machine: first installation, real browser uploads/ZIP extraction, Korean PDF visual/design approval, trusted PREMIUM extracted CMD predictions, font/third-party license and explicit commercial signoff **NOT RUN**. Github hosted Windows runner never grants those approvals.
- **Next candidate P6E12 / OWNER GATE**: observe new Actions and repair only reproduced faults, then if no more independently useful engineering work, prepare final one-round Windows owner approval checklist. No main merge, public deploy, price listing or sale authorization without user consent.


## Final P6E11 verified CI (2026-10-27 KST)

- [Windows code-only 40461040277](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461040277), at `a7a328fa1f51c82c8cf1371a04fe5b1fe0359764`: **SUCCESS, 67 PASS /9 warnings**; PowerShell parse and prior regression checks PASS. This run did not separately test a different server identity.
- [Windows real/foreign-server 40461091189](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40461091189), at exact combined application-script/CI SHA `5a7e56679a14a658586f18010449bee242f77fa2`: **SUCCESS, 67 PASS /9 warnings**; verified success of actual local AutoML API identity; refusal of unrelated Python stdlib HTTP server; previous occupied-port and Python3.11 launcher fallback checks PASS; no job error lines. These are real native GitHub runner processes on 127.0.0.1, not an owner Windows desktop.
- Manual future one-round owner physical signoff updated at `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`: three tiers, local Korean PDF, trust-bounded private PREMIUM prediction, licensing and visual decisions. **NOT RUN**.
- **Next READY P6E12 / OWNER MACHINE RELEASE GATE**. No additional independently supported software failure known at this exact checkpoint. Before claiming release, require first install, browser ZIP/PDF and owner human approval; all SKUs **NO-GO**, P0–P6 accepted **5/7=71%**. No production/Vercel, original main unchanged.
