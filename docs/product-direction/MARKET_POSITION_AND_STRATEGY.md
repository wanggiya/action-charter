# Market position and strategy options

Recorded 2026-11-02 from a discussion with the project owner.

> **Decision 2026-11-02:** the owner chose to develop this as a product with **its own
> agent platform**, opt-in interop with external agents, and single/multi-agent modes.
> See the [decision note](../decisions/2026-11-02-own-platform-direction.md). Sections below that recommend not building a platform,
> building on another vendor's platform, or blocking platform work on validation are
> **superseded**; the assessment of strengths, weaknesses and market risk still applies.

Market facts below are from general knowledge as of
late 2026 and were not re-verified; check them before relying on them.

Related: [vision and competitor table](VISION_AND_ASSESSMENT.md#competitive-landscape),
[working method and delivery plan](WORKING_METHOD.md).

## Short answer

As a **general data-science agent**, the project cannot win. Codex, Claude Code,
OpenClaw-style personal agents, Databricks' agents and similar products have frontier
models, large teams and distribution. A solo project on a 9B local model will not beat
them on capability, speed or ease of use, and the gap grows.

Its one real asset is **deterministic governance of what an agent may do with data**:
typed operations, policy-based authorization, hash-verified lineage and an audit trail a
compliance officer can read. Market value depends on building around that asset, not on
competing as a full data-science agent.

## Honest assessment

| | Where it stands |
|---|---|
| Real strengths | Governance design stronger than most open-source agents (which run arbitrary generated code). Fully offline. Broad engineering scope. 2,254 tests. |
| Real weaknesses | No users, no benchmark. Real-model planning 40–120 s per call with timeouts. UI built for engineers. No package or installer. Very broad scope for one person. |
| Market risk | Big vendors are adding on-prem/private-cloud options. Many regulated organizations can now use frontier models inside their own cloud tenant (Azure OpenAI, Bedrock, Vertex), which weakens "data cannot go to external APIs" as the selling point. |
| Sales reality | Hospitals and governments buy from vendors with compliance certifications, support and references. Sales cycles of 6–18 months. Very hard solo without a design partner. |

**Biggest single limit:** the self-imposed "local small model only" rule. It makes the
product slow and unreliable — the first things users notice.

## Three ways to treat the project

### 1. Portfolio (lowest risk; value already exists)
Already strong evidence of agent-safety engineering, architecture and testing discipline.
To present it well:
- Clear README, a 3-minute demo video of one journey, a diagram of the authority model.
- A small benchmark with honest numbers, failures included.
- Finish P0-2 (workspace root) so the repo looks like a product, not a lab bench.

Best audiences: companies building agents, AI safety/governance teams, health and
government data teams.

### 2. Narrow product in one niche (possible only with validation)
Not "an autonomous data platform". One painful regulated workflow, for example:
- **Health research in secure data environments** (NHS SDEs, trusted research
  environments, hospital research units with no internet). Pitch: an audited analysis
  assistant that produces a reproducible report and lineage for the ethics/data committee.
- **Public-sector GIS:** governed publishing to PostGIS/GeoServer with rollback.

Validation gate: talk to 10–15 people in the niche **before more platform code**.
Continue only if 2–3 agree to be design partners. If none do within about 2–3 months,
treat that as the answer.

### 3. Governance layer for other agents (superseded as the main path; kept as the interop feature)
Do not compete with Codex / Claude Code / OpenClaw-style agents; sit **underneath** them.
Expose typed operations, policy, approvals, verification and the audit ledger as an MCP
server or gateway. Their agent thinks; this layer decides what it may execute on
sensitive data and records proof.
- Uses their model quality and momentum, removing the biggest weakness.
- Matches the core principle: models propose, deterministic software authorizes.
- The MCP server already exists, so this is a refocus, not a restart.
- Caveat: agent-security and MCP-gateway startups already exist. Survey them before committing.

## Improvements that help every path

1. **Pluggable model:** local Ollama, the customer's private-cloud frontier model, or
   on-site vLLM. "Fully offline" becomes one option, not the only one.
2. **One hero journey only**, fast and reliable; freeze the rest.
3. **Benchmark.** No product or portfolio claim is credible without numbers.
4. **Governance shown in plain language:** "what the agent did, what it was allowed to
   do, and proof the result is correct." This is what buyers and employers respond to.

## Competing with startups

Not on features — funded startups out-build a solo founder. Win on:
- **Niche depth:** know one domain's rules and workflows better than a general product.
- **Trust:** auditability and offline operation for buyers who must prove compliance.
- **Speed of learning:** talk to users weekly. Most startups fail by building the wrong
  thing, not by building too slowly.

## Recommendation (superseded 2026-11-02 — kept for history)

Treat it as a **portfolio project now, with a time-boxed product test**:
1. Finish P0-2, the benchmark and one polished demo — useful for every path.
2. Over the next 2–3 months, run customer conversations for one niche (path 2) or for
   the governance-layer angle (path 3).
3. **Do not build the server platform** (working-method step 6+) until a real user or
   design partner asks for it.

## Open decision (resolved 2026-11-02: product with own platform)

The right plan depended on the owner's goal:
- career / job (→ path 1 first),
- business (→ path 2 or 3 with the validation gate),
- research / learning (→ path 1, plus publishable benchmark results).

When decided, record it here and update the step order in
[WORKING_METHOD.md](WORKING_METHOD.md).

## Public communication (LinkedIn, talks, posts)

Recorded 2026-11-03. Another company working on a similar platform does not prevent
posting; the work was done independently and the repository is public (Apache 2.0) with
dated commits. Guidelines:
- Describe what this project does; do not claim "first" or "only".
- Lead with the data-work value (verified process/outcome workspaces, Data Card, measured
  efficiency, offline/any-model). Sandboxing, including future MicroVMs, is the means, not
  the headline; MicroVM agent sandboxes are a common building block that nobody owns.
- Do not publish non-public details from other companies' talks; do not criticise them by name.
- Show evidence: a short demo and honest benchmark numbers (real vs fixture labelled).
- Before promoting: check the public repository for secrets and real data, check whether
  the name "ActionCharter" is already used by another product, and (if employed or a
  student) check the employment contract or university policy on side projects and IP.
- This is general guidance, not legal advice.

## Guidance for agents

- Do not describe the project as competitive with general agents (Codex, Claude Code,
  Databricks, etc.) in README, docs or pitches. Position it as governance, auditability
  and offline operation for regulated data.
- Platform work follows the phase order in [WORKING_METHOD.md](WORKING_METHOD.md).
- Do not imitate a competitor's design; build the differentiators in the decision note.
- Keep recommending real-user conversations in one domain; they are no longer a blocker.
- Prefer work that serves all paths: Phase 0, benchmark, hero journey, plain-language
  governance, pluggable model.
