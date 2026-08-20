# Runtime and filesystem boundaries

## Agent roles

| Component | Read access | Write access | Network/tool access |
|---|---|---|---|
| Planner | manifests and trusted context | none | shared local model only |
| Executor | plans, recipes, approvals, workflow state | none directly | fixed approval-gated MCP tools |
| Critic | traces and reports | none | model network only; no MCP or PostGIS |
| MCP GIS | trusted inputs, recipes, approvals and registry | controlled artifact and GIS output roots | fixed GIS functions and approved PostGIS connection |
| Human operator | project artifacts | explicit save and approval actions | controls workflow progression |

## Important mounts

| Host directory | MCP GIS access | Purpose |
|---|---|---|
| `data/input` | read-only | Approved GIS input datasets |
| `data/output` | read-write | Validated GIS output artifacts |
| `context` | read-only | Skill registry and trusted policy context |
| `workflow-recipes` | read-only during MCP execution | Immutable saved recipes |
| `approvals` | read-only during MCP execution | Append-only approval records |
| `plans` | read-only | Validated workflow plans |
| `recipe-runs` | read-write | Immutable authoritative run results |
| `recipe-evidence` | read-write | Lineage and evidence manifests |
| `traces` | read-write by execution boundary | Structured execution traces |
| `reports` | read-write by reporting boundary | Authoritative reports |

## Host write permissions

Runtime-writable bind-mounted directories must be writable by the
non-root GIS container identity, currently UID/GID `10001`.

Directories should retain group inheritance where configured, for
example mode `2775`. Permissions must be scoped only to explicitly
approved runtime output directories. Input, recipe, approval, and
context directories remain read-only inside the GIS container.

Never solve permission failures by:

- running the GIS container as root;
- granting `777` recursively;
- mounting the entire repository read-write;
- granting the Planner or Executor direct output-directory writes;
- putting PostGIS credentials in agent containers.

## Write gates

`ENABLE_WRITE_TOOLS=false` is the safe default.

A controlled write requires:

1. a schema-valid artifact;
2. deterministic policy validation;
3. exact digest-bound approval;
4. server-side envelope reconstruction;
5. a fixed allowlisted MCP operation;
6. deterministic post-write validation;
7. durable result, evidence, lineage, and report persistence.

Natural-language proposal generation does not cross this write gate.

