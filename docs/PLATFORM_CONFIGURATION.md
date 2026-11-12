# Platform configuration and compatibility

R2, [issue #67](https://github.com/wanggiya/action-charter/issues/67), 2026-11-05.
Shared configuration is owned by `geoagent_harness.platform`, independent of HTTP,
MCP, CLI and model-client implementations. Existing launch options and defaults work.

```text
trusted environment / explicit mapping / explicit layout
                           |
                  load_configuration()
             immutable allowlisted snapshot
                  + one LayoutConfiguration
                           |
          +----------------+---------------+----------------+
          |                |               |                |
       tools            model          mcp_client         replay
  database, paths,    model endpoint,   internal URL,     approved replay
  startup flags      limits, overrides timeout           roots
          |                |               |                |
         existing services / transports / exact execution policy
```

## Ownership and existing imports

| Current owner | Compatibility module retained |
|---|---|
| `platform/settings.py` | `mcp_server.settings` |
| `platform/model_settings.py` | `model.settings` |
| `platform/client_settings.py` | `mcp_client.settings` |
| `platform/replay_settings.py` | `snakemake_export.settings` |
| `contracts/tool_results.py` | `mcp_server.schemas` |

The old modules alias the actual owner, preserving class/function/error/ContextVar
identity. Production source imports the neutral owners directly. Historical generated
candidate strings keep their original imports; installed/stored artifacts are not
rewritten. Existing class names, public fields, default values, validation messages,
operation names and execution contracts remain compatible.

`platform/configuration.py` owns the snapshot and typed lazy views;
`platform/layout.py` is the single parser for legacy `GEOAGENT_*_ROOT` inputs.
These environment aliases remain supported for launchers, Compose and old scripts.
This moves parsing ownership; it does not change mount destinations or migrate files.

## Loading and precedence

Trusted application code can use:

```python
from geoagent_harness.platform import load_configuration

configuration = load_configuration()
tool_settings = configuration.tools
# Only access configuration.model when this operation actually needs a model.
```

- Without an explicit mapping, each load snapshots allowlisted values from the current
  process environment. The existing launcher still loads its allowlisted `.env` values
  and preserves terminal overrides; this Python layer does not open `.env` itself.
- Existing loaders (`load_settings`, `load_model_settings`, internal-client and replay
  loaders) delegate to this same owner and retain their old call signatures/results.
  There is no global configuration cache. Later loads see new request settings.
- An explicit mapping is isolated from process values. As before, model/reasoning
  request overrides are ignored for explicit mappings.
- Otherwise, the current model/reasoning ContextVars are captured when the snapshot
  is created. Later access to its model view uses those captured overrides; a new
  request gets a new snapshot. Model selection and reasoning changes still work
  without restarting the launcher.
- An explicit `LayoutConfiguration` replaces the whole environment-derived layout.
  A trusted `project_root=` argument overrides its project root. Other typed fields
  use the captured environment and unchanged defaults. Models cannot choose layout
  objects or the platform provider.
- Views validate independently and lazily. File-only tool/replay commands require no
  configured model. An invalid database port does not prevent loading a valid model
  view. An absent/invalid model still raises the existing model configuration error
  when its view is requested.

The layout and captured values are immutable copies. Typed views are freshly derived,
not shared mutable caches; changing an existing mutable client-settings view cannot
change the snapshot or a later view. No new dependency, settings page or setup step
is required.

## Workspace and authority

The layout includes source/input/output, tool evidence/authority and replay roots.
`layout.workspace()` explicitly loads the existing workspace resolver without creating,
copying or moving records. Normal settings loading does not open workspace files.

The existing `authority_workspace_settings` helper still resolves only default runtime
roots through the configured workspace; explicit paths remain explicit. Input/output
data and agents remain in their existing places. Legacy-record/missing-destination
checks, source-bound ownership, exact hashes, expiry, write sessions and approval
checks are preserved. Reading settings does not enable writes or create authority.

Only credential **file paths** and non-secret connection settings are retained. Plain
database/password/API-key environment values are not captured. No credential contents
are opened by configuration loading, and no connection/model request is made. The
snapshot's representation omits captured environment/override values.

`deployment_profile` currently identifies **Personal only**, as a composition seam.
No server profile, credential broker, scheduler, remote model gateway or standing
automation authority is implemented by R2. P0-2b's stable project-ID identity and real
owner cutover, P0-5b's ledger/concurrency contracts and R12 remain separate work.

## Dependency result

The reviewed [R1 baseline](IMPORT_LAYERS.md) drops **109 → 75** distinct upward
dependencies and **128 → 87** occurrences. All 34 removed pairs disappeared from
the actual graph; no new/increased upward dependency was accepted. New `platform`
and `contracts` packages are explicitly L1 and L0; existing classifications were not
relaxed to hide debt. There are now 421 application modules, 28 visible aliases and
the same one reviewed non-literal API export resolver. Strict mode still fails.

## Verification and manual smoke check

Focused configuration/settings/layer/lightweight-import tests: **87 passed (5.09 s)**.
Workspace authority, sessions, lifecycle, transport parity, candidate and replay
checks: **116 passed (23.73 s)**. An initial sandbox socket denial was rerun with
temporary loopback access; it required no application change. `make interface-validate`
passed (existing bundle-size warning). Two isolated actual-backend browser journeys
passed with zero page errors: relocated-state API/CLI/PTY continuation/model settings,
and runtime-write-policy/exact-authorization transitions. These use fixture models,
temporary data and separate browser profiles, with no live database/service calls.
Final full `make test`: **2,529 passed**, 13 existing spatial warnings,
**678.41 s (11:18)**. No source edits during that run. Documentation checks validated
249 local links/anchors and the roadmap size. Logs and remaining scope are recorded
in CURRENT_STATUS and WORK_RESUME; no real local-model quality claim is implied.

For a manual check, restart your usual launcher with the same options. In Settings,
confirm the expected model and reasoning preference. Send
`Run a new read-only inspection of sample_orders.csv.` Execute once if inspection on
send is OFF, then reopen the saved run after refresh. No new configuration is needed.
Use disposable local files for a write check through the normal Allow writes →
Authorize → Execute flow; do not use a live database merely to validate this move.
