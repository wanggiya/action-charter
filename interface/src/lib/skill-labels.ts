/** Presentation labels only. Backend IDs remain the capability authority. */
const names: Record<string, string> = {
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
