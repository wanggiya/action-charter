# Architecture

- **Model:** one shared Qwen-compatible endpoint; no per-agent large model.
- **Agents:** planner, executor, and critic are logical roles with independent
  instructions and permissions.
- **Loop:** plan → approved execution → deterministic validation → report.
- **Harness:** will own state, allowlists, approvals, redaction, timeouts,
  errors, and traces.
- **Container:** isolates GIS dependencies and uses narrow mounts.
- **Skill:** a versioned, tested GIS workflow with typed input and output.
- **Verifier:** non-LLM Python/GDAL/rasterio/SQL checks.
- **Trace:** redacted structured evidence, never a substitute for validation.

Checkpoint 1 flow:

```text
Typer CLI → path policy → inspect_vector → Pydantic result → JSON
```

Deployment topology:

- Planner, executor, and critic run as independent containers built from one
  lightweight agent image.
- All agents will call one shared Ollama service on the laptop.
- GIS/MCP execution uses a separate GIS-tools image.
- PostGIS is an existing external container joined through a named Docker
  network; this repository does not create or own it.

Trust boundaries:

1. Model output is untrusted and must match schemas.
2. Only allowlisted MCP tools may execute.
3. Input is read-only; writes are limited to designated output roots.
4. Overwrite requires approval; deletion is unavailable.
5. Success is impossible until deterministic validation passes.
