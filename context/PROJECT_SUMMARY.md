# Project Summary

GeoAgent Skill Harness is a CLI-first, local-first, containerized system for
planning approved GIS workflows, executing narrow tools, deterministically
validating outputs, and recording reproducible reports and traces.

The implemented MVP vertical slice can:

1. build a concise task-specific context pack;
2. use the Planner Agent to produce a structured plan;
3. validate the plan using deterministic policy;
4. bind human approval to the exact plan digest and approved steps;
5. translate the approved plan into a typed execution envelope;
6. execute one composite allowlisted MCP workflow;
7. inspect an approved vector dataset;
8. load it into a new table in an allowlisted PostGIS schema;
9. deterministically validate the resulting PostGIS layer;
10. generate a Markdown report and secret-redacted trace;
11. build a deterministic critic evidence pack;
12. use the read-only Critic Agent to identify risks and explain the result.

The system uses an externally managed PostGIS container and one shared local
Ollama/Qwen runtime. Planner, Executor, Critic, and GIS/MCP run as separate
container services.

The deterministic verifier, not an LLM, determines workflow success. Model
output is treated as untrusted and must pass schema and policy validation.