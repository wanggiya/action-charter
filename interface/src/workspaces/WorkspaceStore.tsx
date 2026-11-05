import {createContext, useContext, useState, useSyncExternalStore, type ReactNode} from 'react';
import {createStore, type Update} from './store';
import {createWorkspaceState, setterKeys, type WorkspaceState, type WorkspaceSetters} from './state';

export function createWorkspaceStore() {
  const store = createStore(createWorkspaceState);
  const setters = Object.fromEntries(Object.entries(setterKeys).map(([name, key]) => [
    name, (value: Update<WorkspaceState, typeof key>) => store.set(key, value),
  ])) as WorkspaceSetters;
  return {...store, setters};
}

const Context = createContext<ReturnType<typeof createWorkspaceStore> | null>(null);

export function WorkspaceStoreProvider({children}: {children: ReactNode}) {
  const [store] = useState(createWorkspaceStore);
  return <Context.Provider value={store}>{children}</Context.Provider>;
}

function useStore() {
  const store = useContext(Context);
  if (!store) throw new Error('Workspace state provider is missing');
  return store;
}

export function useWorkspaceSnapshot() {
  const store = useStore();
  return useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
}

export function useWorkspaceSetters() { return useStore().setters; }
export function useWorkspaceBatch() { return useStore().batch; }

/** Stable field snapshots let future workspaces subscribe only to what they need. */
export function useWorkspaceValue<K extends keyof WorkspaceState>(key: K) {
  const store = useStore();
  return useSyncExternalStore(store.subscribe, () => store.getSnapshot()[key], () => store.getSnapshot()[key]);
}
