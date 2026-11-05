
import {createContext,useContext} from 'react';
import type {WorkspaceModel} from './useWorkspaceModel';
import type {WorkspaceActions} from './action-contracts';

export type WorkspaceUI = WorkspaceModel & WorkspaceActions & {connectionCompatible:boolean};
const Context=createContext<WorkspaceUI|null>(null);
export const WorkspaceContextProvider=Context.Provider;
export function useWorkspace() {const value=useContext(Context);if(!value)throw new Error('Workspace provider is missing');return value;}
