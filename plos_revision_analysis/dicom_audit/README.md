# Comment 46 DICOM audit

This script reads DICOM headers only. It does not modify DICOM files or load pixel data.

## Dependency

```powershell
python -m pip install -r requirements.txt
```

## Fast preliminary audit (default)

Read only the first 1,000 directly stored DICOM instances. ZIP files are skipped:

```powershell
python plos_revision_analysis/dicom_audit/run_comment46_dicom_audit.py --root "<path-to-dicom-root>"
```

This is a rapid convenience sample and may not represent all five institutions.

## Full audit

```powershell
python plos_revision_analysis/dicom_audit/run_comment46_dicom_audit.py --root "<path-to-dicom-root>" --max-files 0 --include-zip
```

The full audit also reads DICOM members inside ZIP archives and may take a long time.

## Outputs

- `comment46_series_metadata.csv`: one de-identified row per CT series
- `comment46_institution_summary.csv`: institution-level protocol summary
- `comment46_dicom_audit_report.md`: concise interpretation and limitations

Patient names, medical record numbers, raw patient IDs, file names, and source paths are not exported.

Anatomical L3/L4 start level, complete knee coverage, and bilateral thigh inclusion cannot be established reliably from headers alone. They require pixel-level review or a separate anatomical-coverage algorithm.

