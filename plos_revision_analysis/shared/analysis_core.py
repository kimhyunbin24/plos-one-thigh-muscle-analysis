from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable

import numpy as np


ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ANALYSIS_ROOT.parent
OUTPUT_DIR = ANALYSIS_ROOT / "outputs"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from table1_print import read_spss_sav  # noqa: E402


def _candidate_data_dirs() -> list[Path]:
    return [PROJECT_ROOT / "data"]


def _resolve_input(env_name: str, filename: str) -> Path:
    explicit = os.environ.get(env_name)
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path
        raise FileNotFoundError(f"{env_name} points to a missing file: {path}")

    configured_dir = os.environ.get("CT_VOLUME_DATA_DIR")
    data_dirs = [Path(configured_dir)] if configured_dir else _candidate_data_dirs()
    checked = []
    for data_dir in data_dirs:
        path = data_dir / filename
        checked.append(path)
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Input file '{filename}' was not found. Checked: "
        + "; ".join(str(path) for path in checked)
        + f". Set {env_name} or CT_VOLUME_DATA_DIR."
    )


def sav_path() -> Path:
    return _resolve_input("CT_VOLUME_SAV_PATH", "data키제곱나눈값.sav")


def excel_path() -> Path:
    preferred = "RWD_muscle_estimation_수술전_1126 - 복사본.xlsx"
    try:
        return _resolve_input("CT_VOLUME_EXCEL_PATH", preferred)
    except FileNotFoundError:
        return _resolve_input(
            "CT_VOLUME_EXCEL_PATH", "RWD_muscle_estimation_수술전_1126.xlsx"
        )


def manuscript_path() -> Path:
    explicit = os.environ.get("CT_VOLUME_MANUSCRIPT_PATH")
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path
        raise FileNotFoundError(
            f"CT_VOLUME_MANUSCRIPT_PATH points to a missing file: {path}"
        )

    candidates = [PROJECT_ROOT / "manuscript.docx"]
    candidates.append(PROJECT_ROOT / "data" / "manuscript.docx")
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Manuscript not found. Checked: "
        + "; ".join(str(path) for path in candidates)
        + ". Set CT_VOLUME_MANUSCRIPT_PATH to manuscript.docx."
    )


def load_analysis_rows() -> list[dict[str, float | str]]:
    return read_spss_sav(sav_path())


def as_float(value: object) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = float(value)
        if math.isfinite(value):
            return value
    return math.nan


def values(rows: list[dict[str, float | str]], name: str) -> np.ndarray:
    return np.asarray([as_float(row.get(name)) for row in rows], dtype=float)


def complete_mask(*arrays: np.ndarray) -> np.ndarray:
    mask = np.ones(len(arrays[0]), dtype=bool)
    for array in arrays:
        mask &= np.isfinite(array)
    return mask


def _beta_fraction(a: float, b: float, x: float) -> float:
    max_iterations = 300
    epsilon = 3.0e-14
    tiny = 1.0e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < epsilon:
            return h
    raise ArithmeticError("Incomplete beta continued fraction did not converge")


def regularized_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_bt = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    bt = math.exp(log_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _beta_fraction(a, b, x) / a
    return 1.0 - bt * _beta_fraction(b, a, 1.0 - x) / b


def student_t_two_sided_p(t_value: float, degrees_freedom: int) -> float:
    if not math.isfinite(t_value) or degrees_freedom <= 0:
        return math.nan
    x = degrees_freedom / (degrees_freedom + t_value * t_value)
    return min(max(regularized_beta(degrees_freedom / 2.0, 0.5, x), 0.0), 1.0)


def student_t_cdf(t_value: float, degrees_freedom: int) -> float:
    if t_value == 0.0:
        return 0.5
    tail_twice = student_t_two_sided_p(t_value, degrees_freedom)
    return 1.0 - tail_twice / 2.0 if t_value > 0 else tail_twice / 2.0


def student_t_critical_975(degrees_freedom: int) -> float:
    low, high = 0.0, 10.0
    for _ in range(100):
        mid = (low + high) / 2.0
        if student_t_cdf(mid, degrees_freedom) < 0.975:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def model_matrix(
    rows: list[dict[str, float | str]], include_bmi: bool
) -> tuple[np.ndarray, list[str], dict[str, str]]:
    columns = [
        np.ones(len(rows)),
        values(rows, "age"),
        (values(rows, "sex") == 1).astype(float),
        (values(rows, "fx_type") == 1).astype(float),
        8.0 - values(rows, "KOVAL"),
        8.0 - values(rows, "FIM"),
        values(rows, "CCI"),
        (values(rows, "anesthesia") == 2).astype(float),
        (values(rows, "anesthesia") == 3).astype(float),
        (values(rows, "surgery_type") == 2).astype(float),
    ]
    names = [
        "Intercept",
        "Age, per year",
        "Male sex",
        "Intertrochanteric fracture",
        "Koval grade, per grade",
        "FIM grade, per grade",
        "CCI, per point",
        "Spinal anesthesia",
        "Epidural anesthesia",
        "Internal fixation",
    ]
    references = {
        "Male sex": "Female",
        "Intertrochanteric fracture": "Femoral neck fracture",
        "Spinal anesthesia": "General anesthesia",
        "Epidural anesthesia": "General anesthesia",
        "Internal fixation": "Arthroplasty",
    }
    if include_bmi:
        columns.append(values(rows, "BMI"))
        names.append("BMI, per kg/m2")
    return np.column_stack(columns), names, references


def basic_matrix(
    rows: list[dict[str, float | str]],
) -> tuple[np.ndarray, list[str], dict[str, str]]:
    return (
        np.column_stack(
            [
                np.ones(len(rows)),
                values(rows, "age"),
                (values(rows, "sex") == 1).astype(float),
            ]
        ),
        ["Intercept", "Age, per year", "Male sex"],
        {"Male sex": "Female"},
    )


def fit_ols(y: np.ndarray, x: np.ndarray, names: list[str]) -> dict[str, object]:
    mask = complete_mask(y, *[x[:, i] for i in range(x.shape[1])])
    y_used = y[mask]
    x_used = x[mask]
    n, k = x_used.shape
    beta = np.linalg.lstsq(x_used, y_used, rcond=None)[0]
    residuals = y_used - x_used @ beta
    sse = float(residuals.T @ residuals)
    degrees_freedom = n - k
    sigma2 = sse / degrees_freedom
    covariance = sigma2 * np.linalg.pinv(x_used.T @ x_used)
    standard_errors = np.sqrt(np.diag(covariance))
    t_critical = student_t_critical_975(degrees_freedom)
    y_centered = y_used - y_used.mean()
    sst = float(y_centered.T @ y_centered)
    r_squared = 1.0 - sse / sst if sst > 0 else math.nan
    adjusted_r_squared = (
        1.0 - (1.0 - r_squared) * (n - 1) / degrees_freedom
        if math.isfinite(r_squared)
        else math.nan
    )
    aic = n * (math.log(2.0 * math.pi) + 1.0 + math.log(sse / n)) + 2.0 * k

    terms = []
    for name, estimate, standard_error in zip(names, beta, standard_errors):
        t_value = float(estimate / standard_error)
        p_value = student_t_two_sided_p(t_value, degrees_freedom)
        terms.append(
            {
                "predictor": name,
                "beta": float(estimate),
                "standard_error": float(standard_error),
                "ci_lower": float(estimate - t_critical * standard_error),
                "ci_upper": float(estimate + t_critical * standard_error),
                "t_value": t_value,
                "p_value": p_value,
            }
        )
    return {
        "terms": terms,
        "n": n,
        "degrees_freedom": degrees_freedom,
        "r_squared": r_squared,
        "adjusted_r_squared": adjusted_r_squared,
        "aic": aic,
        "rank": int(np.linalg.matrix_rank(x_used)),
        "parameter_count": k,
    }


def outcome_specs(
    rows: list[dict[str, float | str]], fat_multiplier: float = 10.0
) -> list[dict[str, object]]:
    return [
        {
            "label": "Total thigh normalized volume",
            "unit": "cm3/m2",
            "formula": "femoral_total_volume * 10",
            "values": values(rows, "femoral_total_volume") * 10.0,
        },
        {
            "label": "Gluteal normalized volume",
            "unit": "cm3/m2",
            "formula": "gluteal_total * 10",
            "values": values(rows, "gluteal_total") * 10.0,
        },
        {
            "label": "Anterior normalized volume",
            "unit": "cm3/m2",
            "formula": "anterior_Total * 10",
            "values": values(rows, "anterior_Total") * 10.0,
        },
        {
            "label": "Gluteal fat-to-pure volume ratio",
            "unit": "manuscript scale" if fat_multiplier == 10.0 else "%",
            "formula": f"gluteal_fat / gluteal_pure * {fat_multiplier:g}",
            "values": values(rows, "gluteal_fat")
            / values(rows, "gluteal_pure")
            * fat_multiplier,
        },
        {
            "label": "Anterior fat-to-pure volume ratio",
            "unit": "manuscript scale" if fat_multiplier == 10.0 else "%",
            "formula": f"anterior_fat / anterior_pure * {fat_multiplier:g}",
            "values": values(rows, "anterior_fat")
            / values(rows, "anterior_pure")
            * fat_multiplier,
        },
    ]


def calculate_vif(x: np.ndarray, names: list[str]) -> list[dict[str, object]]:
    results = []
    for column_index in range(1, x.shape[1]):
        y = x[:, column_index]
        other = np.delete(x, column_index, axis=1)
        mask = complete_mask(y, *[other[:, i] for i in range(other.shape[1])])
        y_used = y[mask]
        other_used = other[mask]
        coefficients = np.linalg.lstsq(other_used, y_used, rcond=None)[0]
        residuals = y_used - other_used @ coefficients
        sse = float(residuals.T @ residuals)
        centered = y_used - y_used.mean()
        sst = float(centered.T @ centered)
        r_squared = 1.0 - sse / sst if sst > 0 else 0.0
        vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else math.inf
        if vif < 2.0:
            interpretation = "Low"
        elif vif < 5.0:
            interpretation = "Moderate"
        else:
            interpretation = "High"
        results.append(
            {
                "predictor": names[column_index],
                "vif": vif,
                "interpretation": interpretation,
                "n": int(mask.sum()),
            }
        )
    return results


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def format_p(value: float) -> str:
    if not math.isfinite(value):
        return "NA"
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"

