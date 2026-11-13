"""ONTOINSIGHT P70: bounded local multi-source intake, attested mapping, exact KPI.

Neither approval nor this module authenticates an actor. An approval receipt is a
local, explicit attestation bound to source bytes and mapping; not a signature.
No source row, raw identifier, or customer file is persisted by this module.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import PurePath
import re
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from backend.app.services.basic_report import MAX_COLUMNS, MAX_ROWS, MAX_UPLOAD_BYTES
from backend.app.services.ontoinsight_p50 import _amount, _candidate_roles, SENSITIVE_TOKENS
from backend.app.services.tabular_input import read_uploaded_table

VERSION = "ontoinsight.p70.local.v1"
_ALLOWED = frozenset({"orders", "refunds", "channels"})
_ROLE_RULES = {
    "orders": {"order_id", "sales", "channel"},
    "refunds": {"order_id", "refund"},
    "channels": {"order_id", "channel"},
}
_REQUIRED = {
    "orders": {"order_id", "sales"},
    "refunds": {"order_id", "refund"},
    "channels": {"order_id", "channel"},
}
_ATTESTATIONS = frozenset({
    "data_use_authorized", "business_meaning_confirmed", "privacy_reviewed",
    "gross_sales_basis_confirmed", "refund_event_basis_confirmed", "tax_policy_confirmed",
})
_ENCODING = frozenset({"utf-8", "utf-8-sig", "cp949", "euc-kr", "cp932"})
_COMMITMENT_KEYS = frozenset({"currency", "tax_basis", "sales_basis", "refund_basis", "time_basis"})


@dataclass(frozen=True)
class InputSource:
    source_id: str
    filename: str
    content: bytes
    encoding: str = "utf-8-sig"


def _stable_hash(data: Any) -> str:
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _limited_xlsx_check(data: bytes) -> None:
    """Reject formula/external link/hidden source that cached-value reads can miss."""
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > 250:
                raise ValueError("XLSX part count outside approved limit.")
            if sum(i.file_size for i in infos) > 80 * 1024 * 1024:
                raise ValueError("XLSX expanded size limit exceeded.")
            if any(i.file_size > 50 * 1024 * 1024 for i in infos):
                raise ValueError("XLSX contains oversized individual part.")
            normalized = [i.filename.replace("\\", "/").lower() for i in infos]
            if len(normalized) != len(set(normalized)):
                raise ValueError("Duplicate/case-colliding XLSX parts blocked.")
            sheets = [i for i in infos if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", i.filename.lower())]
            if len(sheets) != 1:
                raise ValueError("P70 requires exactly one visible XLSX worksheet.")
            if any("externallinks" in n or "vbaproject" in n or n.endswith(".bin") for n in normalized):
                raise ValueError("External links and macro binary XLSX parts blocked.")
            for item in infos:
                name = item.filename.lower()
                if not (name.endswith(".rels") or name == "xl/workbook.xml" or item in sheets):
                    continue
                try:
                    doc = ET.fromstring(archive.read(item))
                except ET.ParseError as exc:
                    raise ValueError("Corrupt or malformed XLSX XML.") from exc
                for node in doc.iter():
                    local = node.tag.rsplit("}", 1)[-1]
                    if local in {"f", "externalLink", "mergeCells"}:
                        raise ValueError("Formula, external reference or merged cells require review.")
                    if local == "sheet" and node.attrib.get("state", "visible") != "visible":
                        raise ValueError("Hidden worksheets require review.")
                    if node.attrib.get("TargetMode", "").lower() == "external":
                        raise ValueError("External workbook relationship rejected.")
    except BadZipFile as exc:
        raise ValueError("Invalid XLSX archive.") from exc


def _raw_csv_rows(data: bytes, encoding: str) -> tuple[list[str], list[dict[str, Any]]]:
    if encoding not in _ENCODING:
        raise ValueError("Explicit, supported CSV encoding is required.")
    try:
        with StringIO(data.decode(encoding), newline="") as stream:
            parsed = csv.reader(stream, strict=True)
            header = next(parsed, None)
            if not header or len(header) > MAX_COLUMNS or len(set(header)) != len(header):
                raise ValueError("Missing/duplicate/oversize CSV header.")
            if any(not c.strip() for c in header):
                raise ValueError("Blank CSV column name.")
            rows = []
            for row in parsed:
                if not row or len(row) != len(header):
                    raise ValueError("Blank/ragged CSV row; no silent row discard.")
                rows.append(dict(zip(header, row, strict=True)))
                if len(rows) > MAX_ROWS:
                    raise ValueError("CSV row limit exceeded.")
            return header, rows
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("CSV encoding or row syntax invalid.") from exc


def _raw_xlsx_rows(data: bytes) -> tuple[list[str], list[dict[str, Any]]]:
    from openpyxl import load_workbook

    workbook = load_workbook(BytesIO(data), read_only=True, data_only=False, keep_links=False)
    try:
        if len(workbook.worksheets) != 1 or workbook.worksheets[0].sheet_state != "visible":
            raise ValueError("P70 requires one visible worksheet.")
        sheet = workbook.worksheets[0]
        sheet.reset_dimensions()
        it = sheet.iter_rows(values_only=True)
        headers = next(it, None)
        if not headers or len(headers) > MAX_COLUMNS or any(not isinstance(c, str) or not c.strip() for c in headers):
            raise ValueError("Invalid XLSX header.")
        if len(set(headers)) != len(headers):
            raise ValueError("Duplicate XLSX column name.")
        rows = []
        for values in it:
            if len(values) > len(headers) and any(x is not None for x in values[len(headers):]):
                raise ValueError("Excel values extend beyond header.")
            if not values or all(x is None for x in values):
                raise ValueError("Blank XLSX row; no silent row discard.")
            if len(rows) >= MAX_ROWS:
                raise ValueError("XLSX row limit exceeded.")
            padded = list(values[:len(headers)]) + [None] * max(0, len(headers) - len(values))
            rows.append(dict(zip(headers, padded, strict=True)))
        return list(headers), rows
    finally:
        workbook.close()


def _read(source: InputSource) -> dict[str, Any]:
    if (source.source_id not in _ALLOWED or not source.filename
            or PurePath(source.filename).name != source.filename
            or "\\" in source.filename or "\x00" in source.filename):
        raise ValueError("Invalid source ID or filename.")
    data = source.content
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_UPLOAD_BYTES:
        raise ValueError("Input is empty, non-binary or exceeds 30 MiB.")
    suffix = source.filename.lower().rsplit(".", 1)[-1]
    if suffix not in {"csv", "xlsx"}:
        raise ValueError("Only CSV and XLSX are supported at P70.")
    if suffix == "xlsx":
        _limited_xlsx_check(data)
    frame = read_uploaded_table(data, source.filename, csv_encoding=source.encoding)
    if suffix == "csv":
        header, rows = _raw_csv_rows(data, source.encoding)
    else:
        header, rows = _raw_xlsx_rows(data)
    if len(rows) != len(frame) or header != list(frame.columns):
        raise ValueError("Original parser and raw source row/schema mismatch.")
    if any(any(token in col.casefold() for token in SENSITIVE_TOKENS) for col in header):
        raise ValueError("Sensitive named columns require separate privacy scope approval; P70 refuses them.")
    return {"source_id": source.source_id, "format": suffix, "sha256": sha256(data).hexdigest(),
            "bytes": len(data), "rows": len(rows), "columns": header, "records": rows}


def _load(sources: list[InputSource]) -> dict[str, dict[str, Any]]:
    if len(sources) not in {2, 3} or {s.source_id for s in sources} not in ({"orders", "refunds"}, _ALLOWED):
        raise ValueError("Provide exactly orders + refunds, optionally one channels source.")
    if sum(len(s.content) if isinstance(s.content, bytes) else 0 for s in sources) > 30 * 1024 * 1024:
        raise ValueError("Combined source size exceeds 30 MiB.")
    return {s.source_id: _read(s) for s in sources}


def _registry(loaded: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {name: {k: row[k] for k in ("sha256", "rows", "format", "columns", "bytes")}
            for name, row in sorted(loaded.items())}


def review_sources(sources: list[InputSource]) -> dict[str, Any]:
    """Return schema metadata only; no business KPI or raw identifier/value."""
    loaded = _load(sources)
    registry = _registry(loaded)
    return {
        "contract": VERSION, "sources": registry,
        "source_set_digest": _stable_hash(registry),
        "candidates": {name: {col: _candidate_roles(col) for col in row["columns"]}
                       for name, row in loaded.items()},
        "relationship_candidates": ["refunds.order_id -> orders.order_id (many_to_one; review required)"] +
                                   (["channels.order_id -> orders.order_id (one_to_one; review required)"]
                                    if "channels" in loaded else []),
        "approval": "REVIEW_HOLD", "kpi": "NOT_COMPUTED", "ml": "ML_NOT_SUITABLE",
        "raw_rows_exported": False,
    }


def _check_mapping(mapping: dict[str, dict[str, str]], loaded: dict[str, dict[str, Any]]) -> None:
    if not isinstance(mapping, dict) or set(mapping) != set(loaded):
        raise ValueError("Mapping must cover every input source exactly.")
    for source_id, roles in mapping.items():
        if not isinstance(roles, dict) or not _REQUIRED[source_id].issubset(roles) or not set(roles) <= _ROLE_RULES[source_id]:
            raise ValueError("Missing/unsupported source role mapping.")
        if any(not isinstance(col, str) or col not in loaded[source_id]["columns"] for col in roles.values()):
            raise ValueError("Mapped column absent from source.")
        if len(set(roles.values())) != len(roles):
            raise ValueError("One column cannot represent multiple roles.")
    if "channels" in loaded and "channel" in mapping["orders"]:
        raise ValueError("Channel column must have one authoritative source.")
    if "channels" not in loaded and "channel" not in mapping["orders"]:
        raise ValueError("A channel role in orders or channels source is required for this P70 KPI scope.")


def _check_semantics(semantics: dict[str, str]) -> None:
    if not isinstance(semantics, dict) or set(semantics) != _COMMITMENT_KEYS:
        raise ValueError("Currency, tax, sales, refunds and time meaning require explicit approval.")
    expected = {"currency": {"KRW", "USD"}, "tax_basis": {"included", "excluded"},
                "sales_basis": {"gross_paid"}, "refund_basis": {"positive_refund_events"},
                "time_basis": {"no_period_reporting"}}
    if any(semantics[key] not in values for key, values in expected.items()):
        raise ValueError("Unsupported business meaning: review required.")


def approve_mapping(review: dict[str, Any], mapping: dict[str, dict[str, str]],
                    semantics: dict[str, str], *, actor: str,
                    acknowledgements: dict[str, bool]) -> dict[str, Any]:
    """Local owner/operator attestation, NOT a verified identity or e-signature."""
    if not isinstance(review, dict) or review.get("contract") != VERSION or review.get("approval") != "REVIEW_HOLD":
        raise ValueError("Only a valid pending P70 review may be attested.")
    registry = review.get("sources")
    if not isinstance(registry, dict) or review.get("source_set_digest") != _stable_hash(registry):
        raise ValueError("Review source registry was modified.")
    pseudo = {name: {"columns": item["columns"]} for name, item in registry.items()}
    _check_mapping(mapping, pseudo)
    _check_semantics(semantics)
    if not isinstance(actor, str) or not 1 <= len(actor.strip()) <= 60:
        raise ValueError("Explicit non-empty local reviewer reference required.")
    if not isinstance(acknowledgements, dict) or set(acknowledgements) != _ATTESTATIONS or any(v is not True for v in acknowledgements.values()):
        raise ValueError("All explicit legal/meaning/privacy attestations must be affirmative.")
    fields = {"version": VERSION, "source_set_digest": review["source_set_digest"],
              "mapping": mapping, "semantics": semantics, "actor_ref": actor.strip(),
              "acknowledgements": acknowledgements, "revision": 1}
    return {**fields, "state": "APPROVED_LOCAL_ATTESTATION", "mapping_digest": _stable_hash(fields),
            "identity_verified": False, "legal_signature": False}


def _verify_receipt(loaded: dict[str, dict[str, Any]], receipt: dict[str, Any]) -> None:
    if not isinstance(receipt, dict) or receipt.get("state") != "APPROVED_LOCAL_ATTESTATION":
        raise ValueError("Explicit approved local receipt required.")
    registry = _registry(loaded)
    if receipt.get("source_set_digest") != _stable_hash(registry):
        raise ValueError("Source digest or schema drift; approval invalidated.")
    fields = {k: receipt.get(k) for k in ("version", "source_set_digest", "mapping", "semantics", "actor_ref", "acknowledgements", "revision")}
    if fields["version"] != VERSION or fields["revision"] != 1 or receipt.get("mapping_digest") != _stable_hash(fields):
        raise ValueError("Approval receipt or mapping digest was modified.")
    _check_mapping(fields["mapping"], loaded)
    _check_semantics(fields["semantics"])
    if not isinstance(fields["actor_ref"], str) or not fields["actor_ref"].strip():
        raise ValueError("Reviewer reference missing.")
    ack = fields["acknowledgements"]
    if not isinstance(ack, dict) or set(ack) != _ATTESTATIONS or any(v is not True for v in ack.values()):
        raise ValueError("Approval attestations missing.")


def _key(value: Any) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("Missing relation key; join blocked.")
    if not isinstance(value, str):
        raise ValueError("Non-text relation key is ambiguous; provide text identifiers.")
    key = str(value).strip()
    if not key or len(key) > 120 or any(ord(ch) < 32 for ch in key):
        raise ValueError("Invalid relation key.")
    return key


def _channel(value: Any) -> str:
    if value is None:
        raise ValueError("Channel missing; left join blocked.")
    label = str(value).strip()
    if not label or len(label) > 32 or not all(c.isalnum() or c in {"_", "-", " "} for c in label):
        raise ValueError("Unsafe/ambiguous channel label; review required.")
    return label


def run_approved(sources: list[InputSource], receipt: dict[str, Any]) -> dict[str, Any]:
    """Exact deterministic order-grain report; never a prediction or legal approval."""
    loaded = _load(sources)
    _verify_receipt(loaded, receipt)
    mapping = receipt["mapping"]
    orders = loaded["orders"]["records"]
    refunds = loaded["refunds"]["records"]
    om, rm = mapping["orders"], mapping["refunds"]
    order_ledger: dict[str, dict[str, Any]] = {}
    gross = Decimal("0")
    for row in orders:
        key = _key(row[om["order_id"]])
        if key in order_ledger:
            raise ValueError("Duplicate order ID: 1:1 order grain violated.")
        sale = _amount(row[om["sales"]])
        gross += sale
        entry = {"sale": sale, "refund": Decimal("0")}
        if "channel" in om:
            entry["channel"] = _channel(row[om["channel"]])
        order_ledger[key] = entry
    refunded = Decimal("0")
    for row in refunds:
        key = _key(row[rm["order_id"]])
        if key not in order_ledger:
            raise ValueError("Refund foreign-key missing in orders; join blocked.")
        amount = _amount(row[rm["refund"]])
        refunded += amount
        order_ledger[key]["refund"] += amount
    if "channels" in loaded:
        cm = mapping["channels"]
        seen: set[str] = set()
        for row in loaded["channels"]["records"]:
            key = _key(row[cm["order_id"]])
            if key in seen:
                raise ValueError("Duplicate channels order ID: 1:1 join violated.")
            seen.add(key)
            if key not in order_ledger:
                raise ValueError("Channel foreign-key missing in orders; join blocked.")
            order_ledger[key]["channel"] = _channel(row[cm["channel"]])
        if seen != set(order_ledger):
            raise ValueError("Unmatched orders in channel mapping; join blocked.")
    net_by_channel: dict[str, dict[str, Any]] = {}
    for row in order_ledger.values():
        if row["refund"] > row["sale"]:
            raise ValueError("Refund exceeds order gross: review required.")
        channel = row["channel"]
        entry = net_by_channel.setdefault(channel, {"gross": Decimal("0"), "refund": Decimal("0"), "count": 0})
        entry["gross"] += row["sale"]
        entry["refund"] += row["refund"]
        entry["count"] += 1
    net = gross - refunded
    if (sum((v["gross"] for v in net_by_channel.values()), Decimal("0")) != gross
            or sum((v["refund"] for v in net_by_channel.values()), Decimal("0")) != refunded
            or sum((v["count"] for v in net_by_channel.values()), 0) != len(orders)):
        raise ValueError("Source and joined channel totals do not reconcile.")
    breakdown = []
    for label, entry in sorted(net_by_channel.items()):
        breakdown.append({"channel_ref": "channel_" + sha256(label.encode("utf-8")).hexdigest()[:12],
                          "orders": entry["count"], "gross_sales": str(entry["gross"]),
                          "refund_amount": str(entry["refund"]),
                          "net_sales": str(entry["gross"] - entry["refund"])})
    count = len(order_ledger)
    return {
        "contract": VERSION, "scope": "LOCAL_EXPLICIT_ATTESTATION_NOT_VERIFIED_CUSTOMER_SIGNATURE",
        "source_set_digest": receipt["source_set_digest"], "mapping_digest": receipt["mapping_digest"],
        "provenance": _registry(loaded), "formula_version": "gross_paid_minus_refund_events.v1",
        "currency": receipt["semantics"]["currency"], "tax_basis": receipt["semantics"]["tax_basis"],
        "approval": "APPROVED_LOCAL_ATTESTATION", "identity_verified": False,
        "metrics": {"order_count": count, "refund_event_count": len(refunds),
                    "gross_sales": str(gross), "refund_amount": str(refunded),
                    "net_sales": str(net),
                    "aov_net": str((net / count).quantize(Decimal("0.01"))) if count else None},
        "channel_aggregates": breakdown,
        "audit": {"source_rows_preserved": all(len(loaded[name]["records"]) == info["rows"]
                                               for name, info in loaded.items()),
                  "order_grain_preserved": count == len(orders),
                  "refund_events_preserved": len(refunds) == loaded["refunds"]["rows"],
                  "source_money_reconciled": sum((r["sale"] for r in order_ledger.values()), Decimal("0")) == gross
                                             and sum((r["refund"] for r in order_ledger.values()), Decimal("0")) == refunded,
                  "channel_reconciled": sum((Decimal(r["net_sales"]) for r in breakdown), Decimal("0")) == net,
                  "originals_unmodified": all(sha256(src.content).hexdigest() == loaded[src.source_id]["sha256"] for src in sources)},
        "ml": "ML_NOT_SUITABLE_NOT_RUN", "prediction": None,
        "release": "RELEASE_HOLD", "raw_rows_exported": False,
    }
