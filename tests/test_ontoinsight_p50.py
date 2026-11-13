"""ONTOINSIGHT new-product P50; only synthetic, explicitly noncustomer rows."""
from __future__ import annotations

import hashlib

import pytest

from backend.app.services.ontoinsight_p50 import inspect_csv, verify_synthetic_kpis

SAMPLE = (b"order_id,sales,refund\n"
          b"O-1,100.00,0.00\n"
          b"O-1,50.00,0.00\n"
          b"O-2,80.00,20.00\n"
          b"O-3,120.00,0.00\n")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_original_automl_csv_path_produces_hold_metadata() -> None:
    result = inspect_csv(SAMPLE, "sample.csv")
    assert result["source"]["sha256"] == _sha(SAMPLE)
    assert result["source"]["rows"] == 4
    assert result["legacy_basic_compatible"] is True
    assert result["approval"]["state"] == "REVIEW_HOLD"
    assert result["metrics"]["state"] == "NOT_COMPUTED"
    assert result["ml"]["state"] == "ML_NOT_SUITABLE"
    assert result["export_allowed"] is False
    assert result["role_candidates"]["sales"] == ["sales"]
    assert result["role_candidates"]["order_id"] == ["order_id"]
    assert "O-1" not in str(result)


def test_exact_five_synthetic_kpis_reconcile_two_source_paths() -> None:
    result = verify_synthetic_kpis(SAMPLE, expected_sha256=_sha(SAMPLE))
    assert result["scope"] == "SYNTHETIC_TEST_ONLY_NOT_CUSTOMER_APPROVAL"
    assert result["kpis"] == {
        "gross_sales": "350.00", "refund_amount": "20.00",
        "net_sales": "330.00", "order_count": 3, "aov": "110.00",
    }
    assert result["reconciled"] is True
    assert all(result["checks"].values())


def test_source_hash_change_invalidates_evidence() -> None:
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_synthetic_kpis(SAMPLE + b"O-4,5.00,0.00\n", expected_sha256=_sha(SAMPLE))


def test_unapproved_customer_like_file_never_emits_metrics() -> None:
    result = inspect_csv(b"customer_id,email,sales\nC1,u@example.invalid,10.00\n", "in.csv")
    assert result["metrics"]["state"] == "NOT_COMPUTED"
    assert "u@example.invalid" not in str(result)
    assert next(col for col in result["data_dictionary"] if col["column"] == "email")["sensitivity"] == "REVIEW_REQUIRED"


def test_refuse_ambiguous_currency_in_synthetic_audit() -> None:
    data = SAMPLE.replace(b"100.00", b"KRW 100")
    with pytest.raises(ValueError, match="Ambiguous"):
        verify_synthetic_kpis(data, expected_sha256=_sha(data))


def test_refuse_missing_amount() -> None:
    data = SAMPLE.replace(b"80.00,20.00", b"80.00,")
    with pytest.raises(ValueError, match="Missing amount"):
        verify_synthetic_kpis(data, expected_sha256=_sha(data))


def test_refuse_duplicate_csv_header_in_original_parser() -> None:
    data = b"sales,sales,refund\n10,20,0\n"
    with pytest.raises(ValueError, match="Duplicate"):
        inspect_csv(data)


def test_refuse_mismatched_amounts_with_refunds_exceeding_gross() -> None:
    data = SAMPLE.replace(b"80.00,20.00", b"80.00,900.00")
    with pytest.raises(ValueError, match="exceeds gross"):
        verify_synthetic_kpis(data, expected_sha256=_sha(data))


def test_reject_xlsx_at_p50_even_if_original_supports_it() -> None:
    with pytest.raises(ValueError, match="one CSV"):
        inspect_csv(b"not-a-workbook", "sample.xlsx")


def test_refuse_missing_order_id_in_audit() -> None:
    data = SAMPLE.replace(b"O-2,80.00", b",80.00")
    with pytest.raises(ValueError, match="Missing order ID"):
        verify_synthetic_kpis(data, expected_sha256=_sha(data))


def test_synthetic_test_does_not_approve_customer_metrics() -> None:
    result = verify_synthetic_kpis(SAMPLE, expected_sha256=_sha(SAMPLE))
    assert "APPROVED" not in result
    assert inspect_csv(SAMPLE)["approval"]["state"] == "REVIEW_HOLD"
