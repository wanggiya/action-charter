
import {useWorkspaceSnapshot,useWorkspaceSetters,useWorkspaceBatch} from './WorkspaceStore';
import {useGraphLocalState} from './useGraphLocalState';
import {useResultsLocalState} from './useResultsLocalState';
import {useAdvancedLocalState} from './useAdvancedLocalState';

export function useWorkspaceBindings() {
 const shared=useWorkspaceSnapshot();
 const setters=useWorkspaceSetters();
 const batchWorkspace=useWorkspaceBatch();
 const graph=useGraphLocalState(shared);
 const results=useResultsLocalState(shared);
 const advanced=useAdvancedLocalState(shared);
 return {...shared,...setters,...graph,...results,...advanced,batchWorkspace};
}
export type WorkspaceBindings = ReturnType<typeof useWorkspaceBindings>;
