# Optional capability acquisition — checkpoint 28.1

Operator decision recorded 2026-10-19. **Original design; not implemented by this document.**
The bounded data-only text pilot is now implemented separately: [28.1 delivery and acceptance](CHECKPOINT28_1.md). General generated Python, RL and memory remain outside that pilot. This refines [the delivery plan](POST_CALCULATION_DELIVERY_PLAN.md)
without renumbering checkpoints or changing historical implementation records.

## Purpose and activation

Acquisition fills a demonstrated gap in executable operations. Workflow
composition combines existing operations; recipes reuse compatible sequences;
memory recalls methods and domain facts. None of those alone implements a new
executable operation. Acquisition should save effort when those existing paths
cannot reasonably satisfy the task, rather than add work to every request.

- OFF by default. Planner checks registered operations and eligible recipes first.
- Enable explicitly for the current conversation/task. New chats start OFF;
  opening a chat must not start generation, tests or a model call automatically.
- Size or complexity alone is not a trigger. A large workflow may need no new
  operation; a small specialist calculation may expose a real capability gap.
- OFF preserves normal planning/reuse. Missing functionality is explained without
  generating code, silently enabling acquisition or repeatedly retrying it.
- ON permits bounded candidate preparation and isolated synthetic testing only
  after the gap is identified. If existing functionality suffices, acquisition
  adds zero candidate-generation calls or fixture runs.
- Reuse an installed compatible operation instead of regenerating it. An accepted
  version persists in the project registry across restarts. Installation previews
  its project-visible metadata; it must not copy private transcripts, credentials,
  task-specific domain memory or execution authority into that metadata.

## Proposed responsibility and implementation

1. **Planner:** describe the gap and expected data contract; search existing
   options; propose a candidate through one restricted calculation/transform
   adapter family. No separate Builder reasoning agent is required.
2. **Backend candidate service:** enforce a shared request budget, typed inputs,
   outputs/effects and the established isolation boundary. Do not expose arbitrary
   Python, shell, unrestricted library calls or automatic dependency installation.
3. **Test service:** run synthetic fixtures, independent held-out cases, negative
   cases and effect checks. Record failures as well as passes with exact candidate
   and dependency versions. Tests must not contact live databases/services.
4. **Critic:** assess recorded test evidence, applicability and limitations. Its
   opinion cannot turn a failed deterministic check into a passing check.
5. **Registry/install service:** explicitly accept/promote only the tested exact
   candidate, record provenance and expose its typed operation through the shared
   planner, graph, execution and CLI contracts. Keep failed candidates unavailable.

The user describes the task rather than writes an adapter definition. Routine
retrieval, candidate construction, fixture preparation and technical repair should
be automatic within the budget. Consequential installation and execution decisions
remain explicit and should be presented compactly, without repeated bookkeeping.

## Bounds and authority

Use one initial candidate plus at most one repair, then stop with an explanation.
This is a proposed ceiling, not a delivered or laptop-calibrated setting. Count
all model calls, discovery calls, fixture batches, failures and repairs across
roles; record elapsed time and actual token usage when available. Tokens alone
cannot bound computation. Set and enforce model deadlines, test wall/CPU time,
memory, process, filesystem/output and network limits before enabling the pilot.
Do not treat missing isolation or an exhausted budget as permission to fall back
to unrestricted execution. Explain what failed and retain the existing workflow.

Acquisition ON is distinct from dependency installation, accepting a registered
operation, allowing writes, exact workflow authorization and Execute. The
acquisition switch grants none of those permissions. Turning it OFF stops new
candidate work at a supported boundary; it does not uninstall accepted operations
or interrupt a separately authorized workflow. No automatic repeated data writes.
Historical/model text never grants authority. Cross-chat memory remains deferred.

## Measurable acceptance and delivery position

- OFF and an ON task satisfied by existing operations both make zero acquisition
  calls/tests and register nothing. New-chat isolation and refresh are tested.
- One genuinely missing bounded operation passes fixtures and held-out checks,
  is explicitly installed once, survives restart and is reused without generation.
- Unsafe/failing candidates never enter the executable catalog. Budget exhaustion
  stops the attempt, reports its consumed budget and preserves the saved workflow.
- Installation does not enable writes or reuse old approvals. The installed
  operation still needs its declared effects, validation and execution authority.
- Compare acquisition OFF/ON on fixed synthetic tasks. Report completion rate,
  correctness, elapsed time, model calls/tokens, tests and human interventions,
  including failures. Predeclare the improvement threshold before evaluating;
  retain the baseline and report no benefit if acquisition adds cost without gain.

Finish checkpoint 27 interaction/evidence/evaluation work first. Then implement
and validate optional 28.1 acquisition, 28.2 learning-policy evaluation and 29
private domain memory before demo/real-data acceptance, as previously requested.
Optional runtime use does not remove the pre-demo implementation/validation gate.
One small acquisition example is sufficient for the bounded pilot; ordinary demo
journeys may keep acquisition OFF. No RL/model-weight training or advanced memory
implementation is implied here. Cross-chat decisions remain checkpoint 30+.
