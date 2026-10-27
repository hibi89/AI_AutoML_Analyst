# P6E18 — Actual owner Windows bootstrap and local browser launch successful

Date: 2026-10-27 KST. Evidence: actual owner-provided PowerShell output and UI screenshots during chat. These are human-supplied local device observations, not screenshots or file artifacts placed in the repository.

## Physical owner evidence — supported
1. Windows owner ran QA script after latest pull in a local project directory with spaces. The latest run DID NOT stop at the previous virtualenv, missing Korean font or shipped PREMIUM batch issues.
2. Windows owner PowerShell: `91 passed, 25 warnings in 42.52s` from actual local pytest suite; these warnings are non-fatal and include known precision UndefinedMetricWarning, StarletteDeprecationWarning, and time parser warnings.
3. Owner physical synthetic pack: printed `Synthetic QA review pack: qa-preview\\p6e5-20261027T080404Z`, BASIC PDF `6` pages manifest PASS, STANDARD PDF `9` pages manifest PASS, PREMIUM PDF `11` pages manifest PASS; local `PREMIUM trusted_demo` with generated model and batch; replay branch completed without error before browser opening. The diagnostic script has a mandatory Windows CMD step, so command success plus subsequent server startup confirms that the owner's actual `predict.cmd` synthetic replay returned success and expected 3 prediction rows.
4. PowerShell then printed `Non-GUI checks passed` and `Local server PID: 27244`, followed by instructions to test the three local browser pages. The PID is the owner-observed server identifier **only for that session**, not a current remote-process guarantee.
5. User supplied screenshots of local Chrome UI at `http://127.0.0.1:8000/standard-mvp` and `/premium-mvp` showing legible Korean labels/forms, then an additional screenshot/window. QA launcher opens BASIC/STANDARD/PREMIUM tabs; evidence establishes successful automatic browser startup and visible STANDARD/PREMIUM pages. The third screenshot should be treated as another shown browser page, without claiming its exact content independently if not verified.
6. The user explicitly expressed fatigue and requested that engineering/verification capable of being done without local PC access continue without user labor. Do not ask them for another full installation or regression run unnecessarily.

## Remaining manual release gates (NOT RUN / not asserted)
- No proof the owner actually clicked all three `CSV/XLSX` file pickers, triggered a report ZIP download from each browser form, manually extracted those downloads, or inspected actual Korean PDF pages/layout/graphics (the synthetic ZIPs/ PDFs do exist and passed structural tests).
- No explicit commercial appearance/quality acceptance, fonts/OFL NOTICE terms approval, legally usable client delivery judgment or per-SKU sale consent.
- Although synthetic generated PREMIUM local `predict.cmd` replay DID pass, customer-style repeat prediction through manual browser-downloaded trusted ZIP has not been independently evidenced. Never upload model, customer data or synthetic ZIPs to this GitHub repo.
- The third screenshot is an additional UI-opening observation; do not overinterpret it as clicked submissions.
- Therefore official frozen P0-P6 strict milestones remain **5/7 = 71%** pending P1 formal physical acceptance and P6 release/quality approval, but *physical first-install/server/local visible UI and synthetic model replay are now PASS* (not BLOCKED).
- BASIC/STANDARD/PREMIUM commercial **NO-GO**; original `main` unchanged, no Vercel/production.

## Future next step
Continue independently runnable engineering and QA on `feature/kmong-v1`, without owner input unless there is a genuine manual GUI/PDF aesthetic or commercial/legal decision. When owner has time, offer a single short local hands-on review using already-generated synthetic QA file(s), not a repeated setup. User may shut down their local server at their leisure with `Stop-Process -Id 27244` only if the process is still the same server; this is not necessary for the GitHub work.

Supporting previous QA:
- [P6E17](./P6E17_OWNER_WINDOWS_CMD.md): shipped Windows CMD replay guard and native CI [40470153374](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40470153374) 78 tests.
- Current physical owner run observed: 91 PASS, synthetic BASIC6 / STANDARD9 / PREMIUM11 and local three-window startup. Distinguish these counts and the owner machine from hosted CI.
