import type { PlannerSkillCatalog } from "./interface-api";

export const skillRecommendationScore = (skill: PlannerSkillCatalog["skills"][number], request: string) => {
  const text = request.toLowerCase();
  const tokens = new Set(text.match(/[a-z0-9]+/g) ?? []);
  const skillTokens = skill.id.split("_");
  let score = skillTokens.filter((token) => tokens.has(token)).length * 3;
  if (/\b(geojson|gpkg|shapefile|vector|feature)\b/.test(text) && skill.id.includes("vector")) score += 2;
  if (/\b(tif|tiff|raster|imagery)\b/.test(text) && skill.id.includes("raster")) score += 2;
  if (/\bpostgis\b/.test(text) && skill.id.includes("postgis")) score += 3;
  if (/\bgeoserver\b/.test(text) && skill.id.includes("geoserver")) score += 3;
  if (/\binspect\b/.test(text) && skill.id.startsWith("inspect_")) score += 4;
  if (/\b(convert|conversion)\b/.test(text) && skill.id.startsWith("convert_")) score += 4;
  if (/\b(load|import)\b/.test(text) && skill.id.startsWith("load_")) score += 4;
  if (/\b(validate|validation|verify)\b/.test(text) && /validate|verify/.test(skill.id)) score += 4;
  if (/\b(report|reporting)\b/.test(text) && skill.id.includes("report")) score += 4;
  return score;
};
