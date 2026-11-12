"""P6E51: one explicit offline batch review for BASIC/STANDARD/PREMIUM owner ZIPs.

Generates only metadata JSON and static HTML; never copies/extracts customer
ZIP contents, executes models, opens a server, or authorizes commercial sale.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path

from scripts.p6e50_owner_zip_review import (
    _no_links, _read_bounded_original, inspect_owner_zip, ReviewBlocked,
)

FORMAT = "automl_three_tier_owner_review_v1"
TIERS = ("BASIC", "STANDARD", "PREMIUM")
HUMAN_GATES = (
    ("actual_windows_customer", "실제 Windows 사용자 PC에서 ZIP/PDF 확인"),
    ("pdf_visual_and_korean_font", "한글·일본어 PDF 모든 페이지·글꼴·클리핑 육안 검수"),
    ("input_data_owner_authorization", "고객 원본 데이터 권리·비식별·활용 승인"),
    ("dependency_and_font_license", "PDF 내장 글꼴·의존성 원문·NOTICE·상업권 확인"),
    ("ml_and_prediction_interpretation", "과적합·누수·홀드아웃·모델 신뢰·재예측 검수"),
    ("buyer_delivery_and_terms", "실제 납품·수정·지원·환불 범위 및 단가 승인"),
    ("per_sku_owner_release", "BASIC/STANDARD/PREMIUM 각각 최종 출시 승인"),
)


def _block() -> ReviewBlocked:
    return ReviewBlocked("THREE_TIER_REVIEW_BLOCKED")


def _new_file(path: Path, suffix: str, forbidden: set[Path]) -> None:
    if (not path.is_absolute() or path.suffix.lower() != suffix
            or path in forbidden or path.exists() or path.is_symlink()):
        raise _block()
    _no_links(path)
    if not path.parent.is_dir():
        raise _block()


def _review_html(report: dict) -> str:
    cells = []
    for row in report["tiers"]:
        # Even metadata-only fields are escaped: this HTML is review data, not a JS app.
        cells.append("<tr><th scope='row'>" + escape(row["tier"]) + "</th>"
                     + "<td>" + str(row["pdf_pages"]) + "</td>"
                     + "<td><code>" + escape(row["zip_sha256"]) + "</code></td>"
                     + "<td>" + str(row["zip_members"]) + "</td>"
                     + "<td>자동 파일 구조 검사 통과 / 판매 보류</td></tr>")
    gates = "".join("<li><span aria-hidden='true'>□</span> " + escape(label)
                    + " <strong>미검증</strong></li>" for _, label in HUMAN_GATES)
    return """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; connect-src 'none'; style-src 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>AI AutoML Analyst — 소유자 납품 검토표 (출시 보류)</title>
<style>
:root{font:15px/1.5 system-ui,'Malgun Gothic',sans-serif;color:#182a40;background:#f6f8fa}
body{max-width:1020px;margin:0 auto;padding:24px}
header,section{background:#fff;border:1px solid #dce3ea;border-radius:12px;margin-bottom:16px;padding:20px}
h1{margin:0 0 10px;font-size:1.45rem}h2{font-size:1.12rem;margin:0 0 12px}
.warning{font-weight:700;color:#9b341e}
table{width:100%;border-collapse:collapse}th,td{text-align:left;border:1px solid #dce3ea;padding:10px;vertical-align:top}
thead{background:#edf4f9}code{font-size:.8em;overflow-wrap:anywhere}
li{padding:5px 0}p{margin:10px 0}
@media print{body{padding:0;background:#fff}header,section{border:0;break-inside:avoid}h1{font-size:17pt}}
</style></head><body>
<header><h1>AI AutoML Analyst | 납품 후보 3종 로컬 검토표</h1>
<p class="warning">구조·해시·PDF 페이지 확인은 판매 승인이나 시각·법적 검수가 아닙니다.</p>
<p>원본 데이터, 고객 ZIP, 모델, 라이선스 원문은 이 HTML에 포함하지 않습니다.
이 문서의 항목은 사람의 실제 점검이 완료될 때까지 모두 미검증입니다.</p></header>
<section><h2>독립 상품별 구조 증거</h2>
<table><thead><tr><th scope="col">상품</th><th scope="col">PDF 페이지</th>
<th scope="col">ZIP SHA-256</th><th scope="col">파일 수</th><th scope="col">상태</th></tr></thead>
<tbody>""" + "".join(cells) + """</tbody></table></section>
<section><h2>출시 전 사람의 확인 사항 — 전부 미검증</h2>
<ol>""" + gates + """</ol>
<p class="warning">BASIC / STANDARD / PREMIUM 모두 판매 금지 · RELEASE HOLD</p></section>
<footer>파일은 소유자가 명시적으로 지정한 로컬 새 경로에만 생성됩니다. 외부 요청·JavaScript 없음.</footer>
</body></html>
"""


def create_three_tier_review(
    sources: dict[str, tuple[Path, str]], output_json: Path, output_html: Path
) -> dict:
    if not isinstance(sources, dict) or set(sources) != set(TIERS):
        raise _block()
    paths = [pair[0] for pair in sources.values()]
    if any(not isinstance(x, Path) for x in paths) or len(set(paths)) != 3:
        raise _block()
    forbidden = set(paths) | {output_json, output_html}
    if output_json == output_html:
        raise _block()
    _new_file(output_json, ".json", set(paths) | {output_html})
    _new_file(output_html, ".html", set(paths) | {output_json})
    entries = []
    for tier in TIERS:
        source, expected = sources[tier]
        entries.append(inspect_owner_zip(source, tier, expected))
    if len({row["zip_sha256"] for row in entries}) != len(entries):
        raise _block()
    # Bind to actual owner ZIPs again immediately before publishing metadata.
    for tier in TIERS:
        path, _ = sources[tier]
        if sha256(_read_bounded_original(path)).hexdigest() != entries[TIERS.index(tier)]["zip_sha256"]:
            raise _block()
    report = {
        "format": FORMAT,
        "status": "THREE_TIER_STRUCTURE_VERIFIED_SEPARATE_HUMAN_REVIEW_REQUIRED",
        "tiers": [{
            "tier": row["tier"],
            "zip_sha256": row["zip_sha256"],
            "zip_bytes": row["zip_bytes"],
            "pdf_sha256": row["pdf_sha256"],
            "pdf_pages": row["pdf_pages"],
            "zip_members": row["zip_members"],
            "shipment_integrity": "VERIFIED",
            "visual_quality": "NOT_VERIFIED",
            "license_and_data_rights": "NOT_VERIFIED",
            "customer_sale_approved": False,
        } for row in entries],
        "human_gates": {key: "NOT_VERIFIED" for key, _ in HUMAN_GATES},
        "actual_owner_windows_run": False,
        "contents_or_local_paths_in_review": False,
        "every_sku_sale_approved": False,
    }
    # Preserve partial files for owner-only manual HOLD. Never unlink by
    # pathname after failure: another writer may replace an output entry.
    for path, content in (
        (output_json, json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"),
        (output_html, _review_html(report)),
    ):
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(content)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline 3-tier owner QA JSON/HTML (no sale)")
    for tier in TIERS:
        parser.add_argument("--" + tier.lower(), type=Path, required=True)
        parser.add_argument("--" + tier.lower() + "-sha256", required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-html", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        sources = {
            tier: (getattr(args, tier.lower()), getattr(args, tier.lower() + "_sha256"))
            for tier in TIERS
        }
        review = create_three_tier_review(sources, args.out_json, args.out_html)
        print("THREE_TIER_OWNER_STRUCTURE_PASS_RELEASE_BLOCKED")
        for row in review["tiers"]:
            print(row["tier"] + "_ZIP_SHA256=" + row["zip_sha256"])
        print("EVERY_SKU_SALE_APPROVED=False")
        return 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        print("THREE_TIER_OWNER_REVIEW_BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
