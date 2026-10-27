# P6E7 — Shipping-policy checks on actual browser downloads and Windows CI

Checked: 2026-10-27 KST. Source: `hibi89/AI_AutoML_Analyst@feature/kmong-v1`.

## Narrow scope / chosen design
- Option A (implemented): reuse the existing P6E6 fail-closed `verify_shipping_zip` inside the P6C real Chromium download smoke; extend existing Windows no-GUI workflow with P6E6 negative shipping-policy tests. No new dependency, release system, hosting or separate artifact format.
- Option B (deferred): build another standalone validator or graphical Windows test infrastructure, which duplicates code or requires font/browser runners and greater maintenance. Existing physical-owner Windows checklist remains the only actual customer-machine acceptance.
- Browser change: `scripts/p6_browser_smoke.py` reads each downloaded synthetic ZIP and validates membership, shipping restrictions, manifest hashes and sizes via `scripts/p6e6_delivery_policy.py`, in addition to checking real UI upload and download.
- Windows change: `.github/workflows/windows-compat.yml` includes `tests/test_p6e6_delivery_policy.py` and tracks its policy file so changes trigger Windows checks.
- Before modifications, original P6E6 Linux CI [40218159484](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40218159484) SUCCESS **125 pass /1 Windows-only skip**, Windows [40218115665](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40218115665) SUCCESS **52 pass**, Linux Chromium [40218115671](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40218115671) SUCCESS. Old successes are *not evidence that P6E7 modifications pass*.

## Actual changes, observed status at this record
1. Browser policy integration commit [27d97b4](https://github.com/hibi89/AI_AutoML_Analyst/commit/27d97b4844081384e01a74696fae99420b24865c), [Chromium run 40454228933](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40454228933) **IN PROGRESS when last queried**. Await actual conclusion.
2. Windows shipping policy regression commit [78f811b](https://github.com/hibi89/AI_AutoML_Analyst/commit/78f811b21724d05c9a191b2ba474cd4c5d828abd), [Windows run 40454311430](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40454311430) **IN PROGRESS when last queried**. Await actual conclusion.
3. Verified via GitHub Git API: author/committer of second commit is `hibi89 <godls5898@gmail.com>`, and its parent is the first commit. No force push, branch change, merge to `main`, deployment or public artifact publication.

## Gates still blocked / NOT equivalent to success
- If either new CI run fails, diagnose its actual logs, minimally fix and rerun, recording the failure. Do not call P6E7 passed until observed.
- Owner's physical Windows 3-tier first install, Chrome/Edge UI and ZIP extraction, Korean PDFs, exact delivered `predict.cmd` under actual owner environment, design acceptance: **NOT RUN / NOT APPROVED**.
- License/distribution: restricted ZIP/PDF + customer independent pip; audit findings are not legal certification. No third-party wheels, standalone font files or packaged EXEs added.
- BASIC / STANDARD / PREMIUM commercial state: **NO-GO / NO-GO / NO-GO**. P0–P6 accepted milestones: **5/7 = 71%**, P1 partial, P6 in progress.
- Production URL / Vercel: **NOT APPLICABLE** (local-first delivery). Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` unchanged. No customer data/secrets used.

## Next READY
**AUTO-KM-P6E8** — Check CI conclusions on exact SHAs, fix only if failed; run/check physical Windows owner steps from `docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md` when evidence is available; compare report samples and per-tier release criteria in `docs/qa/P6E4_TIER_RELEASE_GATE.md`. No permission yet for main merge, production, listing or selling.

## Final observed P6E7 CI outcomes (2026-10-27 KST)
- **Chromium success**: [Actions 40454228933](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40454228933), executed on `27d97b4844081384e01a74696fae99420b24865c`. Direct captured log: BASIC ZIP **481,878 bytes**, STANDARD **636,499 bytes**, PREMIUM **729,738 bytes**; all three actual file-picker/click/download flows completed and now passed the P6E6 strict archive validator. Real Windows desktop was **NOT** covered.
- **Windows success**: [Actions 40454311430](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40454311430), executed on `78f811b21724d05c9a191b2ba474cd4c5d828abd`. Raw Windows Python3.11 job log: **66 passed, 9 warnings in 10.14 s**, including P6E6 ZIP policy tests. Physical owner script full GUI flow was **NOT** executed.
- Both run/job conclusions read live as **SUCCESS** and relevant test step successful. These tested executable changes have not been modified further; subsequent docs-only commits do not constitute new runs on their own HEAD.
- **Next READY AUTO-KM-P6E8**: physical owner Windows first-install + Edge/Chrome uploads, ZIP/PDF aesthetics and premium `predict.cmd` replay; user/owner commercial release authorization and license terms. Until then BASIC, STANDARD and PREMIUM remain **NO-GO**; P0–P6 accepted **5/7=71%**, no production/Vercel and no main merge.
