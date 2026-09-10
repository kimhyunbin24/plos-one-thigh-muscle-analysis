# Comment 26 post hoc analysis

This analysis compares height-squared normalized total muscle volumes measured repeatedly in the same participants.

- Primary family: four anatomical compartments, assessed by one-way repeated-measures ANOVA with Greenhouse-Geisser correction and six paired t-tests with Holm correction.
- Exploratory family: 21 individual muscles, assessed by paired t-tests with Holm correction within a separate family.
- IMAT is intentionally excluded until its operational definition and scale are finalized.

Run from the project root after setting `CT_VOLUME_SAV_PATH` or `CT_VOLUME_DATA_DIR`:

```powershell
python plos_revision_analysis\comment26_posthoc\run_comment26_posthoc.py
```

Aggregate CSV, Word, and response-draft outputs are saved under `plos_revision_analysis/outputs/comment26_posthoc/`.

