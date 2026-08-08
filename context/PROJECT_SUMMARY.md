# Project Summary

GeoAgent Skill Harness is a CLI-first, local-first, containerized system for
planning approved GIS workflows, executing narrow tools, deterministically
validating outputs, and recording reproducible traces.

The implemented deterministic vertical slice can:

1. inspect an approved vector dataset;
2. load it into an allowlisted PostGIS schema;
3. validate the resulting PostGIS layer;
4. generate a Markdown report;
5. save a structured, secret-redacted trace.

The system uses an externally managed PostGIS container and one shared local
Ollama model runtime. Planner, executor, and critic are separate logical agents
designed to run in independent containers.

The current development focus is the Planner Agent. It will receive a concise
task-specific context pack and produce a structured plan. It cannot execute
commands, modify files, or access PostGIS.