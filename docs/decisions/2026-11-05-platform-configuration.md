# R2: one configuration owner with compatibility views

Context: core services imported MCP-owned settings/contracts; tool and replay roots
were parsed separately. Model overrides must remain per request, and data-only work
must not require an available model. R1 measures rather than hides these dependencies.

Decision: use a platform-owned immutable allowlisted environment/layout snapshot with
lazy typed tool, model, internal-client and replay views. Preserve old loader signatures,
defaults and module identities through aliases; move tool-result schemas to contracts.
Centralize root parsing without removing environment compatibility. Capture request
overrides at snapshot creation; never cache configuration globally or load credentials.
Update native import statements while leaving generated candidate source unchanged.

Consequences: the layer baseline shrinks without new upward dependencies; existing
launchers, settings UI and exact-authority services retain their behavior. Personal is
the only current profile. Stable project ID, real-record migration, ledger/concurrency
contracts and server seams remain separately tracked, not silently delivered by a move.
See [scope, precedence, verification and limits](../PLATFORM_CONFIGURATION.md).
