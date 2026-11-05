import {batchActions} from './workspaces/store';
import {WorkspaceStoreProvider} from './workspaces/WorkspaceStore';
import {WorkspaceContextProvider} from './workspaces/WorkspaceContext';
import {useWorkspaceBindings} from './workspaces/useWorkspaceBindings';
import {useWorkspaceModel} from './workspaces/useWorkspaceModel';
import {useWorkspaceEffects} from './workspaces/useWorkspaceEffects';
import type {WorkspaceActions} from './workspaces/action-contracts';
import {createSettingsActions} from './workspaces/createSettingsActions';
import {createPlannerActions} from './workspaces/createPlannerActions';
import {createGraphActions} from './workspaces/createGraphActions';
import {createResultsActions} from './workspaces/createResultsActions';
import {createSourcesActions} from './workspaces/createSourcesActions';
import {createAdvancedActions} from './workspaces/createAdvancedActions';
import {WorkspaceHeader} from './workspaces/WorkspaceHeader';
import {SettingsWorkspace} from './workspaces/SettingsWorkspace';
import {SavedRecordsWorkspace} from './workspaces/SavedRecordsWorkspace';
import {AdvancedWorkspace} from './workspaces/AdvancedWorkspace';
import {PlannerWorkspace} from './workspaces/PlannerWorkspace';
import {GraphWorkspace} from './workspaces/GraphWorkspace';
import {ResultsWorkspacePanel} from './workspaces/ResultsWorkspacePanel';
import {GraphInspector} from './workspaces/GraphInspector';

function WorkspaceShell() {
 const bindings=useWorkspaceModel(useWorkspaceBindings());
 let actions: WorkspaceActions;
 const context={...bindings,actions:()=>actions};
 actions=batchActions({...createSettingsActions(context), ...createPlannerActions(context), ...createGraphActions(context), ...createResultsActions(context), ...createSourcesActions(context), ...createAdvancedActions(context)},bindings.batchWorkspace);
 const {connectionTarget,selected,newEdgeKind}=bindings;
 const {canConnect}=actions;
 const connectionCompatible = Boolean(connectionTarget && canConnect(selected.id, connectionTarget.id, newEdgeKind));
 const value={...bindings,...actions,connectionCompatible};
 useWorkspaceEffects(value);
 const {appearance,advancedOpen,intentOpen,textPlannerOpen,rightPanelOpen,outcomeOpen,inspectorClosed}=value;
 return <WorkspaceContextProvider value={value}><main className={`app-shell ${advancedOpen ? "advanced-open" : ""}`} data-button-style={appearance.buttonStyle} data-filled-text={appearance.filledText}>
 <WorkspaceHeader/>
 <SettingsWorkspace/>
 <SavedRecordsWorkspace/>
 <AdvancedWorkspace/>
 <div className={`workspace ${intentOpen || textPlannerOpen ? "intent-open" : ""} ${textPlannerOpen ? "text-planner-open" : ""} ${rightPanelOpen ? "right-panel-open" : ""} ${outcomeOpen ? "outcome-page" : ""} ${inspectorClosed ? "inspector-closed" : ""}`}>
  <PlannerWorkspace/>
  <GraphWorkspace/>
  <ResultsWorkspacePanel/>
  <GraphInspector/>
 </div>
 </main></WorkspaceContextProvider>;
}

export default function App(){return <WorkspaceStoreProvider><WorkspaceShell/></WorkspaceStoreProvider>;}
