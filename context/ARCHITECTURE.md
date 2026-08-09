# Architecture

## Core components

- **Model:** one shared local Ollama/Qwen endpoint; no model is duplicated
  inside individual agent containers.
- **Planner Agent:** receives a concise context pack and creates a structured,
  non-executing workflow plan.
- **Executor Agent:** accepts only an exact approved plan and calls one
  composite approval-gated MCP workflow.
- **Critic Agent:** reads deterministic evidence, identifies unresolved risks,
  and produces a schema-constrained assessment.
- **Loop:** context → plan → approve → execute → validate → report → critique.
- **Harness:** owns schemas, state, policies, approvals, redaction, timeouts,
  error handling, traces, and artifact rules.
- **GIS/MCP container:** isolates GIS dependencies and exposes only typed,
  allowlisted tools.
- **Skill:** a versioned and tested GIS workflow implementation.
- **Verifier:** deterministic Python/PostGIS checks; it is not an LLM agent.
- **Trace:** structured, secret-redacted execution evidence.

## Deployment topology

```text
                         Shared Ollama/Qwen
                         ↑               ↑
                  model network     model network
                         │               │
                ┌──────────────┐  ┌──────────────┐
                │   Planner    │  │    Critic    │
                │ plan only    │  │ evidence only│
                │ no tools     │  │ no tools     │
                └──────┬───────┘  └──────────────┘
                       │
                structured plan
                       │
                human approval
                       │
                ┌──────▼───────┐
                │   Executor   │
                │ approved MCP │
                │ workflow only│
                └──────┬───────┘
                       │ internal control network
                ┌──────▼───────┐
                │   GIS/MCP    │
                │ skills and   │
                │ verifier     │
                └──────┬───────┘
                       │ external backend network
                ┌──────▼───────┐
                │   PostGIS    │
                │ externally   │
                │ managed      │
                └──────────────┘