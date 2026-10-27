"""P6E21: dimension-less and falsely dimensioned XLSX must be bounded.

Synthetic-only workbooks. Some XLSX generators omit or misstate the optional
worksheet <dimension> tag; never truncate customer rows/columns on its basis.
"""
from __future__ import annotations

from io import BytesIO
import re
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook
import pytest

from backend.app.services.tabular_input import read_xlsx_bounded


def _xlsx_with_dimension(replacement: bytes | None, width: int = 3) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.append([f"column_{j}" for j in range(width)])
    sheet.append(list(range(width)))
    sheet.append([7])  # An intentionally ragged record.
    buffer = BytesIO()
    book.save(buffer)
    book.close()

    output = BytesIO()
    with ZipFile(BytesIO(buffer.getvalue())) as source, ZipFile(
            output, "w", compression=ZIP_DEFLATED) as target:
        for member in source.infolist():
            body = source.read(member.filename)
            if member.filename == "xl/worksheets/sheet1.xml":
                body, matches = re.subn(
                    rb'<dimension ref="[^"]+"\s*/>',
                    replacement if replacement is not None else b"",
                    body,
                    count=1,
                )
                assert matches == 1, "Fixture requires an original worksheet dimension"
            target.writestr(member, body)
    return output.getvalue()


@pytest.mark.parametrize("declaration", [None, b'<dimension ref="A1"/>'])
def test_xlsx_missing_or_undersized_dimensions_preserve_actual_cells(declaration):
    frame = read_xlsx_bounded(_xlsx_with_dimension(declaration))
    assert frame.shape == (2, 3)
    assert list(frame.columns) == ["column_0", "column_1", "column_2"]
    assert frame.iloc[0].tolist() == [0, 1, 2]
    assert frame.iloc[1, 0] == 7
    assert frame.iloc[1, 1:].isna().all()


def test_underreported_dimensions_cannot_hide_extra_columns():
    # The XLSX claims just A1 although 51 real columns exist.
    with pytest.raises(ValueError, match="XLSX limit exceeded"):
        read_xlsx_bounded(_xlsx_with_dimension(b'<dimension ref="A1"/>', width=51))


def test_overdeclared_dimensions_are_still_rejected_before_expansion():
    # A claimed oversized worksheet remains a fail-closed preflight check.
    with pytest.raises(ValueError, match="XLSX limit exceeded"):
        read_xlsx_bounded(_xlsx_with_dimension(b'<dimension ref="A1:AX30000"/>'))
