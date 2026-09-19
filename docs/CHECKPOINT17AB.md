# Checkpoint 17AB — Planner execution-envelope preview

Checkpoint 17AB adds a non-executing preview built by the existing Executor
policy. It reloads independently verified plan and approval evidence and calls
`build_execution_envelope`; it does not invent a browser-only execution format.

The existing Executor currently supports one fixed four-step vertical slice:
`inspect_vector`, `load_vector_to_postgis`, `validate_postgis_layer`, then
`generate_report`. A one-step `convert_vector` plan is valid for testing plan
approval but will be rejected clearly at preview because it is not executable by
that established envelope. The interface must not pretend otherwise.

The preview displays its canonical digest and complete redacted envelope. It
sets `execution_available=false` and `execution_performed=false`; no MCP call,
database write, report, or Executor run is possible here.

Preview-policy failures render beside the preview control as a persistent red
`PREVIEW BLOCKED` outcome. They no longer appear only in the general notice near
the top of the scrollable Planner dialog. A blocked preview does not invalidate
or erase correctly recorded approval evidence.

Next: add restart-safe plan and approval inventories, then separately expose
execution only for the exact supported, previewed envelope.
