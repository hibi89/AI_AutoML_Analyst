"""P70 synthetic fixtures only. No customer files or external requests."""
from __future__ import annotations

from io import BytesIO
import json
from zipfile import ZipFile, ZIP_DEFLATED

import pytest
from openpyxl import Workbook

from backend.app.services.ontoinsight_p70 import (
    InputSource, approve_mapping, review_sources, run_approved,
)

ORDERS = b"order_id,gross,channel\n001,100.00,web\n002,250.00,store\n003,150.00,web\n"
REFUNDS = b"order_id,amount\n001,10.00\n001,5.00\n002,20.00\n"
CHANNELS = b"order_id,channel\n001,web\n002,store\n003,web\n"
BASE_MEANINGS = {
    "currency": "KRW", "tax_basis": "included", "sales_basis": "gross_paid",
    "refund_basis": "positive_refund_events", "time_basis": "no_period_reporting",
}
BASE_ACKS = {name: True for name in (
    "data_use_authorized", "business_meaning_confirmed", "privacy_reviewed",
    "gross_sales_basis_confirmed", "refund_event_basis_confirmed", "tax_policy_confirmed",
)}


def src(which, data, filename=None):
    return InputSource(which, filename or f"{which}.csv", data)


def standard_sources(three=False):
    orders = ORDERS if not three else ORDERS.replace(b",channel", b"", 1).replace(b",web", b"").replace(b",store", b"")
    sources = [src("orders", orders), src("refunds", REFUNDS)]
    if three:
        sources.append(src("channels", CHANNELS))
    return sources


def mapping(three=False):
    result = {"orders": {"order_id": "order_id", "sales": "gross"},
              "refunds": {"order_id": "order_id", "refund": "amount"}}
    if three:
        result["channels"] = {"order_id": "order_id", "channel": "channel"}
    else:
        result["orders"]["channel"] = "channel"
    return result


def approved(sources, three=False):
    return approve_mapping(review_sources(sources), mapping(three), BASE_MEANINGS,
                           actor="synthetic-reviewer", acknowledgements=BASE_ACKS)


def workbook_bytes(columns, rows, formula=False, hidden=False):
    wb = Workbook()
    ws = wb.active
    ws.append(columns)
    for row in rows:
        ws.append(row)
    if formula:
        ws["B2"] = "=SUM(1,1)"
    if hidden:
        ws2 = wb.create_sheet("hidden")
        ws2.sheet_state = "hidden"
        ws2.append(["ignored"])
    b = BytesIO()
    wb.save(b)
    return b.getvalue()


def test_review_two_sources_requires_hold_and_no_numeric_metrics():
    review = review_sources(standard_sources())
    assert review["approval"] == "REVIEW_HOLD"
    assert review["kpi"] == "NOT_COMPUTED"
    assert review["ml"] == "ML_NOT_SUITABLE"
    assert review["sources"]["orders"]["rows"] == 3
    assert review["relationship_candidates"]
    assert "001" not in json.dumps(review)


def test_two_csv_approved_exact_reconciliation_1_to_many():
    sources = standard_sources()
    result = run_approved(sources, approved(sources))
    assert result["metrics"] == {
        "order_count": 3, "refund_event_count": 3, "gross_sales": "500.00",
        "refund_amount": "35.00", "net_sales": "465.00", "aov_net": "155.00",
    }
    assert all(result["audit"].values())
    assert len(result["channel_aggregates"]) == 2
    assert sum(x["orders"] for x in result["channel_aggregates"]) == 3
    assert all("channel_label" not in x for x in result["channel_aggregates"])
    assert result["prediction"] is None


def test_three_csv_channel_join_preserves_order_grain():
    sources = standard_sources(three=True)
    result = run_approved(sources, approved(sources, three=True))
    assert result["metrics"]["net_sales"] == "465.00"
    assert result["metrics"]["refund_event_count"] == 3
    assert result["audit"]["order_grain_preserved"]
    assert result["provenance"]["channels"]["rows"] == 3


def test_original_bytes_unchanged_during_review_and_report():
    sources = standard_sources()
    content = [x.content for x in sources]
    run_approved(sources, approved(sources))
    assert [x.content for x in sources] == content


def test_csv_codes_with_leading_zero_remain_distinct():
    sources = standard_sources()
    result = run_approved(sources, approved(sources))
    assert result["metrics"]["order_count"] == 3


def test_mixed_xlsx_orders_and_csv_refunds():
    orderxlsx = workbook_bytes(["order_id", "gross", "channel"],
                               [["001", 100, "web"], ["002", 250, "store"], ["003", 150, "web"]])
    sources = [src("orders", orderxlsx, "orders.xlsx"), src("refunds", REFUNDS)]
    review = review_sources(sources)
    assert review["sources"]["orders"]["format"] == "xlsx"
    report = run_approved(sources, approved(sources))
    assert report["metrics"]["net_sales"] == "465.00"


def test_three_mixed_xlsx_channels_and_two_csv():
    srcs = standard_sources(three=True)
    srcs[-1] = src("channels", workbook_bytes(["order_id", "channel"],
                            [["001", "web"], ["002", "store"], ["003", "web"]]), "channels.xlsx")
    assert run_approved(srcs, approved(srcs, True))["metrics"]["net_sales"] == "465.00"


def test_no_approval_receipt_is_hold():
    with pytest.raises(ValueError, match="approval|approved|receipt"):
        run_approved(standard_sources(), {})


def test_source_change_invalidates_review_approval():
    sources = standard_sources()
    receipt = approved(sources)
    modified = [src("orders", ORDERS.replace(b"250.00", b"260.00")), sources[1]]
    with pytest.raises(ValueError, match="Source digest"):
        run_approved(modified, receipt)


def test_mapping_tampering_invalidates_digest():
    sources = standard_sources()
    receipt = approved(sources)
    receipt["mapping"]["orders"]["sales"] = "order_id"
    with pytest.raises(ValueError, match="mapping digest"):
        run_approved(sources, receipt)


def test_missing_owner_attestation_blocks():
    sources = standard_sources()
    flags = BASE_ACKS.copy()
    flags["privacy_reviewed"] = False
    with pytest.raises(ValueError, match="attestations"):
        approve_mapping(review_sources(sources), mapping(), BASE_MEANINGS,
                        actor="reviewer", acknowledgements=flags)


def test_invalid_semantics_block():
    sources = standard_sources()
    values = BASE_MEANINGS.copy()
    values["tax_basis"] = "unknown"
    with pytest.raises(ValueError, match="Unsupported business meaning"):
        approve_mapping(review_sources(sources), mapping(), values,
                        actor="reviewer", acknowledgements=BASE_ACKS)


def test_wrong_mapping_column_blocks_before_export():
    sources = standard_sources()
    bad = mapping()
    bad["refunds"]["refund"] = "unknown"
    with pytest.raises(ValueError, match="absent"):
        approve_mapping(review_sources(sources), bad, BASE_MEANINGS,
                        actor="reviewer", acknowledgements=BASE_ACKS)


def test_duplicate_order_id_blocked():
    sources = standard_sources()
    bad = [src("orders", ORDERS.replace(b"003,", b"002,")), sources[1]]
    with pytest.raises(ValueError, match="Duplicate order"):
        run_approved(bad, approved(bad))


def test_refund_missing_parent_blocks():
    sources = [standard_sources()[0], src("refunds", REFUNDS.replace(b"002,20.00", b"999,20.00"))]
    with pytest.raises(ValueError, match="foreign-key"):
        run_approved(sources, approved(sources))


def test_over_refund_order_blocks():
    sources = [standard_sources()[0], src("refunds", REFUNDS.replace(b"001,10.00", b"001,900.00"))]
    with pytest.raises(ValueError, match="exceeds order gross"):
        run_approved(sources, approved(sources))


def test_duplicate_channel_join_key_blocks():
    sources = standard_sources(True)
    sources[-1] = src("channels", CHANNELS.replace(b"003,web", b"002,web"))
    with pytest.raises(ValueError, match="Duplicate channels"):
        run_approved(sources, approved(sources, True))


def test_unmatched_channel_join_blocks():
    sources = standard_sources(True)
    sources[-1] = src("channels", CHANNELS.replace(b"003,web", b"999,web"))
    with pytest.raises(ValueError, match="foreign-key"):
        run_approved(sources, approved(sources, True))


def test_missing_channel_mapping_blocks():
    sources = standard_sources(True)
    sources[-1] = src("channels", CHANNELS.replace(b"003,web\n", b""))
    with pytest.raises(ValueError, match="Unmatched orders"):
        run_approved(sources, approved(sources, True))


def test_dirty_formula_amount_blocks():
    sources = [src("orders", ORDERS.replace(b"100.00", b"=1+2")), src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="Ambiguous"):
        run_approved(sources, approved(sources))


def test_null_financial_amount_blocks():
    sources = [src("orders", ORDERS.replace(b"100.00", b"")), src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="Missing amount|Ambiguous"):
        run_approved(sources, approved(sources))


def test_duplicate_csv_header_blocks():
    sources = [src("orders", ORDERS.replace(b"order_id,gross,channel", b"order_id,order_id,channel")), src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="Duplicate|duplicate"):
        review_sources(sources)


def test_partial_csv_row_blocks():
    sources = [src("orders", ORDERS.replace(b"003,150.00,web", b"003,150.00")), src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="ragged"):
        review_sources(sources)


def test_sensitive_columns_block_before_review():
    sources = [src("orders", ORDERS.replace(b",channel", b",email,channel").replace(b",web", b",a@example.com,web").replace(b",store", b",b@example.com,store")), src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="Sensitive"):
        review_sources(sources)


def test_unknown_encoding_requires_explicit_supported_choice():
    sources = [InputSource("orders", "orders.csv", ORDERS, encoding="latin1"), src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="encoding"):
        review_sources(sources)


def test_xlsx_formula_blocks_even_with_cached_value_reader():
    xlsx = workbook_bytes(["order_id", "gross", "channel"], [["001", 100, "web"]], formula=True)
    with pytest.raises(ValueError, match="Formula"):
        review_sources([src("orders", xlsx, "orders.xlsx"), src("refunds", REFUNDS)])


def test_xlsx_hidden_sheet_blocks():
    xlsx = workbook_bytes(["order_id", "gross", "channel"], [["001", 100, "web"]], hidden=True)
    with pytest.raises(ValueError, match="worksheet"):
        review_sources([src("orders", xlsx, "orders.xlsx"), src("refunds", REFUNDS)])


def test_xlsx_external_relationship_blocks():
    xlsx = workbook_bytes(["order_id", "gross", "channel"], [["001", 100, "web"]])
    result = BytesIO()
    with ZipFile(BytesIO(xlsx)) as zin, ZipFile(result, "w", compression=ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            val = zin.read(info.filename)
            if info.filename == "xl/_rels/workbook.xml.rels":
                val = val.replace(b"</Relationships>", b'<Relationship Id="rId999" Target="http://unsafe.invalid" TargetMode="External" Type="external"/></Relationships>')
            zout.writestr(info.filename, val)
    with pytest.raises(ValueError, match="External"):
        review_sources([src("orders", result.getvalue(), "orders.xlsx"), src("refunds", REFUNDS)])


def test_xlsx_numeric_order_id_requires_manual_text_mapping():
    xlsx = workbook_bytes(["order_id", "gross", "channel"], [[1.0, 100, "web"]])
    sources = [src("orders", xlsx, "orders.xlsx"), src("refunds", b"order_id,amount\n1,0\n")]
    with pytest.raises(ValueError, match="relation key"):
        run_approved(sources, approved(sources))


def test_more_than_three_inputs_refused():
    sources = standard_sources(True) + [src("refunds", REFUNDS)]
    with pytest.raises(ValueError, match="exactly"):
        review_sources(sources)


def test_failed_mapping_does_not_mutate_sources():
    sources = standard_sources(True)
    before = [x.content for x in sources]
    bad = mapping(True)
    bad["channels"]["channel"] = "missing"
    with pytest.raises(ValueError):
        approve_mapping(review_sources(sources), bad, BASE_MEANINGS,
                        actor="owner", acknowledgements=BASE_ACKS)
    assert [x.content for x in sources] == before
