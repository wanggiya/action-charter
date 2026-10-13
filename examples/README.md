# Examples by function

Choose by outcome below. Checkpoint directories remain in place for historical compatibility.

| Function | Example | What it demonstrates |
| --- | --- | --- |
| Clean, join and aggregate orders | [Regional order totals](checkpoint24/regional_csv_plan.json) | CSV inspection, column selection, filtering, missing values, join, grouping and export |
| Extract spatial attributes | [Spatial attributes to CSV](checkpoint24/spatial_attributes_plan.json) | GeoJSON inspection and attribute-table export; geometry is not retained in CSV |
| Add a supported operation | [Extract order identifiers adapter](checkpoint25/order_identity.operation.json) | Test temporary fixtures, explicitly install a fixed CSV projection operation; no workflow approval implied |
| Execute an installed adapter | [Order identifiers workflow](checkpoint25/installed_adapter_plan.json) | Inspection → installed projection → export, exact package binding and separate authorization |
| Convert vector data | [Vector conversion proposal](interface-parity/checkpoint17l-vector-conversion-proposal.json) | Historical proposal-format example; inspect compatibility before using |

Use the Planner to describe these outcomes or inspect the JSON as a typed reference.
The adapter package is uploaded through Settings → Operations & libraries → Test / Install.
A plan JSON is a workflow definition, not an adapter package: do not upload it to the adapter installer.
Use fresh output paths. Review the exact proposal before authorizing and executing.
Examples use repository sample data; do not substitute private data for a public demo.
