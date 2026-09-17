# Checkpoint 17S — Exact execution preview

Checkpoint 17S shows the exact approved execution envelope before the interface
receives any execution authority.

After independent approval verification, the operator may select **Preview
approved execution**. The loopback service then re-reads the immutable recipe
and approval, reruns policy, verifies the approval, and builds the same
`RecipeExecutionEnvelope` used by the governed MCP execution boundary.

The preview displays:

- exact recipe and approval identities;
- deterministic topological step order;
- skill, access class and dependencies for every step;
- redacted arguments and declared outputs;
- approval and post-write validation requirements;
- the `recipe-runs/` and `recipe-evidence/` destination roots.

## Authority boundary

The response explicitly states `execution_available: false` and
`execution_performed: false`. There is no execute control. Preview generation
does not invoke MCP, a skill, Snakemake, a shell command or an Ollama model.

Checkpoint 17T may add one separately confirmed, approval-gated execution action
for this exact envelope.
