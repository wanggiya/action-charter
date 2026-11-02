# Checkpoint 17AN — governed resource selection

Checkpoint 17AN corrects the interface direction from path-entry convenience to
bounded project-resource selection.

- The loopback API inventories supported files below `data/input` without
  following symlinks and exposes existing directories below `data/output`.
- Trusted template forms can select an existing input, an output directory and
  an output filename. Advanced explicit relative paths remain available.
- The Planner workspace can select existing inputs as explicit bounded context.
  The service adds those references to model context while preserving the
  operator's original request in durable plan evidence.
- Inventory is read-only and grants no approval or execution authority.

The workflow graph remains the continuous representation of the reviewed plan
or active recipe. Future Checkpoint 17 slices must preserve that graph while
adding Critic/release, Snakemake, database/server and Builder/skill workspaces.
