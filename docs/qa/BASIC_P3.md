# P3 Korean BASIC report — QA evidence and operating contract

Checked 2026-10-25 KST. Repo `hibi89/AI_AutoML_Analyst`, development branch `feature/kmong-v1`.

## Delivered architecture
- `backend/app/services/basic_p3.py`: accepts bounded validated DataFrame from existing `basic_report.py`; derives metrics (shape, missing, duplicates, numeric medians), 3–5 data-grounded findings when possible, up to 3 qualified actions. Chooses **at most five schema-justified** charts (numeric histogram, missingness, numeric correlation, categorical frequency, box plot, optional date trend); no fabricated visual filler on sparse input. Charts obscure raw category names.
- Uses **ReportLab with embedded NanumGothic TTF** for Korean PDF creation. CI installs `fonts-nanum`, uses `pypdf` for page count and text extraction, Poppler `pdftoppm` for actual raster output and PIL non-blank checking. PDF pages are genuinely produced, not renamed text.
- Archive: `report.pdf`, `summary.csv` (spreadsheet formula-escaped column names), `summary.json`, `README.txt`, available `charts/*.png`, `manifest.json`. Manifest SHA-256 and size cover all non-manifest files. Raw input rows are not shipped.
- Existing `GET /basic-mvp` and `POST /api/basic-report` retained. Page copy now reflects PDF + conditional charts. Original other FastAPI routes and `main` branch remain unchanged.
- Target 6–8 pages on sufficiently rich data, fewer for sparse data; no padding for its own sake. BASIC **never fits ML**.

## Executed verification
- Python 3.11 GitHub Actions https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40202112886
  - **42 passed, 0 failed, 6 warnings in 7.17s** on SHA `fdccd288d792139463d6ea62138530f6d352b85c`.
  - A rich **synthetic** 150-row, 5-column Korean dataset -> **five charts**, PDF `6 <= page count <= 8`, searchable Korean text, Poppler raster of cover (resolution/nonblank asserts), manifest checksum for every archived file. Original 36 P0/P1/P2 tests remained PASS.
  - Sparse 3-row data -> 0 charts, shorter report; does not pad. API upload UTF-8-sig and cp949; 30MiB/20k rows/50 columns controls preserved.
- First P3 suite https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40201984225 had **41 passed, 1 failed**: a three-row category chart was created. Root cause missing minimum-support count. Corrected in SHA `898c0853c34974fe37bd2e73b944e5cd7cba60b0`. Final CI 42/42 success.
- An additional Actions workflow generation step creates **synthetic only** PDF/ZIP and rendered page previews, published temporarily as `basic-synthetic-pdf-review` (7-day retention). Review the latest run's artifact before relying on its visible design; visual/manual inspection is separate from automated nonblank raster test.

## Local run / fonts / boundaries
```sh
python -m pip install -r requirements-ci.txt
# Linux: install fonts-nanum and poppler-utils using your OS package manager
# Windows: install appropriately licensed NanumGothic.ttf;
#          optional environment AUTOML_KOREAN_FONT_PATH points to trusted local TTF
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/basic-mvp`, select authorized, de-identified CSV and download ZIP.

No hidden font download or paid external request occurs; missing font returns a diagnostic instead of producing broken Hangul glyphs. This dependency is **not** bundled in GitHub; verify redistribution/embedding license and Windows installation before commercial sale.

## Incomplete, explicitly NOT claimed
- **Manual visual inspection** of every rendered PDF page, Windows native use / web click/download, long-column overflow and Korean typography edge cases.
- `/api/basic-report` currently accepts CSV only; original commercial specification permits XLSX: defer XLSX ingestion to later P3 follow-up/P6. CSV is currently the tested delivery path.
- Original old folder/path routes and permissive CORS remain unsafe if made public: local-only, no SaaS.
- Group/time-safe ML, independent holdout, real prediction not in BASIC; P4–P5. Final licensing, input/DoS and distribution check in P6.
- BASIC package is **not sale-ready** until final Windows/browser/pdf visual/security gate.

## Next
P4: build STANDARD evaluation route with up to three challengers + Dummy, leak/group/time-aware validation when data semantics permit, honest scoring and holdout evidence, comparison PDF/ZIP. Reuse P3 BASIC PDFs/charts where possible. Keep CI 42 tests green and add targeted P4 cases. Continue updated `STATUS.md`, `HANDOFF.md`, `ACTIVE_TASK.md` on each turn.

## P3 final illustrated QA result — 2026-10-25 23:32 KST
- Final code commit `ea3d61454e17d6ef09e412da44fafe41204c481b`. GitHub Actions [40202695270](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40202695270): **42 passed, 0 failed, 6 warnings in 4.22s**; synthetic demo: **5 charts, 6 rendered PDF pages, 208,799-byte PDF and 240,062-byte inner ZIP**. The workflow uploaded `basic-synthetic-pdf-review`, GitHub artifact ID `12601789595` (7-day retention).
- The first 8-page preview had excessive whitespace (one plot per page). Reorganized to **two charts/page** with Korean figure titles, now 6 pages. Retrieved the final workflow preview ZIP and **visually examined all 6 page PNG images** (contact sheet). All pages appeared readable, Korean embedded glyphs displayed, and no obvious clipping or chart overlap at 1100px previews. Page 2 and page 5 remain comparatively sparse; final typography/polish remains release QA.
- Inspected `report.pdf` with the PDF inspector: 6 A4 pages, not encrypted; NanumGothic TrueType font embedded and subsets have Unicode mapping, searchable Korean text confirmed by pypdf tests. All six pages were rendered by GitHub CI `pdftoppm`.
- No human review of Windows rendering, physical print, accessibility reading order, font legal compliance or user-specific customer dataset. These remain P6 gates; **BASIC NOT SALE READY**.
- Previous CI [40202259190](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40202259190) had **42 tests passed** but failed the **demo generation step** because direct script execution lacked the repository module path (`ModuleNotFoundError: backend`). Fixed by running `python -m scripts.create_basic_preview`; do not repeat direct `python scripts/...` launch.
