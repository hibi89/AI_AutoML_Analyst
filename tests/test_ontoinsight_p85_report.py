"""Synthetic P85 offline delivery proof; no customer source or model files."""
from __future__ import annotations

from io import BytesIO
import json
import socket
from zipfile import ZipFile, ZIP_DEFLATED

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from backend.app.services.ontoinsight_p70 import (
    InputSource, review_sources, approve_mapping,
)
from backend.app.services.ontoinsight_p85_report import (
    build_offline_bundle, verify_offline_bundle,
)

ORDERS = b"order_id,gross,channel\n001,100.00,web\n002,250.00,store\n003,150.00,web\n"
REFUNDS = b"order_id,amount\n001,10.00\n001,5.00\n002,20.00\n"


def source_pair():
    return [InputSource("orders", "orders.csv", ORDERS), InputSource("refunds", "refunds.csv", REFUNDS)]


def approval(sources):
    return approve_mapping(
        review_sources(sources),
        {"orders": {"order_id": "order_id", "sales": "gross", "channel": "channel"},
         "refunds": {"order_id": "order_id", "refund": "amount"}},
        {"currency": "KRW", "tax_basis": "included", "sales_basis": "gross_paid",
         "refund_basis": "positive_refund_events", "time_basis": "no_period_reporting"},
        actor="synthetic-reviewer",
        acknowledgements={k: True for k in (
            "data_use_authorized", "business_meaning_confirmed", "privacy_reviewed",
            "gross_sales_basis_confirmed", "refund_event_basis_confirmed", "tax_policy_confirmed")},
    )


def sample_bundle():
    sources = source_pair()
    return build_offline_bundle(sources, approval(sources))


def _replace_member(data, filename, content):
    out = BytesIO()
    with ZipFile(BytesIO(data)) as old, ZipFile(out, "w", compression=ZIP_DEFLATED) as new:
        for name in old.namelist():
            new.writestr(name, content if name == filename else old.read(name))
    return out.getvalue()


def test_static_four_formats_manifest_and_independent_verification():
    payload = sample_bundle()
    report = verify_offline_bundle(payload)
    assert report["verified"] is True
    assert report["members"] == 6
    assert report["net_sales"] == "465.00"
    assert report["release"] == "RELEASE_HOLD"
    assert report["ml_status"] == "ML_NOT_REQUESTED"


def test_pdf_has_text_and_is_openable():
    with ZipFile(BytesIO(sample_bundle())) as archive:
        pdf = archive.read("report.pdf")
    assert pdf.startswith(b"%PDF-")
    text = PdfReader(BytesIO(pdf)).pages[0].extract_text()
    assert "net_sales: 465.00" in text
    assert "RELEASE HOLD" in text


def test_xlsx_is_openable_and_contains_derived_not_source():
    with ZipFile(BytesIO(sample_bundle())) as archive:
        content = archive.read("report.xlsx")
    book = load_workbook(BytesIO(content), data_only=True)
    try:
        assert book.sheetnames == ["Summary", "Channels"]
        assert book["Channels"].max_row == 3
        assert book["Summary"]["A1"].value.startswith("ONTOINSIGHT")
        assert book["Channels"]["A2"].value.startswith("channel_")
        assert book["Channels"]["A2"].value != "store"
    finally:
        book.close()


def test_html_is_offline_static_no_javascript():
    with ZipFile(BytesIO(sample_bundle())) as archive:
        html = archive.read("report.html").decode()
    assert "default-src 'none'" in html
    assert "<script" not in html.lower()
    assert "465.00" in html
    assert "RELEASE HOLD" in html
    assert "<title>" in html


def test_export_contains_no_raw_customer_records():
    raw = sample_bundle()
    assert b"001," not in raw
    with ZipFile(BytesIO(raw)) as archive:
        text = archive.read("summary.json")
        assert b"\"001\"" not in text
        assert b"store" not in text
        assert b"\"web\"" not in text
        assert json.loads(text)["raw_source_rows_included"] is False


def test_bundle_rejects_changed_source_sha():
    sources = source_pair()
    receipt = approval(sources)
    sources[0] = InputSource("orders", "orders.csv", ORDERS.replace(b"100.00", b"900.00"))
    with pytest.raises(ValueError, match="Source digest"):
        build_offline_bundle(sources, receipt)


def test_bundle_rejects_no_local_approval():
    with pytest.raises(ValueError, match="approved|approval"):
        build_offline_bundle(source_pair(), {})


def test_bundle_needs_complete_ml_pair():
    sources = source_pair()
    with pytest.raises(ValueError, match="ML source and approval"):
        build_offline_bundle(sources, approval(sources), ml_receipt={})


def test_verifier_rejects_modified_html_member():
    data = sample_bundle()
    changed = _replace_member(data, "report.html", b"<script>alert(1)</script>")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_offline_bundle(changed)


def test_verifier_rejects_modified_json_metrics_even_with_valid_zip():
    data = sample_bundle()
    with ZipFile(BytesIO(data)) as archive:
        summary = json.loads(archive.read("summary.json"))
    summary["kpi"]["metrics"]["net_sales"] = "999.00"
    changed = _replace_member(data, "summary.json", json.dumps(summary).encode())
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_offline_bundle(changed)


def test_verifier_rejects_duplicate_zip_member():
    data = sample_bundle()
    buf = BytesIO()
    with ZipFile(BytesIO(data)) as old, ZipFile(buf, "w", compression=ZIP_DEFLATED) as new:
        for name in old.namelist():
            new.writestr(name, old.read(name))
        new.writestr("summary.json", old.read("summary.json"))
    with pytest.raises(ValueError, match="duplicate"):
        verify_offline_bundle(buf.getvalue())


def test_no_network_calls_in_report_build(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("Network access attempted")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    assert verify_offline_bundle(sample_bundle())["verified"] is True


def test_original_inputs_are_unchanged():
    sources = source_pair()
    before = [s.content for s in sources]
    build_offline_bundle(sources, approval(sources))
    assert [s.content for s in sources] == before


def test_undefined_conversion_roas_and_customer_metrics_are_not_invented():
    with ZipFile(BytesIO(sample_bundle())) as archive:
        data = json.loads(archive.read("summary.json"))
    assert "roas" not in data["kpi"]["metrics"]
    assert "conversion_rate" not in data["kpi"]["metrics"]
    assert "repeat_customer_rate" not in data["kpi"]["metrics"]
    assert data["ml"]["status"] == "ML_NOT_REQUESTED"


def test_previously_approved_receipt_invalidates_after_refund_change():
    sources = source_pair()
    receipt = approval(sources)
    sources[-1] = InputSource("refunds", "refunds.csv", REFUNDS.replace(b"10.00", b"100.00"))
    with pytest.raises(ValueError, match="Source digest"):
        build_offline_bundle(sources, receipt)
