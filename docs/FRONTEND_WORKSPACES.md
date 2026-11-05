# Frontend workspaces and state

P0-6, [issue #63](https://github.com/wanggiya/action-charter/issues/63).
The existing interface is organized into workspace views/controllers over a shared
in-memory state store. Layout, navigation, control labels, graph gestures, API contracts
and browser storage keys are preserved. No dependency, new agent, data operation or
Guided mode is introduced.

```text
App (composition shell)
  |
  WorkspaceStoreProvider (one instance per mounted app)
  |
  local state hooks -> model/projections -> typed action ports -> effects
  |
  +-- Planner / existing conversation component
  +-- Graph / sources / inspector
  +-- Results / review / history
  +-- Settings
  +-- Advanced / existing technical forms
             |
       existing API clients
             |
       governed backend services
```

## Ownership

All new modules live under `interface/src/workspaces/`.

| Module | Responsibility |
|---|---|
| `App.tsx` | Compose providers, controllers and workspace views; formerly 2,683 lines, now under 100 |
| `state.ts`, `store.ts`, `WorkspaceStore.tsx` | Typed initial state/setters, immutable top-level snapshots, subscriptions and synchronous UI batching using existing React facilities |
| `use*LocalState.ts` | Keep graph/DOM references and transient or legacy form controls mounted across panel switches |
| `useWorkspaceBindings.ts`, `useWorkspaceModel.ts` | Combine state and derive current graph, selection, run evidence and presentation |
| `model.ts` | Pure graph projections, labels and geometry helpers previously in App |
| `createPlannerActions.ts` | Existing plan generation/save/restoration and technical Planner commands |
| `createGraphActions.ts`, `createSourcesActions.ts` | Existing graph gestures, edit/validation commands and source selection |
| `createResultsActions.ts` | Review, exact authorization/execution and recorded-result actions |
| `createSettingsActions.ts` | Existing appearance persistence |
| `createAdvancedActions.ts` | Existing recipe, assurance, task-history and technical operations |
| `useWorkspaceEffects.ts` | Existing startup/read/polling/listener/cleanup effects, called unconditionally |
| `*Workspace.tsx`, `GraphInspector.tsx`, `WorkspaceHeader.tsx` | Render existing markup through the typed UI context |

The store holds 52 formerly separate shared fields plus the selected conversation ID.
133 transient/legacy state fields remain in local hooks. Views use fragments, retaining
DOM order and CSS relationships. This is a responsibility split; the legacy Advanced
controllers are still larger than the other groups and are not a new product feature.

## State and scope

- A provider creates its own store. There is no module-global mutable app store or
  new cross-project/chat persistence. Existing appearance preferences still use their
  existing key; saved workflows and runs remain backend records.
- Snapshots retain reference identity until a value changes. Functional setters use
  the latest field value; synchronous batches notify subscribers after the complete
  UI transition. Batching is not a database transaction and does not roll back data.
- Action ports bind to the render that created them. An old asynchronous action does
  not silently invoke another chat's newest closure. Existing scope epochs, execution
  references and backend checks remain in place.
- TextPlanner reports its selected conversation ID. Recorded-run lookup accepts that
  same explicit scope; legacy callers can still use the original storage-based default.
- A chat change clears the previous plan/draft/review/authorization/result selection
  as one synchronous UI batch. Read-only run selection remains bound to chat + plan.
- Opening Settings, Outcome or history does not dispatch a workflow. Existing explicit
  inspection-on-send behavior is unchanged. Graph edits still need backend validation.
- Store defaults contain no saved approval/review/run authority. All execution still
  goes through existing exact-scope backend verification; frontend state cannot grant
  permission. Restoration, changing write availability or revising a plan cannot reuse
  mismatched authority.

All hooks remain unconditional. Workspace controllers stay mounted while panels hide,
preserving their in-memory state. DOM drag previews, animation-frame cleanup, zoom and
layout persistence use the existing implementations. This work makes no performance
or mature-product parity claim; rendering optimization needs measurement.

## Verification

`tests/test_frontend_workspaces.py` covers store isolation, lazy initialization,
functional/no-op updates, nested batching, unsubscribe/error bookkeeping, safe defaults
and workspace ownership. Existing projection/restoration tests now read their new
owners with unchanged behavior assertions. Frontend type/build validation is required.

Isolated browser acceptance covers:

- Relocated backend state, saved-chat/run restoration, Outcome tabs, reports and
  frontend-to-CLI/PTY continuation without replay.
- Fractional node dragging, cursor-anchored wheel zoom, recipe/Planner continuation
  and real temporary CSV writes with deterministic validation.
- Shared toolbar/Settings write availability, stale-approval rejection, fresh exact
  authorization, refresh and stopping the next write after writes are disabled.
- Development hot refresh restoring the saved chat/workflow without hook-order errors
  or automatic execution.

These use actual backend services and temporary data with fixture models, disposable
browser profiles and no live database calls. Final `make test`: **2,483 passed** in
938.96 s, with 13 existing spatial warnings. `make interface-validate`, nine focused
checks and all four browser journeys passed with zero page errors. The frontend
build retains its existing bundle-size warning; no performance improvement is claimed.
Logs are recorded in WORK_RESUME.

## Manual smoke check

Restart your usual launcher with the same options. Send
`Run a new read-only inspection of sample_orders.csv.` If Inspection on send is OFF,
click Execute once. Check Outcome; switch back to the graph, open/close Settings and
Execution History, then reopen the same run. Its result should remain available.
Drag a node and use wheel zoom; refresh to confirm existing layout/chat restoration.
For write checks, use disposable local outputs and the normal enable → Authorize →
Execute flow. No live database change or new setup is needed for this refactor.
