"""Local-only ONTOINSIGHT P70 review/attest/run. All outputs are new files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.services.ontoinsight_p70 import (
    InputSource, approve_mapping, review_sources, run_approved,
)


def _sources(args: argparse.Namespace) -> list[InputSource]:
    collected = []
    for key in ("orders", "refunds", "channels"):
        path = getattr(args, key)
        if path is None:
            continue
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {".csv", ".xlsx"}:
            raise ValueError("Require regular, non-symlink authorized CSV/XLSX paths.")
        if not 0 < path.stat().st_size <= 30 * 1024 * 1024:
            raise ValueError("Source size outside 30 MiB per-file limit.")
        collected.append(InputSource(key, path.name, path.read_bytes(), encoding=args.encoding))
    return collected


def _read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 100_000:
        raise ValueError("Require regular local, bounded JSON input.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object.")
    return payload


def _write_new(path: Path, payload: dict) -> None:
    if path.is_symlink() or path.exists() or not path.parent.is_dir():
        raise ValueError("Choose a fresh output file in an existing directory.")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="ONTOINSIGHT P70 offline review (never sells or uploads data)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("review", "run"):
        sub = commands.add_parser(name)
        sub.add_argument("--orders", type=Path, required=True)
        sub.add_argument("--refunds", type=Path, required=True)
        sub.add_argument("--channels", type=Path)
        sub.add_argument("--encoding", default="utf-8-sig", choices=["utf-8", "utf-8-sig", "cp949", "euc-kr", "cp932"])
        if name == "run":
            sub.add_argument("--receipt", type=Path, required=True)
        sub.add_argument("--out", type=Path, required=True)
    attest = commands.add_parser("attest")
    attest.add_argument("--review", type=Path, required=True)
    attest.add_argument("--choices", type=Path, required=True, help="JSON with mapping, semantics, acknowledgements")
    attest.add_argument("--actor", required=True, help="Local reviewer reference, not authenticated identity")
    attest.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "review":
        result = review_sources(_sources(args))
    elif args.command == "attest":
        choices = _read_json(args.choices)
        if set(choices) != {"mapping", "semantics", "acknowledgements"}:
            raise ValueError("Explicit mapping, semantics and acknowledgements required.")
        result = approve_mapping(_read_json(args.review), choices["mapping"], choices["semantics"],
                                 actor=args.actor, acknowledgements=choices["acknowledgements"])
    else:
        result = run_approved(_sources(args), _read_json(args.receipt))
    _write_new(args.out, result)
    print("WROTE LOCAL JSON: RELEASE_HOLD; approval identity NOT VERIFIED; no external transfer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
