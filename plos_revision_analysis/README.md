# PLOS ONE Revision Analysis

This folder contains new, revision-specific analysis code and outputs. The original data,
manuscript, and analysis scripts outside this folder were not modified.

## Status

| Comment | Analysis completed | Key finding | Manuscript change needed | Output files |
|---|---|---|---|---|
| 15 | Yes, for the model reconstructable from the available revision code | Full beta, SE, 95% CI, p-value, N, and fit statistics were generated for five outcomes | Yes. Confirm model specification and resolve the fat scale before insertion | `comment15_regression_full.csv`, `comment15_regression_table.xlsx`, `Table3_regression_results.docx`, `comment15_key_results.md` |
| 18 | Availability audit completed; exploratory model not run | No postoperative outcome has adequate completeness. Mortality is usable in only 126 of 1,287 records | State that postoperative outcomes were unavailable and add a prospective-study limitation | `comment18_outcome_availability.csv`, `comment18_outcome_availability_report.md` |
| 20 | Existing figure counts reconciled; fracture-related union independently reproduced | Figure 2 totals reconcile to 1,287 and the combined fracture-related exclusion remains exactly 852 in the available master registry. Separate pathologic-fracture and patient-level CT/record flags remain unavailable | Retain the verified combined fracture-related category unless the archived screening log is recovered | `comment20_exclusion_sequential.csv`, `comment20_exclusion_overlap.csv`, `comment20_flow_counts.md` |
| 24 | Audit completed | Table 2 uses absolute cm3. Current regression code uses normalized cm3/m2. The printed fat percentage is one tenth of the Excel source percentage | Revise Methods, Results, Table 2, and regression labels after author decision | `comment24_volume_measure_audit.csv`, `comment24_fat_percentage_scale_check.csv`, `comment24_volume_measure_audit.md` |
| 27 | Yes, for the reconstructable model | BMI VIF is 1.03; maximum VIF is 4.97. Age and sex significance status is unchanged in all 10 comparisons | Report VIF and BMI sensitivity, but do not use VIF as evidence against causal overadjustment | `comment27_vif.csv`, `comment27_bmi_sensitivity.csv`, `comment27_bmi_sensitivity_summary.md` |

## Inputs

- `data키제곱나눈값.sav`: final analysis cohort, 1,287 records.
- `RWD_muscle_estimation_수술전_1126 - 복사본.xlsx`: CT and clinical registry export.
- `manuscript.docx`: manuscript methods and results statements.
- Existing project scripts: `table1_print.py`, `table2_print.py`, and `revision_adjusted_analysis.py`.
- Existing Figure 2: aggregate cohort flow counts.

No patient-level data are copied into this folder. Output tables contain aggregate counts or
model coefficients only.

## Run

Set the approved input paths before execution:

```powershell
$env:CT_VOLUME_DATA_DIR = "<path-to-analysis-data>"
$env:CT_VOLUME_MANUSCRIPT_PATH = "<path-to-manuscript.docx>"
python plos_revision_analysis\run_all.py
python plos_revision_analysis\comment15_regression_table\build_table3_docx.py
node plos_revision_analysis\shared\build_comment15_xlsx.mjs
```

The scripts check the local `data` directory by default. Environment variables
should be used when the restricted input files are stored outside the repository.

The Python analysis uses `numpy`, `openpyxl`, and `python-docx`. The Excel builder uses
`@oai/artifact-tool`. Source data remain read-only.

## Current decision points

The outputs are analysis evidence, not automatic manuscript edits. The author must decide the
final fat percentage definition, age coding, fracture-side adjustment, and primary BMI model.
Comment 20 still requires the archived screening log for a defensible pathologic-fracture split and patient-level reconstruction of the record/CT exclusions.

