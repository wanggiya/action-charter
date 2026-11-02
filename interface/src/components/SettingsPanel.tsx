import {WritePolicySettings} from "../lib/write-policy";
import { MethodHelperSettings } from "./MethodHelperSettings";
import { OperationsPanel } from "./OperationsPanel";
import { ModelSettings } from "./ModelSettings";
import { X, Settings as SettingsIcon, Play, CircleAlert } from "lucide-react";
import type { AppearancePreferences } from "../lib/appearance";
type Props = { onClose: () => void; appearance: AppearancePreferences; appearanceSaved: boolean; onAppearanceChange: (value: AppearancePreferences) => void };
export function SettingsPanel({ onClose, appearance, appearanceSaved, onAppearanceChange }: Props) {
  return <div className="template-overlay"><section className="settings-workspace record-workspace" role="dialog" aria-modal="true" aria-labelledby="settings-title"><header className="template-workspace-head"><h2 id="settings-title"><SettingsIcon size={20}/> Settings</h2><button aria-label="Close settings" onClick={onClose}><X size={18}/></button></header><section className="appearance-settings" aria-labelledby="appearance-title"><h3 id="appearance-title">Appearance</h3>
      <label>Interface style<select aria-label="Interface style" value={appearance.buttonStyle} onChange={(event) => onAppearanceChange({ ...appearance, buttonStyle: event.target.value === "outline" ? "outline" : "filled" })}><option value="filled">Solid fill</option><option value="outline">Outline · tinted edges</option></select></label>
      <label>Solid-fill text color<select aria-label="Solid-fill text color" value={appearance.filledText} disabled={appearance.buttonStyle === "outline"} onChange={(event) => onAppearanceChange({ ...appearance, filledText: event.target.value === "white" ? "white" : "black" })}><option value="black">Black</option><option value="white">White</option></select></label>
      <p>{appearance.buttonStyle === "outline" ? "Outline controls and graph blocks use softly tinted top/bottom edges, a clear center and opaque text/icons." : "Solid controls, graph blocks and information sections use the selected text color. Fill shades adapt to keep labels readable."}</p>
      <div className="appearance-preview" aria-label="Button appearance preview"><span className="appearance-sample">Action</span><span className="appearance-sample authorize-button"><CircleAlert size={16}/> Authorize</span><span className="appearance-sample execute-button"><Play size={16} fill="currentColor"/> Execute</span></div>
      <small role="status">{appearanceSaved ? "Changes apply immediately and are remembered in this browser." : "Changes apply for this session. Browser storage is unavailable."}</small>
    </section><WritePolicySettings/><MethodHelperSettings/><ModelSettings/><OperationsPanel/></section></div>;
}
