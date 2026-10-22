# Domain knowledge acquisition and portable methods — proposed design

Recorded 2026-10-21 from the operator discussion. Documentation only: no new
memory retrieval, model training, package promotion or execution behavior is delivered.

## User goal

Continued work on the same background data should require progressively less
repeated explanation. Retain relevant domain knowledge and processing habits,
then reuse applicable methods in the same chat. The desired later experience
also includes different chats in the same project and portable methods for
another project or user. Do not silently pool transcripts to achieve this.
Data testing should leave reusable assets, rather than only execution records.

## Separate the retained assets

| Asset | Example | Applicability |
| --- | --- | --- |
| Dataset definitions | Column units, identifier encoding, missing-value codes | Exact dataset/version or explicitly established dataset family |
| Domain knowledge | Conditions under which an analytical method is appropriate | Source-backed assumptions and domain scope |
| User preferences | Preferred output format or inspection order | Revisable preference, not a scientific rule |
| Parameterized recipes | Inspect, clean, aggregate and verify | Typed inputs, preconditions, supported operations and checks |
| Executable capabilities | Specialized supported calculation | Tested registered contract and runtime requirements |

A successful workflow establishes only what its checks actually verified.
It does not prove medical, statistical or industrial correctness. Unknown field
semantics require documentation, specialist guidance or another trustworthy
source; do not infer authoritative definitions from values alone.

## Proposed acquisition loop and responsibilities

1. Planner retrieves applicable knowledge and proposes the current workflow.
2. Existing execution services enforce effects and exact authorization, execute,
   and retain outcomes and deterministic checks.
3. Critic proposes reusable lessons, recipes, assumptions and limitations from
   the discussion and recorded evidence. It cannot certify unsupported claims.
4. Backend services validate record structure, scope and provenance, version and
   index records, and distinguish uncertain candidates from verified methods.
5. Later requests retrieve relevant records within an explicit context budget;
   Planner checks compatibility with current data and operations before use.

No separate Builder agent is required. Extraction should be bounded and cached;
opening a chat should not trigger repeated model calls. Capture routine
candidates automatically; ask for clarification only when material ambiguity
cannot be resolved. Uncertain records remain low-priority advice, not trusted
execution defaults. Corrections supersede outdated claims while preserving
provenance; support invalidation when sources, data or operation contracts change.

Minimum proposed record fields: identity, type, content, source/evidence
references, dataset/project scope, assumptions, verification status, version,
superseded record, sensitivity and retrieval keywords. Dataset identity must
handle versions and avoid assuming unrelated same-named files are equivalent.
Retrieved text, history and learned preferences never grant execution authority.

## Chat, project and portability boundaries

Conversation history remains private to its conversation. Proposed project
knowledge is a selected scoped asset, not a merged transcript. Cross-chat use
requires revisiting the existing checkpoint-30-or-later decision gate; this
record does not authorize implementation in checkpoints 28 or 29. First validate
capture, correction and retrieval in one conversation. Project isolation and
sharing policy must be tested before project-wide retrieval is enabled.

Future explicit export/import packages may include generalized recipes, sourced
domain definitions, conditions, limitations, synthetic fixtures, expected results
and tested capability definitions. Exclude private transcripts, credentials,
identifying data and dataset-specific sensitive facts by default. Import must
validate schemas, dependencies, operation contracts and compatibility; it grants
no write approval. Do not claim multi-user isolation without implementation and
tests. A knowledge package, callable MCP adapter and trained model are different
artifacts: MCP does not inherently learn and saved knowledge does not alter
Ollama model weights.

## Frontend direction

Keep normal work in conversation. Proposed controls: a simple knowledge-use
preference, compact disclosure of knowledge used, expandable sources/assumptions
and verification status, correction/invalidation, a knowledge browser, and later
explicit package export/import. Do not crowd the composer or require manual
knowledge forms after each run. Cross-chat controls wait for the sharing gate.
Existing visualization and inspection UI work remains in checkpoint 28.3 and
INSPECTION_ON_SEND_EXPANSION.md; this knowledge UI is additional planned work.

## Dependency order and acceptance

1. Finish current inspection/result interaction and recovery acceptance.
2. Checkpoint 29: single-chat acquisition, bounded retrieval, corrections and
   private knowledge provenance. Test that a later compatible request uses a
   sourced definition without repeated input, an incompatible dataset does not,
   and a correction supersedes an older claim. Helper failure preserves workflow.
3. Checkpoint 30 or later: reconsider scoped project knowledge across chats.
   Require explicit operator decision, isolation tests, inspectable retrieval and
   no unrelated transcript leakage before enabling it.
4. Later portability: export a sanitized method package and import into a clean
   project; repeat fixture checks, reject incompatible requirements and retain
   fresh authorization for actual writes. Cross-user packages require privacy review.

Use synthetic fixtures first. Representative data work should accumulate
validated reusable assets once capture/retrieval is accepted; preserve existing
pre-demo capability, private-memory and learning evaluation gates. RL may later
improve selection among eligible methods, using recorded decisions, verified
outcomes, a baseline and held-out cases. It does not replace knowledge storage
or justify calling fixed scoring a learned policy. General code generation,
model-weight training and automatic MCP creation are not delivered by this plan.
