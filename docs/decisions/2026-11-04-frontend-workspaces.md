# P0-6: frontend workspaces and provider-owned state

Context: App.tsx combined workspace rendering, 185 state fields, projections, effects
and most action handlers. Existing components alone did not provide clear ownership
for a future Guided/Studio interface. Restoration and authority checks must survive
the split without a navigation or visual redesign.

Decision: retain App as composition and move projections, local state, action factories,
effects and workspace views into `interface/src/workspaces`. Use existing React context
and useSyncExternalStore over a provider-owned store for shared fields; keep transient
controls local. Typed action ports capture their originating render. Synchronous UI
batches preserve coupled transitions. Selected-chat identity is explicit for run lookup.

Consequences: existing markup/order, keys, API requests and authority checks remain.
No state dependency, backend feature, new agent or Guided mode. Store state is not
durable evidence or permission. Browser journeys must prove restoration, graph gestures,
authorization and hook refresh; fixture success does not establish real-model quality.
Advanced controllers remain substantial; broader optimization/redesign is separate.
