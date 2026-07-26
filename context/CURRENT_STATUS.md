# Current Status

## Checkpoint 1 — scaffold and inspect_vector

Status: implementation prepared; runtime verification awaits user execution.

Prepared:

- package, CLI, schemas, and bounded vector inspection;
- sample GeoJSON and pytest cases;
- Compose scaffold for external PostGIS connectivity and GIS tools;
- independent agent-container definitions and validated manifests;
- external PostGIS network configuration;
- shared host-Ollama configuration without model calls;
- GIS tools image, context records, and future skill placeholders.

Not started:

- shared model adapter and context-pack builder;
- live MCP server and allowlisted tool dispatch;
- conversion, PostGIS loading, deterministic PostGIS verifier;
- approvals, redaction, traces, and Markdown reporting.

Next checkpoint candidate: expose `inspect_vector` as a typed, allowlisted MCP
tool and persist a redacted trace while keeping the CLI behavior stable.
