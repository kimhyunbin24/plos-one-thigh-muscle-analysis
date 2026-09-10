from __future__ import annotations

import math
import os
from pathlib import Path
from statistics import mean, stdev

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt
from openpyxl import load_workbook


DATA_DIR = Path(os.environ.get("CT_VOLUME_DATA_DIR", Path(__file__).with_name("data")))
EXCEL_PATH = Path(
    os.environ.get(
        "CT_VOLUME_EXCEL_PATH",
        DATA_DIR / "RWD_muscle_estimation_수술전_1126 - 복사본.xlsx",
    )
)
SHEET_NAME = "수술전 (2)"
OUTPUT_DOCX = Path(__file__).with_name("table2_output.docx")


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not (isinstance(value, float) and math.isnan(value))


def load_preop_rows(path: Path = EXCEL_PATH) -> tuple[list[str], list[list[object]]]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[SHEET_NAME]

    headers: list[str] = []
    rows: list[list[object]] = []

    for row_i, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        values = list(row)
        if row_i == 2:
            headers = [str(v).strip() if v is not None else "" for v in values]
        elif row_i >= 3 and len(values) > 1 and values[1] == "수술전":
            rows.append(values)

    workbook.close()
    return headers, rows


def mean_sd_by_column(rows: list[list[object]], col_1based: int, scale: float = 1.0) -> str:
    idx = col_1based - 1
    values = [float(row[idx]) / scale for row in rows if len(row) > idx and is_number(row[idx])]
    return f"{mean(values):.2f}±{stdev(values):.2f}"


def mean_sd_by_header(rows: list[list[object]], headers: list[str], header: str, scale: float = 1.0) -> str:
    idx = headers.index(header)
    values = [float(row[idx]) / scale for row in rows if len(row) > idx and is_number(row[idx])]
    return f"{mean(values):.2f}±{stdev(values):.2f}"


def muscle_row(
    label: str,
    rows: list[list[object]],
    headers: list[str],
    prefix: str | None = None,
    cols: tuple[int, int, int, int] | None = None,
) -> tuple[str, str, str, str, str]:
    """Return row in manuscript order: total, pure, fat, fat percentage.

    Volume columns are stored as mm3 in Excel and printed as cm3.
    The manuscript's fat percentage column matches Excel percentage / 10.
    """
    if cols is not None:
        total_col, pure_col, fat_col, percent_col = cols
        return (
            label,
            mean_sd_by_column(rows, total_col, 1000),
            mean_sd_by_column(rows, pure_col, 1000),
            mean_sd_by_column(rows, fat_col, 1000),
            mean_sd_by_column(rows, percent_col, 10),
        )

    if prefix is None:
        raise ValueError("Either prefix or cols must be provided.")

    return (
        label,
        mean_sd_by_header(rows, headers, f"{prefix}_total_volume_mm3", 1000),
        mean_sd_by_header(rows, headers, f"{prefix}_pure_volume_mm3", 1000),
        mean_sd_by_header(rows, headers, f"{prefix}_fat_volume_mm3", 1000),
        mean_sd_by_header(rows, headers, f"{prefix}_fat_percentage", 10),
    )


def build_table_2() -> list[tuple[str, str, str, str, str]]:
    headers, rows = load_preop_rows()

    # Group rows use duplicate Excel headers ("Total", "Fat", "Pure", "Fat"),
    # so they are mapped by fixed 1-based Excel column numbers.
    return [
        ("Muscles", "Total muscle volume (cm3, mean±SD)", "Pure muscle volume (cm3, mean±SD)", "Fat volume (cm3, mean±SD)", "Fat percentage (%, mean±SD)"),
        muscle_row("Anterior group", rows, headers, cols=(27, 29, 28, 30)),
        muscle_row("Sartorius", rows, headers, "sartorius"),
        muscle_row("Rectus femoris", rows, headers, "rectus_femoris"),
        muscle_row("Vastus lateralis", rows, headers, "vastus_lateralis"),
        muscle_row("Vastus intermedius", rows, headers, "vastus_intermedius"),
        muscle_row("Vastus medialis", rows, headers, "vastus_medialis"),
        ("", "", "", "", ""),
        muscle_row("Medial group", rows, headers, cols=(51, 53, 52, 54)),
        muscle_row("Adductor longus", rows, headers, "adductor_longus"),
        muscle_row("Adductor brevis", rows, headers, "adductor_brevis"),
        muscle_row("Adductor magnus", rows, headers, "adductor_magnus"),
        muscle_row("Gracilis", rows, headers, "gracilis"),
        muscle_row("Pectineus", rows, headers, "pectineus"),
        ("", "", "", "", ""),
        muscle_row("Posterior group", rows, headers, cols=(103, 105, 104, 106)),
        muscle_row("Semitendinosus", rows, headers, "semitendinosus"),
        muscle_row("Semimembranosus", rows, headers, "semimembranosus"),
        muscle_row("Biceps femoris", rows, headers, "biceps_femoris"),
        ("", "", "", "", ""),
        muscle_row("Gluteal group", rows, headers, cols=(87, 89, 88, 90)),
        muscle_row("Gluteus maximus", rows, headers, "gluteus_maximus"),
        muscle_row("Gluteus medius", rows, headers, "gluteus_medius"),
        muscle_row("Gluteus minimus", rows, headers, "gluteus_minimus"),
        muscle_row("Tensor fascia latae", rows, headers, "tensor_fascia_latae"),
        muscle_row("Piriformis", rows, headers, "piriformis"),
        muscle_row("Obturator internus", rows, headers, "obturator_internus"),
        muscle_row("Obturator externus", rows, headers, "obturator_externus"),
        muscle_row("Quadratus femoris", rows, headers, "quadratus_femoris"),
        ("", "", "", "", ""),
        muscle_row("Others", rows, headers, cols=(127, 129, 128, 130)),
        muscle_row("Iliacus", rows, headers, "iliacus"),
        muscle_row("Iliopsoas", rows, headers, "iliopsoas"),
        muscle_row("Abdominal oblique", rows, headers, "abdominal_oblique"),
        muscle_row("Multifidus", rows, headers, "multifidus"),
        muscle_row("Rectus abdominis", rows, headers, "rectus_abdominis"),
        ("", "", "", "", ""),
        muscle_row("Total thigh muscle volume", rows, headers, "femoral"),
    ]


def save_table_2_docx(table: list[tuple[str, str, str, str, str]], output_path: Path = OUTPUT_DOCX) -> None:
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.55)
    section.right_margin = Inches(0.55)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(7.5)

    title = doc.add_paragraph()
    title_run = title.add_run("Table 2. Muscle volume and fat composition")
    title_run.bold = True
    title_run.font.name = "Arial"
    title_run.font.size = Pt(10.5)

    word_table = doc.add_table(rows=len(table), cols=5)
    word_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    word_table.style = "Table Grid"
    word_table.autofit = False

    col_widths = (Inches(2.25), Inches(1.75), Inches(1.75), Inches(1.65), Inches(1.65))
    for row_i, row_values in enumerate(table):
        cells = word_table.rows[row_i].cells
        is_header = row_i == 0
        is_group = row_values[0] in {
            "Anterior group",
            "Medial group",
            "Posterior group",
            "Gluteal group",
            "Others",
            "Total thigh muscle volume",
        }
        for col_i, value in enumerate(row_values):
            cell = cells[col_i]
            cell.width = col_widths[col_i]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(value)
            run.font.name = "Arial"
            run.font.size = Pt(7.4 if is_header else 7.6)
            run.bold = is_header or is_group

    doc.save(output_path)


def print_table_2() -> None:
    table = build_table_2()
    for row in table:
        print("\t".join(row))
    save_table_2_docx(table)
    print(f"\nSaved Word table: {OUTPUT_DOCX}")


if __name__ == "__main__":
    print_table_2()

