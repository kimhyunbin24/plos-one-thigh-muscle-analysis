from __future__ import annotations

import math
import sys
from pathlib import Path


ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
if str(ANALYSIS_ROOT / "shared") not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT / "shared"))

from analysis_core import (  # noqa: E402
    OUTPUT_DIR,
    calculate_vif,
    fit_ols,
    format_p,
    load_analysis_rows,
    model_matrix,
    outcome_specs,
    write_csv,
)


def fit_models(rows: list[dict[str, float | str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    x_with, names_with, _ = model_matrix(rows, include_bmi=True)
    x_without, names_without, _ = model_matrix(rows, include_bmi=False)

    vif_rows = []
    for model_name, x, names in [
        ("Model A adjusted with BMI", x_with, names_with),
        ("Model B adjusted without BMI", x_without, names_without),
    ]:
        for row in calculate_vif(x, names):
            vif_rows.append({"model": model_name, **row})

    sensitivity_rows = []
    for outcome in outcome_specs(rows, fat_multiplier=10.0):
        model_a = fit_ols(outcome["values"], x_with, names_with)
        model_b = fit_ols(outcome["values"], x_without, names_without)
        terms_a = {row["predictor"]: row for row in model_a["terms"]}
        terms_b = {row["predictor"]: row for row in model_b["terms"]}
        for predictor in names_without[1:]:
            a = terms_a[predictor]
            b = terms_b[predictor]
            beta_a = float(a["beta"])
            beta_b = float(b["beta"])
            change = (
                abs(beta_a - beta_b) / abs(beta_b) * 100.0
                if abs(beta_b) > 1.0e-12
                else math.nan
            )
            sensitivity_rows.append(
                {
                    "outcome": outcome["label"],
                    "outcome_unit": outcome["unit"],
                    "predictor": predictor,
                    "beta_model_a_with_bmi": beta_a,
                    "ci_lower_model_a": a["ci_lower"],
                    "ci_upper_model_a": a["ci_upper"],
                    "p_model_a": a["p_value"],
                    "beta_model_b_without_bmi": beta_b,
                    "ci_lower_model_b": b["ci_lower"],
                    "ci_upper_model_b": b["ci_upper"],
                    "p_model_b": b["p_value"],
                    "direction_same": (beta_a >= 0) == (beta_b >= 0),
                    "significance_same_at_0_05":
                    (float(a["p_value"]) < 0.05) == (float(b["p_value"]) < 0.05),
                    "absolute_effect_change_percent": change,
                    "sample_size_model_a": model_a["n"],
                    "sample_size_model_b": model_b["n"],
                    "r_squared_model_a": model_a["r_squared"],
                    "r_squared_model_b": model_b["r_squared"],
                    "adjusted_r_squared_model_a": model_a["adjusted_r_squared"],
                    "adjusted_r_squared_model_b": model_b["adjusted_r_squared"],
                    "aic_model_a": model_a["aic"],
                    "aic_model_b": model_b["aic"],
                }
            )
    return vif_rows, sensitivity_rows


def write_summary(vif_rows: list[dict[str, object]], sensitivity_rows: list[dict[str, object]]) -> None:
    with_bmi = [row for row in vif_rows if row["model"] == "Model A adjusted with BMI"]
    highest = max(with_bmi, key=lambda row: float(row["vif"]))
    bmi = next(row for row in with_bmi if row["predictor"] == "BMI, per kg/m2")
    key_rows = [
        row
        for row in sensitivity_rows
        if row["predictor"] in {"Age, per year", "Male sex"}
    ]
    stable_direction = sum(bool(row["direction_same"]) for row in key_rows)
    stable_significance = sum(bool(row["significance_same_at_0_05"]) for row in key_rows)

    lines = [
        "# Comment 27 VIF and BMI sensitivity",
        "",
        "## VIF results",
        "",
        f"The highest VIF in the BMI-included model was {float(highest['vif']):.2f} "
        f"for {highest['predictor']}. The BMI VIF was {float(bmi['vif']):.2f}. "
        "This does not indicate strong linear dependence between BMI and the other "
        "covariates in the reconstructable model.",
        "",
        "VIF evaluates multicollinearity. It does not establish whether BMI is a causal "
        "overadjustment variable or whether the model is clinically appropriate.",
        "",
        "Koval and FIM were entered as ordinal numeric scores. Anesthesia was represented "
        "by separate spinal and epidural indicator variables with general anesthesia as "
        "the reference. Dummy-level VIFs are reported rather than a multi-degree-of-freedom GVIF.",
        "",
        "## BMI sensitivity",
        "",
        f"Across the {len(key_rows)} age and sex comparisons, direction was unchanged in "
        f"{stable_direction} and statistical significance at p < 0.05 was unchanged in "
        f"{stable_significance}. Predictor-level estimates and model-fit measures are in "
        "comment27_bmi_sensitivity.csv.",
        "",
        "The current code omits fracture side and uses continuous age, whereas the manuscript "
        "states adjustment for fracture side and age group. Resolve that specification before "
        "describing the BMI sensitivity analysis as the final manuscript model.",
        "",
        "The fat outcome scaling warning in Comment 15 also applies here. Multiplying the fat "
        "ratio by 100 instead of 10 changes beta coefficients and confidence intervals by a "
        "factor of 10 but leaves p-values, VIFs, and model fit conclusions unchanged.",
    ]
    (OUTPUT_DIR / "comment27_bmi_sensitivity_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    rows = load_analysis_rows()
    vif_rows, sensitivity_rows = fit_models(rows)
    write_csv(
        OUTPUT_DIR / "comment27_vif.csv",
        vif_rows,
        ["model", "predictor", "vif", "interpretation", "n"],
    )
    write_csv(
        OUTPUT_DIR / "comment27_bmi_sensitivity.csv",
        sensitivity_rows,
        [
            "outcome",
            "outcome_unit",
            "predictor",
            "beta_model_a_with_bmi",
            "ci_lower_model_a",
            "ci_upper_model_a",
            "p_model_a",
            "beta_model_b_without_bmi",
            "ci_lower_model_b",
            "ci_upper_model_b",
            "p_model_b",
            "direction_same",
            "significance_same_at_0_05",
            "absolute_effect_change_percent",
            "sample_size_model_a",
            "sample_size_model_b",
            "r_squared_model_a",
            "r_squared_model_b",
            "adjusted_r_squared_model_a",
            "adjusted_r_squared_model_b",
            "aic_model_a",
            "aic_model_b",
        ],
    )
    write_summary(vif_rows, sensitivity_rows)
    print(f"VIF rows written: {len(vif_rows)}")
    print(f"Sensitivity rows written: {len(sensitivity_rows)}")
    print(OUTPUT_DIR / "comment27_vif.csv")


if __name__ == "__main__":
    main()


