# Comment 15 Regression Table

## Input data

- `data키제곱나눈값.sav`, 1,287 final-cohort records.

## Existing analysis code reviewed

- `revision_adjusted_analysis.py` for outcome definitions, covariates, coding, and the three model forms.
- `manuscript.docx` for the stated regression method.

The original pre-submission regression script was not found. This analysis reproduces the model
currently implemented in `revision_adjusted_analysis.py` and uses Student t confidence intervals
and p-values.

## Purpose

Generate coefficients, standard errors, 95% confidence intervals, p-values, sample sizes, and
model-fit statistics for the available multivariable regression models.

## Run

```powershell
python plos_revision_analysis\comment15_regression_table\run_comment15_regression.py
python plos_revision_analysis\comment15_regression_table\build_table3_docx.py
node plos_revision_analysis\shared\build_comment15_xlsx.mjs
```

## Outputs

- `outputs/comment15_regression_full.csv`
- `outputs/comment15_regression_full.json`, intermediate input for document builders.
- `outputs/comment15_regression_table.xlsx`
- `outputs/Table3_regression_results.docx`
- `outputs/comment15_key_results.md`

## Main results

All models used N = 1,287. The BMI-included adjusted model shows statistically supported age and
sex associations for the three normalized-volume outcomes, except age for the two fat-ratio
outcomes. Exact values are in the output table.

Muscle group was not a predictor in the available model. Separate group metrics were used as
outcomes, so a group predictor was not added.

## Manuscript and response cautions

- Current code uses continuous age, but the manuscript states age-group adjustment.
- Current code omits fracture side, but the manuscript states that fracture side was included.
- Koval and FIM are reversed and treated as linear ordinal grades.
- Fat outcomes use `fat / pure * 10`, which matches the current script but is not a conventional percentage scale.
- The outcome labeled Total thigh uses `femoral_total_volume`; its anatomical definition requires confirmation.
- The Word table is a candidate for author review and must not be inserted unchanged until these points are resolved.

