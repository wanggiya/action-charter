# Trusted registry and installed-package metadata

R6b2, [issue #73](https://github.com/wanggiya/action-charter/issues/73), 2026-11-06.
This is a bounded registry/contracts follow-up within R6b, also removing two package
metadata dependencies from data code. This R6b2 slice is complete and verified.
Subsequent policy/ledger/data ownership and native moves are implemented in
[R6 completion](R6_COMPLETION_AND_ACCEPTANCE.md). Paths/counts below describe this
earlier slice; historical imports remain supported.

## Responsibility split

```text
fixed SKILLS_INDEX.yaml + installed package records
                         |
           shared registry / metadata readers
                         |
           typed current registry and definitions
                         |
        existing policy / proposal / review services
                         |
          existing exact installation or run decision
                         |
        existing package testing / fixed operation execution
```

Reading the registry does not perform the installation or run steps shown below it.
Package metadata declares the existing fixed adapter/verifier names; reading those
strings never imports or invokes the declared functions.

| Owner | Existing responsibility | Compatibility |
|---|---|---|
| `contracts/skill_registry.py` | Skill enums, definitions and registry schema/methods | `skill_registry.schemas` aliases the exact module |
| `platform/skill_registry.py` | Fixed registry path, bounded YAML parsing/load and verified installed-package merge | `skill_registry.service` aliases the exact module; public package exports remain |
| `contracts/table_arguments.py` | Common strict/exclusive CSV-source arguments and schema helper | Same classes/functions re-exported by `tabular.schemas` |
| `contracts/text_transform.py` | Closed text-step/transform definitions | Same classes re-exported by `capabilities.text`; runtime functions stay there |
| `contracts/operation_packages.py` | Data-only manifests, projection arguments, package errors, canonical bytes/hash/configuration/parse | Same objects re-exported by `operations.packages` |
| `storage/operation_packages.py` | Verified installed-record reads and conversion to skill metadata | Same functions re-exported by `operations.packages` |

The storage module also owns the existing safe directory-opening helper. Its explicit
create branch remains used by the installer; ordinary metadata reads do not create
package records, run fixtures or grant authority. Installation/testing/execution stay
in `operations.packages`, using the same directory helper, locks and publication code.

Native imports in 50 files use these owners. Generated/stored references, fixed adapter
and verifier strings, registry YAML and installed record bytes are not rewritten.
Existing public entry points and function/class/error identities remain. Three intent
fixtures now patch the shared registry reader rather than the former package re-export;
their assertions are unchanged. Direct legacy service/schema modules remain exact aliases.

## Freshness and authority

- Each registry load reads the current fixed YAML and installed records. There is no
  new cache or model-supplied list replacing the trusted reader. A previously returned
  registry remains a detached object; a subsequent load observes changed metadata.
- Existing schema validation, byte/count bounds, no-follow descriptor reads, identity/
  digest checks and package conflict handling remain. Malformed or tampered installed
  metadata blocks registry loading rather than silently omitting the operation.
- Approval creation still reloads the registry and runs the complete existing Planner,
  table and PostgreSQL policy chain. This slice does not remove or replace any check
  with a caller's boolean, saved summary or model assertion.
- Plan approval still binds the exact plan/steps and expiry. Runtime recipe/adapter
  paths retain their existing current-contract and exact package-digest checks.
  This refactor does not add a new version pin to legacy plan approval formats.
- Installing a package still requires the exact tested definition and explicit install
  decision. It does not install a Python dependency or authorize execution. Reads do not
  retest packages; explicit installation retains its existing fixture tests.
- The finite package adapters and text language do not become unrestricted Python,
  arbitrary entrypoints or executable discovery records.

All 22 affected registry/package/table/text JSON schemas match the pre-change snapshot;
the prior 12 public Critic/Executor schemas also match. Registry schemas are an unchanged
source copy. Moved definitions, remaining package execution/install functions, registry
behavior and native caller control flow retain the original ASTs apart from imports.

## Verification and remaining scope

Seven targeted upward dependencies are removed, **33 -> 26 pairs and occurrences**:
approval service, release assessment, Snakemake planning/replay and task relationships
no longer import registry implementation from the capability layer; table policy and
service no longer import package execution for a schema or metadata read. Layer
classifications are unchanged. Current graph: 456 modules, 2,328 import occurrences,
45 compatibility aliases and one unchanged dynamic-import review. Normal gate passes;
strict mode still rejects remaining debt.

Verified:

- **149 existing registry/approval/package/acquisition/table/write-policy/action cases
  passed (20.09 s)**, with temporary local HTTP fixtures and no live database.
- **98 boundary/layer/intent/action cases passed (4.27 s)**, including **29 new cases**:
  clean imports, identity, fresh reads, no implicit testing/install/dispatch, corrupted
  metadata, unsafe paths, byte bounds, approval freshness/expiry/hash and process restart.
  Default and relocated workspace roots are covered.
- Schema and moved-definition/caller comparisons pass. Frontend validation passed
  (4.59 s build, existing bundle-size warning); the isolated relocated browser/API/CLI/
  PTY journey passed with zero page errors and one authorized temporary write.
- Documentation: 512 local links/168 fragments across 33 changed Markdown files pass,
  including owner authorization-design changes. Roadmap remains below 64 KB; this
  task's working-method edits are Status-only, preserving the owner's other changes.
- Confirmed final `make test`: **2,673 passed**, 13 existing spatial warnings,
  **716.81 s (11:56)**. The 47 resumed boundary/layer checks also passed (2.33 s).
  Normal layer and whitespace checks pass; strict mode correctly rejects remaining debt.

An initial focused run hit sandbox-blocked HTTP sockets. A first extraction check found
a missing `Literal` import in the moved source schema; it was corrected. New approval
test IDs were corrected to match the existing ID format. A later execution-environment
interruption removed the first full test process and its temporary logs; that full run
is not counted as passing. Source persisted unchanged; the replacement full run passed
as recorded above.
Previously completed checks are recorded above. The updated owner model-approver design
remains future, unimplemented work outside this slice. Assertions and policy guards
were retained. These fixture results are not a real-local-model/live-database benchmark.

Planner-policy ownership, recipe-ledger relationships, remaining data/runtime and
transport boundaries, physical moves and P0-5b concurrency contracts remain separate.
No new agent, operation, UI, model call or record migration is introduced. Owner manual
write acceptance remains pending. See the [R6 checklist](product-direction/RESTRUCTURE_PLAN.md#r6-reviewable-slices).

For manual validation, restart the normal launcher, open Settings → Operations &
libraries, and confirm existing installed operations remain visible after reopening.
Run a normal read-only inspection and reopen its recorded outcome in frontend/CLI.
Do not reinstall packages merely to browse them. An existing installed adapter can be
tested with disposable output and fresh authorization; that write check remains optional
owner acceptance and is not a live-service change performed by this task.
