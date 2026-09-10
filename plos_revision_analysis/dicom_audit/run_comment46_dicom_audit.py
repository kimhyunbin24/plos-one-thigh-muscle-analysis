from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import io
import math
import secrets
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import BinaryIO, Iterable

try:
    import pydicom
except ImportError:
    print(
        "pydicom is required. Install it in this environment with: "
        "python -m pip install pydicom",
        file=sys.stderr,
    )
    raise


HERE = Path(__file__).resolve().parent

TAGS = [
    "PatientID",
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
    "InstitutionName",
    "Manufacturer",
    "ManufacturerModelName",
    "StationName",
    "DeviceSerialNumber",
    "SoftwareVersions",
    "StudyDate",
    "AcquisitionDate",
    "SeriesDate",
    "Modality",
    "BodyPartExamined",
    "ProtocolName",
    "SeriesDescription",
    "PatientPosition",
    "ImageLaterality",
    "Laterality",
    "KVP",
    "XRayTubeCurrent",
    "Exposure",
    "SliceThickness",
    "SpacingBetweenSlices",
    "PixelSpacing",
    "Rows",
    "Columns",
    "ConvolutionKernel",
    "ReconstructionDiameter",
    "ImagePositionPatient",
    "SliceLocation",
    "InstanceNumber",
]

INSTITUTION_PATH_LABELS = {
    "경상국립대학교병원": "GNUH",
    "노원을지대학교병원": "NEMC",
    "대전을지대학교병원": "DEMC",
    "아주대학교병원": "AUMC",
    "인하대학교병원": "IHUH",
}
PATIENT_HASH_KEY = secrets.token_bytes(32)


def text_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\\".join(str(item).strip() for item in value)
    return str(value).strip()


def float_value(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def pair_value(value: object) -> tuple[float, float] | None:
    if value is None:
        return None
    try:
        values = list(value)
        if len(values) >= 2:
            return float(values[0]), float(values[1])
    except (TypeError, ValueError):
        pass
    return None


def hash_id(value: object, prefix: str) -> str:
    raw = text_value(value)
    if not raw:
        return ""
    digest = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def hash_patient_id(value: object) -> str:
    raw = text_value(value)
    if not raw:
        return ""
    digest = hmac.new(
        PATIENT_HASH_KEY, raw.encode("utf-8", errors="replace"), hashlib.sha256
    ).hexdigest()[:16]
    return f"patient_{digest}"


def infer_institution(source_label: str) -> str:
    for folder_name, abbreviation in INSTITUTION_PATH_LABELS.items():
        if folder_name in source_label:
            return abbreviation
    return "UNKNOWN"


def read_dataset(source: str | Path | BinaryIO):
    return pydicom.dcmread(
        source,
        stop_before_pixels=True,
        force=True,
        specific_tags=TAGS,
    )


def iter_datasets(
    root: Path, include_zip: bool, max_files: int
) -> Iterable[tuple[object, str, str]]:
    processed = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".dcm":
            try:
                yield read_dataset(path), str(path.parent), "file"
                processed += 1
            except Exception:
                continue
        elif include_zip and suffix == ".zip":
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        if not member.filename.lower().endswith((".dcm", ".dicom", ".ima")):
                            continue
                        try:
                            data = archive.read(member)
                            yield (
                                read_dataset(io.BytesIO(data)),
                                str(path.parent),
                                "zip",
                            )
                            processed += 1
                        except Exception:
                            continue
                        if max_files and processed >= max_files:
                            return
            except (OSError, zipfile.BadZipFile):
                continue
        if max_files and processed >= max_files:
            return


def z_position(dataset: object) -> float | None:
    position = getattr(dataset, "ImagePositionPatient", None)
    try:
        if position is not None and len(position) >= 3:
            return float(position[2])
    except (TypeError, ValueError):
        pass
    return float_value(getattr(dataset, "SliceLocation", None))


def initialize_series(dataset: object, source_label: str, source_kind: str) -> dict:
    pixel_spacing = pair_value(getattr(dataset, "PixelSpacing", None))
    rows = int(getattr(dataset, "Rows", 0) or 0)
    columns = int(getattr(dataset, "Columns", 0) or 0)
    path_institution = infer_institution(source_label)
    header_institution = text_value(getattr(dataset, "InstitutionName", None))
    institution = (
        path_institution if path_institution != "UNKNOWN" else header_institution or "UNKNOWN"
    )
    return {
        "institution": institution,
        "patient_hash": hash_patient_id(getattr(dataset, "PatientID", None)),
        "study_hash": hash_id(getattr(dataset, "StudyInstanceUID", None), "study"),
        "series_hash": hash_id(getattr(dataset, "SeriesInstanceUID", None), "series"),
        "manufacturer": text_value(getattr(dataset, "Manufacturer", None)),
        "scanner_model": text_value(getattr(dataset, "ManufacturerModelName", None)),
        "software_versions": text_value(getattr(dataset, "SoftwareVersions", None)),
        "study_date": text_value(getattr(dataset, "StudyDate", None)),
        "acquisition_date": text_value(getattr(dataset, "AcquisitionDate", None)),
        "modality": text_value(getattr(dataset, "Modality", None)),
        "body_part": text_value(getattr(dataset, "BodyPartExamined", None)),
        "protocol_name": text_value(getattr(dataset, "ProtocolName", None)),
        "series_description": text_value(getattr(dataset, "SeriesDescription", None)),
        "patient_position": text_value(getattr(dataset, "PatientPosition", None)),
        "laterality": text_value(
            getattr(dataset, "ImageLaterality", None)
            or getattr(dataset, "Laterality", None)
        ),
        "kvp": float_value(getattr(dataset, "KVP", None)),
        "tube_current_ma": float_value(getattr(dataset, "XRayTubeCurrent", None)),
        "exposure_mas": float_value(getattr(dataset, "Exposure", None)),
        "slice_thickness_mm": float_value(getattr(dataset, "SliceThickness", None)),
        "spacing_between_slices_mm": float_value(
            getattr(dataset, "SpacingBetweenSlices", None)
        ),
        "pixel_spacing_row_mm": pixel_spacing[0] if pixel_spacing else None,
        "pixel_spacing_col_mm": pixel_spacing[1] if pixel_spacing else None,
        "rows": rows or None,
        "columns": columns or None,
        "fov_row_mm": rows * pixel_spacing[0] if rows and pixel_spacing else None,
        "fov_col_mm": columns * pixel_spacing[1] if columns and pixel_spacing else None,
        "reconstruction_diameter_mm": float_value(
            getattr(dataset, "ReconstructionDiameter", None)
        ),
        "kernel": text_value(getattr(dataset, "ConvolutionKernel", None)),
        "source_kinds": {source_kind},
        "sop_hashes": set(),
        "z_positions": [],
    }


def series_key(dataset: object, source_label: str) -> str:
    uid = text_value(getattr(dataset, "SeriesInstanceUID", None))
    if uid:
        return uid
    fallback = "|".join(
        [
            source_label,
            text_value(getattr(dataset, "StudyInstanceUID", None)),
            text_value(getattr(dataset, "SeriesDescription", None)),
        ]
    )
    return "missing-uid:" + hashlib.sha256(fallback.encode("utf-8")).hexdigest()


def collect_series(root: Path, include_zip: bool, max_files: int) -> tuple[list[dict], int]:
    grouped: dict[str, dict] = {}
    instances_read = 0
    for dataset, source_label, source_kind in iter_datasets(root, include_zip, max_files):
        if text_value(getattr(dataset, "Modality", None)).upper() not in {"", "CT"}:
            continue
        instances_read += 1
        key = series_key(dataset, source_label)
        record = grouped.setdefault(
            key, initialize_series(dataset, source_label, source_kind)
        )
        record["source_kinds"].add(source_kind)
        sop_uid = getattr(dataset, "SOPInstanceUID", None)
        if sop_uid:
            record["sop_hashes"].add(hash_id(sop_uid, "sop"))
        z = z_position(dataset)
        if z is not None:
            record["z_positions"].append(z)

    rows: list[dict] = []
    for record in grouped.values():
        positions = sorted(set(record.pop("z_positions")))
        intervals = [
            abs(right - left)
            for left, right in zip(positions, positions[1:])
            if abs(right - left) > 1e-6
        ]
        sop_hashes = record.pop("sop_hashes")
        record["source_kind"] = ";".join(sorted(record.pop("source_kinds")))
        record["instance_count"] = len(sop_hashes) or len(positions)
        record["unique_z_count"] = len(positions)
        record["z_min_mm"] = min(positions) if positions else None
        record["z_max_mm"] = max(positions) if positions else None
        record["z_coverage_mm"] = (
            max(positions) - min(positions) if len(positions) >= 2 else None
        )
        record["median_reconstruction_interval_mm"] = (
            statistics.median(intervals) if intervals else None
        )
        record["coverage_requires_image_review"] = "Yes"
        rows.append(record)
    return rows, instances_read


SERIES_FIELDS = [
    "institution",
    "patient_hash",
    "study_hash",
    "series_hash",
    "study_date",
    "acquisition_date",
    "manufacturer",
    "scanner_model",
    "software_versions",
    "modality",
    "body_part",
    "protocol_name",
    "series_description",
    "patient_position",
    "laterality",
    "kvp",
    "tube_current_ma",
    "exposure_mas",
    "slice_thickness_mm",
    "spacing_between_slices_mm",
    "median_reconstruction_interval_mm",
    "pixel_spacing_row_mm",
    "pixel_spacing_col_mm",
    "rows",
    "columns",
    "fov_row_mm",
    "fov_col_mm",
    "reconstruction_diameter_mm",
    "kernel",
    "instance_count",
    "unique_z_count",
    "z_min_mm",
    "z_max_mm",
    "z_coverage_mm",
    "source_kind",
    "coverage_requires_image_review",
]


def format_set(values: Iterable[object]) -> str:
    normalized = sorted({text_value(value) for value in values if text_value(value)})
    return "; ".join(normalized)


def institution_summary(series_rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in series_rows:
        groups[row["institution"]].append(row)
    output: list[dict] = []
    for institution, rows in sorted(groups.items()):
        output.append(
            {
                "institution": institution,
                "patients_n": len({row["patient_hash"] for row in rows if row["patient_hash"]}),
                "studies_n": len({row["study_hash"] for row in rows if row["study_hash"]}),
                "series_n": len(rows),
                "scanner_manufacturers": format_set(row["manufacturer"] for row in rows),
                "scanner_models": format_set(row["scanner_model"] for row in rows),
                "kvp_values": format_set(row["kvp"] for row in rows),
                "slice_thickness_values_mm": format_set(
                    row["slice_thickness_mm"] for row in rows
                ),
                "reconstruction_interval_values_mm": format_set(
                    row["median_reconstruction_interval_mm"] for row in rows
                ),
                "pixel_spacing_values_mm": format_set(
                    f"{row['pixel_spacing_row_mm']}x{row['pixel_spacing_col_mm']}"
                    for row in rows
                    if row["pixel_spacing_row_mm"] is not None
                    and row["pixel_spacing_col_mm"] is not None
                ),
                "matrix_values": format_set(
                    f"{row['rows']}x{row['columns']}"
                    for row in rows
                    if row["rows"] and row["columns"]
                ),
                "kernels": format_set(row["kernel"] for row in rows),
                "series_descriptions_n": len(
                    {row["series_description"] for row in rows if row["series_description"]}
                ),
                "missing_institution_header_n": sum(
                    row["institution"] == "UNKNOWN" for row in rows
                ),
            }
        )
    return output


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    root: Path, series_rows: list[dict], summary_rows: list[dict], instances_read: int
) -> None:
    configurations = {
        (
            row["manufacturer"],
            row["scanner_model"],
            row["kvp"],
            row["slice_thickness_mm"],
            row["median_reconstruction_interval_mm"],
            row["kernel"],
        )
        for row in series_rows
    }
    lines = [
        "# Comment 46 DICOM metadata audit",
        "",
        f"Input root: `{root}`",
        f"DICOM instances read: {instances_read:,}",
        f"CT series summarized: {len(series_rows):,}",
        f"Institutions represented: {len(summary_rows):,}",
        f"Distinct recorded acquisition/reconstruction configurations: {len(configurations):,}",
        "",
        "## Interpretation rule",
        "",
        "A single standardized acquisition protocol should not be claimed when scanner models, kVp, slice thickness, pixel spacing, matrix, or reconstruction kernels vary materially across institutions or series. Describe the observed ranges and state any preprocessing or harmonization that was actually performed.",
        "",
        "## Important limitation",
        "",
        "DICOM headers provide physical field of view and z-axis extent, but do not reliably identify whether the cranial boundary is L3 versus L4, whether the knee/distal femur is anatomically complete, or whether both thighs are fully visible. Those items require pixel-level image review or an explicit anatomical-coverage algorithm. This audit intentionally does not infer them from header metadata alone.",
        "",
        "## Institution summary",
        "",
        "| Institution | Patients | Studies | Series | Scanner models | kVp | Slice thickness (mm) | Kernels |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['institution']} | {row['patients_n']} | {row['studies_n']} | "
            f"{row['series_n']} | {row['scanner_models'] or 'Not recorded'} | "
            f"{row['kvp_values'] or 'Not recorded'} | "
            f"{row['slice_thickness_values_mm'] or 'Not recorded'} | "
            f"{row['kernels'] or 'Not recorded'} |"
        )
    (HERE / "comment46_dicom_audit_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only DICOM metadata audit for PLOS ONE Reviewer Comment 46."
    )
    parser.add_argument(
        "--root", type=Path, required=True, help="Root directory containing DICOM data."
    )
    parser.add_argument(
        "--include-zip",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Read DICOM members inside ZIP archives (default: disabled for speed).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=1000,
        help="Stop after this many DICOM instances (default: 1000); 0 scans all files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.root.is_dir():
        raise FileNotFoundError(f"DICOM root was not found: {args.root}")
    HERE.mkdir(parents=True, exist_ok=True)
    series_rows, instances_read = collect_series(
        args.root, args.include_zip, args.max_files
    )
    if not series_rows:
        raise RuntimeError("No readable CT DICOM series were found.")
    summary_rows = institution_summary(series_rows)
    write_csv(HERE / "comment46_series_metadata.csv", series_rows, SERIES_FIELDS)
    summary_fields = list(summary_rows[0])
    write_csv(
        HERE / "comment46_institution_summary.csv", summary_rows, summary_fields
    )
    write_report(args.root, series_rows, summary_rows, instances_read)
    print(f"DICOM instances read: {instances_read:,}")
    print(f"CT series summarized: {len(series_rows):,}")
    print(f"Institutions represented: {len(summary_rows):,}")
    print(f"Outputs: {HERE}")


if __name__ == "__main__":
    main()

