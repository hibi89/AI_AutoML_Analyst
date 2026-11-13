"""ONTOINSIGHT AX P50: local, fail-closed CSV semantics review.

This is NOT an approval service or an ML prediction API. Customer source rows
are never stored or returned. All inferred business meanings remain on HOLD.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import StringIO
from typing import Any

import pandas as pd

from backend.app.services.basic_report import MAX_UPLOAD_BYTES, _quality_rows
from backend.app.services.tabular_input import read_uploaded_table

CONTRACT = "ontoinsight.semantic.p50.v1"
ROLE_ALIASES: dict[str, frozenset[str]] = {
    "order_id": frozenset({"order_id", "orderid", "주문번호", "주문id"}),
    "customer_id": frozenset({"customer_id", "customerid", "고객번호", "고객id"}),
    "sku": frozenset({"sku", "product_sku", "상품코드"}),
    "date": frozenset({"payment_date", "order_date", "주문일", "결제일"}),
    "sales": frozenset({"sales", "gross_sales", "판매금액", "매출액"}),
    "refund": frozenset({"refund", "refund_amount", "환불금액"}),
}
SENSITIVE_TOKENS = ("email", "phone", "mobile", "address", "ssn", "주민등록", "이메일", "전화번호", "휴대폰", "주소")


def _candidate_roles(column: str) -> list[str]:
    key = column.strip().casefold().replace(" ", "").replace("-", "_")
    return [role for role, aliases in ROLE_ALIASES.items() if key in aliases]


def inspect_csv(data: bytes, filename: str = "data.csv", *, encoding: str = "auto") -> dict[str, Any]:
    """Parse through the original AutoML ingestion path; return metadata only.

    Treat the entire file as unapproved until the later signed approval stage.
    No predicted KPI, ML score, sample value, or raw identifier is exported.
    """
    if not filename.casefold().endswith(".csv"):
        raise ValueError("P50 only supports one CSV; XLSX is a later stage.")
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("CSV is empty or exceeds the original 30 MiB limit.")
    frame = read_uploaded_table(data, filename, csv_encoding=encoding)
    digest = sha256(data).hexdigest()
    quality = _quality_rows(frame)
    candidates: list[dict[str, Any]] = []
    for entry in quality:
        name = entry["column"]
        roles = _candidate_roles(name)
        sensitive = any(token in name.casefold() for token in SENSITIVE_TOKENS)
        candidates.append({
            "column": name,
            "dtype": entry["dtype"],
            "missing": entry["missing"],
            "unique": entry["unique"],
            "sensitivity": "REVIEW_REQUIRED" if sensitive or "customer_id" in roles else "UNASSESSED",
            "role_candidates": roles,
            "confidence": "INFERRED" if roles else "UNASSESSED",
            "approval": "REVIEW_HOLD",
        })
    roles_to_columns = {
        role: [item["column"] for item in candidates if role in item["role_candidates"]]
        for role in ROLE_ALIASES
    }
    return {
        "contract": CONTRACT,
        "source": {"sha256": digest, "format": "csv", "bytes": len(data),
                   "rows": int(len(frame)), "columns": int(len(frame.columns))},
        "data_dictionary": candidates,
        "role_candidates": roles_to_columns,
        "legacy_basic_compatible": True,
        "approval": {"state": "REVIEW_HOLD", "mapping_digest": None, "actor": None},
        "metrics": {"state": "NOT_COMPUTED", "reason": "Business meaning is not approved."},
        "ml": {"state": "ML_NOT_SUITABLE", "reason": "No approved target or leakage review."},
        "export_allowed": False,
    }


def _amount(value: Any) -> Decimal:
    if value is None or pd.isna(value):
        raise ValueError("Missing amount: cannot calculate a financial KPI.")
    original = str(value).strip()
    # No locale, currency, exponent, formula, NaN or infinity guessing at P50.
    if not original or any(c not in "0123456789.-" for c in original) or original.count(".") > 1:
        raise ValueError("Ambiguous or invalid amount; requires review.")
    try:
        result = Decimal(original)
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary amount.") from exc
    if not result.is_finite() or result < 0 or result.as_tuple().exponent < -2:
        raise ValueError("Money must be nonnegative and have <=2 decimal places.")
    return result


def verify_synthetic_kpis(csv_bytes: bytes, *, expected_sha256: str) -> dict[str, Any]:
    """Bounded synthetic-only exact KPI audit with independent raw CSV totals.

    Do not call on customer records. A real approval-bound calculator is in P70.
    Returns numbers labeled as synthetic evidence, never customer insights.
    """
    if sha256(csv_bytes).hexdigest() != expected_sha256:
        raise ValueError("Source changed: digest mismatch, prior review invalid.")
    inspected = inspect_csv(csv_bytes, "synthetic.csv", encoding="utf-8")
    frame = read_uploaded_table(csv_bytes, "synthetic.csv", csv_encoding="utf-8")
    expected = {"order_id", "sales", "refund"}
    if set(frame.columns) != expected:
        raise ValueError("Synthetic audit requires exactly order_id,sales,refund.")
    if frame["order_id"].isna().any() or frame["order_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Missing order ID: order count cannot be validated.")
    order_ids = frame["order_id"].astype(str).tolist()
    # Path A: original AutoML parsed table -> Decimal-safe calculations.
    gross = sum((_amount(v) for v in frame["sales"]), Decimal("0")).quantize(Decimal("0.01"))
    refund = sum((_amount(v) for v in frame["refund"]), Decimal("0")).quantize(Decimal("0.01"))
    net = gross - refund
    if net < 0:
        raise ValueError("Refund total exceeds gross in synthetic data.")
    unique_orders = len(set(order_ids))
    aov = (net / unique_orders).quantize(Decimal("0.01")) if unique_orders else None
    # Path B: independent raw CSV streaming reconciliation (no pandas totals).
    try:
        raw = csv.DictReader(StringIO(csv_bytes.decode("utf-8-sig")), strict=True)
        if raw.fieldnames is None or set(raw.fieldnames) != expected or len(raw.fieldnames) != 3:
            raise ValueError("Invalid synthetic CSV header.")
        events = list(raw)
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("Invalid synthetic CSV encoding or format.") from exc
    if len(events) != inspected["source"]["rows"]:
        raise ValueError("Parsed row count differs from original input.")
    if any(None in row or row.get("order_id") is None or not row["order_id"].strip() for row in events):
        raise ValueError("Malformed raw CSV row or missing ID.")
    raw_gross = sum((_amount(row["sales"]) for row in events), Decimal("0"))
    raw_refund = sum((_amount(row["refund"]) for row in events), Decimal("0"))
    raw_orders = len({row["order_id"] for row in events})
    if (gross, refund, unique_orders) != (raw_gross, raw_refund, raw_orders):
        raise ValueError("Raw source and derived KPI disagree; hold.")
    return {
        "contract": CONTRACT,
        "scope": "SYNTHETIC_TEST_ONLY_NOT_CUSTOMER_APPROVAL",
        "source_sha256": expected_sha256,
        "reconciled": True,
        "metric_formula_version": "synthetic.v1/gross-refund/net-per-order",
        "kpis": {
            "gross_sales": str(gross), "refund_amount": str(refund),
            "net_sales": str(net), "order_count": unique_orders,
            "aov": str(aov) if aov is not None else None,
        },
        "checks": {"raw_vs_parsed_gross": True, "raw_vs_parsed_refund": True,
                   "net_identity": net == gross - refund, "unique_order_grain": True,
                   "row_count": True},
    }
