"""P85 core30 explicit, distinct 36-catalog scenario selectors on actual code."""
from __future__ import annotations
import subprocess
import sys

CORE = {
    1: "tests/test_ontoinsight_p50.py::test_original_automl_csv_path_produces_hold_metadata",
    2: "tests/test_ontoinsight_p85_core_edges.py::test_core02_cp949_data_parses_as_explicit_encoding",
    3: "tests/test_ontoinsight_p85_core_edges.py::test_core03_utf8_bom_csv_preserves_source_identity",
    4: "tests/test_ontoinsight_p70.py::test_unknown_encoding_requires_explicit_supported_choice",
    5: "tests/test_ontoinsight_p85_core_edges.py::test_core05_empty_csv_fails_closed",
    6: "tests/test_ontoinsight_p85_core_edges.py::test_core06_missing_header_fails_closed",
    7: "tests/test_ontoinsight_p70.py::test_duplicate_csv_header_blocks",
    9: "tests/test_ontoinsight_p70.py::test_dirty_formula_amount_blocks",
    11: "tests/test_ontoinsight_p70.py::test_mixed_xlsx_orders_and_csv_refunds",
    12: "tests/test_ontoinsight_p85_core_edges.py::test_core12_encrypted_or_fake_xlsx_fails_closed",
    13: "tests/test_ontoinsight_p70.py::test_xlsx_external_relationship_blocks",
    15: "tests/test_ontoinsight_p85_core_edges.py::test_core15_quoted_thousands_amount_requires_manual_normalization",
    16: "tests/test_ontoinsight_p70.py::test_invalid_semantics_block",
    17: "tests/test_ontoinsight_p70.py::test_duplicate_order_id_blocked",
    19: "tests/test_ontoinsight_p70.py::test_two_csv_approved_exact_reconciliation_1_to_many",
    20: "tests/test_ontoinsight_p70.py::test_refund_missing_parent_blocks",
    21: "tests/test_ontoinsight_p70.py::test_original_bytes_unchanged_during_review_and_report",
    22: "tests/test_ontoinsight_p85_math.py::test_core22_decimal_nonbinary_exact_money",
    24: "tests/test_ontoinsight_p85_report.py::test_undefined_conversion_roas_and_customer_metrics_are_not_invented",
    25: "tests/test_ontoinsight_p70.py::test_source_change_invalidates_review_approval",
    26: "tests/test_ontoinsight_p85_report.py::test_no_network_calls_in_report_build",
    27: "tests/test_ontoinsight_p70.py::test_sensitive_columns_block_before_review",
    28: "tests/test_ontoinsight_p85_ml.py::test_feature_same_as_target_rejected",
    29: "tests/test_ontoinsight_p85_ml.py::test_time_split_is_chronological",
    30: "tests/test_ontoinsight_p85_ml.py::test_group_split_heldout_has_no_group_overlap",
    31: "tests/test_ontoinsight_p85_core_edges.py::test_core31_no_skill_challenger_is_not_marketed_as_gain",
    32: "tests/test_ontoinsight_p85_ml.py::test_small_imbalanced_class_abstain",
    33: "tests/test_ontoinsight_p85_ml.py::test_explicit_classification_dummy_cv_and_single_heldout",
    34: "tests/test_ontoinsight_p85_math.py::test_core34_cv_heldout_separation_has_no_exported_prediction_rows",
    35: "tests/test_ontoinsight_p85_report.py::test_verifier_rejects_modified_html_member",
}

def main() -> int:
    if len(CORE) != 30 or len(set(CORE.values())) != 30:
        raise SystemExit("CORE30 inventory must have 30 distinct test selectors.")
    print("P85 CORE30 case IDs:", sorted(CORE), flush=True)
    return subprocess.run([sys.executable,"-m","pytest","-q",*CORE.values()],check=False).returncode

if __name__ == "__main__":
    raise SystemExit(main())
