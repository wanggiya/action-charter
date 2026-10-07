export type AppearancePreferences = {
  buttonStyle: "filled" | "outline";
  filledText: "black" | "white";
};
export const APPEARANCE_STORAGE_KEY = "actioncharter:appearance:v2";
export const DEFAULT_APPEARANCE: AppearancePreferences = { buttonStyle: "outline", filledText: "black" };

export function loadAppearance(): AppearancePreferences {
  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(APPEARANCE_STORAGE_KEY) ?? "null");
    if (value && typeof value === "object" && "buttonStyle" in value && "filledText" in value
        && (value.buttonStyle === "filled" || value.buttonStyle === "outline")
        && (value.filledText === "black" || value.filledText === "white")) {
      return { buttonStyle: value.buttonStyle, filledText: value.filledText };
    }
    // Start the expanded material defaults in Outline while retaining the prior
    // filled-text choice. Explicit selections saved in v2 remain authoritative.
    const legacy: unknown = JSON.parse(window.localStorage.getItem("actioncharter:appearance:v1") ?? "null");
    if (legacy && typeof legacy === "object" && "filledText" in legacy && legacy.filledText === "white") {
      return { buttonStyle: "outline", filledText: "white" };
    }
  } catch { /* A blocked store or malformed preference must not block the workspace. */ }
  return { ...DEFAULT_APPEARANCE };
}
