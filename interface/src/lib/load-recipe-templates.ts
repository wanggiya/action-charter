import { recipeTemplateCatalogSchema, type RecipeTemplate } from "./recipe-templates";
import { loadApiRecipeTemplates } from "./interface-api";

const MAX_TEMPLATE_CATALOG_BYTES = 250_000;

export async function loadRecipeTemplates(): Promise<RecipeTemplate[]> {
  try {
    return await loadApiRecipeTemplates();
  } catch {
    // Keep the bounded static projection as an offline/read-only fallback.
  }
  const response = await fetch("/runtime/recipe-templates.json", { cache: "no-store", credentials: "same-origin" });
  if (!response.ok) throw new Error("recipe template catalog is unavailable");
  const declaredLength = Number(response.headers.get("content-length") ?? "0");
  if (declaredLength > MAX_TEMPLATE_CATALOG_BYTES) throw new Error("recipe template catalog is too large");
  const text = await response.text();
  if (new TextEncoder().encode(text).byteLength > MAX_TEMPLATE_CATALOG_BYTES) throw new Error("recipe template catalog is too large");
  return recipeTemplateCatalogSchema.parse(JSON.parse(text)).templates;
}
