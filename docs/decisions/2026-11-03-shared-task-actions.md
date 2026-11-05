# P0-4: shared task actions

Context: current workflow coordination lived under `interface_api`, while exact
approved dispatch lived under `mcp_server`. CLI and other backend callers imported
these transport-named services, and workflow actions imported the HTTP server for
approval and execution functions.

Decision: move the connected existing services into `geoagent_harness.task_actions`.
Extract immutable-artifact contracts/actions and exact dispatch/progress from the
server. Keep compatibility module aliases and public exports, and point production
callers at the shared owners. Preserve all external schemas, hashes and authority
checks. Add no operation, role, permission or UI feature.

Consequences: shared services load without the HTTP server; existing callers share
the same locks, execution context and durable records. Tests patch dependencies at
their new owner, preserving their behavioral assertions. Legacy Advanced/assurance
and router separation, settings relocation and the P0-5 storage repository remain
separate work. Fixture parity does not establish live-model or database reliability.
