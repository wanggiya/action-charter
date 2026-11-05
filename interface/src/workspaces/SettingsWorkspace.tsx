import { SettingsPanel } from "../components/SettingsPanel";
import {useWorkspace} from './WorkspaceContext';

export function SettingsWorkspace() {
 const { settingsOpen, appearance, appearanceSaved, updateAppearance, setSettingsOpen, 
}=useWorkspace();
 return <>{settingsOpen && <SettingsPanel appearance={appearance} appearanceSaved={appearanceSaved} onAppearanceChange={updateAppearance} onClose={() => setSettingsOpen(false)}/>}</>;
}
