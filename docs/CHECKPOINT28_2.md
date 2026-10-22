# Checkpoint 28.2 — optional outcome recommendations

Implemented slice: a conservative, deterministic own-chat evidence selector and
conversation settings popover. This is not model training, an exploratory RL
agent, reliable domain recall or general learned workflow generation. The wider
pre-demo learning gate requires measured benefit. [Paired evaluation and current
execution interaction](CHECKPOINT28_2_EVALUATION.md) implement the comparison
harness; its real-model results must be assessed separately from fixture tests.

## Structure

Plain-text flow (terminal compatible):

    request + current chat
        -> allowed registered operations / composable recipes
        -> own-chat, current-contract check evidence
        -> short advisory operation list + recipe relevance tie-break
        -> Planner -> existing validation -> authorization -> execution
        -> deterministic checks -> bounded evidence recorder

No additional agent or container. Critic remains advisory in existing run
assessment; its opinions do not change numerical ranking. Existing operation
contracts, registry availability and typed validation remain authoritative.
Allowed-operation filtering is deterministic; request-specific semantic/data
compatibility is still checked through ordinary planning/validation, not proved
by historical scores. This pilot does not claim automatic contract unification.

The shared `planner.outcome_recommendations` service records terminal durable
run checks after dispatch. It uses an additive versioned `outcome_rank_v1` table
in the existing successful-workflows SQLite database. It never backfills old
runs automatically, modifies recipes or repeats execution. Normal UI and CLI
use the same durable-run services and conversation coordinator. Direct legacy
synchronous execution does not collect this new durable-run evidence.

## Evidence and policy

- Only runs with chat identity, dispatch-time contract snapshot, execution and
  terminal timestamp are eligible. Step identities must match the snapshot.
- A validated successful step contributes one positive check. A deterministic
  `validation_failed` step with `passed=false` contributes a negative check.
- Generic dispatch errors, configuration/service failures, cancellation and
  interruption are excluded. Completion without a recorded passed check adds
  no positive evidence. Historical successes are not universal correctness.
- Retained payload contains operation ID, contract SHA and check classification.
  No raw rows, arguments, file paths, credentials or transcripts are copied.
- Only the current chat is queried. Changed/uninstalled contracts are ignored.
  There is no cross-chat memory retrieval or global shared learned policy.
- Fixed score: `(passes - failures) / (passes + failures + 4)`. At most five
  operation summaries reach Planner. Counts are observations, not probabilities.
- Recipe ranking retains keyword relevance first; mean operation score only
  breaks relevance ties. It does not claim that the whole recipe was verified.
- Max 200 immutable run observations project-wide; full storage stops recording
  without silent eviction. Existing database size/symlink bounds are reused.
- Recording failure is fail-soft after execution; planning can fall back to the
  original ranking when derived evidence is unavailable. No new model call.
- Disabling recommendations stops their use, not run evidence collection.
  Reset deletes this chat's derived observations and preserves durable evidence.
  Past observations are not automatically rebuilt after reset.

No exploration, installation, write enabling, authorization reuse or dispatch
is performed by ranking. It cannot enlarge the operation allowlist. OFF retains
baseline ranking; new chats default OFF. No claim of general RL benefit is made.

## Interface and CLI

Conversation header gear opens an existing-style popover. It closes with its X,
Escape or an outside click. Controls:

- Chat memory: existing browser-wide preference remains persistent.
- Acquire capabilities: existing chat-only default OFF preference.
- Use outcome recommendations: chat-only default OFF preference.

Server preferences use exact conversation revision checks and survive refresh.
Settings actions make no inference/fixture/execution calls. A request receipt
records recommendations used; the disclosure stays visible while enabled,
including an explanation when no eligible checks were supplied. Check counts
appear only when an actual last request supplied recommendations. It is historical request
information, not a prediction that the next request will use the same shortlist.

CLI `outcome-recommendations CHAT --enabled/--disabled --expected-revision N
--project-root PATH` uses the same preference action.
`reset-outcome-recommendations CHAT --project-root PATH` deletes derived ranking
metadata only. Normal CLI conversation turns consume the same shortlist.

## Validation and limits

`tests/test_outcome_recommendations.py` covers persistence, privacy, changed
contracts, duplicate/conflicting evidence, negative checks, generic failures,
incomplete evidence, inventory bounds, reset, setting revisions, private-chat
scope, recipe relevance and deterministic-model ON/OFF equivalence.

`scripts/checkpoint28_recommendation_evaluation.py` uses only temporary synthetic
evidence and three frozen selector cases: baseline 2/3, evidence policy 3/3.
It measures local selector latency, zero model calls, zero execution calls and
zero intervention. These are deliberately small constructed cases; they do not
establish model quality, faster workflows, real-world improvement or a useful
RL reward function. Runtime remains optional OFF. The follow-up acceptance must
compare real Planner outcomes with ON/OFF on representative fixed tasks, report
invalid plans, correct outputs, latency, model calls and interventions, and keep
the feature optional if no benefit is established.

Manual acceptance:

1. Restart the existing launcher and refresh the interface.
2. Open Planner's gear; confirm all three controls and their scope explanations.
3. Toggle chat memory, refresh/new chat; its browser preference persists.
4. Toggle recommendations/acquisition, refresh the same chat; values persist.
   A new chat starts both OFF. Toggling makes no model call or output file.
5. In one chat execute a supported transformation with output validation through
   normal review, authorization and run. Inspection-only completion has no separate
   validation check and is not sufficient for a verified-check recommendation. Enable recommendations, then ask a related follow-up.
6. Inspect “Recommendations from verified checks”: only eligible current-chat
   operation counts should appear. Formula/output checks remain unchanged.
7. Turn recommendations OFF: subsequent request receipt says disabled; saved
   workflow/output/history remain. New chat cannot retrieve another's counts.
8. Confirm outside click/Escape closes settings and drafting stays usable.

Next: representative model evaluation before claiming completion of the full
28.2 benefit gate; then 28.3 visualization and checkpoint 29 private knowledge.
Cross-chat memory stays deferred to 30+. No packaging/publication is implied.

### Verified in this checkout

- `make test`: 1,878 passed. After the small evidence-transaction locking change,
  all 11 new recommendation tests passed again.
- `make interface-validate`: typecheck and production build passed; existing
  large-bundle advisory remains.
- Acquisition/settings browser journey: 8 cases passed, including actual temporary
  durable execution feeding the next request's own-chat recommendation receipt.
- Private-chat browser regression: 10 cases passed, including memory preferences,
  restoration, fresh authorization/execution and optional helper behavior.
  Both journeys use deterministic model fixtures and temporary browser profiles;
  no browser-cache/dependency installation or live database access.
- Offline selector evaluation passed its 3 cases; baseline 2/3 vs policy 3/3 is
  constructed selector evidence only, not an actual-model benchmark.
- CLI registration, script syntax and `git diff --check` passed.

### Empty inspection evidence follow-up

An operator CSV inspection completed with `validation_outcome=null`. The former
UI hid the disclosure for an empty list, and the earlier inspection-only test
instructions incorrectly promised a passed check. The disclosure now explains
empty evidence while enabled. Runs with no verified checks return
`no_verified_checks` instead of storing an empty observation as “recorded”. No
historic run is relabelled or automatically re-executed.

Follow-up frontend validation and the 9-case acquisition/settings browser journey
passed, including enabled empty-state guidance and verified transformation
evidence. Tests use temporary fixtures and a deterministic model.

See [paired evaluation delivery](CHECKPOINT28_2_EVALUATION.md) for one-click
read-only execution, the unchanged write gates, recommendation rationale and
fixed full-journey acceptance cases.

## Inspection-only scope follow-up

A saved automatic-scope proposal incorrectly appended PostGIS validation and a
report to `Inspect sample_orders.csv. Return row count and column names. No writes.`
The conversation coordinator now recognizes a narrow, complete single-file
metadata request, supplies only its inspector argument schema and constrains the
decoder to one step. Backend validation independently rejects additional steps
before storage, including recipe-composed proposals, with the existing one-repair
budget. Existing saved proposals are not rewritten. Broader requests and
transformation follow-ups retain the general path; this is not a general proof
of natural-language task coverage. No execution authority is inferred.

Restart the launcher, create a fresh chat and submit that exact request with
automatic skill selection. Confirm one CSV inspection operation, no PostGIS or
report operations, then use Execute directly with writes OFF.

Scope-follow-up verification: five focused regression cases passed, including
bounded repair and unchanged saved workflow after repeated rejection. Frontend
typecheck/build and four temporary-backend browser execution journeys passed
(model fixture only; no live service calls). This does not establish general
real-model task coverage.

`make test`: 1,906 passed. The final prompt clarification and additional saved-state
regression were checked with the five focused cases afterward.

## Proposed next interaction slice

[Inspection on send design](INSPECTION_ON_SEND_DESIGN.md) records the intended
backend policy, bounded CSV-first scope, durable duplicate protection, interface/CLI
integration and acceptance order. It is design only: sending still proposes and
Execute remains separate. It adds no agent and does not complete learning gates.

## Inspection submission delivery and learning alternatives

The [bounded CSV submit slice](CHECKPOINT28_2_INSPECTION_SUBMIT.md) now implements
explicit default-OFF inspection on send, source/contract binding, durable
duplicate protection and receipt reconciliation. Older proposal-only statements
in this document describe the previous state. General learning acceptance stays
open; [non-RL alternatives](LEARNING_WITHOUT_RL.md) separate existing experimental
ranking from proposed case-based feedback/retrieval and later trained policies.
