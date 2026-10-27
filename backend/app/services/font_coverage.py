"""ReportLab/Matplotlib CJK glyph coverage and local font fallback.

No network fetch or bundled font binary. The caller selects preinstalled fonts
and fails before exporting broken Japanese text if a glyph has no local font.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from xml.sax.saxutils import escape


def _existing(candidates):
    return next((Path(p) for p in candidates if p and Path(p).is_file()), None)


def _primary_path() -> Path:
    path = _existing([
        os.environ.get("AUTOML_KOREAN_FONT_PATH", ""),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/local/share/fonts/NanumGothic.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
        str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts/NanumGothic.ttf"),
        "C:/Windows/Fonts/malgun.ttf",
    ])
    if path is None:
        raise RuntimeError(
            "Korean PDF font missing: install a licensed NanumGothic TTF "
            "or set AUTOML_KOREAN_FONT_PATH."
        )
    return path


def _japanese_path() -> Path | None:
    return _existing([
        os.environ.get("AUTOML_JAPANESE_FONT_PATH", ""),
        # TrueType outlines (not CFF/OTF) are necessary for ReportLab embedding.
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
    ])


def _register(path: Path, prefix: str) -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Different directories, e.g. temporary QA font, cannot reuse one name.
    name = prefix + sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    if name not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
        except Exception as exc:
            raise ValueError(
                "Installed CJK font cannot be embedded. Select a licensed "
                "TrueType TTF/TTC via AUTOML_JAPANESE_FONT_PATH."
            ) from exc
    return name


def _has_glyph(font: str, char: str) -> bool:
    from reportlab.pdfbase import pdfmetrics

    if char.isspace():
        return True
    return ord(char) in pdfmetrics.getFont(font).face.charToGlyph


def resolve_report_fonts(required_text: str = "") -> tuple[str, str | None]:
    """Register an embeddable primary and optional fallback covering user text."""
    primary = _register(_primary_path(), "AutoMLKorean")
    missing = {ch for ch in required_text if not _has_glyph(primary, ch)}
    if not missing:
        return primary, None
    path = _japanese_path()
    if path is None:
        raise ValueError(
            "Japanese/Unicode report font lacks required glyphs. "
            "Install an appropriately licensed Japanese TrueType font "
            "and set AUTOML_JAPANESE_FONT_PATH before retrying."
        )
    fallback = _register(path, "AutoMLJapanese")
    unsupported = sorted(ord(ch) for ch in missing if not _has_glyph(fallback, ch))
    if unsupported:
        points = ", ".join("U+%04X" % p for p in unsupported[:5])
        raise ValueError(
            "Report font missing Unicode glyphs: " + points
            + ". Install a suitable TrueType font using AUTOML_JAPANESE_FONT_PATH."
        )
    return primary, fallback


def safe_pdf_markup(text: object, primary_font: str, fallback_font: str | None) -> str:
    """Keep ReportLab Paragraph XML escaped while switching only missing glyphs."""
    text = str(text)
    parts = []
    for ch in text:
        token = escape(ch)
        if _has_glyph(primary_font, ch):
            parts.append(token)
        elif fallback_font and _has_glyph(fallback_font, ch):
            parts.append('<font name="' + fallback_font + '">' + token + "</font>")
        else:
            # Decorative/report-authored Unicode symbols may be absent from a
            # licensed Korean font. Do not turn an otherwise valid report into
            # HTTP 400 or silently render tofu. Caller-provided feature names
            # are strictly validated by resolve_report_fonts(required_text)
            # before reaching this presentation fallback.
            parts.append("[U+%04X]" % ord(ch))
    return "".join(parts)


def chart_font_families(required_text: str = "") -> list[str]:
    """Pass a ranked TrueType family list to Matplotlib's glyph fallbacks."""
    from matplotlib import font_manager

    primary_name, fallback_name = resolve_report_fonts(required_text)
    from reportlab.pdfbase import pdfmetrics

    paths = [pdfmetrics.getFont(primary_name).face.filename]
    if fallback_name:
        paths.append(pdfmetrics.getFont(fallback_name).face.filename)
    names = []
    for filename in paths:
        font_manager.fontManager.addfont(str(filename))
        family = font_manager.FontProperties(fname=str(filename)).get_name()
        if family not in names:
            names.append(family)
    return names
