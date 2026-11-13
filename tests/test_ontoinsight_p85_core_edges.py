"""P85 acceptance edge cases filling original 36-scenario synthetic matrix."""
from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from backend.app.services.ontoinsight_p70 import InputSource, review_sources, run_approved
from backend.app.services import ontoinsight_p85_ml as ml
from test_ontoinsight_p85_ml import sample, approved


def _sources(order_data, *, encoding="utf-8-sig"):
    return [
        InputSource("orders", "orders.csv", order_data, encoding=encoding),
        InputSource("refunds", "refunds.csv", b"order_id,amount\n001,10.00\n"),
    ]


def test_core02_cp949_data_parses_as_explicit_encoding():
    orders = "order_id,gross,channel\n001,100.00,가게\n".encode("cp949")
    rev = review_sources(_sources(orders, encoding="cp949"))
    assert rev["sources"]["orders"]["rows"] == 1


def test_core03_utf8_bom_csv_preserves_source_identity():
    source = _sources(b"\xef\xbb\xbforder_id,gross,channel\n001,100.00,web\n")
    rev = review_sources(source)
    assert rev["sources"]["orders"]["rows"] == 1
    assert len(rev["sources"]["orders"]["sha256"]) == 64


def test_core05_empty_csv_fails_closed():
    with pytest.raises(ValueError, match="empty|Invalid|CSV|Input"):
        review_sources(_sources(b""))


def test_core06_missing_header_fails_closed():
    with pytest.raises(ValueError, match="header|CSV"):
        review_sources(_sources(b"\n001,100.00,web\n"))


def test_core12_encrypted_or_fake_xlsx_fails_closed():
    sources = _sources(b"not-a-valid-ooxml-archive")
    sources[0] = InputSource("orders", "orders.xlsx", sources[0].content)
    with pytest.raises(ValueError, match="XLSX|archive|Invalid"):
        review_sources(sources)


def test_core15_quoted_thousands_amount_requires_manual_normalization():
    from backend.app.services.ontoinsight_p70 import approve_mapping
    source = _sources(b'order_id,gross,channel\n001,"1,000.00",web\n')
    rev = review_sources(source)
    approval = approve_mapping(
        rev, {"orders": {"order_id": "order_id", "sales": "gross", "channel": "channel"},
              "refunds": {"order_id": "order_id", "refund": "amount"}},
        {"currency": "KRW", "tax_basis": "included", "sales_basis": "gross_paid",
         "refund_basis": "positive_refund_events", "time_basis": "no_period_reporting"},
        actor="test-operator", acknowledgements={k: True for k in (
            "data_use_authorized", "business_meaning_confirmed", "privacy_reviewed",
            "gross_sales_basis_confirmed", "refund_event_basis_confirmed", "tax_policy_confirmed")}
    )
    with pytest.raises(ValueError, match="Ambiguous"):
        run_approved(source, approval)


def test_core31_no_skill_challenger_is_not_marketed_as_gain(monkeypatch):
    # A challenger with the exact dummy policy cannot outperform the baseline.
    source = sample()
    monkeypatch.setattr(ml, "_pipeline", lambda features, classification: Pipeline(
        [("model", DummyClassifier(strategy="most_frequent"))]))
    result = ml.evaluate_approved_ml(source, approved(source))
    assert result["status"] == "BASELINE_NOT_BEATEN"
    assert result["marketing_claim_allowed"] is False


def test_input_xlsx_uncached_formula_rejected():
    w = Workbook()
    s = w.active
    s.append(["order_id", "gross", "channel"])
    s.append(["001", "=1+1", "web"])
    b = BytesIO()
    w.save(b)
    sources = _sources(b"some")
    sources[0] = InputSource("orders", "orders.xlsx", b.getvalue())
    with pytest.raises(ValueError, match="Formula"):
        review_sources(sources)
