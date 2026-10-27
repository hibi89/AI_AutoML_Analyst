# P6E10 — Windows localhost port-conflict safety gate

Checked: 2026-10-27 KST. Repository `hibi89/AI_AutoML_Analyst`, branch `feature/kmong-v1`.

## Risk found in existing source
The owner launcher `scripts/windows_release_qa.ps1 -OpenBrowser` starts a hidden Uvicorn process on localhost port 8000 and polls `http://127.0.0.1:8000/health`. Before this change it did **not first verify that port 8000 was free**. If another service occupies the port and exposes `/health`, a response from that unrelated service could be mistaken for proof that the new process owns the port; the launched Uvicorn instance could exit during the race. This is a source-supported risk, not a user-machine observation.

## Technical choice
- **Selected:** fail closed if an IPv4 localhost TCP connection can be established on the requested port **before** launching. No force-kill, no port takeover, no external network, no change to default 8000. Allow optional `-Port` override for an independent local port and `-PortProbeOnly` for read-only Windows CI.
- **Rejected:** killing a process already using 8000, silently switching ports, or introducing third-party port-discovery dependencies. They could disrupt unrelated user work or conceal which local server is running.
- Scope limit: this is a practical pre-launch guard and simple own-process `HasExited` observation remains; it cannot eliminate every time-of-check/time-of-use race or validate an owner GUI screenshot. App binds to `127.0.0.1`, not public interfaces.

## Code and CI
1. [Code commit 51a91fc](https://github.com/hibi89/AI_AutoML_Analyst/commit/51a91fc161d8e35ce6fd1eaf8d54ceece5182659): PowerShell `Test-LoopbackPortOccupied`, optional `-PortProbeOnly -Port N`; `-OpenBrowser` refuses busy ports with an actionable error before starting anything new; dynamic port used consistently by server, health check and all three browser URLs.
2. [CI commit 2b31465](https://github.com/hibi89/AI_AutoML_Analyst/commit/2b314653241a2bbf527476841b4a78ed0a882e28): native Windows workflow starts an ephemeral loopback `TcpListener`, demands rejection of the occupied port, stops listener in `finally`, then demands `LOCAL_PORT_AVAILABLE=N` on freed port. It also continues Python3.11 launcher and prior 67 native test checks.
3. [Windows code CI 40459918851](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459918851) and [full collision CI 40459966750](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459966750) were **IN PROGRESS at document creation**. Check final conclusions and raw logs before claiming PASS.

## Prior unchanged accepted evidence
- P6E9 native Windows [40459036865](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459036865) 67 tests PASS /9 warnings.
- P6E8 Linux full [40458277791](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277791) 125 PASS /2 Windows-only SKIP; Chromium [40458238868](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458238868) actual BASIC/STANDARD/PREMIUM synthetic upload/download ZIPs PASS on earlier app SHA. P6E10 changes only Windows local QA script and Windows CI, not backend, model, PDF or browser code.
- No user's physical Windows machine was accessed, no client data/secrets deployed, no font files committed, no external hosting, no Vercel.

## Release and next
- P0–P6 strictly accepted **5/7=71%**; P1 physical owner browser remains PARTIAL and P6 final sale release NOT ACCEPTED. BASIC / STANDARD / PREMIUM all **NO-GO**.
- Real first-install/Edge-Chrome upload/ZIP extraction/PDF aesthetics/owner approval remain mandatory; CI is not substitute for physical owner signoff.
- **Next P6E11/OWNER GATE candidate:** reconcile P6E10 CI outcome, repair only reproduced regressions, and if no remaining useful independent QA, prepare the single owner-local acceptance round described in `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md`. Do not force an owner action now; no main merge, public deployment or commercial listing without explicit permission.


## Final observed P6E10 CI — 2026-10-27 KST

- [Windows 40459918851](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459918851): SUCCESS at source commit `51a91fc161d8e35ce6fd1eaf8d54ceece5182659`. Raw job log **67 PASS /9 warnings**; PowerShell parse and prior native regression checks PASS. It did not yet include the new occupied-port simulation.
- [Windows 40459966750](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459966750): **SUCCESS** at combined source+CI SHA `2b314653241a2bbf527476841b4a78ed0a882e28`. Windows PowerShell parse SUCCESS; Python3.11 broken-`py` launcher fallback SUCCESS; **local port collision guard SUCCESS** for ephemeral occupied localhost port and freed same port; native regressions **67 PASS /9 warnings**. No `##[error]` lines in job log.
- This proves controlled ephemeral IPv4 loopback port occupancy detection on one GitHub Windows runner; it does **not** prove a physical owner's browser/PDF approval or eliminate every rare bind race. No Linux/Chromium workflow triggered because no backend, frontend or data output changes.
- **Next READY AUTO-KM-P6E11**: review actual remaining Windows owner release gates; add only grounded no-owner regressions. If the rest requires physical visual judgment, preserve OWNER ACTION REQUIRED instead of inflating percentage. P0–P6 accepted **5/7 (71%)** and BASIC/STANDARD/PREMIUM sale **NO-GO**. `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` unchanged, no production deployment.
