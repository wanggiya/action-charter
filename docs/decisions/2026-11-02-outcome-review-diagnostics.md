# Separate execution evidence from advisory review diagnostics

Context: a real completed inspect_csv run was followed by a 15-second Critic timeout.
The enclosing executor/workflow phase incorrectly labelled the model failure as executor.

Decision: scope execution and standalone outcome review separately; keep workflow status
and review status independent and link status-only diagnostic metadata to the durable run.
Retain historical bytes and identify legacy labels in the UI. Add a revision-checked
project preference for the standalone review budget, pinned with request settings.
Default remains 15 seconds; limits 5–180. Planning and coordinated report budgets stay
separate. Source records, approval rules, execution retries and data operations are unchanged.

Consequences: a successful operation can have an unavailable review. Settings changes
apply only to future requests and never trigger a retry. Fixture verification establishes
failure handling, not local-model review quality or adequate latency for any given model.
