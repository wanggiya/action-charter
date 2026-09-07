# Project Summary

ActionCharter is a CLI-first, local-first governed execution harness for AI
agents using professional tools. Models interpret requests and propose bounded
work; deterministic software owns authorization, execution, validation,
verification, and evidence. The current reference domain is geospatial
automation.

The core trust rule is:

> Models propose; deterministic software authorizes, executes, validates, and
> records evidence.

## Implemented architecture

The system separates:

- a model-assisted Planner that creates typed, non-executing proposals;
- a deterministic governance layer that validates schemas, policy, scope, and
  artifact digests;
- exact human approval for consequential steps;
- an Executor that can dispatch only already-authorized operations;
- allowlisted GIS/MCP adapters that retain professional tools and credentials;
- deterministic validation and independent state verification;
- a read-only Critic that cannot change authoritative status;
- immutable evidence, operational history, release, and replay artifacts; and
- an isolated Builder lifecycle for generated extension candidates.

The Planner and Critic may share a local Ollama/Qwen runtime, but receive
different contexts and permissions. The Executor has no model access or direct
database authority. Generated text and generated code remain untrusted until
they pass their respective deterministic governance boundaries.

## Reference workflows

Checkpoint 14F demonstrates the integrated workflow path:

```text
request
-> constrained proposal
-> deterministic compilation
-> exact human approval
-> controlled PostGIS execution
-> deterministic validation
-> operational history
-> separate Critic evidence
-> authoritative release inspection
-> approved Snakemake replay
```

Checkpoints 15A–15K demonstrate a complete consequential PostGIS lifecycle:

```text
inspect
-> compare
-> assess
-> plan promotion
-> approve promotion
-> execute promotion transactionally
-> independently verify promotion
-> plan rollback
-> approve rollback
-> execute rollback transactionally
-> independently verify rollback
```

Every promotion and rollback artifact is bound by canonical SHA-256 identities.
The independent verifiers reload the authoritative plan, approval, and
execution evidence and inspect resulting PostGIS state rather than trusting an
executor's success claim.

## Current position

The project is an alpha research and pilot implementation, not a hardened
multi-user production control plane. It now proves an end-to-end governed,
reversible mutation lifecycle in its PostGIS reference domain. The next
checkpoint will be selected after documentation alignment and an explicit
review of product priorities.

Primary development is performed on Ubuntu 24.04 LTS under WSL2. Hosted CI
exercises offline tests and container contracts on Ubuntu.
