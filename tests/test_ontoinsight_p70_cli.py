"""CLI round trip: review -> explicit attestation -> exact report, no overwrite."""
from __future__ import annotations

import json
import sys

import pytest

from scripts import ontoinsight_p70_cli as cli


def _invoke(monkeypatch, *args: str) -> None:
    monkeypatch.setattr(sys, "argv", ["ontoinsight_p70_cli", *args])
    assert cli.main() == 0


def _choices():
    return {"mapping": {"orders": {"order_id": "order_id", "sales": "gross", "channel": "channel"},
                        "refunds": {"order_id": "order_id", "refund": "amount"}},
            "semantics": {"currency": "KRW", "tax_basis": "included", "sales_basis": "gross_paid",
                          "refund_basis": "positive_refund_events", "time_basis": "no_period_reporting"},
            "acknowledgements": {name: True for name in (
                "data_use_authorized", "business_meaning_confirmed", "privacy_reviewed",
                "gross_sales_basis_confirmed", "refund_event_basis_confirmed", "tax_policy_confirmed")}}


def _round_trip(tmp_path, monkeypatch):
    orders = tmp_path / "orders.csv"
    refunds = tmp_path / "refunds.csv"
    orders.write_bytes(b"order_id,gross,channel\n001,100.00,web\n002,200.00,store\n")
    refunds.write_bytes(b"order_id,amount\n001,10.00\n001,5.00\n")
    review = tmp_path / "review.json"
    choice_path = tmp_path / "choices.json"
    receipt = tmp_path / "receipt.json"
    result = tmp_path / "result.json"
    choice_path.write_text(json.dumps(_choices()), encoding="utf-8")
    inputs = ("--orders", str(orders), "--refunds", str(refunds))
    _invoke(monkeypatch, "review", *inputs, "--out", str(review))
    assert json.loads(review.read_text(encoding="utf-8"))["approval"] == "REVIEW_HOLD"
    _invoke(monkeypatch, "attest", "--review", str(review), "--choices", str(choice_path),
            "--actor", "synthetic-reviewer", "--out", str(receipt))
    _invoke(monkeypatch, "run", *inputs, "--receipt", str(receipt), "--out", str(result))
    return orders, refunds, review, receipt, result, inputs


def test_cli_three_phases_real_file_json_and_original_integrity(tmp_path, monkeypatch):
    orders, refunds, review, receipt, result, inputs = _round_trip(tmp_path, monkeypatch)
    report = json.loads(result.read_text(encoding="utf-8"))
    assert report["metrics"]["gross_sales"] == "300.00"
    assert report["metrics"]["refund_amount"] == "15.00"
    assert report["metrics"]["net_sales"] == "285.00"
    assert all(report["audit"].values())
    assert report["raw_rows_exported"] is False
    assert orders.read_bytes() == b"order_id,gross,channel\n001,100.00,web\n002,200.00,store\n"
    assert refunds.read_bytes() == b"order_id,amount\n001,10.00\n001,5.00\n"
    previous_result = result.read_bytes()
    with pytest.raises(ValueError, match="fresh output"):
        _invoke(monkeypatch, "run", *inputs, "--receipt", str(receipt), "--out", str(result))
    assert result.read_bytes() == previous_result


def test_cli_source_change_after_approval_blocks(tmp_path, monkeypatch):
    orders, refunds, review, receipt, result, inputs = _round_trip(tmp_path, monkeypatch)
    orders.write_bytes(orders.read_bytes().replace(b"200.00", b"250.00"))
    other_result = tmp_path / "changed.json"
    with pytest.raises(ValueError, match="Source digest"):
        _invoke(monkeypatch, "run", *inputs, "--receipt", str(receipt), "--out", str(other_result))
    assert not other_result.exists()
