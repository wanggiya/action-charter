# Security Policy

## MVP trust boundaries

- Model output is untrusted and must pass typed schema and policy checks.
- There is no unrestricted shell tool or unrestricted SQL tool.
- Input datasets are mounted read-only.
- Writes are limited to `data/output`, `traces`, and `reports`.
- Overwrite requires explicit approval; deletion is unavailable.
- Database secrets must not enter prompts, tool results, traces, or reports.
- Deterministic verification is the only success gate.
- Planner and critic have no database or GIS execution access.
- The shared model is reached through a configured local Ollama endpoint.

## Prototype limitations

Compose network settings do not constitute a complete egress firewall. The
prototype needs local access to host Ollama, and Docker/host firewall rules must
enforce any strict host-only egress policy. The Checkpoint 1 agent services only
validate their manifests; the agent loop and MCP transport are not implemented.

## Reporting

Do not open a public issue containing credentials, private datasets, traces, or
database details. Rotate any credential accidentally committed to version
control; removing it from the latest commit is not sufficient.

