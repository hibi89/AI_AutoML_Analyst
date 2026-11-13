"""OFFLINE P85 aggregate-only package from prior local P70 source approval."""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import os

from backend.app.services.ontoinsight_p70 import InputSource
from backend.app.services.ontoinsight_p85_report import (
    build_offline_bundle, verify_offline_bundle,
)


def _read_bounded_file(path: Path, size=30 * 1024 * 1024) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= size:
        raise ValueError("Require regular local source with bounded size.")
    return path.read_bytes()


def _json(path: Path) -> dict:
    content = _read_bounded_file(path, 150_000)
    result = json.loads(content.decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Approval receipt must be a JSON object.")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="ONTOINSIGHT P85 offline output only, RELEASE HOLD")
    p.add_argument("--orders", type=Path, required=True)
    p.add_argument("--refunds", type=Path, required=True)
    p.add_argument("--channels", type=Path)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--ml-file", type=Path)
    p.add_argument("--ml-receipt", type=Path)
    p.add_argument("--out", type=Path, required=True, help="New never-overwritten ZIP")
    p.add_argument("--encoding", choices=["utf-8", "utf-8-sig", "cp949", "euc-kr", "cp932"], default="utf-8-sig")
    args = p.parse_args()
    out = args.out
    if out.suffix.lower() != ".zip" or out.is_symlink() or out.exists() or not out.parent.is_dir():
        raise ValueError("Output must be a fresh ZIP file in an existing directory.")
    sources = []
    for label in ("orders", "refunds", "channels"):
        source = getattr(args, label)
        if source is None:
            continue
        if source.suffix.lower() not in {".csv", ".xlsx"}:
            raise ValueError("CSV/XLSX required.")
        sources.append(InputSource(label, source.name, _read_bounded_file(source), encoding=args.encoding))
    if (args.ml_file is None) != (args.ml_receipt is None):
        raise ValueError("ML CSV + ML approval must be supplied together.")
    ml = None
    ml_receipt = None
    if args.ml_file is not None:
        if args.ml_file.suffix.lower() != ".csv":
            raise ValueError("ML input must be CSV.")
        ml = InputSource("ml", args.ml_file.name, _read_bounded_file(args.ml_file), encoding=args.encoding)
        ml_receipt = _json(args.ml_receipt)
    payload = build_offline_bundle(sources, _json(args.receipt), ml_source=ml, ml_receipt=ml_receipt)
    verified = verify_offline_bundle(payload)
    if not verified["verified"] or verified["release"] != "RELEASE_HOLD":
        raise ValueError("Independent delivery verification failed.")
    # O_EXCL prevents overwrite even if another process creates the path during
    # generation. No automatic unlink of a potentially replaced owner file.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(out), flags, 0o600)
    with os.fdopen(fd, "wb") as file:
        file.write(payload)
    print(json.dumps({"verified": True, "release": "RELEASE_HOLD",
                      "members": verified["members"], "net_sales": verified["net_sales"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
