from __future__ import annotations

import math
import os
from pathlib import Path
from statistics import mean, stdev

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt

from table1_print import read_spss_sav


DATA_DIR = Path(os.environ.get("CT_VOLUME_DATA_DIR", Path(__file__).with_name("data")))
SAV_PATH = Path(
    os.environ.get("CT_VOLUME_SAV_PATH", DATA_DIR / "analysis_data.sav")
)
OUTPUT_DOCX = Path(__file__).with_name("table2_output.docx")


TABLE2_ROWS = [
    ("Anterior group", "anterior_Total", "anterior_pure", "anterior_fat", "group"),
    ("Sartorius", "sartorius_total_volume", "sartorius_pure_volume", "sartorius_fat_volume", "muscle"),
    ("Rectus femoris", "rectus_femoris_total_volume", "rectus_femoris_pure_volume", "rectus_femoris_fat_volume", "muscle"),
    ("Vastus lateralis", "vastus_lateralis_total_volume", "vastus_lateralis_pure_volume", "vastus_lateralis_fat_volume", "muscle"),
    ("Vastus intermedius", "vastus_intermedius_total_volume", "vastus_intermedius_pure_volume", "vastus_intermedius_fat_volume", "muscle"),
    ("Vastus medialis", "vastus_medialis_total_volume", "vastus_medialis_pure_volume", "vastus_medialis_fat_volume", "muscle"),
    ("", "", "", "", "blank"),
    ("Medial group", "medial_total", "medial_pure", "medial_fat", "group"),
    ("Adductor longus", "adductor_longus_total_volume", "adductor_longus_pure_volume", "adductor_longus_fat_volume", "muscle"),
    ("Adductor brevis", "adductor_brevis_total_volume", "adductor_brevis_pure_volume", "adductor_brevis_fat_volume", "muscle"),
    ("Adductor magnus", "adductor_magnus_total_volume", "adductor_magnus_pure_volume", "adductor_magnus_fat_volume", "muscle"),
    ("Gracilis", "gracilis_total_volume", "gracilis_pure_volume", "gracilis_fat_volume", "muscle"),
    ("Pectineus", "pectineus_total_volume", "pectineus_pure_volume", "pectineus_fat_volume", "muscle"),
    ("", "", "", "", "blank"),
    ("Posterior group", "posterior_total", "posterior_pure", "posterior_fat", "group"),
    ("Semitendinosus", "semitendinosus_total_volume", "semitendinosus_pure_volume", "semitendinosus_fat_volume", "muscle"),
    ("Semimembranosus", "semimembranosus_total_volume", "semimembranosus_pure_volume", "semimembranosus_fat_volume", "muscle"),
    ("Biceps femoris", "biceps_femoris_total_volume", "biceps_femoris_pure_volume", "biceps_femoris_fat_volume", "muscle"),
    ("", "", "", "", "blank"),
    ("Gluteal group", "gluteal_total", "gluteal_pure", "gluteal_fat", "group"),
    ("Gluteus maximus", "gluteus_maximus_total_volume", "gluteus_maximus_pure_volume", "gluteus_maximus_fat_volume", "muscle"),
    ("Gluteus medius", "gluteus_medius_total_volume", "gluteus_medius_pure_volume", "gluteus_medius_fat_volume", "muscle"),
    ("Gluteus minimus", "gluteus_minimus_total_volume", "gluteus_minimus_pure_volume", "gluteus_minimus_fat_volume", "muscle"),
    ("Tensor fascia latae", "tensor_fascia_latae_total_volume", "tensor_fascia_latae_pure_volume", "tensor_fascia_latae_fat_volume", "muscle"),
    ("Piriformis", "piriformis_total_volume", "piriformis_pure_volume", "piriformis_fat_volume", "muscle"),
    ("Obturator internus", "obturator_internus_total_volume", "obturator_internus_pure_volume", "obturator_internus_fat_volume", "muscle"),
    ("Obturator externus", "obturator_externus_total_volume", "obturator_externus_pure_volume", "obturator_externus_fat_volume", "muscle"),
    ("Quadratus femoris", "quadratus_femoris_total_volume", "quadratus_femoris_pure_volume", "quadratus_femoris_fat_volume", "muscle"),
    ("", "", "", "", "blank"),
    ("Others", "other_total", "other_pure", "other_fat", "group"),
    ("Iliacus", "iliacus_total_volume", "iliacus_pure_volume", "iliacus_fat_volume", "muscle"),
    ("Iliopsoas", "iliopsoas_total_volume", "iliopsoas_pure_volume", "iliopsoas_fat_volume", "muscle"),
    ("Abdominal oblique", "abdominal_oblique_total_volume", "abdominal_oblique_pure_volume", "abdominal_oblique_fat_volume", "muscle"),
    ("Multifidus", "multifidus_total_volume", "multifidus_pure_volume", "multifidus_fat_volume", "muscle"),
    ("Rectus abdominis", "rectus_abdominis_total_volume", "rectus_abdominis_pure_volume", "rectus_abdominis_fat_volume", "muscle"),
    ("", "", "", "", "blank"),
    ("Total thigh muscle volume", "femoral_total_volume", "femoral_pure_volume", "femoral_fat_volume", "total"),
]


def is_valid_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(float(value))


def get_values(rows: list[dict[str, float | str]], name: str, scale: float = 1.0) -> list[float]:
    return [float(row[name]) * scale for row in rows if is_valid_number(row.get(name))]


def mean_sd(values: list[float]) -> str:
    return f"{mean(values):.2f}±{stdev(values):.2f}"


def build_table_2() -> list[tuple[str, str, str, str, str]]:
    rows = read_spss_sav(SAV_PATH)
    table = [
        (
            "Muscles",
            "Total muscle volume (cm3/m2, mean±SD)",
            "Pure muscle volume (cm3/m2, mean±SD)",
            "IMAT volume (cm3/m2, mean±SD)",
            "IMAT percentage (%, mean±SD)",
        )
    ]

    for label, total_name, pure_name, fat_name, row_type in TABLE2_ROWS:
        if row_type == "blank":
            table.append(("", "", "", "", ""))
            continue

        total = get_values(rows, total_name, scale=10.0)
        pure = get_values(rows, pure_name, scale=10.0)
        fat = get_values(rows, fat_name, scale=10.0)
        imat_percentage = [
            float(row[fat_name]) / float(row[pure_name]) * 10.0
            for row in rows
            if is_valid_number(row.get(fat_name))
            and is_valid_number(row.get(pure_name))
            and float(row[pure_name]) != 0.0
        ]
        table.append((label, mean_sd(total), mean_sd(pure), mean_sd(fat), mean_sd(imat_percentage)))

    return table


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
    title_run = title.add_run("Table 2. Height-normalized muscle volume and IMAT composition")
    title_run.bold = True
    title_run.font.name = "Arial"
    title_run.font.size = Pt(10.5)

    note = doc.add_paragraph()
    note_run = note.add_run(
        "Values are mean±SD. Total, pure, and IMAT volumes are height-squared normalized "
        "values expressed as cm3/m2."
    )
    note_run.font.name = "Arial"
    note_run.font.size = Pt(7.5)

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

