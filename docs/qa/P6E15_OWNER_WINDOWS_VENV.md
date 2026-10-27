# P6E15 — Physical Windows first-install venv failure and launcher correction

Date: 2026-10-27 KST. This is a **real physical owner-machine report**, unlike prior CI only.

## Owner-provided symptom (redacted)
- Cloned `feature/kmong-v1` into a local project folder with spaces in its name.
- Owner has both a Windows `py.exe` launcher and direct Python `python.exe` installed; direct Python 3.11.9 version is known from the reported environment.
- On executing `powershell -ExecutionPolicy Bypass -File .\scripts\windows_release_qa.ps1 -OpenBrowser`, the system printed Python 3.11.9 interactive REPL (`>>>`) instead of progressing. After typing `exit()`, the script tried to invoke `.venv-automl-qa\Scripts\python.exe`, which did not exist, and failed at the first venv Python version check.
- Observed: **owner physical first-install FAILED**, no full browser/ZIP/PDF review completed. This report alone does not establish precisely why the legacy `py` wrapper entered interactive mode; do not ascribe root cause to global Python corruption.

## Source-supported defect
Before correction, launcher probing preferred `py -3.11` over a direct Python executable. Virtualenv creation used `& $exe @argsPrefix -m venv $venvRoot`, trusted a zero exit status but **did not verify** that `Scripts\python.exe` was created. Consequently Python could enter an interactive mode / fail to create an environment without a useful error, and the next script line failed with a generic PowerShell command-not-found.

## Implemented in development branch only
1. [Source 1112775](https://github.com/hibi89/AI_AutoML_Analyst/commit/1112775feb003b1b59eac1b007d94b7ce55a7833): choose actual verified Python 3.11 `python.exe` path first; if only Windows `py -3.11` is usable, ask it for `sys.executable` and execute that resolved binary directly. Use the real executable to create `-m venv`, **verify** `Scripts\python.exe` exists, then verify the venv is Python 3.11. Preserve any partial files rather than deleting them. Add read-only/synthetic `-VenvOnly` smoke path (no font checks/pip/browser) and keep `-ProbeOnly`.
2. [CI workflow 04c7172](https://github.com/hibi89/AI_AutoML_Analyst/commit/04c71723d36d73fd9e162d6fbb3d69636f1eef0f): native Windows PowerShell 5.1 copies the exact owner script under a directory called `AI AutoML Analyst`, creates an isolated venv, confirms Python 3.11 in the resulting executable, reruns idempotently, and cleans only the test temp directory. Update old launcher probe assertions for executable path.
3. [Final source 4245f7b](https://github.com/hibi89/AI_AutoML_Analyst/commit/4245f7b7020719a000c147a5d3279ad4bcd9e23e): remove obsolete `@argsPrefix` splatting from pip/pytest/synthetic preview because the resolved venv executable now takes commands directly. No changes to backend/tiers/model/PDF.

## Actual CI proof (not owner retest)
- First intermediate [Windows 40466952431](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40466952431) **FAIL** because existing CI was still expecting the original single launcher-probe line; updated workflow in the next commit. Do not misrepresent intermediate red CI.
- [Windows 40467053350](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40467053350): SUCCESS including the new path-with-spaces venv creation and 77 native tests.
- [FINAL Windows 40467176162](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40467176162) at exact executable SHA `4245f7b7020719a000c147a5d3279ad4bcd9e23e`: **SUCCESS**, launcher fallback PASS, actual first-venv creation and second reuse on Windows under path with spaces PASS, native **77 PASS /9 warnings**, no job errors.
- CI does not reproduce the exact owner's Python launcher configuration. We have **not yet observed** whether re-running this patch on the owner's physical PC succeeds. Don't claim the owner machine is fixed until its next output confirms it.

## Owner next step / scope
From the existing clone root on the physical Windows PC, **do not clone again**. Update without discarding local edits and rerun once:

```powershell
cd "E:\AI AutoML Analyst"
git pull --ff-only origin feature/kmong-v1
powershell -ExecutionPolicy Bypass -File .\scripts\windows_release_qa.ps1 -OpenBrowser
```

If a different error appears, report the redacted output and preserve other local Python projects. Script might next request properly licensed NanumGothic.ttf or fail on actual dependency install; those outcomes were not observed in this owner run. Do not upload customer/model data, install globally or delete existing venvs without diagnosis.

Release remains **P1 physical Windows acceptance PARTIAL (first attempt FAILED)**, P6 final seller gate NOT ACCEPTED, strict P0–P6 **5/7=71%**. BASIC/STANDARD/PREMIUM sale NO-GO; original `main` preserved, no Vercel/production, no commercial consent.
