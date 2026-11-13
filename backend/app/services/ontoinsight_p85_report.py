"""P85 offline, source-revalidated aggregate evidence ZIP (no source rows).

Exact JSON + static HTML + safe XLSX + PDF + hashes; no network, JS,
customer records, model pickle or external font distribution.
"""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from html import escape
from io import BytesIO
import json
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

from backend.app.services.ontoinsight_p70 import InputSource, run_approved, _stable_hash
from backend.app.services.ontoinsight_p85_ml import evaluate_approved_ml

REPORT_VERSION = "ontoinsight.report.p85.v1"
_MEMBERS = frozenset({"summary.json", "report.html", "report.xlsx", "report.pdf",
                      "README.txt", "manifest.json"})
_MAX_BYTES = 12 * 1024 * 1024


def _json(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _static_html(summary: dict) -> bytes:
    kpis = summary["kpi"]["metrics"]
    status = summary["ml"]["status"]
    rows = "".join(
        "<tr><td>" + escape(key) + "</td><td>" + escape(str(val)) + "</td></tr>"
        for key, val in kpis.items()
    )
    groups = "".join(
        "<tr><td>" + escape(row["channel_ref"]) + "</td><td>" +
        escape(str(row["orders"])) + "</td><td>" + escape(row["net_sales"]) + "</td></tr>"
        for row in summary["kpi"]["channel_aggregates"]
    )
    page = (
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
        "img-src data:; style-src 'unsafe-inline'; form-action 'none'; base-uri 'none'\">"
        "<title>ONTOINSIGHT AX | Offline evidence</title><style>"
        "body{font-family:system-ui,sans-serif;max-width:800px;margin:36px auto;color:#12283b}"
        "h1{font-size:24px}table{border-collapse:collapse;width:100%;margin:15px 0}"
        "th,td{padding:9px 14px;border:1px solid #c9d3df;text-align:left}"
        "th{background:#e9eff6}.hold{background:#f1f3f6;padding:14px;border-radius:6px}"
        "</style></head><body><h1>ONTOINSIGHT AX — 근거 기반 데이터 보고서 (검토용)</h1>"
        "<p class='hold'>RELEASE HOLD · 합성 또는 로컬 확인 데이터 · 고객 최종 승인 아님</p>"
        "<h2>검증된 집계</h2><table><tr><th>항목</th><th>수치</th></tr>" + rows + "</table>"
        "<h2>채널별 순매출</h2><table><tr><th>익명 채널 참조</th>"
        "<th>주문수</th><th>순매출</th></tr>" + groups + "</table>"
        "<h2>모델 판단</h2><p>" + escape(status) + "</p>"
        "<p>관찰 사실과 수학적 파생 지표만 표시합니다. 인과관계 또는 예상 수익을 보장하지 않습니다.</p>"
        "<p>Source set SHA: " + escape(summary["kpi"]["source_set_digest"]) +
        "</p><p>Approval mapping SHA: " + escape(summary["kpi"]["mapping_digest"]) +
        "</p><p>Original data is not included in this package.</p></body></html>"
    )
    return page.encode("utf-8")


def _xlsx(summary: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    overview = wb.active
    overview.title = "Summary"
    overview.append(["ONTOINSIGHT AX — LOCAL REVIEW ONLY", "RELEASE HOLD"])
    overview.append(["Source digest", summary["kpi"]["source_set_digest"]])
    overview.append(["Mapping digest", summary["kpi"]["mapping_digest"]])
    overview.append(["ML status", summary["ml"]["status"]])
    overview.append(["Metric", "Value"])
    for key, value in summary["kpi"]["metrics"].items():
        # No raw data or potentially interpreted formula is written.
        # All numeric values are derived from Decimal-validated aggregate strings.
        cell_value = value
        if key == "aov_net" and value is None:
            cell_value = None
        elif key in {"order_count", "refund_event_count"}:
            cell_value = int(value)
        elif value is not None:
            cell_value = float(Decimal(str(value)))
        overview.append([key, cell_value])
    channels = wb.create_sheet("Channels")
    channels.append(["Channel ref", "Orders", "Gross", "Refund", "Net"])
    for row in summary["kpi"]["channel_aggregates"]:
        channels.append([row["channel_ref"], int(row["orders"]),
                         float(Decimal(row["gross_sales"])),
                         float(Decimal(row["refund_amount"])),
                         float(Decimal(row["net_sales"]))])
    if len(summary["kpi"]["channel_aggregates"]) > 0:
        plot = BarChart()
        plot.title = "Net sales by pseudonymous channel"
        plot.y_axis.title = "Amount"
        plot.x_axis.title = "Channel"
        last = channels.max_row
        plot.add_data(Reference(channels, min_col=5, min_row=1, max_row=last), titles_from_data=True)
        plot.set_categories(Reference(channels, min_col=1, min_row=2, max_row=last))
        channels.add_chart(plot, "G2")
    for sheet in wb.worksheets:
        sheet.freeze_panes = "A2"
        sheet.column_dimensions["A"].width = 40
        sheet.column_dimensions["B"].width = 72 if sheet.title == "Summary" else 20
        sheet["A1"].font = Font(color="FFFFFF", bold=True)
        sheet["A1"].fill = PatternFill(fill_type="solid", fgColor="223D5B")
    out = BytesIO()
    wb.save(out)
    wb.close()
    return out.getvalue()


def _pdf(summary: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas

    out = BytesIO()
    canvas = Canvas(out, pagesize=A4, pageCompression=0)
    canvas.setTitle("ONTOINSIGHT AX source-bound offline report - RELEASE HOLD")
    width, height = A4
    canvas.setFont("Helvetica-Bold", 17)
    canvas.drawString(42, height-52, "ONTOINSIGHT AX - SOURCE-BOUND REPORT")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(42, height-76, "RELEASE HOLD - local operator review, not an audited client delivery")
    pos = height-117
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(42,pos,"Derived, independently checked metrics")
    canvas.setFont("Helvetica", 10)
    for name,val in summary["kpi"]["metrics"].items():
        pos -= 21
        canvas.drawString(50,pos,f"{name}: {val}")
    pos -= 40
    canvas.drawString(42,pos, "Channel references (pseudonymous; original identifiers excluded)")
    for i, group in enumerate(summary["kpi"]["channel_aggregates"]):
        pos -= 22
        canvas.drawString(50,pos, f"Group {i+1}: orders={group['orders']} net={group['net_sales']}")
        bar = min(200.0, max(0.0, float(Decimal(group["net_sales"])) / max(1.0, float(Decimal(summary["kpi"]["metrics"]["gross_sales"]))) * 200.0))
        canvas.rect(300, pos, bar, 10, stroke=0, fill=1)
    pos -= 40
    canvas.drawString(42,pos, "ML: "+summary["ml"]["status"])
    canvas.drawString(42,pos-25,"No causal or revenue guarantee. No source rows are distributed.")
    canvas.drawString(42,pos-50,"Source SHA: "+summary["kpi"]["source_set_digest"][:35])
    canvas.save()
    return out.getvalue()


def build_offline_bundle(sources: list[InputSource], receipt: dict,
                         *, ml_source: InputSource | None = None,
                         ml_receipt: dict | None = None) -> bytes:
    """Runs original P70 checks again before packaging, never trusts caller KPIs."""
    if (ml_source is None) != (ml_receipt is None):
        raise ValueError("ML source and approval receipt must be supplied together.")
    kpi = run_approved(sources, receipt)
    ml = evaluate_approved_ml(ml_source, ml_receipt) if ml_source is not None else {
        "status": "ML_NOT_REQUESTED", "model_fitted": False, "prediction": None
    }
    summary = {
        "contract": REPORT_VERSION, "release": "RELEASE_HOLD",
        "kpi": kpi, "ml": ml,
        "evidence_layers": ["OBSERVED_SOURCE_DIGEST", "DERIVED_VERIFIED_KPI",
                            "ML_EVALUATION_IF_APPROVED", "HYPOTHESIS_NOT_ESTABLISHED"],
        "raw_source_rows_included": False, "customer_approval_authenticated": False,
    }
    parts = {
        "summary.json": _json(summary),
        "report.html": _static_html(summary),
        "report.xlsx": _xlsx(summary),
        "report.pdf": _pdf(summary),
        "README.txt": b"ONTOINSIGHT P85 offline audit. RELEASE HOLD. No source rows. Keep originals offline. Confirm rights and actual Windows acceptance separately.\n",
    }
    manifest = {
        "contract": REPORT_VERSION, "release": "RELEASE_HOLD",
        "sha256": {name: sha256(content).hexdigest() for name, content in sorted(parts.items())},
        "source_set_digest": kpi["source_set_digest"],
        "mapping_digest": kpi["mapping_digest"],
    }
    parts["manifest.json"] = _json(manifest)
    buf = BytesIO()
    with ZipFile(buf, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in sorted(parts.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, content)
    if len(buf.getvalue()) > _MAX_BYTES:
        raise ValueError("Oversized report package refused.")
    return buf.getvalue()


def verify_offline_bundle(data: bytes) -> dict:
    """Independent package/member/XLSX/PDF/JSON vs source-bound KPI check."""
    from openpyxl import load_workbook
    from pypdf import PdfReader

    if not isinstance(data, bytes) or not 0 < len(data) <= _MAX_BYTES:
        raise ValueError("Invalid package length.")
    with ZipFile(BytesIO(data)) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(infos) != len(_MEMBERS) or set(names) != _MEMBERS or len(set(names)) != len(names):
            raise ValueError("Missing/duplicate/extra ZIP members.")
        if any(info.file_size > 2 * 1024 * 1024 or info.flag_bits & 1 for info in infos):
            raise ValueError("Unsafe oversized/encrypted ZIP member.")
        parts = {name: archive.read(name) for name in names}
    manifest = json.loads(parts["manifest.json"])
    summary = json.loads(parts["summary.json"])
    expected = _MEMBERS - {"manifest.json"}
    if manifest.get("contract") != REPORT_VERSION or set(manifest.get("sha256", {})) != expected:
        raise ValueError("Invalid report manifest.")
    if any(sha256(parts[name]).hexdigest() != manifest["sha256"][name] for name in expected):
        raise ValueError("Report manifest hash mismatch.")
    kpi = summary.get("kpi")
    if (summary.get("contract") != REPORT_VERSION or summary.get("release") != "RELEASE_HOLD"
            or kpi.get("source_set_digest") != manifest.get("source_set_digest")
            or kpi.get("mapping_digest") != manifest.get("mapping_digest")
            or not all(kpi.get("audit", {}).values())):
        raise ValueError("Source, mapping or reconciliation audit mismatch.")
    total = sum((Decimal(r["net_sales"]) for r in kpi["channel_aggregates"]), Decimal("0"))
    if total != Decimal(kpi["metrics"]["net_sales"]):
        raise ValueError("Independent channel net total mismatch.")
    if Decimal(kpi["metrics"]["gross_sales"]) - Decimal(kpi["metrics"]["refund_amount"]) != total:
        raise ValueError("Independent gross/refund net identity mismatch.")
    page = parts["report.html"].decode("utf-8")
    if "<script" in page.lower() or kpi["metrics"]["net_sales"] not in page:
        raise ValueError("Static HTML report content mismatch.")
    book = load_workbook(BytesIO(parts["report.xlsx"]), read_only=True, data_only=False)
    try:
        sheet = book["Summary"]
        values = {str(row[0]): row[1] for row in sheet.iter_rows(min_row=6, max_col=2, values_only=True)}
        if Decimal(str(values["net_sales"])) != total:
            raise ValueError("XLSX report net mismatch.")
    finally:
        book.close()
    extracted = "\n".join(page.extract_text() for page in PdfReader(BytesIO(parts["report.pdf"])).pages)
    if "net_sales: " + kpi["metrics"]["net_sales"] not in extracted:
        raise ValueError("PDF report net mismatch.")
    return {
        "verified": True, "contract": REPORT_VERSION,
        "source_set_digest": kpi["source_set_digest"],
        "members": len(_MEMBERS), "net_sales": str(total),
        "ml_status": summary["ml"]["status"], "release": "RELEASE_HOLD",
    }
