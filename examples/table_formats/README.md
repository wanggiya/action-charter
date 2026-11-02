# Flat record tables

Synthetic, unrelated-to-health data for shared table-source acceptance. IDs are text;
x/y are explicitly declared measurements in the analysis example, not inferred units.
Both files contain the same four records. No XLSX binary or private dataset is bundled;
automated tests generate XLSX workbooks in temporary projects.

Copy `records.json` or `records.jsonl` under data/input to use the normal interface.
Ask to inspect it, then compute descriptive statistics for x grouped by region.
Expect four rows, mean x=1.5, sample variance=5/3, group A mean=0.5 and B mean=2.5.
Pearson x/y is approximately 0.982707629824, conditional on the documented assumptions.
No writes are required for inspection/analysis; report download is local browser export.

[Combined frontend/CLI/MCP validation](../../docs/TABLE_FORMATS_AND_STATISTICAL_FIGURES.md).
