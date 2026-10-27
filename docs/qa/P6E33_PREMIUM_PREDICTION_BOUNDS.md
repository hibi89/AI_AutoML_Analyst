# P6E33 — bounded client-side PREMIUM prediction CSV input

Date: 2026-10-27 KST
Branch: `feature/kmong-v1`
Code SHA: `29592147f689ee6cc047d3d1035633f008c82331`
Tests SHA: `85b41695a57ff5928ff4048fa649bbc3e0018732`

## Finding
Shipped `backend/app/services/premium_predict.py` checked the 30 MiB file size before parsing but invoked `pandas.read_csv` **without an `nrows` bound**. Only after the full CSV had been allocated did it reject inputs exceeding the 20,000-row limit. Very large row counts within a modest byte size could needlessly consume memory/CPU. The input header/schema was also only compared after allocating the DataFrame.

## Fix
1. Inspect original CSV header under the supported encoding before loading the tabular rows; reject blank, duplicate, wrong-order, wrong-name headers before Pandas reads the data.
2. Apply `pd.read_csv(path, encoding=encoding, nrows=MAX_ROWS + 1)`; distinguish exactly the allowed 20,000 rows from overflow with one extra parsed row. Never silently sample 20,001 rows as valid.
3. Report malformed CSV parser failures as controlled `ValueError` for the client-side CLI rather than Python traceback.
4. Keep explicit CP932 inputs supported and preserve existing model/schema/CSV output controls. Do not change pricing, model training, ZIP contents, or default BASIC/ STANDARD behavior.

## Test evidence
- New `tests/test_p6e33_premium_prediction_bounds.py` contains 5 deterministic synthetic tests: 20,000 accepted; >20,000 rejected with an asserted parser row budget; mismatched header rejected without calling Pandas; Japanese CP932 schema preserved; 30 MiB byte guard respected.
- New code/test tree: [Linux run 40507768720](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40507768720), **208 passed / 3 skipped / 66 warnings, 0 failed**.
- Source-equivalent earlier commit (implementation code only, before new tests): [Windows native 40507706560](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40507706560), [Windows Chromium 40507706705](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40507706705), [Linux Chromium 40507706657](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40507706657), [Docker 40507706517](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40507706517): SUCCESS. Those jobs do not include the new test file, but exercised the same updated runtime code.
- Product PDFs and ZIP manifests were regenerated in Linux CI: BASIC 6, STANDARD 9, PREMIUM 11 pages, manifests PASS.
- This tests bounded *row parsing*, not full memory proof against every malformed compressed/file/multipart input. Do not claim full application upload threat testing.

## Remaining restrictions
- A previous Codex worker reported unfinished local upload security edits, but no such uncommitted files can be retrieved through GitHub. This change is independent; do not overwrite local Codex modifications without inspecting their diff in a future explicit reconciliation.
- Human visual approval of final client-delivered PDF/ZIP, real font provenance and rights, legal notices and tier-specific commercial decision remain P6E22 owner-only. Sale GO for BASIC/STANDARD/PREMIUM remains **NO**; P0–P6 accepted gates remain **5/7 (71%)**.
