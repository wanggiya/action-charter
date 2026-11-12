# Preserve CLI contracts while separating command owners

Date: 2026-11-08. [R7, issue #75](https://github.com/wanggiya/action-charter/issues/75).

## Context

After R6, shared services have native layer owners, but the main CLI still contains
7,463 lines. The owner authorized the command-group split, preserving pending work,
user commands and deterministic authority. Git integration remains owner-managed.

## Decision

Move existing command/helper definitions into responsibility modules under `apps/cli`.
Keep app construction and named callback exports in a small main module, and explicit
registration in one registry preserving the original order/decorator arguments.
Move eight existing small registrars intact, with exact aliases at old paths.
Command groups share only the existing failure renderer and do not import one another's
dispatch logic. Existing task actions/services retain policy, execution and storage.

Keep the public `geoagent_harness.cli` app/module entrypoint and flat command syntax.
Capture exact option/default/type metadata, all help screens and original function
AST hashes before editing; verify those contracts and existing tests after extraction.
Do not add a CLI framework, new commands, agent behavior, dependency or UI feature.

## Consequences

The composition module is 142 lines; the registry is 290 lines; the largest command
module is 783 lines. Existing command-local dependency loading and lazy shared-service
bindings remain. Historical script/import paths work through audited compatibility
adapters, whose eventual retirement remains R11. Different Python `-m` invocations
naturally identify their own invoked module in Usage.

This improves code ownership and review scope; it does not establish faster models,
new processing capabilities or server readiness. [Implementation, evidence and manual
validation](../CLI_COMMAND_STRUCTURE.md) distinguish automated fixtures from local-model
and owner acceptance. R8 HTTP decomposition and storage/server gates remain separate.
