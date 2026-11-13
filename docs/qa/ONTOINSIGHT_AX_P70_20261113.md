# ONTOINSIGHT AX P70 — phase verification and limitations
2026-11-13 KST | Executed source SHA: 34e7b16a2fef5e1b0d21f4e6d097c6faaaaf9012 | RELEASE HOLD

## Design and verified scope
- Source blueprint: private hibi89/Freelancer product/ontoinsight-ax-data-analytics docs/FINAL_BLUEPRINT.md. This P70 is a phase milestone, NOT official final product 70%. Full-design weighting remains UNASSESSED.
- Alternatives: external LLM upload was rejected for confidentiality and API cost; direct pandas joins were rejected for 1:N refund revenue multiplication. Selected: original AutoML bounded CSV/XLSX intake, local explicit business meaning review and attestation, order-grain Decimal ledger, audit.
- Implementation: backend/app/services/ontoinsight_p70.py, scripts/ontoinsight_p70_cli.py, tests/test_ontoinsight_p70.py, tests/test_ontoinsight_p70_cli.py and dedicated CI workflow. Original AutoML engines and P50 feature unchanged.
- Two or three sources: orders/refunds and optional channels, CSV or XLSX mixed. Safe formats, one visible XLSX worksheet, formula/external link rejection, 30MiB combined inputs, 20k rows per file, max 50 columns, approved fixed roles and source SHA/mapping digest.
- Refund events are accumulated per order; per-order refund > gross and channel 1:1 duplicate/unmatched are blocked. Raw source and aggregate totals are checked for exact Decimal equality.

## Executed source verification
- GitHub Actions: https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/43378733016
- SHA 34e7b16a2fef5e1b0d21f4e6d097c6faaaaf9012 completed SUCCESS 2/2: Ubuntu24.04 44 PASS / 0 FAIL / 0 SKIP; Windows Server2025 44 PASS / 0 FAIL / 0 SKIP. Python3.11, compileall PASS on both.
- Command: python -m pytest -q tests/test_ontoinsight_p50.py tests/test_ontoinsight_p70.py tests/test_ontoinsight_p70_cli.py
- Counts: P50 11; P70 ingestion/semantics/joins 31; P70 CLI review-attest-run, no overwrite and source-drift 2.
- Synthetic example: 3 orders gross 500.00; refund events 3 totaling 35.00; net 465.00; AOV net 155.00. Source SHA bound and 1:N refund grain preserved. These are synthetic data, NOT customer financial facts.
- Failure-mode tests include source/approval mutation, wrong schema, duplicate keys, orphan refunds, over-refund, no consent, unsafe amount, missing amount, ambiguous encoding, XLSX formula/hidden/external, PII-marked header and no-overwrite.

## Local usage (customer source requires external authorization first)
1. python -m scripts.ontoinsight_p70_cli review --orders orders.csv --refunds refunds.csv --out new-review.json
2. Human/operator prepares choices.json with mapping of orders (order_id/sales/channel) and refunds (order_id/refund), explicit currency, tax basis, gross_paid, positive_refund_events, no_period_reporting, and six affirmative use/meaning/privacy attestations.
3. python -m scripts.ontoinsight_p70_cli attest --review new-review.json --choices choices.json --actor local-review-ref --out new-receipt.json
4. python -m scripts.ontoinsight_p70_cli run --orders orders.csv --refunds refunds.csv --receipt new-receipt.json --out fresh-report.json
- A third channels.xlsx may be supplied with matching --channels argument in review and run; then mapping requires channel from channels source, not orders.
- Output is aggregate-only JSON with source hashes/derived formula and hashed channel references, not a raw-record export. Hashed channel names are pseudonyms, NOT guaranteed anonymous.

## Exclusions, security and acceptance
- The local operator actor string is not authenticated; receipt is NOT cryptographic or legal consent. Customer rights and source purpose must be verified externally.
- Identical refunds without unique refund-event ID remain ambiguous (whether legitimate equal events vs duplicated input); no claim of independent refund de-duplication. Currency conversion, time-basis KPIs, customer cohort/ML and PDF/Excel/HTML delivery are not yet supported in new product.
- Full existing AutoML 300+ regression, real user Windows10/11, customer data, legal license review, real browser, external APIs and production are NOT VERIFIED or NOT APPLICABLE. RELEASE HOLD remains.
- Future P85: time/group/target leakage ML gate, dummy baseline/abstain, offline reports and additional 30/36 core negative tests. P95/P100: authorized customer acceptance, actual Windows, rights and release approval.
- Full final-design official completion UNASSESSED until owner-approved whole-100 point weights and requirement-level proof exist. Central ONTOINSIGHT [작업중] must stay.

## Recovery
- Feature parent/rollback base: 8defbec4a943e081a12a6aaff1ae59f135ef05d0. Select previous SHA in a new branch; no force-push. Customer originals, secrets, main and production unchanged.
