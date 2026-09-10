# AI-based Thigh Muscle Volume Profiling Analysis Code

This repository contains author-generated analysis scripts for the manuscript:

Artificial Intelligence-based Thigh Muscle Volume Profiling on CT in Elderly East Asian Patients with Hip Fracture

## Contents

- `table1_print.py`: Reproduces Table 1 baseline characteristics and exports a Word table.
- `table2_print.py`: Reproduces Table 2 muscle volume and fat percentage descriptive results and exports a Word table.
- `revision_adjusted_analysis.py`: Generates revision analyses, including height-squared normalized volume summaries, pairwise group comparisons with multiple-comparison correction, multivariable regression models, BMI sensitivity analyses, and variance inflation factors.

## Files Not Included

Patient-level clinical data, CT-derived datasets, spreadsheet files, SPSS files, Word outputs, and PDF files are not included in this repository.

## Data Availability

The clinical imaging dataset is not included in this repository because it contains patient-level clinical and CT-derived information and is subject to institutional and ethical restrictions. Qualified researchers may request access according to the Data Availability Statement in the published manuscript.

## Requirements

The scripts were written and tested with:

- Python 3.12.14
- numpy 2.3.5
- python-docx 1.2.0
- openpyxl 3.1.5

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Place the approved analysis dataset files in a local `data/` directory:

- `data/data키제곱나눈값.sav`
- `data/RWD_muscle_estimation_수술전_1126 - 복사본.xlsx`

Alternatively, set environment variables:

- `CT_VOLUME_DATA_DIR`: directory containing the approved analysis files
- `CT_VOLUME_SAV_PATH`: full path to the SPSS `.sav` file
- `CT_VOLUME_EXCEL_PATH`: full path to the Excel file used for Table 2

Then run:

```bash
python table1_print.py
python table2_print.py
python revision_adjusted_analysis.py
```

The scripts print the results to the console and save Word-format output tables in the working directory.

## Expected Outputs

- `table1_output.docx`
- `table2_output.docx`
- `revision_normalized_volume_table.docx`
- `revision_pairwise_comparison_table.docx`
- `revision_adjusted_regression_table.docx`
- `revision_vif_table.docx`

These output files are generated locally and are intentionally excluded from the public repository.

## Code Availability Statement

The author-generated analysis code supporting the findings of this study will be made publicly available without restriction upon publication at:

`https://github.com/kimhyunbin24/plos-one-thigh-muscle-analysis`

## License

This code is released under the MIT License.

