# generate_report

Implemented as an evidence-persistence request, not free-form model success reporting.
The step itself returns report_pending_evidence_persistence; the authoritative Markdown
is finalized after validated run evidence is assembled. It includes recorded analytical
findings and a technical handoff with source/output digests, actual available database
column/key metadata and recovery limitations. Unsupported checks are not invented.

Saved durable workflow reports are also available through workflow_report, the CLI
chat report command and Outcome -> Report. Opening/downloading existing evidence does
not execute a workflow or grant authority. Backend report-file creation retains the
existing governed report/persistence path; browser Markdown/PDF exports stay local.


Planner compatibility boundary: this legacy operation requires dependent PostGIS
validation under existing deterministic policy. Do not add it or unrelated database
steps for ordinary CSV/JSON/XLSX inspection/statistical reports; those reports derive
from saved results in Outcome Report. Explicit legacy requests receive current task
identity from the backend before review; this grants no execution/write authority.
