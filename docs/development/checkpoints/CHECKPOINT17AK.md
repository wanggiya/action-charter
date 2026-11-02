# Checkpoint 17AK — complete plan restoration and fresh decision

Checkpoint 17AK restores the complete operator-visible planning context when an
immutable plan is selected: the original task request and the exact allowed
skill set are repopulated alongside the plan and latest decision evidence.

Expired or otherwise blocked approval evidence remains immutable and visible.
The verification result now offers **Record a fresh decision**, which clears
only the browser's active decision selection and all downstream preview or
compiled state. The existing approval artifact is preserved. A new decision is
then recorded append-only against the same server-derived prepared scope.

The fresh decision defaults to no expiry only when the operator leaves the
optional duration field blank. It performs no execution.
