# R4: shared data access with task-owned authority

Context: lower-level discovery/tabular services still obtained reads and errors from
task actions. Moving the reader alone would retain a task-owned worker/snapshot/render
dependency. Shared action/format definitions and context redaction also had higher owners.

Decision: move the fixed reader and necessary worker/snapshot/rendering helpers into
the existing sandbox layer. Put unchanged self-contained contracts/redaction under
contracts and root/result helpers under platform. Reuse R3's error identity. Retain
eligibility, revisions, authority, execution contexts and run/concurrency scope in task
actions. Keep compatibility aliases/exports and update native imports only.

Consequences: all 12 directly assigned R4 dependencies disappear without new upward
imports or relaxed layer classifications. Existing limits, formats, hashes, redaction
profiles and behavior remain. This adds no execution capability or stronger container
boundary. Three observer/role-type dependencies remain explicitly under R4/R6 for the
R6 ownership review. Owner manual acceptance remains deferred, not claimed completed.
See [scope and validation](../DATA_ACCESS_BOUNDARY.md).
