"""P6E50: bounded owner-only ZIP/PDF evidence review, never a sales approval.

Use only ZIPs created by this repository from owner-authorized deidentified data.
Do not execute or extract archive contents. Never load a serialized model.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile

from pypdf import PdfReader
from scripts.p6e6_delivery_policy import verify_shipping_zip

FORMAT = "automl_local_owner_zip_preflight_v1"
MAX_ARCHIVE = 72 * 1024 * 1024
MAX_MEMBER = 24 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_MEMBERS = 80
MAX_RATIO = 250
PAGE_BOUNDS = {"BASIC": (6, 8), "STANDARD": (8, 12), "PREMIUM": (10, 15)}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ReviewBlocked(ValueError):
    """No approval or receipt can be inferred from invalid evidence."""


def _block() -> ReviewBlocked:
    return ReviewBlocked("LOCAL_OWNER_DELIVERY_REVIEW_BLOCKED")


def _no_links(path: Path) -> None:
    if not path.is_absolute():
        raise _block()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise _block()


def _read_bounded_original(path: Path) -> bytes:
    _no_links(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_ARCHIVE:
        raise _block()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
                != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)):
            raise _block()
        with os.fdopen(os.dup(fd), "rb") as stream:
            raw = stream.read(MAX_ARCHIVE + 1)
        after = os.fstat(fd)
        latest = path.lstat()
        if (len(raw) != opened.st_size or len(raw) > MAX_ARCHIVE
                or (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
                or (latest.st_dev, latest.st_ino, latest.st_size, latest.st_mtime_ns)
                != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)):
            raise _block()
        return raw
    finally:
        os.close(fd)


def _safe_member_inventory(archive: ZipFile) -> None:
    entries = archive.infolist()
    if not 1 <= len(entries) <= MAX_MEMBERS:
        raise _block()
    total = 0
    seen: set[str] = set()
    for entry in entries:
        name = entry.filename
        if (not name or name.casefold() in seen or name.startswith(("/", "\\"))
                or "\\" in name or entry.is_dir() or name.endswith("/")
                or any(segment in {"", ".", ".."} for segment in name.split("/"))
                or entry.flag_bits & 1
                or entry.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                or entry.file_size < 0 or entry.file_size > MAX_MEMBER
                or entry.compress_size < 0):
            raise _block()
        seen.add(name.casefold())
        if entry.file_size and (
            entry.compress_size == 0 or
            entry.file_size / entry.compress_size > MAX_RATIO
        ):
            raise _block()
        total += entry.file_size
        if total > MAX_EXPANDED:
            raise _block()


def inspect_owner_zip(path: Path, tier: str, expected_sha256: str) -> dict:
    """Physical ZIP identity, shipping manifest and PDF structure; not visual/legal review."""
    if (tier not in PAGE_BOUNDS or not isinstance(expected_sha256, str)
            or SHA256.fullmatch(expected_sha256) is None):
        raise _block()
    raw = _read_bounded_original(path)
    digest = sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise _block()
    with ZipFile(BytesIO(raw)) as archive:
        _safe_member_inventory(archive)
        # Reuse exact original SKU/manifest/dependency policy rather than rewriting it.
        verified = verify_shipping_zip(raw, tier)
        pdf = archive.read("report.pdf")
    if not pdf.startswith(b"%PDF-") or len(pdf) > MAX_MEMBER:
        raise _block()
    reader = PdfReader(BytesIO(pdf), strict=True)
    if reader.is_encrypted:
        raise _block()
    pages = len(reader.pages)
    low, high = PAGE_BOUNDS[tier]
    if not low <= pages <= high:
        raise _block()
    for page in reader.pages:
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        if not 100 <= width <= 2000 or not 100 <= height <= 2000:
            raise _block()
    # Recheck the actual original file after potentially costly parsing.
    if sha256(_read_bounded_original(path)).hexdigest() != digest:
        raise _block()
    return {
        "format": FORMAT,
        "status": "STRUCTURE_AND_PAGE_COUNT_VERIFIED_HUMAN_REVIEW_REQUIRED",
        "tier": tier,
        "zip_sha256": digest,
        "zip_bytes": len(raw),
        "pdf_sha256": sha256(pdf).hexdigest(),
        "pdf_pages": pages,
        "zip_members": verified["members"],
        "manifest_member_checksums": "VERIFIED",
        "delivery_policy": "VERIFIED_STRUCTURE_NOT_LEGAL",
        "pdf_visual_readability": "NOT_VERIFIED",
        "pdf_embedded_font_original_rights": "NOT_VERIFIED",
        "third_party_license_notice_rights": "NOT_VERIFIED",
        "owner_data_authorization": "NOT_VERIFIED",
        "physical_windows_customer_qa": "NOT_VERIFIED",
        "human_sku_acceptance": "NOT_VERIFIED",
        "customer_sale_approved": False,
        "source_paths_or_customer_values_in_receipt": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline private owner ZIP/PDF review (not sale)")
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--tier", choices=sorted(PAGE_BOUNDS), required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if (not args.out.is_absolute() or args.out.suffix.lower() != ".json"
                or args.out == args.zip or args.out.exists() or args.out.is_symlink()):
            raise _block()
        _no_links(args.out)
        if not args.out.parent.is_dir():
            raise _block()
        result = inspect_owner_zip(args.zip, args.tier, args.expected_sha256)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
        fd = os.open(args.out, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as target:
            json.dump(result, target, sort_keys=True, ensure_ascii=True, indent=2)
            target.write("\n")
        print("OWNER_ZIP_STRUCTURE_PASS_RELEASE_BLOCKED")
        print("ZIP_SHA256=" + result["zip_sha256"])
        print("PDF_PAGES=" + str(result["pdf_pages"]))
        print("CUSTOMER_SALE_APPROVED=False")
        return 0
    except (OSError, ValueError, KeyError, TypeError, BadZipFile, ImportError, OverflowError):
        # Do not remove the pathname after failure: a concurrent writer may
        # have replaced it. A partial file is HOLD for manual owner review.
        print("LOCAL_OWNER_DELIVERY_REVIEW_BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
