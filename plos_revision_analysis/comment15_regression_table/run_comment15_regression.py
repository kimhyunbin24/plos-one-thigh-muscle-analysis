from __future__ import annotations

import sys
from pathlib import Path


ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
if str(ANALYSIS_ROOT / "shared") not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT / "shared"))

from analysis_core import (  # noqa: E402
    OUTPUT_DIR,
    basic_matrix,
    fit_ols,
    format_p,
    load_analysis_rows,
    model_matrix,
    outcome_specs,
    sav_path,
    write_csv,
    write_json,
)


def build_results() -> list[dict[str, object]]:
    rows = load_analysis_rows()
    model_definitions = []

    basic_x, basic_names, basic_refs = basic_matrix(rows)
    model_definitions.append(
        ("Model 1 basic", basic_x, basic_names, basic_refs)
    )

    adjusted_x, adjusted_names, adjusted_refs = model_matrix(rows, include_bmi=False)
    model_definitions.append(
        ("Model 2 adjusted without BMI", adjusted_x, adjusted_names, adjusted_refs)
    )

    bmi_x, bmi_names, bmi_refs = model_matrix(rows, include_bmi=True)
    model_definitions.append(
        ("Model 3 adjusted with BMI", bmi_x, bmi_names, bmi_refs)
    )

    output_rows = []
    for outcome in outcome_specs(rows, fat_multiplier=10.0):
        for model_name, x, names, references in model_definitions:
            fitted = fit_ols(outcome["values"], x, names)
            for term in fitted["terms"]:
                output_rows.append(
                    {
                        "outcome": outcome["label"],
                        "outcome_unit": outcome["unit"],
                        "outcome_formula": outcome["formula"],
                        "model": model_name,
                        "predictor": term["predictor"],
                        "reference_category": references.get(term["predictor"], ""),
                        "beta": term["beta"],
                        "standard_error": term["standard_error"],
                        "ci_lower": term["ci_lower"],
                        "ci_upper": term["ci_upper"],
                        "t_value": term["t_value"],
                        "p_value": term["p_value"],
                        "sample_size": fitted["n"],
                        "degrees_freedom": fitted["degrees_freedom"],
                        "r_squared": fitted["r_squared"],
                        "adjusted_r_squared": fitted["adjusted_r_squared"],
                        "aic": fitted["aic"],
                    }
                )
    return output_rows


def write_key_results(results: list[dict[str, object]]) -> None:
    selected_model = "Model 3 adjusted with BMI"
    selected = [row for row in results if row["model"] == selected_model]
    lines = [
        "# Comment 15 regression results",
        "",
        "## Reproducibility status",
        "",
        "The original pre-submission regression script is not present in the project. "
        "These results reproduce the model implemented in revision_adjusted_analysis.py, "
        "using Student t confidence intervals and p-values.",
        "",
        "The reconstructable script uses continuous age, omits fracture side, and treats "
        "Koval and FIM grades as reversed ordinal scores. These choices differ from parts "
        "of the manuscript methods and require author review before submission.",
        "",
        "## Main adjusted model with BMI",
        "",
    ]

    for outcome in sorted({str(row["outcome"]) for row in selected}):
        lines.append(f"### {outcome}")
        lines.append("")
        outcome_rows = [row for row in selected if row["outcome"] == outcome]
        key_terms = {
            "Age, per year",
            "Male sex",
            "BMI, per kg/m2",
        }
        report_rows = [
            row
            for row in outcome_rows
            if row["predictor"] in key_terms
            or (row["predictor"] != "Intercept" and float(row["p_value"]) < 0.05)
        ]
        for row in report_rows:
            reference = (
                f" vs {row['reference_category']}" if row["reference_category"] else ""
            )
            lines.append(
                f"- {row['predictor']}{reference}: beta {float(row['beta']):.4f}, "
                f"95% CI {float(row['ci_lower']):.4f} to "
                f"{float(row['ci_upper']):.4f}, p {format_p(float(row['p_value']))}, "
                f"n = {row['sample_size']}."
            )
        lines.append("")

    lines.extend(
        [
            "## Muscle group predictor",
            "",
            "Muscle group was not used as a regression predictor in the available code. "
            "The models use separate muscle-group outcomes. It was not added solely because "
            "the reviewer listed it as an example.",
            "",
            "## Fat outcome scale warning",
            "",
            "The available revision script calculates fat outcomes as fat volume divided by "
            "pure volume multiplied by 10. The source Excel percentage is fat divided by pure "
            "volume multiplied by 100. Therefore, the manuscript-scaled fat coefficients are "
            "one tenth of percentage-point coefficients. Resolve the outcome definition and "
            "Table 2 scale before using this table in the manuscript.",
            "",
            "The outcome labeled Total thigh normalized volume is sourced from the variable "
            "femoral_total_volume. Its anatomical meaning and whether it represents a total "
            "thigh compartment require confirmation before publication.",
        ]
    )
    (OUTPUT_DIR / "comment15_key_results.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    results = build_results()
    fields = [
        "outcome",
        "outcome_unit",
        "outcome_formula",
        "model",
        "predictor",
        "reference_category",
        "beta",
        "standard_error",
        "ci_lower",
        "ci_upper",
        "t_value",
        "p_value",
        "sample_size",
        "degrees_freedom",
        "r_squared",
        "adjusted_r_squared",
        "aic",
    ]
    write_csv(OUTPUT_DIR / "comment15_regression_full.csv", results, fields)
    write_json(OUTPUT_DIR / "comment15_regression_full.json", results)
    write_key_results(results)
    print(f"Input: {sav_path()}")
    print(f"Regression rows written: {len(results)}")
    print(OUTPUT_DIR / "comment15_regression_full.csv")
    print(OUTPUT_DIR / "comment15_key_results.md")


if __name__ == "__main__":
    main()

