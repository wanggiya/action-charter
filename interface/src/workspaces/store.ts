/** In-memory, provider-owned UI state. This store cannot authorize or dispatch work. */
export type Update<S, K extends keyof S> = S[K] | ((previous: S[K]) => S[K]);

export function createStore<S extends object>(initialize: () => S) {
  let state = initialize();
  const listeners = new Set<() => void>();
  let depth = 0;
  let pending = false;
  const publish = () => {
    if (depth) { pending = true; return; }
    pending = false;
    for (const listener of [...listeners]) listener();
  };
  return {
    getSnapshot: () => state,
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => { listeners.delete(listener); };
    },
    set<K extends keyof S>(key: K, update: Update<S, K>) {
      const next = typeof update === 'function'
        ? (update as (previous: S[K]) => S[K])(state[key]) : update;
      if (Object.is(next, state[key])) return;
      state = {...state, [key]: next};
      publish();
    },
    batch<T>(change: () => T): T {
      depth++;
      try { return change(); }
      finally { depth--; if (!depth && pending) publish(); }
    },
  };
}

/** Batch synchronous UI transitions; async work and authority remain with the API. */
export function batchActions<T extends object>(actions: T, batch: <R>(change: () => R) => R): T {
  return Object.fromEntries(Object.entries(actions).map(([name, action]) => [
    name, (...args: unknown[]) => batch(() => Reflect.apply(action, undefined, args)),
  ])) as T;
}
