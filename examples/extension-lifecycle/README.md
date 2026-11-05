# Historical extension lifecycle inputs

These are source examples, separate from generated runtime state:

- `builder-request.json`: a bounded proposal-only Builder request. The existing Compose
  Builder profile mounts this file read-only; it does not mount runtime evidence.
- `skill-definitions/inspect_raster.skill.yaml` and `convert_raster.skill.yaml`:
  declarative definitions used by the existing storage/contract/scaffold/promotion tests.
  They grant no execution, code generation, promotion or dependency-install authority.

Use an explicit `--definition-root examples/extension-lifecycle/skill-definitions` when
working with these definitions. Generated artifacts use the configured workspace defaults.
Legacy copies in top-level `builder-requests/` and `skill-definitions/` remain compatible
and are preserved by offline migration; they are no longer required by tests or Compose.
