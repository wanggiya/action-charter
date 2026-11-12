# R11: native callers and supported compatibility boundaries

[Issue #80](https://github.com/wanggiya/action-charter/issues/80), 2026-11-09.
Implementation and required automated gates complete. No Git integration,
owner workspace cutover, live database work, new agent or processing feature.

2026-11-10 manual closeout: the owner reported startup, read-only CSV inspection and
refresh/reopen recovery passed. Execution History navigation and terminal continuity
remain the two required owner checks. The optional write journey is untested manually;
workspace cutover is separate. [Current acceptance record](R_SERIES_ACCEPTANCE.md#acceptance-record).

## Result and structure

The graph falls from 903 modules to 613: **290 obsolete adapters removed, 117
supported boundaries retained, all 496 native implementation modules preserved**.
Native imports have zero upward or unresolved dynamic debt. Ordinary source,
test, script and launcher imports point at native owners. Entry points for new
installations and the analytical worker use native application modules.

```text
Maintained frontend / CLI / MCP / scripts
                  |
           Native application owners
                  |
      Existing shared task actions and services
                  |
       Existing policy / data / storage owners

Supported older entrypoints / generated SDK / schema exports
                  |
      117 explicit compatibility boundaries
                  |
         Same native objects and services
```

The 117 include 60 package/export boundaries and 57 exact module aliases. Retention
is intentional: installed/python-module entrypoints, public package exports, the
94 frozen schema exports, R2 configuration views, registry/validator identifiers,
generated raster skill namespaces, Snakemake replay and required package parents.
They are not a second copy of execution services. Some names appear in immutable
records or candidate source; changing them would invalidate contracts or hashes.

The original R11 sentence “no shims” is not claimed literally. The owner-approved
direction preserves required public/historical support. The delivered exit is:
**no unclassified adapter, no obsolete adapter source, no ordinary internal caller
of a compatibility module, and explicit tested public/SDK boundaries**. Removing
those remaining supported paths would require a separately reviewed breaking
compatibility transition, not another automatic cleanup pass.

## Inventory and regression gates

`tests/architecture/r6_module_owners.json` remains unchanged historical evidence.
`tests/architecture/r11_compatibility.json` partitions all 407 entries into retired
and retained records, preserves original owners/hashes and records retention reasons.
It also binds unchanged registry, schema, CLI/HTTP/MCP and generated-SDK contracts.
The retired records provide a complete old-to-native import map.

```bash
.venv/bin/python scripts/check_import_layers.py --strict
.venv/bin/python scripts/check_compatibility.py
```

Both are read-only source checks. The gate rejects missing classifications,
changed historical identities/contracts, restored retired files, unclassified
aliases and new implementation files under supported legacy package roots. Ordinary
caller imports are checked separately from explicitly identified compatibility
tests and the isolated SDK loader. Static analysis cannot discover every unknown
external client or arbitrary dynamically constructed import.

`tests/test_r11_compatibility.py` checks all retired paths, retained re-export object
identity, negative manifest/import cases and the real analytical worker build context.
An empty cached directory can still resolve as a Python namespace; it contains no
retired implementation or public exports. Owner caches are not deleted to disguise it.
Earlier compatibility-only tests now verify retired paths fail or retained paths
share the native module. Functional, authority and source/evidence assertions remain.

Three old task-action alias-only parameter rows disappear with their wrapper files;
the exhaustive retired-path check replaces that coverage. Fifteen new R11 cases
include parametrized failures. The 94-schema, 150-original-command/165-help-screen,
HTTP and 27-tool MCP fixtures retain their original bytes.

## Worker and SDK boundaries

The analytical image build script previously copied old wrapper paths. It now copies
the minimal native CSV/profile/worker package and standard-library contracts. Its
Docker entrypoint imports the native worker. A fake `docker build` captures the
actual bundle and runs its profile calculation under Python `-I -S`, outside the
installed project; full row count and numeric mean must match. No image was built
and no Docker service was started for that test.

The candidate test runner still provisions `geoagent_harness.skills` and
`geoagent_harness.skill_adapters`. These are reserved generated-SDK namespaces;
redirecting that overlay into trusted native implementation packages would be wrong.
Generated templates, registry IDs, replay contracts and stored artifacts are unchanged.
No write permission, SQL access or execution authority is added.

## Acceptance and limits

Use the [combined R-series manual guide](R_SERIES_ACCEPTANCE.md) after automated gates.
It checks launcher, read-only execution, chat/history recovery, frontend/terminal
continuity and one optional explicitly authorized new fixture output. The real owner
workspace backup/cutover remains separate. [Stable identity limits](PROJECT_IDENTITY.md)
still apply; container alias provisioning is not delivered by adapter retirement.

Tests and browser acceptance use temporary projects and fake models. They establish
structural/behavioral regression evidence, not actual Ollama performance, domain
expertise, live PostGIS readiness or a new Docker image's runtime isolation.

Final `make test`: **2,808 passed, 13 existing spatial warnings, 859.92 s (14:19)**.
Frontend typecheck/build passed (5.44 s build; existing bundle warning). Renewed
stable-ID relocated browser/API/CLI/terminal journey passed with zero page errors
and one explicitly authorized temporary write. Strict dependency and compatibility
checks pass: 613 modules / 3,016 imports, 496 native modules, 117 supported boundaries,
290 retired adapters, zero upward/dynamic debt and no ordinary legacy callers.
The interrupted run's final outcome was unavailable; this is the completed rerun.
These are fixture results; combined owner manual acceptance remains pending.
