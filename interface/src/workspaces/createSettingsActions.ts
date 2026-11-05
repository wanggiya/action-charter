import { APPEARANCE_STORAGE_KEY, type AppearancePreferences } from "../lib/appearance";
import type {ActionContext} from './action-contracts';

export function createSettingsActions(context: ActionContext) {
 const { setAppearance, setAppearanceSaved, 
}=context;
const updateAppearance = (next: AppearancePreferences) => {
    setAppearance(next);
    try { window.localStorage.setItem(APPEARANCE_STORAGE_KEY, JSON.stringify(next)); setAppearanceSaved(true); }
    catch { setAppearanceSaved(false); }
  };
 return {updateAppearance};
}
