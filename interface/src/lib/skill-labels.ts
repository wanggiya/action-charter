/** Presentation labels only. Backend IDs remain the capability authority. */
const names: Record<string, string> = {
  calculate_csv_columns:"Calculate table columns",inspect_csv:"Inspect CSV table",select_csv_columns:"Select table columns",filter_csv_rows:"Filter table rows",handle_csv_missing:"Handle missing table values",join_csv:"Join CSV tables",aggregate_csv:"Group and aggregate table",export_csv:"Export CSV results",vector_attributes_to_csv:"Extract vector attributes as CSV",
  export_snakemake_workflow: "Export to Snakemake", verify_snakemake_export: "Verify Snakemake package",
  inspect_vector: "Inspect vector dataset", inspect_raster: "Inspect raster dataset",
  convert_vector: "Convert vector format", convert_raster: "Convert raster format",
  inspect_postgis_table: "Inspect PostGIS table", compare_postgis_tables: "Compare PostGIS tables",
  load_vector_to_postgis: "Load vector into PostGIS", validate_postgis_layer: "Validate PostGIS layer",
  generate_report: "Create workflow report", assess_spatial_data_contract: "Check spatial data requirements",
  inspect_geoserver_layer: "Inspect GeoServer layer", plan_geoserver_publication: "Plan GeoServer publication",
  assess_postgis_change: "Assess PostGIS changes", plan_postgis_promotion: "Plan PostGIS promotion",
};
export function skillLabel(id: string): string {
  return names[id] ?? id.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

export function registerSkillNames(skills: {id:string;name?:string}[]) {
  for (const skill of skills) if (skill.name) names[skill.id]=skill.name;
}
