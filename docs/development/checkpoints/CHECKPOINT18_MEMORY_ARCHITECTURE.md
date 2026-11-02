# Checkpoint 18 task-history and context architecture

ActionCharter will not implement long-term continuity as an autonomous agent
that silently remembers arbitrary conversation. It will first build governed,
inspectable task history and deterministic context assembly.

## Authority chain

1. **Task history** appends immutable events from the user, agents, execution,
   validation, and evidence services.
2. **Context assembly** selects a bounded and redacted subset using explicit
   task identity, event types, artifact relationships, recency, and size rules.
3. **Context Curator** may create a referenced summary when source records do
   not fit, but the summary never replaces those records.
4. **Intent Agent** receives the reviewed context package and proposes a goal-
   level process or clarification question.
5. **Planner** maps reviewed intent to implemented capabilities and typed
   arguments.
6. Existing deterministic policy, approval, execution, validation, Critic,
   release, and evidence boundaries remain authoritative.

## Task-history event contract

Every event should include:

- schema version, task ID, event ID, timestamp, and event type;
- source identity: user, Intent Agent, Planner, Executor, Critic, or system;
- immutable content digest and references to related events or artifacts;
- sensitivity and redaction classification;
- bounded display summary plus a reference to authoritative content;
- explicit authority flags showing that history itself grants no approval or
  execution permission.

Initial event types should cover requests, clarifications, selected inputs,
intent proposals, plans, human decisions, executions, validations, failures,
retries, outcomes, and unresolved questions.

## Context-package contract

A context package should record:

- task identity and the operator's current request;
- selected source event IDs and artifact digests;
- deterministic selection reasons;
- omitted-event counts and truncation warnings;
- redactions and sensitivity rules applied;
- exact character or token budget;
- derived summaries with references to their source ranges; and
- a canonical package digest.

The interface must show the operator what the Intent Agent will receive. A
model must not search unrelated tasks, secrets, raw evidence directories, or
unbounded conversation history.

## Failure behavior

- Missing or contradictory source records fail closed.
- A summary without resolvable sources is rejected.
- Context overflow produces a visible bounded-package warning rather than
  silently dropping recent authority or validation findings.
- Model output cannot modify history, approve work, or execute tools.
- Retrying an Intent Agent call records a new derived event and preserves the
  previous result.

## Sequence

- **Checkpoint 21:** implement storage, inventory, context selection, redaction, digest,
  and read-only interface timeline without a model call.
- **Checkpoint 22:** add the Context Curator and Intent Agent on top of the accepted Checkpoint 21
  contract, followed by review before Planner handoff.
