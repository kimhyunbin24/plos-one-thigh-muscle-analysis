import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const analysisRoot = path.dirname(scriptDir);
const outputDir = path.join(analysisRoot, "outputs");
const qaDir = path.join(scriptDir, "_qa");
const records = JSON.parse(
  await fs.readFile(path.join(outputDir, "comment15_regression_full.json"), "utf8"),
);

const workbook = Workbook.create();
const regression = workbook.worksheets.add("Regression");
const specifications = workbook.worksheets.add("Model Specs");
const authorReview = workbook.worksheets.add("Author Review");

regression.showGridLines = false;
specifications.showGridLines = false;
authorReview.showGridLines = false;

const title = regression.getRange("A1");
title.values = [["Comment 15 regression results"]];
title.format.font = { name: "Arial", size: 15, bold: true, color: "#000000" };
regression.getRange("A2").values = [[
  "Unstandardized coefficients reconstructed from the available revision code",
]];
regression.getRange("A2").format.font = { name: "Arial", size: 10, italic: true, color: "#404040" };

const headers = [
  "Outcome",
  "Unit",
  "Model",
  "Predictor",
  "Reference",
  "Beta",
  "SE",
  "CI lower",
  "CI upper",
  "p value",
  "N",
  "Adjusted R2",
  "AIC",
];
regression.getRange("A4:M4").values = [headers];

const matrix = records.map((record) => [
  record.outcome,
  record.outcome_unit,
  record.model,
  record.predictor,
  record.reference_category,
  Number(record.beta),
  Number(record.standard_error),
  Number(record.ci_lower),
  Number(record.ci_upper),
  Number(record.p_value),
  Number(record.sample_size),
  Number(record.adjusted_r_squared),
  Number(record.aic),
]);
regression.getRange(`A5:M${matrix.length + 4}`).values = matrix;

const headerRange = regression.getRange("A4:M4");
headerRange.format = {
  fill: "#1F4E78",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "all", style: "thin", color: "#D9D9D9" },
};
const dataRange = regression.getRange(`A5:M${matrix.length + 4}`);
dataRange.format.font = { name: "Arial", size: 9, color: "#000000" };
dataRange.format.verticalAlignment = "center";
dataRange.format.borders = { preset: "all", style: "thin", color: "#E6E6E6" };
regression.getRange(`F5:J${matrix.length + 4}`).format.numberFormat = "0.0000";
regression.getRange(`K5:K${matrix.length + 4}`).format.numberFormat = "#,##0";
regression.getRange(`L5:L${matrix.length + 4}`).format.numberFormat = "0.000";
regression.getRange(`M5:M${matrix.length + 4}`).format.numberFormat = "0.0";
regression.getRange(`A5:E${matrix.length + 4}`).format.wrapText = true;
regression.freezePanes.freezeRows(4);
regression.freezePanes.freezeColumns(3);

const widths = [27, 16, 25, 27, 23, 12, 12, 12, 12, 12, 9, 14, 13];
widths.forEach((width, index) => {
  regression.getRangeByIndexes(0, index, matrix.length + 4, 1).format.columnWidth = width;
});
regression.getRange("1:4").format.autofitRows();

for (let row = 5; row <= matrix.length + 4; row += 2) {
  regression.getRange(`A${row}:M${row}`).format.fill = "#F4F7FA";
}

specifications.getRange("A1").values = [["Regression model specification"]];
specifications.getRange("A1").format.font = { name: "Arial", size: 15, bold: true, color: "#000000" };
specifications.getRange("A3:D3").values = [["Item", "Implementation", "Reference category", "Author review"]];
specifications.getRange("A4:D14").values = [
  ["Age", "Continuous years", "", "Manuscript states age group"],
  ["Sex", "Male indicator", "Female", ""],
  ["Fracture type", "Intertrochanteric indicator", "Femoral neck", ""],
  ["Fracture side", "Not included", "", "Manuscript states it was included"],
  ["Koval", "Reversed ordinal grade 8 minus source code", "", "Treated as linear"],
  ["FIM", "Reversed ordinal grade 8 minus source code", "", "Treated as linear"],
  ["CCI", "Continuous points", "", ""],
  ["Anesthesia", "Spinal and epidural indicators", "General", "Dummy-level coefficients"],
  ["Surgery", "Internal fixation indicator", "Arthroplasty", ""],
  ["BMI", "Continuous kg/m2 in Model 3", "", "Model 2 omits BMI"],
  ["Fat outcome", "Fat divided by pure volume times 10", "", "Not a conventional percent scale"],
];

authorReview.getRange("A1").values = [["Potential inconsistencies requiring author review"]];
authorReview.getRange("A1").format.font = { name: "Arial", size: 15, bold: true, color: "#000000" };
authorReview.getRange("A3:B3").values = [["Issue", "Required decision"]];
authorReview.getRange("A4:B9").values = [
  ["Original regression code absent", "Confirm that the reconstructable revision model is the intended final analysis"],
  ["Age coding differs", "Choose continuous age or manuscript age groups and revise consistently"],
  ["Fracture side omitted", "Add it if the manuscript continues to state that it was adjusted"],
  ["BMI primary-model wording differs", "Choose BMI-included or BMI-excluded primary model"],
  ["Fat percentage divided by 10", "Define denominator and correct Table 2 and regression units"],
  ["Total thigh label uses femoral variable", "Confirm the anatomical definition of femoral_total_volume"],
];

for (const sheet of [specifications, authorReview]) {
  const used = sheet.getUsedRange();
  used.format.font = { name: "Arial", size: 10, color: "#000000" };
  used.format.wrapText = true;
  used.format.verticalAlignment = "center";
  const headerRow = sheet.name === "Model Specs" ? sheet.getRange("A3:D3") : sheet.getRange("A3:B3");
  headerRow.format = {
    fill: "#404040",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: "#D9D9D9" },
  };
  used.format.autofitRows();
}
specifications.getRange("A:D").format.columnWidth = 27;
specifications.getRange("B:B").format.columnWidth = 42;
specifications.getRange("D:D").format.columnWidth = 35;
authorReview.getRange("A:A").format.columnWidth = 32;
authorReview.getRange("B:B").format.columnWidth = 70;

const inspection = await workbook.inspect({
  kind: "table",
  range: "Regression!A1:M14",
  include: "values,formulas",
  tableMaxRows: 14,
  tableMaxCols: 13,
});
console.log(inspection.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(qaDir, { recursive: true });
const previews = [
  ["Regression", "A1:M25", "comment15_regression_xlsx_preview.png"],
  ["Model Specs", "A1:D14", "comment15_model_specs_xlsx_preview.png"],
  ["Author Review", "A1:B9", "comment15_author_review_xlsx_preview.png"],
];
for (const [sheetName, range, filename] of previews) {
  const preview = await workbook.render({ sheetName, range, scale: 1.3, format: "png" });
  await fs.writeFile(path.join(qaDir, filename), new Uint8Array(await preview.arrayBuffer()));
}
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(path.join(outputDir, "comment15_regression_table.xlsx"));
console.log(path.join(outputDir, "comment15_regression_table.xlsx"));

