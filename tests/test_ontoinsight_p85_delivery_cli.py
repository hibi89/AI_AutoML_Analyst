"""P85 CLI produces local verified ZIP, rejects overwrite and changed source."""
from __future__ import annotations

import json
import sys

import pytest

from backend.app.services.ontoinsight_p70 import InputSource
from backend.app.services.ontoinsight_p85_report import verify_offline_bundle
from scripts import ontoinsight_p85_delivery_cli as app
from test_ontoinsight_p85_report import ORDERS, REFUNDS, approval


def _invoke(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["ontoinsight_p85_delivery_cli"] + args)
    return app.main()


def _paths(tmp_path):
    orders, refunds = tmp_path / "orders.csv", tmp_path / "refunds.csv"
    orders.write_bytes(ORDERS)
    refunds.write_bytes(REFUNDS)
    sources = [InputSource("orders", orders.name, ORDERS), InputSource("refunds", refunds.name, REFUNDS)]
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(approval(sources)), encoding="utf-8")
    return orders, refunds, receipt


def test_delivery_cli_outputs_verifiable_bundle_without_modifying_sources(tmp_path, monkeypatch):
    orders, refunds, receipt = _paths(tmp_path)
    out = tmp_path / "offline.zip"
    args = ["--orders", str(orders), "--refunds", str(refunds),
            "--receipt", str(receipt), "--out", str(out)]
    assert _invoke(monkeypatch, args) == 0
    assert verify_offline_bundle(out.read_bytes())["net_sales"] == "465.00"
    assert orders.read_bytes() == ORDERS
    assert refunds.read_bytes() == REFUNDS
    before = out.read_bytes()
    with pytest.raises(ValueError, match="fresh ZIP"):
        _invoke(monkeypatch, args)
    assert out.read_bytes() == before


def test_delivery_cli_invalidates_changed_source(tmp_path, monkeypatch):
    orders, refunds, receipt = _paths(tmp_path)
    orders.write_bytes(ORDERS.replace(b"250.00", b"260.00"))
    out = tmp_path / "invalid.zip"
    with pytest.raises(ValueError, match="Source digest"):
        _invoke(monkeypatch, ["--orders", str(orders), "--refunds", str(refunds),
                              "--receipt", str(receipt), "--out", str(out)])
    assert not out.exists()
