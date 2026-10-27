# Domain knowledge acquisition and portable methods — proposed design

## Latest clarification — alternatives parked, data testing next

[Current retention, role options and data-test handoff](MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md)
clarifies mutable content/priority with old versions recoverable by default, not
absolute irreversible retention. Both separate/common memories and combined/separate
Critic-curator roles remain recorded and undecided. Earlier “requires separate agent”
wording describes the preceding A proposal, not a final selected architecture.
Prepare controlled data testing next; no runtime work is authorized by this note.

Recorded 2026-10-21 from the operator discussion. Documentation only: no new
memory retrieval, model training, package promotion or execution behavior is delivered.

## Latest A-specific direction — 2026-10-23

[Revised A](MEMORY_A_GROWING_SHARED_JSON.md) uses retained growing shared JSON with editable content/priority and a separate knowledge-management agent. It supersedes the earlier optional-Critic-only curation proposal for A; B remains unchanged. A/B are memory architectures, not merely storage backends. This is documentation only and does not authorize cross-chat sharing or runtime changes.

## Checkpoint 29 clarification — 2026-10-22, documentation only

Begin after checkpoint-28 inspection/UI fixes, shared-service consistency,
multi-inspection and evaluated experience-retrieval acceptance. Retain automatic
candidate capture from discussions and verified outcomes, indexed retrieval with
sources/scope/applicability, and versioned corrections/supersession. Distinguish
model inference, operator-supplied definitions and independently checked facts;
a successful execution is not proof of domain correctness.

Planner consumes relevant knowledge; Critic can propose lessons from recorded
outcomes; backend services preserve provenance, versions, isolation and retrieval
budgets. Frontend provides compact inspectable sources/corrections without
mandatory bookkeeping forms. No additional mandatory agent or container.

Acceptance uses synthetic fixtures first: recall a relevant sourced definition
without repeated explanation, exclude unrelated/incompatible data and other chats,
prefer corrected knowledge over superseded claims, expose uncertainty/provenance,
and preserve workflows when extraction/retrieval fails. Neither memory nor retrieved
text may authorize execution. This starts within one conversation; cross-chat or
project sharing stays checkpoint 30+ and requires a separate decision.

Evaluated method reuse and private knowledge should precede broader realistic-data
testing/demo preparation. This does not require or claim model-weight RL; portable
knowledge packages, general code generation and new MCP creation remain later work.

## Ordered implementation plan

[Checkpoint 29 delivery plan](CHECKPOINT29_PRIVATE_KNOWLEDGE.md) specifies storage,
capture, retrieval/correction, UI/CLI and acceptance slices. Documentation only;
no new memory behavior is delivered by recording this plan.

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

## Learning-process clarification — 2026-10-22

The operator challenges the gap between a capability list and an actual learning
method. Start with a human-learning analogy before selecting a technical stack.
This is a proposed engineering model, not a scientific claim that agents learn
like humans. Extracting and summarizing are useful parts of learning; they do not
alone establish understanding, executable ability or improvement.

### Individual learning as a proposed process

1. Establish a concrete problem and a criterion for a correct answer.
2. Observe a worked example and its supporting sources; distinguish observations
   from explanations, assumptions and unknowns.
3. Explain why each consequential step was taken, its preconditions and what
   would make it inappropriate. Store a candidate rule rather than a transcript
   summary alone.
4. Predict the result on a new example before seeing its result. Identify which
   variables should matter and which changes should leave the method applicable.
5. Practise on small controlled examples, including counterexamples. Compare
   predicted and observed results against independent checks where possible.
6. Diagnose disagreement: incorrect domain assumption, inappropriate method,
   incorrect parameter, execution failure or insufficient evidence. Do not turn
   every failure into a general domain rule.
7. Revise the explanation/procedure and preserve the reason for correction.
8. Later retrieve it without the original walkthrough and test transfer to an
   unseen compatible case. Retain known exclusions and uncertainty.

Working artifacts: a question, source-linked explanation, conditional rule,
parameterized procedure, predicted result, check result and correction history.
A candidate remains tentative when independent checking is unavailable. A correct
numeric output alone does not establish a correct domain interpretation.

### Group learning and division of work

A group can maintain a shared problem definition, have a practitioner propose a
method, have a reviewer challenge its assumptions, try small exercises, and keep
an edited handbook of lessons and exclusions. In ActionCharter, these are duties:
Planner proposes and predicts; Critic explains/challenges and proposes revisions;
deterministic services execute permitted operations, check outcomes and retain
traceable records. The user or supplied trustworthy sources resolve domain facts
that the system cannot independently establish. Agreement between model roles is
not independent evidence; adding agents alone does not improve correctness.

Not every duty needs a separate agent or model call. Use structured execution
facts directly, and invoke interpretation only for a specific unresolved question.

### Small functions derived from this process

| Function | Input → output | Concrete method |
| --- | --- | --- |
| Frame an exercise | Task and evidence → target and check | Name the result and a check before attempting it; record unknown semantics. |
| Explain an example | Steps and sources → conditional rationale | Identify why a step is necessary, its prerequisites and an exclusion. |
| Propose a lesson | Explanation → tentative rule/procedure | Separate dataset literals from parameters; attach sources and unresolved assumptions. |
| Design practice | Candidate lesson → small cases | Vary one relevant condition, include an incompatible case and reserve an unseen case. |
| Predict | Candidate and case → expected result | Commit the prediction before execution; do not infer the answer from the observed output. |
| Check and diagnose | Prediction and evidence → discrepancy category | Use trusted fixture answers/domain checks; separate semantic, planning and runtime failures. |
| Revise | Discrepancy and source → new lesson version | Narrow scope, adjust conditions or reject; preserve the counterexample and reason. |
| Recall and transfer | New task → eligible lesson and adaptation | Check applicability, adapt parameters, then rerun normal validation; abstain if unsupported. |

These are responsibilities and input/output boundaries, not a commitment to a new
framework, storage technology, separate agent for each row or automatic code creation.
The prior record/capture/retrieval proposal is supporting infrastructure for this
process; it is not itself the complete learning mechanism.

### Example and acceptance

Use synthetic precipitation data with an explicit supplied data dictionary: rainfall
is in tenths of a millimetre and -999 denotes missing. A worked example excludes
missing codes before conversion and aggregation. The candidate lesson explains why,
parameterizes the scale/sentinel, and limits applicability to documented fields.

Practice includes a compatible new file, a file already in millimetres, a file with
a different missing code and a file lacking unit documentation. Expected values
come from fixture definitions, not model agreement. A held-out compatible case
must use the lesson without repeating the walkthrough; incompatible cases must not
inherit its conversion. Missing documentation should result in uncertainty or a
focused question. A correction must change the next prediction and procedure.

Measure correct results, inappropriate transfer, repeated explanations, corrections,
model calls and elapsed time against the original baseline. Merely producing a
summary, retrieving a record or running a successful command does not pass this test.
When the required procedure cannot be expressed by installed operations, retain an
unexecutable method candidate and identify the capability gap. Do not pretend that
knowledge storage installs a new ability. Existing bounded adapters may cover some
gaps; general capability creation requires separate validation and authorization.

### Relationship to checkpoint scope

Record this as a design clarification before revising implementation slices.
Checkpoint 29 should connect its storage/capture/retrieval functions to an explicit
explanation → practice → correction → transfer test. No new runtime work is performed
by this update. Cross-chat learning remains a separately authorized scope expansion;
model-weight training and adaptive/RL selection remain unimplemented. Design their
interfaces around recorded choices and independently checked feedback, without
assuming a reward signal or demonstrated benefit already exists.

## Role memory, curation and recovery clarification — 2026-10-23

[Detailed proposal](ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md) records per-role tiers,
agent-led semantic curation plus deterministic record management, explicit sharing
indices, domain labels, correction propagation and bounded export/restore. No fixed
agent/service ratio or automatic scope broadening; design only.

## Curation, A/B prototype and portability clarification — 2026-10-23

[Detailed continuation](ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md#knowledge-curation-function-and-experimental-comparison--2026-10-23) records the Critic extraction contract and practice loop, isolated test-only file/transactional adapters, and selected knowledge packages for a clean compatible installation. No need for two Git branches or extra memory agents. Portable external knowledge is distinct from model-weight training and executable capability installation. Design only; sharing and implementation gates remain.
