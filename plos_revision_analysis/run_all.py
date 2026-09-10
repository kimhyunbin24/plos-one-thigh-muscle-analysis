from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    ROOT / "comment15_regression_table" / "run_comment15_regression.py",
    ROOT / "comment18_postop_outcomes" / "run_comment18_outcome_audit.py",
    ROOT / "comment20_exclusion_counts" / "run_comment20_exclusion_counts.py",
    ROOT / "comment24_volume_measure_audit" / "run_comment24_audit.py",
    ROOT / "comment27_vif_sensitivity" / "run_comment27_vif.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"\nRunning {script.relative_to(ROOT)}", flush=True)
        subprocess.run([sys.executable, str(script)], check=True)
    print("\nAnalysis CSV and Markdown outputs completed.")
    print("Run comment15_regression_table/build_table3_docx.py for the Word table.")
    print("Run shared/build_comment15_xlsx.mjs with Node.js for the Excel workbook.")


if __name__ == "__main__":
    main()

