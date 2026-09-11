from __future__ import annotations

import math
import os
import struct
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt


DATA_DIR = Path(os.environ.get("CT_VOLUME_DATA_DIR", Path(__file__).with_name("data")))
SAV_PATH = Path(
    os.environ.get("CT_VOLUME_SAV_PATH", DATA_DIR / "data키제곱나눈값.sav")
)
OUTPUT_DOCX = Path(__file__).with_name("table1_output.docx")


def _pad4(n: int) -> int:
    return (4 - n % 4) % 4


def _clean_bytes(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").rstrip("\x00 ").strip()


def read_spss_sav(path: Path) -> list[dict[str, float | str]]:
    """Small SPSS .sav reader for this file.

    It handles the standard compressed numeric/string layout used by
    data키제곱나눈값.sav, avoiding a dependency on pyreadstat.
    """
    data = path.read_bytes()
    endian = "<"

    def i4(offset: int) -> int:
        return struct.unpack_from(endian + "i", data, offset)[0]

    def f8(offset: int) -> float:
        return struct.unpack_from(endian + "d", data, offset)[0]

    case_size = i4(68)
    ncases = i4(80)
    bias = f8(84)

    offset = 176
    var_records: list[dict[str, int | str]] = []
    long_names: dict[str, str] = {}

    while offset < len(data):
        record_type = i4(offset)
        offset += 4

        if record_type == 2:
            var_type = i4(offset)
            has_label = i4(offset + 4)
            n_missing = i4(offset + 8)
            short_name = _clean_bytes(data[offset + 20 : offset + 28])
            offset += 28

            if has_label:
                label_len = i4(offset)
                offset += 4 + label_len + _pad4(label_len)

            offset += 8 * abs(n_missing)
            var_records.append({"short": short_name, "type": var_type})

        elif record_type == 3:
            label_count = i4(offset)
            offset += 4
            for _ in range(label_count):
                offset += 8
                label_len = data[offset]
                offset += 1 + label_len
                offset += (8 - ((1 + label_len) % 8)) % 8

        elif record_type == 4:
            var_count = i4(offset)
            offset += 4 + 4 * var_count

        elif record_type == 6:
            line_count = i4(offset)
            offset += 4 + 80 * line_count

        elif record_type == 7:
            subtype = i4(offset)
            size = i4(offset + 4)
            count = i4(offset + 8)
            offset += 12
            payload = data[offset : offset + size * count]
            offset += size * count
            if subtype == 13:
                text = _clean_bytes(payload)
                for part in text.replace("\n", "\t").split("\t"):
                    if "=" in part:
                        short, long = part.split("=", 1)
                        long_names[short.strip()] = long.strip()

        elif record_type == 999:
            offset += 4
            break

        else:
            raise ValueError(f"Unsupported SPSS dictionary record: {record_type}")

    slots: list[bytes | None] = []
    pos = offset
    target_slots = case_size * ncases

    while pos < len(data) and len(slots) < target_slots:
        codes = data[pos : pos + 8]
        pos += 8
        for code in codes:
            if len(slots) >= target_slots:
                break
            if code == 0:
                continue
            if code == 252:
                pos = len(data)
                break
            if code == 253:
                slots.append(data[pos : pos + 8])
                pos += 8
            elif code == 254:
                slots.append(b"        ")
            elif code == 255:
                slots.append(None)
            else:
                slots.append(struct.pack(endian + "d", float(code - bias)))

    variables = []
    record_i = 0
    while record_i < len(var_records):
        record = var_records[record_i]
        var_type = int(record["type"])
        short = str(record["short"])

        if var_type == -1:
            record_i += 1
            continue

        if var_type > 0:
            segment_count = (var_type + 7) // 8
            variables.append(
                {
                    "name": long_names.get(short, short),
                    "type": "string",
                    "width": var_type,
                    "slots": list(range(record_i, record_i + segment_count)),
                }
            )
            record_i += segment_count
        else:
            variables.append(
                {
                    "name": long_names.get(short, short),
                    "type": "numeric",
                    "slots": [record_i],
                }
            )
            record_i += 1

    rows = []
    for row_i in range(ncases):
        base = row_i * case_size
        row: dict[str, float | str] = {}
        for var in variables:
            name = str(var["name"])
            var_slots = list(var["slots"])
            if var["type"] == "string":
                width = int(var["width"])
                raw = b"".join(slots[base + s] or b"        " for s in var_slots)
                row[name] = _clean_bytes(raw[:width])
            else:
                raw = slots[base + var_slots[0]]
                row[name] = math.nan if raw is None else struct.unpack(endian + "d", raw)[0]
        rows.append(row)

    return rows


def valid_numbers(rows: list[dict[str, float | str]], name: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(name)
        if isinstance(value, (int, float)) and not math.isnan(float(value)):
            values.append(float(value))
    return values


def mean_sd(rows: list[dict[str, float | str]], name: str) -> str:
    values = valid_numbers(rows, name)
    return f"{mean(values):.1f}±{stdev(values):.1f}"


def count_percent(
    rows: list[dict[str, float | str]],
    name: str,
    codes: list[int],
    decimals: int | list[int] = 1,
) -> str:
    values = valid_numbers(rows, name)
    counts = Counter(int(v) for v in values)
    total = len(values)

    out = []
    for i, code in enumerate(codes):
        n = counts.get(code, 0)
        dec = decimals[i] if isinstance(decimals, list) else decimals
        pct = n / total * 100
        if dec == 0:
            out.append(f"{n}({pct:.0f}%)")
        else:
            out.append(f"{n}({pct:.{dec}f}%)")
    return "/".join(out)


def build_table_1() -> list[tuple[str, str]]:
    rows = read_spss_sav(SAV_PATH)
    n = len(rows)

    return [
        ("Variables", f"Total (n = {n:,})"),
        ("Age (years, mean±SD)", mean_sd(rows, "age")),
        ("Sex (men/women, n(%))", count_percent(rows, "sex", [1, 2], 1)),
        ("Height (cm, mean±SD)", mean_sd(rows, "height")),
        ("Weight (kg, mean±SD)", mean_sd(rows, "weight")),
        ("Body mass index (kg/m2, mean±SD)", mean_sd(rows, "BMI")),
        ("Fracture side (left/right, n (%))", count_percent(rows, "fx_side", [1, 2], 1)),
        ("Fracture type (intertrochanter/neck, n (%))", count_percent(rows, "fx_type", [1, 2], 1)),
        (
            "Pre-injury Koval grade (1/2/3/4/5/6/7, n (%))",
            count_percent(rows, "KOVAL", [7, 6, 5, 4, 3, 2, 1], 0),
        ),
        (
            "Functional Independence Measure "
            "(Complete Independence/Modified Independence/Supervision/Minimal Assistance/"
            "Moderate Assistance/Maximal Assistance/Total Assistance, n (%))",
            count_percent(rows, "FIM", [7, 6, 5, 4, 3, 2, 1], 0),
        ),
        ("Charlson Comorbidity Score (mean±SD)", mean_sd(rows, "CCI")),
        (
            "Anesthesia (general/spinal/epidural, n(%))",
            count_percent(rows, "anesthesia", [1, 2, 3], [0, 1, 1]),
        ),
        ("Surgery type (arthroplasty/internal fixation, n (%))", count_percent(rows, "surgery_type", [1, 2], 1)),
    ]


def save_table_1_docx(table: list[tuple[str, str]], output_path: Path = OUTPUT_DOCX) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(9)

    title = doc.add_paragraph()
    title_run = title.add_run("Table 1. Baseline characteristics")
    title_run.bold = True
    title_run.font.name = "Arial"
    title_run.font.size = Pt(11)

    word_table = doc.add_table(rows=len(table), cols=2)
    word_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    word_table.style = "Table Grid"
    word_table.autofit = False

    col_widths = (Inches(4.7), Inches(2.2))
    for row_i, (left, right) in enumerate(table):
        cells = word_table.rows[row_i].cells
        values = (left, right)
        for col_i, value in enumerate(values):
            cell = cells[col_i]
            cell.width = col_widths[col_i]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(value)
            run.font.name = "Arial"
            run.font.size = Pt(8.5)
            if row_i == 0:
                run.bold = True

    doc.save(output_path)


def print_table_1() -> None:
    table = build_table_1()
    for left, right in table:
        print(f"{left}\t{right}")
    save_table_1_docx(table)
    print(f"\nSaved Word table: {OUTPUT_DOCX}")


if __name__ == "__main__":
    print_table_1()

