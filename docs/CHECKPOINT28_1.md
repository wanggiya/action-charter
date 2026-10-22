# Checkpoint 28.1 — optional bounded text capability pilot

Implementation: 2026-10-20. Operator acceptance and actual-model findings are
recorded below; implementation does not establish general code-generation or
model reliability. Preserve the original [acquisition design](OPTIONAL_CAPABILITY_ACQUISITION_PLAN.md).

## Delivered structure

Planner remains the task coordinator. When this chat's **Acquire capabilities**
switch is ON, its closed reply schema can propose a `capability_request` containing
an explanation and text definition. There is no new Builder model or agent
container. The proposal does not become a workflow step before installation.

`capabilities/text.py` implements one finite CSV adapter language: strip, uppercase,
lowercase, collapse whitespace and literal replacement, at most five steps. One
ASCII identifier source column produces one NEW column; original columns and row
order remain. Empty CSV fields remain missing; a transform producing an empty
field follows that existing CSV missing-value convention. Regex, Python, SQL,
imports, arbitrary functions, dependency installation and column replacement are
not supported. This creates a reusable executable adapter definition within a
trusted family; it is not arbitrary generated Python. The broader Python isolation
milestone remains future work.

`capabilities/service.py` owns candidate construction, exact hashes, private
attempt receipts and promotion. Backend-owned fixtures contain synthetic values,
not user rows. A separate worker supplies held-out Unicode, whitespace, null,
identifier and code-like literal cases. A scalar implementation independently
checks the pandas implementation. Wrong transformed values, changed originals,
overwrite, unsafe paths, disabled writes and unexpected outputs are checked.
A failed candidate never enters the operation registry.

`capabilities/testing.py` launches the fixed worker with `-I -B`, a scrubbed
environment and one BLAS thread. Linux limits: 10 CPU seconds, 2 GiB virtual address
space, 1 MiB per file, 64 open files, process/thread limit 16, and at most 20 seconds
wall time (shorter when the turn deadline has less remaining). Definitions are data,
not executable code; the worker exposes no network or arbitrary filesystem
primitives to definitions. **This is not an OS sandbox for arbitrary Python.**
Non-Linux acquisition testing refuses instead of using an unrestricted fallback.
No browser profile/cache, dependency or container is installed by this feature.

Critic uses its existing validated read-only role in one separate structured
request, capped at 15 seconds. It assesses applicability to the original request
and synthetic evidence. `needs_review`/`not_suitable` blocks eligibility. A timeout
is explicitly `unavailable`, not a successful assessment; deterministic tests can
still produce a reviewable candidate, with that limitation visible before explicit
installation. Critic cannot override failed tests or authorize execution.

## Lifecycle and authority

1. OFF by default for each new chat. ON persists in that chat across refresh.
   Opening a chat/configuring the switch makes no model/test call. The UI prevents configuration/chat changes while a turn is active; in-flight candidate cancellation is not part of this pilot.
2. Existing registered operations and recipes are considered first. A normal
   supported request adds zero candidate batches or Critic calls. An exact
   compatible installed definition is reused without acquisition tests.
3. A candidate receives an immutable private receipt bound to conversation,
   revision, definition/package hash, tests and Critic status. Failed preparations
   retain a private failure/budget receipt without committing a workflow revision.
4. **Install and update workflow** explicitly confirms the exact eligible digest,
   repeats tests and uses the existing atomic package installer. Public package
   metadata includes the fixed definition and synthetic fixtures, not the private
   transcript, original input filename, Critic note or authority.
5. The UI then asks Planner for the ordinary full workflow using the registered
   operation. No user-written JSON is required. Failed replanning leaves the saved
   workflow intact and the installed operation remains available.
6. Allow writes, exact Authorize and Execute remain separate. Runtime checks the
   package digest and source lineage. CSV output is create-only and independently
   verified against its original source and installed definition. It can feed
   later CSV operations through a validated ancestor `source_step`.

Turning OFF or changing the chat invalidates pending installation scope; accepted
operations persist. New chats inherit no private candidate/memory but can use
explicitly installed project-visible operations with compatible contracts.
Legacy projection manifests retain their canonical hashes and dispatch path.
The existing explicit package installer is a separate operator action, not a tool
Planner can invoke by generated text.

## Quantitative limits

A Planner turn retains at most four model calls, two discovery calls and one
candidate fixture batch. Initial response plus one structural correction is the
candidate-proposal ceiling; there is no unbounded regeneration. A batch contains
multiple cases; its cases are reported separately from the tool-call count. Critic
and failed calls consume the same model budget. ON turns have a 180-second ceiling
(or a smaller configured deadline); late results cannot update the workflow.
Explicit promotion retests are a separate operator action and return their own
fixture receipt. At most 16 private attempts per chat / 128 per project, and 20
installed packages. Tests/dependencies are pinned to pandas 3.0.5; installation
never installs that dependency.

The UI and CLI share `conversation_turn`, candidate and package services:
`capability-acquisition`, `planning-conversation-turn`,
`planning-conversation-read`, `capability-attempts`, `install-chat-capability`,
normal workflow commands and the existing package commands. CLI installation
requires explicit confirmation and the exact candidate/conversation revision.

## Acceptance and evaluation

Required checks: OFF isolation, ON persistence, zero unnecessary acquisition,
failed/unsafe candidate rejection, exact/stale/cross-chat promotion checks, private
receipt integrity, legacy hash compatibility, no authority on install, independent
runtime values, downstream CSV lineage and a complete UI authorization journey.

The actual-model driver `scripts/checkpoint28_acquisition_evaluation.py` operates
only on temporary synthetic CSV files. Its declared threshold is no registration
with OFF, correct ON output with at most five model calls in the ON phase, and
correct changed-input reuse with acquisition OFF and no candidate regeneration.
Report elapsed time/calls/tokens, failures and Critic status. This is capability
correctness, not proof of net speedup or a human-effort baseline. Its
`--prepare-only` mode diagnoses candidate preparation and cannot establish full
workflow acceptance. Reports live in `/tmp`; source data and temporary authority
are removed. No live database/service mutation is permitted.

## Follow-on checkpoints

Finish this bounded pilot's acceptance before 28.2. Learning/RL, Ollama weight
updates, broader renderer/CRS/database-map work (28.3), private domain knowledge
(29), and cross-chat memory (30+) are not implemented here. Packaging remains
sequenced after the agreed demo/data gates. General generated Python requires a
separately validated OS isolation boundary and adapter family; a subprocess and
this data-only interpreter do not establish that boundary.

## Actual-model record — 2026-10-20

Local `qwen3:4b-instruct`, reasoning_effort=none, 120-second per-request setting and 1,024 output tokens; the acquisition turn itself is capped at 180 seconds. All projects/data/decisions were temporary. The declared functional threshold passed in `/tmp/actioncharter-checkpoint28-acquisition-contract-bound.json`:

| Phase | Result | Model calls | Model-call time |
|---|---|---:|---:|
| OFF | Explains unsupported text work; no candidate/registration | 1 | 11.207 s |
| ON preparation | Correct strip→upper definition; synthetic/held-out/effect tests; Critic suitable | 2 | 31.275 s |
| ON installed workflow | Fresh exact authorization; correct 3-row output with original IDs/columns | 1 | 45.657 s |
| New-chat OFF reuse | Same installed adapter, changed input, fresh authority/output; correct 2-row result | 1 | 66.896 s |

Five calls total, 155.035 seconds of model-call time (not end-to-end wall time), zero correction/discovery calls in the final profile. ON used three model calls against the declared ceiling of five. Candidate preparation recorded one fixture batch and two model calls in its shared budget. Promotion separately repeated tests. Prompt tokens totaled 23,290; completion tokens 1,230. The Critic's suitability/limitations remain unvalidated commentary and can mischaracterize evidence; deterministic source/result checks are authoritative. This is one successful synthetic trial, not general-model reliability, net effort savings or a comparison to a human baseline. No Ollama weights changed.

Earlier attempts are retained rather than omitted: the first full trial failed before tests with an invalid workflow; diagnostic output placed text steps inside numeric CalculateColumns; a gap-decoder development error made zero model calls and was corrected by plain/branched-schema tests; an unconstrained gap reply asked/explained instead of preparing; explicit candidate constraints then passed a preparation-only trial (two calls, about 29.7 s); the next full trial prepared/installed correctly but selected an incompatible inspection operation during replanning. Narrow, independently validated catalogue/input bindings now prevent those substitutions for this explicit simple task. More complex tasks keep the general planning path and may still fail model validation.

The narrow gap classifier recognizes explicit CSV text instructions and negations; it is not a general semantic oracle. For an explicit nonambiguous `uppercase/lowercase <source> into a new <output> column` request, an optional strip plus case conversion can be bound from the user’s literal facts. It does not synthesize an executable fallback plan. Exact matching installed contracts with one declared CSV source and a simple inspection/transform request get a typed two-step decoder and source/dependency checks. Additional filtering/joining/grouping/conversion requests keep general composition. Conflicting or incomplete semantics retain clarification rather than silent inference. Deadlines bound acceptance/waiting, not a claim that the external Ollama process is forcibly terminated.

Final verification: `make test` passed 1,866 tests; the subsequent bounded package-name adjustment and all 31 acquisition-specific tests passed. `make interface-validate` passed with the existing bundle-size warning. The 17-case Results browser regression and six-case acquisition journey passed with no page errors. Shell syntax, Python compilation and `git diff --check` passed. Tests used temporary fixtures; no live database/service data, Git publication or dependency installation was performed. Operator interface acceptance remains the next step.
